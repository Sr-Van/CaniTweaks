"""Implementação real do TweakPort baseada no catálogo declarativo de operações."""
import logging
import threading
from typing import Dict, List

from app.adapters.catalog.context import CatalogEntry
from app.adapters.errors import SystemOperationError
from app.adapters.operations.base import SystemOperation
from app.adapters.state_backup import JsonStateBackup
from app.domain.entities import Tweak
from app.domain.enums import TweakKind, TweakStatus
from app.domain.result import Result
from app.ports.tweak_port import TweakPort

logger = logging.getLogger(__name__)


class CatalogTweakAdapter(TweakPort):
    """Aplica, reverte e consulta tweaks executando as operações declaradas no catálogo.

    - Aplicação atômica: se uma operação falha, as anteriores são desfeitas.
    - Reversão fiel: restaura o estado salvo antes da aplicação (ou o padrão do Windows).
    """

    def __init__(self, entries: List[CatalogEntry], backup: JsonStateBackup, windows_build: int):
        self._entries: Dict[str, CatalogEntry] = {entry.tweak.id: entry for entry in entries}
        self._backup = backup
        self._windows_build = windows_build
        self._lock = threading.RLock()  # Serializa escritas no sistema e no arquivo de backup.

    def get_all_tweaks(self) -> List[Tweak]:
        return [entry.tweak for entry in self._entries.values()]

    def check_status(self, tweak_id: str) -> TweakStatus:
        entry = self._entries.get(tweak_id)
        if entry is None:
            return TweakStatus.UNKNOWN
        if not self._is_supported(entry.tweak):
            return TweakStatus.UNSUPPORTED
        if entry.tweak.kind == TweakKind.ACTION:
            return TweakStatus.INACTIVE
        try:
            applied = all(operation.is_applied() for operation in entry.operations)
        except (SystemOperationError, OSError) as exc:
            logger.warning("Não foi possível verificar '%s': %s", tweak_id, exc)
            return TweakStatus.UNKNOWN
        return TweakStatus.ACTIVE if applied else TweakStatus.INACTIVE

    def apply(self, tweak_id: str) -> Result:
        entry = self._entries.get(tweak_id)
        if entry is None:
            return Result.failure(f"Tweak desconhecido: {tweak_id}")
        if not self._is_supported(entry.tweak):
            return Result.failure("Indisponível nesta versão do Windows.")
        with self._lock:
            try:
                if entry.tweak.kind == TweakKind.ACTION:
                    return self._run_action(entry)
                return self._apply_toggle(entry)
            except (SystemOperationError, OSError) as exc:
                logger.error("Falha ao aplicar '%s': %s", tweak_id, exc)
                return Result.failure(str(exc))

    def revert(self, tweak_id: str) -> Result:
        entry = self._entries.get(tweak_id)
        if entry is None:
            return Result.failure(f"Tweak desconhecido: {tweak_id}")
        if entry.tweak.kind == TweakKind.ACTION:
            return Result.failure("Esta ação é pontual e não pode ser revertida.")
        with self._lock:
            try:
                return self._revert_toggle(entry)
            except OSError as exc:  # Falha ao gravar/remover o arquivo de backup.
                logger.error("Falha ao reverter '%s': %s", tweak_id, exc)
                return Result.failure(str(exc))

    # --- Execução de ações pontuais ---------------------------------------------------------

    @staticmethod
    def _run_action(entry: CatalogEntry) -> Result:
        message = entry.action.run()
        return Result.success(message)

    # --- Aplicação de ajustes reversíveis ---------------------------------------------------

    def _apply_toggle(self, entry: CatalogEntry) -> Result:
        tweak = entry.tweak
        saved_backup = self._save_backup_if_needed(entry)

        completed: List[SystemOperation] = []
        try:
            for operation in entry.operations:
                operation.apply()
                completed.append(operation)
        except SystemOperationError:
            self._rollback(completed, tweak.id)
            if saved_backup:
                self._backup.delete(tweak.id)
            raise
        return Result.success(needs_restart=tweak.requires_restart)

    def _save_backup_if_needed(self, entry: CatalogEntry) -> bool:
        """Guarda o estado original do usuário. Retorna True se um novo backup foi criado.

        Não sobrescreve um backup existente (o original já está guardado) nem cria backup
        quando o tweak já estava aplicado fora do app (reverter usará o padrão do Windows).
        """
        tweak_id = entry.tweak.id
        if self._backup.get(tweak_id) is not None:
            return False
        if all(operation.is_applied() for operation in entry.operations):
            return False
        snapshots = {operation.key: operation.snapshot() for operation in entry.operations}
        self._backup.save(tweak_id, snapshots)
        return True

    def _rollback(self, completed: List[SystemOperation], tweak_id: str) -> None:
        """Desfaz, em ordem inversa, as operações já concluídas após uma falha."""
        saved = self._backup.get(tweak_id) or {}
        for operation in reversed(completed):
            try:
                if operation.key in saved:
                    operation.restore(saved[operation.key])
                else:
                    operation.reset_to_default()
            except SystemOperationError:
                logger.exception("Falha ao desfazer '%s' de %s", operation.key, tweak_id)

    # --- Reversão ---------------------------------------------------------------------------

    def _revert_toggle(self, entry: CatalogEntry) -> Result:
        tweak = entry.tweak
        saved = self._backup.get(tweak.id) or {}
        errors: List[str] = []

        for operation in entry.operations:
            try:
                if operation.key in saved:
                    operation.restore(saved[operation.key])
                else:
                    operation.reset_to_default()
            except SystemOperationError as exc:
                logger.error("Falha ao reverter '%s' (%s): %s", tweak.id, operation.key, exc)
                errors.append(str(exc))

        if errors:
            return Result.failure("; ".join(errors))
        self._backup.delete(tweak.id)
        return Result.success(needs_restart=tweak.requires_restart)

    def _is_supported(self, tweak: Tweak) -> bool:
        return self._windows_build >= tweak.min_windows_build

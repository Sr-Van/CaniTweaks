"""Caso de uso: consulta e execução individual de tweaks."""
import logging
import unicodedata
from typing import Dict, List, Optional

from app.domain.entities import Tweak
from app.domain.enums import TweakCategory, TweakStatus
from app.domain.result import Result
from app.ports.tweak_port import TweakPort

logger = logging.getLogger(__name__)


def _normalize(text: str) -> str:
    """Minúsculas e sem acentos, para busca tolerante (ex.: 'latencia' encontra 'Latência')."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


class TweakManager:
    """Orquestra a listagem, busca, consulta de estado e execução de tweaks."""

    def __init__(self, port: TweakPort):
        self._port = port

    def get_tweaks(self, category: TweakCategory = TweakCategory.ALL, query: str = "") -> List[Tweak]:
        """Lista tweaks filtrando por categoria e por texto (nome, resumo ou detalhe técnico)."""
        tweaks = self._port.get_all_tweaks()
        if category != TweakCategory.ALL:
            tweaks = [tweak for tweak in tweaks if tweak.category == category]
        needle = _normalize(query.strip())
        if needle:
            tweaks = [tweak for tweak in tweaks if needle in self._searchable_text(tweak)]
        return tweaks

    def get_tweak(self, tweak_id: str) -> Optional[Tweak]:
        return next((tweak for tweak in self._port.get_all_tweaks() if tweak.id == tweak_id), None)

    def get_status(self, tweak_id: str) -> TweakStatus:
        return self._port.check_status(tweak_id)

    def get_statuses(self) -> Dict[str, TweakStatus]:
        """Consulta o estado real de todos os tweaks (operação potencialmente lenta)."""
        return {tweak.id: self._port.check_status(tweak.id) for tweak in self._port.get_all_tweaks()}

    def apply_tweak(self, tweak_id: str) -> Result:
        return self._safe_call(self._port.apply, tweak_id)

    def revert_tweak(self, tweak_id: str) -> Result:
        return self._safe_call(self._port.revert, tweak_id)

    @staticmethod
    def _safe_call(operation, tweak_id: str) -> Result:
        """Garante que falhas inesperadas do adapter virem Result.failure e sejam registradas."""
        try:
            return operation(tweak_id)
        except Exception as exc:  # noqa: BLE001 - fronteira de segurança com a infraestrutura
            logger.exception("Erro inesperado no tweak %s", tweak_id)
            return Result.failure(f"Erro inesperado: {exc}")

    @staticmethod
    def _searchable_text(tweak: Tweak) -> str:
        return _normalize(f"{tweak.name} {tweak.summary} {tweak.technical_detail}")

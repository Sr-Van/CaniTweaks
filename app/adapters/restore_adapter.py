"""Adaptador de Ponto de Restauração do Windows via PowerShell."""
import logging

from app.adapters.errors import SystemOperationError
from app.adapters.process_runner import CommandRunner
from app.domain.result import Result
from app.ports.restore_port import RestorePointPort

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 180


class SystemRestoreAdapter(RestorePointPort):
    """Cria pontos de restauração com Checkpoint-Computer."""

    def __init__(self, runner: CommandRunner):
        self._runner = runner

    def create_restore_point(self, description: str) -> Result:
        # O Windows limita a um ponto por 24h por padrão; nesse caso o comando só avisa e retorna 0.
        safe_description = description.replace("'", "''")
        script = (
            "Enable-ComputerRestore -Drive ($env:SystemDrive + '\\'); "
            f"Checkpoint-Computer -Description '{safe_description}' -RestorePointType MODIFY_SETTINGS"
        )
        try:
            result = self._runner.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", script],
                timeout=_TIMEOUT_SECONDS,
            )
        except SystemOperationError as exc:
            return Result.failure(str(exc))

        if not result.ok:
            logger.warning("Falha ao criar ponto de restauração: %s", result.output)
            return Result.failure(result.output or "Não foi possível criar o ponto de restauração.")
        return Result.success("Ponto de restauração criado.")

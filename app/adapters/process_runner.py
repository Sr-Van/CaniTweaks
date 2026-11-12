"""Execução de comandos externos (sc, powercfg, shutdown, powershell)."""
import logging
import subprocess
from dataclasses import dataclass
from typing import Sequence

from app.adapters.errors import SystemOperationError

logger = logging.getLogger(__name__)

_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


@dataclass(frozen=True)
class CommandResult:
    """Saída de um comando externo."""

    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0

    @property
    def output(self) -> str:
        """Melhor texto disponível para exibir em mensagens de erro."""
        return (self.stderr or self.stdout).strip()


class CommandRunner:
    """Executa comandos sem abrir janelas de console e com decodificação OEM."""

    def run(self, args: Sequence[str], timeout: float = 60) -> CommandResult:
        logger.debug("Executando comando: %s", list(args))
        try:
            completed = subprocess.run(
                list(args),
                capture_output=True,
                text=True,
                encoding="oem",
                errors="replace",
                timeout=timeout,
                creationflags=_NO_WINDOW,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SystemOperationError(f"Falha ao executar '{args[0]}': {exc}") from exc
        return CommandResult(completed.returncode, completed.stdout or "", completed.stderr or "")

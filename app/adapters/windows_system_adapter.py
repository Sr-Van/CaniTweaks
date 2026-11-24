"""Adaptador do SystemPort: informações do Windows, reinício e elevação."""
import sys

from app.adapters import uac_helper
from app.adapters.errors import SystemOperationError
from app.adapters.process_runner import CommandRunner
from app.domain.entities import SystemInfo
from app.domain.result import Result
from app.ports.system_port import SystemPort

_WINDOWS_11_FIRST_BUILD = 22000
_RESTART_REASON = "CaniTweaks: reinício necessário para concluir as otimizações."


class WindowsSystemAdapter(SystemPort):
    """Implementação do SystemPort para Windows."""

    def __init__(self, runner: CommandRunner):
        self._runner = runner

    def get_info(self) -> SystemInfo:
        build = sys.getwindowsversion().build
        family = "Windows 11" if build >= _WINDOWS_11_FIRST_BUILD else "Windows 10"
        return SystemInfo(
            is_admin=uac_helper.is_admin(),
            windows_label=f"{family} (build {build})",
            windows_build=build,
        )

    def restart_computer(self, delay_seconds: int) -> Result:
        return self._run_shutdown(["/r", "/t", str(delay_seconds), "/c", _RESTART_REASON])

    def cancel_restart(self) -> Result:
        return self._run_shutdown(["/a"])

    def relaunch_as_admin(self) -> bool:
        return uac_helper.relaunch_as_admin()

    def _run_shutdown(self, arguments: list) -> Result:
        try:
            result = self._runner.run(["shutdown", *arguments])
        except SystemOperationError as exc:
            return Result.failure(str(exc))
        if not result.ok:
            return Result.failure(result.output or "O comando shutdown falhou.")
        return Result.success()

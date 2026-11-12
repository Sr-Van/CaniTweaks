"""Caso de uso: informações do ambiente, reinício e elevação de privilégios."""
from app.domain.entities import SystemInfo
from app.domain.result import Result
from app.ports.system_port import SystemPort

RESTART_DELAY_SECONDS = 15


class SystemService:
    """Fachada sobre o SystemPort para a camada de apresentação."""

    def __init__(self, port: SystemPort):
        self._port = port

    def get_info(self) -> SystemInfo:
        return self._port.get_info()

    def restart_computer(self) -> Result:
        """Agenda o reinício com um intervalo que permite cancelar."""
        return self._port.restart_computer(RESTART_DELAY_SECONDS)

    def cancel_restart(self) -> Result:
        return self._port.cancel_restart()

    def relaunch_as_admin(self) -> bool:
        return self._port.relaunch_as_admin()

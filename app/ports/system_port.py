"""Contrato (Port) para informações e controle do sistema operacional."""
from abc import ABC, abstractmethod

from app.domain.entities import SystemInfo
from app.domain.result import Result


class SystemPort(ABC):
    """Interface para consultar o ambiente e controlar reinício/elevação."""

    @abstractmethod
    def get_info(self) -> SystemInfo:
        """Retorna privilégios, versão e build do Windows."""

    @abstractmethod
    def restart_computer(self, delay_seconds: int) -> Result:
        """Agenda o reinício do computador após o atraso informado."""

    @abstractmethod
    def cancel_restart(self) -> Result:
        """Cancela um reinício agendado."""

    @abstractmethod
    def relaunch_as_admin(self) -> bool:
        """Reabre o aplicativo com privilégios de administrador. True se a elevação foi aceita."""

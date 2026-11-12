"""Contrato (Port) para criação de Ponto de Restauração do Windows."""
from abc import ABC, abstractmethod

from app.domain.result import Result


class RestorePointPort(ABC):
    """Interface para criar pontos de restauração antes de alterações em lote."""

    @abstractmethod
    def create_restore_point(self, description: str) -> Result:
        """Cria um ponto de restauração com a descrição informada."""

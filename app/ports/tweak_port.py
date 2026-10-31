"""Contrato (Port) para operações de execução e consulta de Tweaks."""
from abc import ABC, abstractmethod
from typing import List
from app.domain.entities import Tweak
from app.domain.enums import TweakStatus


class TweakPort(ABC):
    """Interface abstrata para manipulação e consulta de tweaks."""

    @abstractmethod
    def get_all_tweaks(self) -> List[Tweak]:
        """Retorna todos os tweaks disponíveis no catálogo."""
        pass

    @abstractmethod
    def check_status(self, tweak_id: str) -> TweakStatus:
        """Verifica o estado real do tweak no sistema operacional."""
        pass

    @abstractmethod
    def apply(self, tweak_id: str) -> bool:
        """Aplica a otimização no sistema."""
        pass

    @abstractmethod
    def revert(self, tweak_id: str) -> bool:
        """Reverte a otimização para o padrão do Windows."""
        pass

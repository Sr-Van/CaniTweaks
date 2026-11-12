"""Contrato (Port) para consulta e execução de Tweaks."""
from abc import ABC, abstractmethod
from typing import List

from app.domain.entities import Tweak
from app.domain.enums import TweakStatus
from app.domain.result import Result


class TweakPort(ABC):
    """Interface abstrata para manipulação e consulta de tweaks."""

    @abstractmethod
    def get_all_tweaks(self) -> List[Tweak]:
        """Retorna todos os tweaks disponíveis no catálogo."""

    @abstractmethod
    def check_status(self, tweak_id: str) -> TweakStatus:
        """Verifica o estado real do tweak no sistema operacional."""

    @abstractmethod
    def apply(self, tweak_id: str) -> Result:
        """Aplica a otimização (ou executa a ação) no sistema. Nunca levanta exceção."""

    @abstractmethod
    def revert(self, tweak_id: str) -> Result:
        """Reverte a otimização ao estado original do usuário. Nunca levanta exceção."""

"""Contratos das operações atômicas que compõem um tweak."""
from abc import ABC, abstractmethod
from typing import Any


class SystemOperation(ABC):
    """Uma alteração reversível no sistema (valor de registro, serviço, plano de energia...).

    Um tweak do tipo TOGGLE é composto por uma ou mais operações. Todas as falhas devem
    ser sinalizadas com SystemOperationError.
    """

    @property
    @abstractmethod
    def key(self) -> str:
        """Identificador estável dentro do tweak, usado como chave no backup."""

    @abstractmethod
    def is_applied(self) -> bool:
        """Indica se o sistema já está no estado otimizado."""

    @abstractmethod
    def snapshot(self) -> Any:
        """Captura o estado atual (serializável em JSON) para restauração futura."""

    @abstractmethod
    def apply(self) -> None:
        """Aplica a otimização."""

    @abstractmethod
    def restore(self, snapshot: Any) -> None:
        """Restaura o estado capturado por `snapshot`."""

    @abstractmethod
    def reset_to_default(self) -> None:
        """Volta ao padrão do Windows quando não há backup do usuário."""


class ActionOperation(ABC):
    """Ação pontual e irreversível (ex.: limpeza de disco)."""

    @abstractmethod
    def run(self) -> str:
        """Executa a ação e retorna uma mensagem de resumo para o usuário."""

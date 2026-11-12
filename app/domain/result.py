"""Resultado padronizado das operações do sistema."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Result:
    """Resultado de uma operação: sucesso/falha, mensagem e necessidade de reinício."""

    ok: bool
    error: str = ""
    message: str = ""
    needs_restart: bool = False

    @classmethod
    def success(cls, message: str = "", needs_restart: bool = False) -> "Result":
        return cls(ok=True, message=message, needs_restart=needs_restart)

    @classmethod
    def failure(cls, error: str) -> "Result":
        return cls(ok=False, error=error)

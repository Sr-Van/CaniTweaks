"""Erros levantados pelos adapters ao interagir com o sistema operacional."""


class SystemOperationError(Exception):
    """Falha ao ler ou alterar o sistema. A mensagem é voltada ao usuário (PT-BR)."""

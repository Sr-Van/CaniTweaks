"""Ação pontual de limpeza de diretórios."""
from typing import Sequence

from app.adapters.disk_clean_adapter import DiskCleanAdapter
from app.adapters.operations.base import ActionOperation
from app.domain.formatting import format_bytes


class CleanDirectoriesAction(ActionOperation):
    """Esvazia diretórios e informa o espaço liberado."""

    def __init__(self, cleaner: DiskCleanAdapter, directories: Sequence[str]):
        self._cleaner = cleaner
        self._directories = directories

    def run(self) -> str:
        summary = self._cleaner.clean(self._directories)
        message = f"{format_bytes(summary.freed_bytes)} liberados"
        if summary.failed_files:
            message += f" ({summary.failed_files} itens em uso foram ignorados)"
        return message

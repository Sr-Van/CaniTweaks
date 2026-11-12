"""Adaptador de limpeza segura de diretórios, contabilizando o espaço liberado."""
import logging
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Tuple

logger = logging.getLogger(__name__)

# Evita apagar raízes de disco ou pastas de topo por engano (ex.: "C:\" ou "C:\Windows").
_MIN_PATH_DEPTH = 3


@dataclass(frozen=True)
class CleanSummary:
    """Resumo de uma limpeza: bytes liberados e arquivos que não puderam ser removidos."""

    freed_bytes: int
    failed_files: int


class DiskCleanAdapter:
    """Esvazia o conteúdo de diretórios, ignorando arquivos em uso e links simbólicos."""

    def clean(self, directories: Iterable[str]) -> CleanSummary:
        freed = failed = 0
        for raw_path in directories:
            path = Path(os.path.expandvars(raw_path))
            if not self._is_safe_target(raw_path, path):
                logger.warning("Diretório ignorado por segurança: %s", raw_path)
                continue
            if not path.is_dir():
                continue
            dir_freed, dir_failed = self._empty_directory(path)
            freed += dir_freed
            failed += dir_failed
        return CleanSummary(freed, failed)

    @staticmethod
    def _is_safe_target(raw_path: str, path: Path) -> bool:
        return "%" not in str(path) and path.is_absolute() and len(path.parts) >= _MIN_PATH_DEPTH

    def _empty_directory(self, directory: Path) -> Tuple[int, int]:
        """Remove o conteúdo de `directory` (mantendo a própria pasta). Retorna (bytes, falhas)."""
        freed = failed = 0
        try:
            entries = list(os.scandir(directory))
        except OSError:
            return 0, 1

        for entry in entries:
            if self._is_link(entry):
                continue  # Nunca segue nem remove links/junções.
            if entry.is_dir(follow_symlinks=False):
                sub_freed, sub_failed = self._empty_directory(Path(entry.path))
                freed += sub_freed
                failed += sub_failed
                if not self._remove_directory(entry.path):
                    failed += 1
            else:
                size = self._remove_file(entry)
                if size is None:
                    failed += 1
                else:
                    freed += size
        return freed, failed

    @staticmethod
    def _is_link(entry: os.DirEntry) -> bool:
        is_junction = getattr(entry, "is_junction", lambda: False)
        return entry.is_symlink() or is_junction()

    @staticmethod
    def _remove_file(entry: os.DirEntry) -> Optional[int]:
        """Remove um arquivo e retorna seu tamanho, ou None se estiver em uso/protegido."""
        try:
            size = entry.stat(follow_symlinks=False).st_size
            try:
                os.remove(entry.path)
            except PermissionError:
                os.chmod(entry.path, stat.S_IWRITE)  # Arquivo somente leitura.
                os.remove(entry.path)
            return size
        except OSError:
            return None

    @staticmethod
    def _remove_directory(path: str) -> bool:
        try:
            os.rmdir(path)
            return True
        except OSError:
            return False

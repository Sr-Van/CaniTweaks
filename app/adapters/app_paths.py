"""Localização dos arquivos de dados do aplicativo (backups e logs)."""
import os
from pathlib import Path

_APP_FOLDER = "WinTweaks"


def data_directory() -> Path:
    """Retorna (criando se preciso) a pasta de dados em %LOCALAPPDATA%\\WinTweaks."""
    base = Path(os.environ.get("LOCALAPPDATA") or Path.home())
    directory = base / _APP_FOLDER
    directory.mkdir(parents=True, exist_ok=True)
    return directory

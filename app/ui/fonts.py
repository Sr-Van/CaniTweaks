"""Carrega a fonte JetBrains Mono embutida (OFL) para uso privado do processo."""
import ctypes
import logging
import sys
from pathlib import Path

import customtkinter as ctk

FONT_FAMILY = "JetBrains Mono"
_FONT_FILE = Path(__file__).resolve().parent.parent / "assets" / "fonts" / "JetBrainsMono-VariableFont_wght.ttf"
_FR_PRIVATE = 0x10

logger = logging.getLogger(__name__)


def apply_default_font() -> None:
    """Faz a fonte embutida ser a padrão de todos os widgets do customtkinter."""
    ctk.ThemeManager.theme["CTkFont"]["family"] = FONT_FAMILY


def load_bundled_fonts() -> None:
    """Registra a fonte só para este processo; se falhar, o Tk usa a fonte padrão."""
    if sys.platform != "win32" or not _FONT_FILE.exists():
        return
    try:
        ctypes.windll.gdi32.AddFontResourceExW(str(_FONT_FILE), _FR_PRIVATE, 0)
    except Exception:  # noqa: BLE001 - fonte é cosmética
        logger.warning("Não foi possível carregar a fonte embutida", exc_info=True)

"""Constantes visuais compartilhadas (cores e textos de estado)."""
from typing import Dict, Tuple

from app.domain.enums import RiskLevel, TweakStatus

# Paleta Caninana
SERPENT_BLACK = "#121212"
COBRA_YELLOW = "#F5C400"
SCALE_GOLD = "#D9A21B"

ACCENT = COBRA_YELLOW
ACCENT_HOVER = SCALE_GOLD
ON_ACCENT = SERPENT_BLACK  # texto sobre o amarelo
NEUTRAL = "#2e2e2e"
NEUTRAL_HOVER = "#3a3a3a"
DANGER = "#c0392b"
DANGER_HOVER = "#962d22"

CARD_BG = ("#2b2b2b", "#181818")
PANEL_BG = ("#232323", "#181818")
BORDER = ("#d4d4d8", "#2a2a2a")
BADGE_BG = "#262626"
BADGE_TEXT = "#bdbdbd"
SIDEBAR_BG = ("#1a1a1a", SERPENT_BLACK)
MUTED_TEXT = "#888888"
BODY_TEXT = ("#cccccc", "#a0a0a0")

COLOR_SUCCESS = "#2ecc71"
COLOR_ERROR = "#e74c3c"
COLOR_WARNING = "#f39c12"
COLOR_INFO = SCALE_GOLD

# (cor do fundo, cor do texto)
RISK_COLORS: Dict[RiskLevel, Tuple[str, str]] = {
    RiskLevel.MEDIUM: ("#7d6608", "#f9e79f"),
    RiskLevel.HIGH: ("#78281f", "#f5b7b1"),
}

# (texto exibido, cor)
STATUS_STYLE: Dict[TweakStatus, Tuple[str, str]] = {
    TweakStatus.ACTIVE: ("● Ativo", COLOR_SUCCESS),
    TweakStatus.INACTIVE: ("○ Inativo", "#95a5a6"),
    TweakStatus.PENDING: ("Processando...", COLOR_INFO),
    TweakStatus.ERROR: ("Erro", COLOR_ERROR),
    TweakStatus.UNKNOWN: ("? Desconhecido", COLOR_WARNING),
    TweakStatus.UNSUPPORTED: ("Indisponível", "#7f8c8d"),
}

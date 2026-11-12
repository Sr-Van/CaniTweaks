"""Constantes visuais compartilhadas (cores e textos de estado)."""
from typing import Dict, Tuple

from app.domain.enums import RiskLevel, TweakCategory, TweakStatus

ACCENT = "#1f6aa5"
ACCENT_HOVER = "#144870"
NEUTRAL = "#34495e"
NEUTRAL_HOVER = "#2c3e50"
DANGER = "#c0392b"
DANGER_HOVER = "#962d22"

CARD_BG = ("#2b2b2b", "#1e1e1e")
PANEL_BG = ("#232323", "#1a1a1a")
MUTED_TEXT = "#888888"
BODY_TEXT = ("#cccccc", "#a0a0a0")

COLOR_SUCCESS = "#2ecc71"
COLOR_ERROR = "#e74c3c"
COLOR_WARNING = "#f39c12"
COLOR_INFO = "#2b7de9"

CATEGORY_COLORS: Dict[TweakCategory, str] = {
    TweakCategory.LATENCY: "#2980b9",
    TweakCategory.FPS: "#8e44ad",
    TweakCategory.INPUT: "#16a085",
    TweakCategory.RAM_PROCESSES: "#d68910",
    TweakCategory.DISK_CLEANUP: "#27ae60",
}

# (cor do fundo, cor do texto)
RISK_COLORS: Dict[RiskLevel, Tuple[str, str]] = {
    RiskLevel.MEDIUM: ("#7d6608", "#f9e79f"),
    RiskLevel.HIGH: ("#78281f", "#f5b7b1"),
}

# (texto exibido, cor)
STATUS_STYLE: Dict[TweakStatus, Tuple[str, str]] = {
    TweakStatus.ACTIVE: ("● Ativo", COLOR_SUCCESS),
    TweakStatus.INACTIVE: ("○ Inativo", "#95a5a6"),
    TweakStatus.PENDING: ("⏳ Processando...", COLOR_INFO),
    TweakStatus.ERROR: ("⚠ Erro", COLOR_ERROR),
    TweakStatus.UNKNOWN: ("? Desconhecido", COLOR_WARNING),
    TweakStatus.UNSUPPORTED: ("⛔ Indisponível", "#7f8c8d"),
}

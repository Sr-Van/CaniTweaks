"""Entidades do domínio (imutáveis e sem conhecimento do sistema operacional)."""
from dataclasses import dataclass
from typing import Tuple

from app.domain.enums import RiskLevel, TweakCategory, TweakKind


@dataclass(frozen=True)
class Tweak:
    """Descreve um tweak do catálogo. O estado atual vem sempre do TweakPort."""

    id: str
    name: str
    summary: str
    category: TweakCategory
    risk: RiskLevel = RiskLevel.LOW
    kind: TweakKind = TweakKind.TOGGLE
    requires_restart: bool = False
    technical_detail: str = ""
    min_windows_build: int = 0

    @property
    def is_reversible(self) -> bool:
        return self.kind == TweakKind.TOGGLE


@dataclass(frozen=True)
class Preset:
    """Perfil pré-configurado que agrupa vários tweaks."""

    id: str
    name: str
    description: str
    tweak_ids: Tuple[str, ...]


@dataclass(frozen=True)
class SystemInfo:
    """Informações do ambiente em que o aplicativo está rodando."""

    is_admin: bool
    windows_label: str
    windows_build: int

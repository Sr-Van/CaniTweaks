"""Entidades do domínio."""
from dataclasses import dataclass
from typing import List, Optional
from app.domain.enums import TweakCategory, TweakStatus


@dataclass
class Tweak:
    """Entidade que representa um Tweak do sistema."""
    id: str
    name: str
    summary: str
    category: TweakCategory
    requires_restart: bool = False
    technical_detail: str = ""
    status: TweakStatus = TweakStatus.INACTIVE


@dataclass
class Preset:
    """Entidade que representa um Preset de otimizações."""
    id: str
    name: str
    description: str
    icon: str
    tweak_ids: List[str]

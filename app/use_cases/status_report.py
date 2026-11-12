"""Caso de uso: geração do relatório de texto com o estado das otimizações."""
from datetime import datetime
from typing import Dict, Iterable

from app.domain.entities import SystemInfo, Tweak
from app.domain.enums import TweakStatus

_STATUS_ICON = {
    TweakStatus.ACTIVE: "[x]",
    TweakStatus.INACTIVE: "[ ]",
    TweakStatus.UNSUPPORTED: "[-]",
}


def build_status_report(
    tweaks: Iterable[Tweak],
    statuses: Dict[str, TweakStatus],
    info: SystemInfo,
    generated_at: datetime,
) -> str:
    """Monta um relatório legível com o estado de cada tweak (para exportar em .txt)."""
    tweaks = list(tweaks)
    lines = [
        "WinTweaks - Relatório de otimizações",
        f"Gerado em: {generated_at:%d/%m/%Y %H:%M}",
        f"Sistema: {info.windows_label} | Administrador: {'sim' if info.is_admin else 'não'}",
        "",
    ]
    current_category = None
    for tweak in tweaks:
        if tweak.category != current_category:
            current_category = tweak.category
            lines += ["", f"== {current_category.value} =="]
        status = statuses.get(tweak.id, TweakStatus.UNKNOWN)
        icon = _STATUS_ICON.get(status, "[?]")
        lines.append(f"{icon} {tweak.name} - {status.value} (risco: {tweak.risk.value})")

    active = sum(1 for tweak in tweaks if statuses.get(tweak.id) == TweakStatus.ACTIVE)
    lines += ["", f"Total: {active} de {len(tweaks)} otimizações ativas."]
    return "\n".join(lines) + "\n"

"""Tweaks da categoria PERIFÉRICOS."""
from typing import List

from app.adapters.catalog.context import CatalogContext, CatalogEntry
from app.adapters.operations.power_operations import PowerSettingOperation
from app.domain.entities import Tweak
from app.domain.enums import TweakCategory

_MOUSE_KEY = "HKCU\\Control Panel\\Mouse"
_ACCESSIBILITY_KEY = "HKCU\\Control Panel\\Accessibility"

_USB_SUBGROUP = "2a737441-1930-4402-8d77-b2bebba308a3"
_USB_SELECTIVE_SUSPEND = "48e6b7a6-50f5-4782-a5d4-53bb8f07e226"


def build_input_entries(ctx: CatalogContext) -> List[CatalogEntry]:
    return [
        CatalogEntry(
            Tweak(
                id="disable_mouse_acceleration",
                name="Desativar Aceleração do Mouse",
                summary="Desliga a 'Precisão do ponteiro', tornando o movimento do mouse linear e "
                        "previsível para mira em jogos de tiro.",
                category=TweakCategory.INPUT,
                requires_restart=True,
                technical_detail="HKCU\\Control Panel\\Mouse: MouseSpeed/Threshold1/Threshold2 = 0 (reentrar na sessão)",
            ),
            [
                ctx.reg_sz(_MOUSE_KEY, "MouseSpeed", "0", default="1"),
                ctx.reg_sz(_MOUSE_KEY, "MouseThreshold1", "0", default="6"),
                ctx.reg_sz(_MOUSE_KEY, "MouseThreshold2", "0", default="10"),
            ],
        ),
        CatalogEntry(
            Tweak(
                id="disable_sticky_keys_prompts",
                name="Desativar Atalhos de Teclas de Aderência",
                summary="Impede o pop-up de Teclas de Aderência/Filtro ao pressionar Shift várias "
                        "vezes, que minimiza o jogo.",
                category=TweakCategory.INPUT,
                requires_restart=True,
                technical_detail="HKCU\\Control Panel\\Accessibility: Flags das teclas de acessibilidade (reentrar na sessão)",
            ),
            [
                ctx.reg_sz(f"{_ACCESSIBILITY_KEY}\\StickyKeys", "Flags", "506", default="510"),
                ctx.reg_sz(f"{_ACCESSIBILITY_KEY}\\ToggleKeys", "Flags", "58", default="62"),
                ctx.reg_sz(f"{_ACCESSIBILITY_KEY}\\Keyboard Response", "Flags", "122", default="126"),
            ],
        ),
        CatalogEntry(
            Tweak(
                id="disable_usb_selective_suspend",
                name="Desativar Suspensão Seletiva de USB",
                summary="Evita que o Windows desligue portas USB ociosas, eliminando atrasos e "
                        "desconexões momentâneas de mouse, teclado e headsets.",
                category=TweakCategory.INPUT,
                technical_detail="powercfg: USB selective suspend = Desativado (plano ativo, tomada)",
            ),
            [PowerSettingOperation(ctx.powercfg, _USB_SUBGROUP, _USB_SELECTIVE_SUSPEND, 0, default=1)],
        ),
    ]

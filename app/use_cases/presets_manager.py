"""Caso de Uso para Gerenciamento e Aplicação de Presets."""
from typing import Callable, List, Optional
from app.domain.entities import Preset, Tweak
from app.use_cases.tweak_manager import TweakManager


class PresetsManager:
    """Gerencia catálogo e aplicação de perfis pré-configurados."""

    def __init__(self, tweak_manager: TweakManager):
        self._tweak_manager = tweak_manager
        self._presets: List[Preset] = [
            Preset(
                id="competitive",
                name="Competitivo / FPS Máximo",
                description="Otimização agressiva voltada para o menor input lag e máxima estabilidade de taxa de quadros (1% lows).",
                icon="🎮",
                tweak_ids=[
                    "hags",
                    "disable_fso",
                    "network_throttling",
                    "game_mode",
                    "cpu_power_throttling",
                    "ultimate_performance",
                    "disable_game_dvr"
                ]
            ),
            Preset(
                id="balanced",
                name="Equilibrado (Gamer & Uso Geral)",
                description="Equilíbrio ideal entre fluidez em jogos e preservação dos recursos visuais e conveniências do Windows.",
                icon="⚖️",
                tweak_ids=[
                    "game_mode",
                    "ultimate_performance",
                    "disable_telemetry",
                    "disable_game_dvr"
                ]
            ),
            Preset(
                id="cleaner",
                name="Limpeza Rápida de Disco",
                description="Remove arquivos temporários residuais, caches de sistema e logs de erro acumulados sem alterar o registro.",
                icon="🧹",
                tweak_ids=[
                    "clean_temp_files",
                    "clean_prefetch_dumps"
                ]
            )
        ]

    def get_presets(self) -> List[Preset]:
        return self._presets

    def apply_preset(
        self,
        preset_id: str,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[str]:
        preset = next((p for p in self._presets if p.id == preset_id), None)
        if not preset:
            return []

        all_tweaks = self._tweak_manager.get_tweaks()
        target_tweaks = [t for t in all_tweaks if t.id in preset.tweak_ids]
        return self._tweak_manager.apply_batch(target_tweaks, progress_callback)

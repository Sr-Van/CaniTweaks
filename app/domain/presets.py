"""Catálogo de presets padrão da aplicação."""
from typing import Tuple

from app.domain.entities import Preset

DEFAULT_PRESETS: Tuple[Preset, ...] = (
    Preset(
        id="competitive",
        name="Competitivo / FPS Máximo",
        description=(
            "Otimização voltada ao menor input lag e à máxima estabilidade de quadros (1% lows) "
            "em jogos competitivos."
        ),
        icon="🎮",
        tweak_ids=(
            "hags",
            "disable_fso",
            "network_throttling",
            "disable_nagle",
            "game_mode",
            "cpu_power_throttling",
            "ultimate_performance",
            "disable_game_dvr",
            "disable_mouse_acceleration",
            "disable_sticky_keys_prompts",
        ),
    ),
    Preset(
        id="balanced",
        name="Equilibrado (Gamer & Uso Geral)",
        description=(
            "Ganho perceptível de fluidez preservando efeitos visuais, serviços multimídia "
            "e conveniências do Windows."
        ),
        icon="⚖️",
        tweak_ids=(
            "game_mode",
            "ultimate_performance",
            "disable_telemetry",
            "disable_consumer_features",
        ),
    ),
    Preset(
        id="privacy",
        name="Privacidade & Segundo Plano",
        description=(
            "Reduz coleta de dados, sugestões patrocinadas e aplicativos rodando em segundo plano, "
            "liberando RAM e rede."
        ),
        icon="🔒",
        tweak_ids=(
            "disable_telemetry",
            "disable_consumer_features",
            "disable_background_apps",
            "disable_web_search",
        ),
    ),
    Preset(
        id="cleaner",
        name="Limpeza Rápida de Disco",
        description=(
            "Remove arquivos temporários, relatórios de erro e dumps acumulados "
            "sem alterar configurações do sistema."
        ),
        icon="🧹",
        tweak_ids=(
            "clean_temp_files",
            "clean_prefetch_dumps",
        ),
    ),
)

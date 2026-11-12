"""Tweaks da categoria ESTABILIDADE DE FPS."""
from typing import List

from app.adapters.catalog.context import CatalogContext, CatalogEntry
from app.adapters.operations.power_operations import UltimatePerformancePlanOperation
from app.domain.entities import Tweak
from app.domain.enums import RiskLevel, TweakCategory


def build_fps_entries(ctx: CatalogContext) -> List[CatalogEntry]:
    return [
        CatalogEntry(
            Tweak(
                id="game_mode",
                name="Habilitar Windows Game Mode",
                summary="Prioriza CPU e GPU para o jogo em execução, evitando que tarefas em "
                        "segundo plano roubem ciclos de processamento.",
                category=TweakCategory.FPS,
                technical_detail="HKCU\\Software\\Microsoft\\GameBar: AutoGameModeEnabled = 1",
            ),
            [
                ctx.reg("HKCU\\Software\\Microsoft\\GameBar", "AutoGameModeEnabled", 1),
                ctx.reg("HKCU\\Software\\Microsoft\\GameBar", "AllowAutoGameMode", 1),
            ],
        ),
        CatalogEntry(
            Tweak(
                id="cpu_power_throttling",
                name="Desativar Power Throttling do Processador",
                summary="Impede que o Windows limite a frequência de processos para economizar "
                        "energia, melhorando a estabilidade dos 1% lows. Aumenta o consumo em notebooks.",
                category=TweakCategory.FPS,
                risk=RiskLevel.MEDIUM,
                requires_restart=True,
                technical_detail="HKLM\\...\\Power\\PowerThrottling: PowerThrottlingOff = 1",
            ),
            [ctx.reg("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Power\\PowerThrottling", "PowerThrottlingOff", 1)],
        ),
        CatalogEntry(
            Tweak(
                id="ultimate_performance",
                name="Ativar Plano 'Desempenho Máximo'",
                summary="Ativa o plano de energia oculto que mantém a CPU em prontidão máxima, "
                        "reduzindo micro-travamentos. Aumenta consumo e temperatura.",
                category=TweakCategory.FPS,
                risk=RiskLevel.MEDIUM,
                technical_detail="powercfg -duplicatescheme e9a42b02-... e ativação do plano",
            ),
            [UltimatePerformancePlanOperation(ctx.powercfg)],
        ),
        CatalogEntry(
            Tweak(
                id="disable_fast_startup",
                name="Desativar Inicialização Rápida",
                summary="Faz o desligamento completar de verdade, descarregando drivers e kernel. "
                        "Evita instabilidades acumuladas entre sessões.",
                category=TweakCategory.FPS,
                technical_detail="HKLM\\...\\Session Manager\\Power: HiberbootEnabled = 0",
            ),
            [ctx.reg("HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Power", "HiberbootEnabled", 0, default=1)],
        ),
    ]

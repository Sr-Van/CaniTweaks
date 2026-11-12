"""Tweaks da categoria RAM & PROCESSOS."""
from typing import List

from app.adapters.catalog.context import CatalogContext, CatalogEntry
from app.adapters.operations.service_operations import DisableServiceOperation
from app.domain.entities import Tweak
from app.domain.enums import RiskLevel, TweakCategory

_CONTENT_DELIVERY = "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\ContentDeliveryManager"
_BACKGROUND_APPS = "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\BackgroundAccessApplications"


def build_ram_entries(ctx: CatalogContext) -> List[CatalogEntry]:
    return [
        CatalogEntry(
            Tweak(
                id="disable_telemetry",
                name="Desativar Telemetria e Diagnósticos (DiagTrack)",
                summary="Para os serviços de coleta de dados em segundo plano, economizando RAM "
                        "(150 a 350 MB) e reduzindo a atividade de disco.",
                category=TweakCategory.RAM_PROCESSES,
                technical_detail="Serviços: DiagTrack e dmwappushservice (início = desativado)",
            ),
            [
                DisableServiceOperation(ctx.services, "DiagTrack", default_mode="auto"),
                DisableServiceOperation(ctx.services, "dmwappushservice", default_mode="demand"),
            ],
        ),
        CatalogEntry(
            Tweak(
                id="disable_game_dvr",
                name="Desativar Xbox Game DVR / Gravação em Fundo",
                summary="Desliga o buffer de captura contínua de vídeo e áudio, liberando GPU e RAM "
                        "durante os jogos.",
                category=TweakCategory.RAM_PROCESSES,
                technical_detail="GameDVR_Enabled = 0, AppCaptureEnabled = 0 e política AllowGameDVR = 0",
            ),
            [
                ctx.reg("HKCU\\System\\GameConfigStore", "GameDVR_Enabled", 0, default=1),
                ctx.reg("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR", "AppCaptureEnabled", 0, default=1),
                ctx.reg("HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\GameDVR", "AllowGameDVR", 0),
            ],
        ),
        CatalogEntry(
            Tweak(
                id="disable_consumer_features",
                name="Desativar Sugestões e Apps Patrocinados",
                summary="Impede a instalação silenciosa de apps patrocinados e as sugestões "
                        "promocionais no Menu Iniciar e nas notificações.",
                category=TweakCategory.RAM_PROCESSES,
                technical_detail="ContentDeliveryManager: SilentInstalledApps, SystemPaneSuggestions, PreInstalledApps = 0",
            ),
            [
                ctx.reg(_CONTENT_DELIVERY, "SilentInstalledAppsEnabled", 0, default=1),
                ctx.reg(_CONTENT_DELIVERY, "SystemPaneSuggestionsEnabled", 0, default=1),
                ctx.reg(_CONTENT_DELIVERY, "PreInstalledAppsEnabled", 0, default=1),
                ctx.reg(_CONTENT_DELIVERY, "OemPreInstalledAppsEnabled", 0, default=1),
            ],
        ),
        CatalogEntry(
            Tweak(
                id="disable_background_apps",
                name="Impedir Apps Universais em Segundo Plano",
                summary="Evita que apps da Microsoft Store rodem em segundo plano, liberando RAM, "
                        "CPU e rede. Apps como E-mail e Calendário deixam de sincronizar sozinhos.",
                category=TweakCategory.RAM_PROCESSES,
                risk=RiskLevel.MEDIUM,
                technical_detail="BackgroundAccessApplications: GlobalUserDisabled = 1",
            ),
            [ctx.reg(_BACKGROUND_APPS, "GlobalUserDisabled", 1, default=0)],
        ),
        CatalogEntry(
            Tweak(
                id="disable_web_search",
                name="Desativar Pesquisa na Web no Menu Iniciar",
                summary="Remove resultados do Bing da busca do Windows, tornando-a mais rápida e "
                        "reduzindo processos de pesquisa em segundo plano.",
                category=TweakCategory.RAM_PROCESSES,
                requires_restart=True,
                technical_detail="HKCU\\Software\\Policies\\Microsoft\\Windows\\Explorer: DisableSearchBoxSuggestions = 1",
            ),
            [ctx.reg("HKCU\\Software\\Policies\\Microsoft\\Windows\\Explorer", "DisableSearchBoxSuggestions", 1)],
        ),
    ]

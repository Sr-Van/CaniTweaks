"""Tweaks da categoria LATÊNCIA & VÍDEO."""
from typing import List

from app.adapters.catalog.context import CatalogContext, CatalogEntry
from app.adapters.operations.registry_operations import InterfaceValuesOperation
from app.adapters.operations.power_operations import PowerSettingOperation
from app.domain.entities import Tweak
from app.domain.enums import RiskLevel, TweakCategory

_GAME_CONFIG_STORE = "HKCU\\System\\GameConfigStore"
_SYSTEM_PROFILE = "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile"
_TCP_INTERFACES = "HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces"
_KERNEL = "HKLM\\SYSTEM\\CurrentControlSet\\Control\\Session Manager\\kernel"

_PCI_EXPRESS_SUBGROUP = "501a4d13-42af-4429-9fd1-a8218c268e20"
_LINK_STATE_POWER_MGMT = "ee12f906-d277-404b-b6da-e5fa1a576df5"

_WINDOWS_10_2004_BUILD = 19041
_WINDOWS_11_BUILD = 22000


def build_latency_entries(ctx: CatalogContext) -> List[CatalogEntry]:
    return [
        CatalogEntry(
            Tweak(
                id="hags",
                name="Hardware-Accelerated GPU Scheduling (HAGS)",
                summary="Permite que a GPU gerencie a própria fila de quadros, reduzindo a latência "
                        "entre CPU e GPU em jogos modernos.",
                category=TweakCategory.LATENCY,
                risk=RiskLevel.MEDIUM,
                requires_restart=True,
                technical_detail="HKLM\\...\\GraphicsDrivers: HwSchMode = 2 (exige GPU/driver compatível)",
                min_windows_build=_WINDOWS_10_2004_BUILD,
            ),
            [ctx.reg("HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers", "HwSchMode", 2)],
        ),
        CatalogEntry(
            Tweak(
                id="disable_fso",
                name="Desativar Otimizações de Tela Inteira (FSO)",
                summary="Remove a camada extra do DWM em jogos de tela cheia, devolvendo resposta "
                        "direta do mouse e teclado.",
                category=TweakCategory.LATENCY,
                technical_detail="HKCU\\System\\GameConfigStore: GameDVR_FSEBehavior(Mode) = 2",
            ),
            [
                ctx.reg(_GAME_CONFIG_STORE, "GameDVR_FSEBehaviorMode", 2),
                ctx.reg(_GAME_CONFIG_STORE, "GameDVR_FSEBehavior", 2),
                ctx.reg(_GAME_CONFIG_STORE, "GameDVR_HonorUserFSEBehaviorMode", 1),
                ctx.reg(_GAME_CONFIG_STORE, "GameDVR_DXGIHonorFSEWindowsCompatible", 1),
            ],
        ),
        CatalogEntry(
            Tweak(
                id="network_throttling",
                name="Desativar Network Throttling Multimídia",
                summary="Remove o limitador de rede do agendador multimídia, estabilizando o ping "
                        "durante jogos e streaming.",
                category=TweakCategory.LATENCY,
                risk=RiskLevel.MEDIUM,
                requires_restart=True,
                technical_detail="SystemProfile: NetworkThrottlingIndex = 0xFFFFFFFF, SystemResponsiveness = 0",
            ),
            [
                ctx.reg(_SYSTEM_PROFILE, "NetworkThrottlingIndex", 0xFFFFFFFF, default=10),
                ctx.reg(_SYSTEM_PROFILE, "SystemResponsiveness", 0, default=20),
            ],
        ),
        CatalogEntry(
            Tweak(
                id="disable_nagle",
                name="Desativar Algoritmo de Nagle (TCP NoDelay)",
                summary="Envia pacotes TCP imediatamente em vez de agrupá-los, reduzindo picos de "
                        "latência em jogos online.",
                category=TweakCategory.LATENCY,
                risk=RiskLevel.MEDIUM,
                requires_restart=True,
                technical_detail="Tcpip\\Parameters\\Interfaces\\*: TcpAckFrequency = 1, TCPNoDelay = 1",
            ),
            [InterfaceValuesOperation(ctx.registry, _TCP_INTERFACES, {"TcpAckFrequency": 1, "TCPNoDelay": 1})],
        ),
        CatalogEntry(
            Tweak(
                id="disable_pcie_link_state",
                name="Desativar Economia de Energia do PCIe (ASPM)",
                summary="Mantém o barramento PCIe da placa de vídeo sempre ativo, evitando atrasos "
                        "ao sair de estados de economia.",
                category=TweakCategory.LATENCY,
                risk=RiskLevel.MEDIUM,
                technical_detail="powercfg: Link State Power Management = Desligado (plano ativo, tomada)",
            ),
            [PowerSettingOperation(ctx.powercfg, _PCI_EXPRESS_SUBGROUP, _LINK_STATE_POWER_MGMT, 0, default=1)],
        ),
        CatalogEntry(
            Tweak(
                id="global_timer_resolution",
                name="Restaurar Resolução de Timer Global",
                summary="No Windows 11, devolve o comportamento anterior do timer do sistema, "
                        "melhorando a consistência de frametimes em alguns jogos.",
                category=TweakCategory.LATENCY,
                risk=RiskLevel.MEDIUM,
                requires_restart=True,
                technical_detail="Session Manager\\kernel: GlobalTimerResolutionRequests = 1 (Windows 11)",
                min_windows_build=_WINDOWS_11_BUILD,
            ),
            [ctx.reg(_KERNEL, "GlobalTimerResolutionRequests", 1)],
        ),
    ]

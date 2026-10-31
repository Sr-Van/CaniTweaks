"""Adapter simulado (Mock) com catálogo de tweaks representativos para pré-visualização."""
import time
from typing import Dict, List
from app.domain.entities import Tweak
from app.domain.enums import TweakCategory, TweakStatus
from app.ports.tweak_port import TweakPort


class FakeTweakAdapter(TweakPort):
    """Implementação simulada para demonstração e visualização da GUI."""

    def __init__(self):
        self._tweaks: Dict[str, Tweak] = {
            "hags": Tweak(
                id="hags",
                name="Hardware-Accelerated GPU Scheduling (HAGS)",
                summary="Permite que a placa de vídeo gerencie sua própria memória de vídeo diretamente, reduzindo a latência de renderização e input lag em jogos modernos.",
                category=TweakCategory.LATENCY,
                requires_restart=True,
                technical_detail="Registro: HKLM\\...\\GraphicsDrivers (HwSchMode = 2)",
                status=TweakStatus.INACTIVE
            ),
            "disable_fso": Tweak(
                id="disable_fso",
                name="Desativar Otimizações de Tela Inteira (FSO)",
                summary="Remove a camada de composição extra do DWM em jogos de tela cheia, garantindo resposta direta do mouse/teclado sem atraso de vídeo.",
                category=TweakCategory.LATENCY,
                requires_restart=False,
                technical_detail="Registro: HKCU\\System\\GameConfigStore (GameDVR_FSEBehavior = 2)",
                status=TweakStatus.INACTIVE
            ),
            "network_throttling": Tweak(
                id="network_throttling",
                name="Desativar Network Throttling (Algoritmo de Nagle)",
                summary="Desliga o limitador de rede multimídia do Windows e a agregação de pacotes TCP, estabilizando o ping e eliminando micro-congelamentos de conexão.",
                category=TweakCategory.LATENCY,
                requires_restart=True,
                technical_detail="Registro: SystemProfile (NetworkThrottlingIndex = 0xFFFFFFFF)",
                status=TweakStatus.INACTIVE
            ),
            "game_mode": Tweak(
                id="game_mode",
                name="Habilitar Windows Game Mode",
                summary="Prioriza threads de CPU e GPU exclusivamente para o processo do jogo ativo, evitando que aplicativos de fundo roubem ciclos de processamento.",
                category=TweakCategory.FPS,
                requires_restart=False,
                technical_detail="Registro: HKCU\\Software\\Microsoft\\GameBar (AutoGameModeEnabled = 1)",
                status=TweakStatus.ACTIVE  # Simulado já ativo
            ),
            "cpu_power_throttling": Tweak(
                id="cpu_power_throttling",
                name="Desativar Power Throttling do Processador",
                summary="Impede que o agendador de energia do Windows limite a frequência de núcleos da CPU durante partidas intensas, melhorando a estabilidade de 1% lows.",
                category=TweakCategory.FPS,
                requires_restart=True,
                technical_detail="Registro: HKLM\\...\\PowerThrottling (PowerThrottlingOff = 1)",
                status=TweakStatus.INACTIVE
            ),
            "ultimate_performance": Tweak(
                id="ultimate_performance",
                name="Ativar Plano 'Desempenho Máximo'",
                summary="Desbloqueia e ativa o esquema de energia oculto do Windows que elimina estados de repouso (C-States) e mantém a CPU em prontidão máxima.",
                category=TweakCategory.FPS,
                requires_restart=False,
                technical_detail="Comando: powercfg -duplicatescheme e9a42b02-...",
                status=TweakStatus.INACTIVE
            ),
            "disable_telemetry": Tweak(
                id="disable_telemetry",
                name="Desativar Telemetria e Diagnósticos (DiagTrack)",
                summary="Para os serviços de rastreamento de dados em segundo plano, economizando até 300MB de memória RAM e aliviando a atividade contínua de disco.",
                category=TweakCategory.RAM_PROCESSES,
                requires_restart=False,
                technical_detail="Serviços: DiagTrack & dmwappushservice",
                status=TweakStatus.INACTIVE
            ),
            "disable_game_dvr": Tweak(
                id="disable_game_dvr",
                name="Desativar Xbox Game DVR em Segundo Plano",
                summary="Desativa o buffer de captura contínua de tela do aplicativo Xbox, liberando recursos da placa de vídeo e memória RAM durante o jogo.",
                category=TweakCategory.RAM_PROCESSES,
                requires_restart=False,
                technical_detail="Registro: HKCU\\...\\GameConfigStore (GameDVR_Enabled = 0)",
                status=TweakStatus.INACTIVE
            ),
            "clean_temp_files": Tweak(
                id="clean_temp_files",
                name="Limpar Arquivos Temporários (%TEMP%)",
                summary="Exclui com segurança arquivos obsoletos de instaladores, caches de jogos e logs antigos das pastas de cache do usuário e do sistema.",
                category=TweakCategory.DISK_CLEANUP,
                requires_restart=False,
                technical_detail="Diretórios: %TEMP% e C:\\Windows\\Temp",
                status=TweakStatus.INACTIVE
            ),
            "clean_prefetch_dumps": Tweak(
                id="clean_prefetch_dumps",
                name="Limpar Prefetch & Relatórios de Erros (WER)",
                summary="Esvazia o cache antigo de pré-carregamento e os relatórios de falha acumulados, liberando espaço e otimizando o tempo de busca em disco.",
                category=TweakCategory.DISK_CLEANUP,
                requires_restart=False,
                technical_detail="Diretórios: C:\\Windows\\Prefetch e WER\\ReportQueue",
                status=TweakStatus.INACTIVE
            ),
        }

    def get_all_tweaks(self) -> List[Tweak]:
        return list(self._tweaks.values())

    def check_status(self, tweak_id: str) -> TweakStatus:
        tweak = self._tweaks.get(tweak_id)
        return tweak.status if tweak else TweakStatus.INACTIVE

    def apply(self, tweak_id: str) -> bool:
        time.sleep(0.3)  # Simula breve processamento de escrita no SO
        if tweak_id in self._tweaks:
            self._tweaks[tweak_id].status = TweakStatus.ACTIVE
            return True
        return False

    def revert(self, tweak_id: str) -> bool:
        time.sleep(0.3)  # Simula breve restauração
        if tweak_id in self._tweaks:
            self._tweaks[tweak_id].status = TweakStatus.INACTIVE
            return True
        return False

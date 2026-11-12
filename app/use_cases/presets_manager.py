"""Caso de uso: consulta e aplicação de presets."""
import logging
from typing import Dict, List, Optional, Sequence, Tuple

from app.domain.batch_report import BatchReport
from app.domain.entities import Preset, Tweak
from app.domain.enums import TweakStatus
from app.use_cases.batch_runner import BatchRunner, CancelCheck, ProgressCallback
from app.use_cases.tweak_manager import TweakManager

logger = logging.getLogger(__name__)


class PresetNotFoundError(KeyError):
    """Levantado quando o ID de preset informado não existe."""


class PresetsManager:
    """Resolve presets em tweaks e delega a execução em lote ao BatchRunner."""

    def __init__(self, presets: Sequence[Preset], tweak_manager: TweakManager, batch_runner: BatchRunner):
        self._presets = list(presets)
        self._tweaks = tweak_manager
        self._runner = batch_runner

    def get_presets(self) -> List[Preset]:
        return list(self._presets)

    def get_preset_tweaks(self, preset_id: str) -> List[Tweak]:
        """Tweaks do preset, na ordem declarada. IDs inexistentes no catálogo são ignorados."""
        preset = self._find(preset_id)
        resolved = []
        for tweak_id in preset.tweak_ids:
            tweak = self._tweaks.get_tweak(tweak_id)
            if tweak is None:
                logger.warning("Preset '%s' referencia tweak inexistente: %s", preset_id, tweak_id)
                continue
            resolved.append(tweak)
        return resolved

    def apply_preset(
        self,
        preset_id: str,
        progress: Optional[ProgressCallback] = None,
        should_cancel: Optional[CancelCheck] = None,
    ) -> BatchReport:
        return self._runner.apply_batch(self.get_preset_tweaks(preset_id), progress, should_cancel)

    def revert_preset(
        self,
        preset_id: str,
        progress: Optional[ProgressCallback] = None,
        should_cancel: Optional[CancelCheck] = None,
    ) -> BatchReport:
        return self._runner.revert_batch(self.get_preset_tweaks(preset_id), progress, should_cancel)

    def get_progress(self, preset_id: str, statuses: Dict[str, TweakStatus]) -> Tuple[int, int]:
        """Retorna (ativos, total) considerando apenas tweaks reversíveis e disponíveis."""
        relevant = [
            tweak for tweak in self.get_preset_tweaks(preset_id)
            if tweak.is_reversible and statuses.get(tweak.id) != TweakStatus.UNSUPPORTED
        ]
        active = sum(1 for tweak in relevant if statuses.get(tweak.id) == TweakStatus.ACTIVE)
        return active, len(relevant)

    def get_all_progress(self) -> Dict[str, Tuple[int, int]]:
        """Progresso (ativos, total) de todos os presets (consulta o sistema; pode ser lento)."""
        statuses = self._tweaks.get_statuses()
        return {preset.id: self.get_progress(preset.id, statuses) for preset in self._presets}

    def _find(self, preset_id: str) -> Preset:
        for preset in self._presets:
            if preset.id == preset_id:
                return preset
        raise PresetNotFoundError(preset_id)

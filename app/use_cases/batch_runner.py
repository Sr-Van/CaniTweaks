"""Caso de uso: aplicação e reversão de tweaks em lote."""
from typing import Callable, Iterable, List, Optional

from app.domain.batch_report import BatchReport, TweakOutcome
from app.domain.entities import Tweak
from app.domain.enums import OutcomeKind, TweakStatus
from app.domain.result import Result
from app.ports.restore_port import RestorePointPort
from app.use_cases.tweak_manager import TweakManager

# (posição atual 1-based, total, nome do tweak em processamento)
ProgressCallback = Callable[[int, int, str], None]
CancelCheck = Callable[[], bool]

RESTORE_POINT_DESCRIPTION = "CaniTweaks - antes de aplicar otimizações"


class BatchRunner:
    """Executa vários tweaks em sequência com progresso, cancelamento e relatório final."""

    def __init__(self, tweak_manager: TweakManager, restore_port: RestorePointPort):
        self._tweaks = tweak_manager
        self._restore = restore_port

    def apply_batch(
        self,
        tweaks: Iterable[Tweak],
        progress: Optional[ProgressCallback] = None,
        should_cancel: Optional[CancelCheck] = None,
    ) -> BatchReport:
        """Aplica os tweaks. Cria um ponto de restauração antes se houver ajustes reversíveis."""
        tweaks = list(tweaks)
        report = BatchReport()
        if any(tweak.is_reversible for tweak in tweaks):
            report.restore_point = self._restore.create_restore_point(RESTORE_POINT_DESCRIPTION)
        self._run(tweaks, report, progress, should_cancel, self._apply_one)
        return report

    def revert_batch(
        self,
        tweaks: Iterable[Tweak],
        progress: Optional[ProgressCallback] = None,
        should_cancel: Optional[CancelCheck] = None,
    ) -> BatchReport:
        """Reverte os tweaks reversíveis; ações pontuais são ignoradas."""
        tweaks = [tweak for tweak in tweaks if tweak.is_reversible]
        report = BatchReport()
        self._run(tweaks, report, progress, should_cancel, self._revert_one)
        return report

    def _run(
        self,
        tweaks: List[Tweak],
        report: BatchReport,
        progress: Optional[ProgressCallback],
        should_cancel: Optional[CancelCheck],
        action: Callable[[Tweak], TweakOutcome],
    ) -> None:
        total = len(tweaks)
        for index, tweak in enumerate(tweaks, start=1):
            if should_cancel and should_cancel():
                report.cancelled = True
                break
            if progress:
                progress(index, total, tweak.name)
            report.outcomes.append(action(tweak))

    def _apply_one(self, tweak: Tweak) -> TweakOutcome:
        status = self._tweaks.get_status(tweak.id)
        if status == TweakStatus.UNSUPPORTED:
            return self._skipped(tweak, "Indisponível nesta versão do Windows.")
        if tweak.is_reversible and status == TweakStatus.ACTIVE:
            return self._skipped(tweak, "Já estava ativo.")
        return self._outcome(tweak, self._tweaks.apply_tweak(tweak.id))

    def _revert_one(self, tweak: Tweak) -> TweakOutcome:
        status = self._tweaks.get_status(tweak.id)
        if status == TweakStatus.UNSUPPORTED:
            return self._skipped(tweak, "Indisponível nesta versão do Windows.")
        if status != TweakStatus.ACTIVE:
            return self._skipped(tweak, "Já estava inativo.")
        return self._outcome(tweak, self._tweaks.revert_tweak(tweak.id))

    @staticmethod
    def _skipped(tweak: Tweak, reason: str) -> TweakOutcome:
        return TweakOutcome(tweak, OutcomeKind.SKIPPED, Result.success(reason))

    @staticmethod
    def _outcome(tweak: Tweak, result: Result) -> TweakOutcome:
        kind = OutcomeKind.DONE if result.ok else OutcomeKind.FAILED
        return TweakOutcome(tweak, kind, result)

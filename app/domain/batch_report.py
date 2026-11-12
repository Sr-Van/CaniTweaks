"""Relatório de execução de um lote de tweaks."""
from dataclasses import dataclass, field
from typing import List, Optional

from app.domain.entities import Tweak
from app.domain.enums import OutcomeKind
from app.domain.result import Result


@dataclass(frozen=True)
class TweakOutcome:
    """Resultado individual de um tweak dentro do lote."""

    tweak: Tweak
    kind: OutcomeKind
    result: Result


@dataclass
class BatchReport:
    """Consolida o que aconteceu durante a aplicação/reversão em lote."""

    outcomes: List[TweakOutcome] = field(default_factory=list)
    cancelled: bool = False
    restore_point: Optional[Result] = None

    def _of_kind(self, kind: OutcomeKind) -> List[TweakOutcome]:
        return [o for o in self.outcomes if o.kind == kind]

    @property
    def done(self) -> List[TweakOutcome]:
        return self._of_kind(OutcomeKind.DONE)

    @property
    def skipped(self) -> List[TweakOutcome]:
        return self._of_kind(OutcomeKind.SKIPPED)

    @property
    def failed(self) -> List[TweakOutcome]:
        return self._of_kind(OutcomeKind.FAILED)

    @property
    def restart_required(self) -> List[str]:
        """Nomes dos tweaks concluídos que exigem reinício para surtir efeito."""
        return [o.tweak.name for o in self.done if o.result.needs_restart]

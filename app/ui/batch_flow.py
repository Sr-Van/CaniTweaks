"""Fluxo de interface compartilhado para operações em lote (progresso, cancelamento e relatório)."""
import threading
from typing import Callable, List

import customtkinter as ctk

from app.domain.batch_report import BatchReport
from app.ui.components.dialogs import BatchReportDialog, InfoDialog
from app.ui.components.progress_panel import ProgressPanel
from app.ui.task_runner import UiTaskRunner
from app.use_cases.batch_runner import CancelCheck, ProgressCallback

# Função que executa o lote recebendo o callback de progresso e a checagem de cancelamento.
BatchJob = Callable[[ProgressCallback, CancelCheck], BatchReport]


class BatchFlow:
    """Executa um lote em segundo plano e conduz a interface do início ao relatório final."""

    def __init__(
        self,
        view: ctk.CTkFrame,
        tasks: UiTaskRunner,
        on_restart_needed: Callable[[List[str]], None],
        on_request_restart: Callable[[], None],
    ):
        self._view = view
        self._tasks = tasks
        self._on_restart_needed = on_restart_needed
        self._on_request_restart = on_request_restart
        self._cancel_event = threading.Event()
        self.panel = ProgressPanel(view, on_cancel=self._cancel)

    def start(self, job: BatchJob, report_title: str, intro: str) -> bool:
        """Inicia o lote. Retorna False se outra operação já estiver em andamento."""
        self._cancel_event.clear()

        def work() -> BatchReport:
            return job(self._report_progress, self._cancel_event.is_set)

        started = self._tasks.run_exclusive(
            work,
            lambda report: self._finish(report, report_title),
            self._fail,
        )
        if started:
            self.panel.show(intro)
        return started

    def _report_progress(self, current: int, total: int, name: str) -> None:
        """Chamado pela thread de trabalho; redireciona a atualização para a thread da UI."""
        self._tasks.post(lambda: self.panel.update_progress(current, total, name))

    def _cancel(self) -> None:
        self._cancel_event.set()
        self.panel.mark_cancelling()

    def _finish(self, report: BatchReport, title: str) -> None:
        self.panel.hide()
        if report.restart_required:
            self._on_restart_needed(report.restart_required)
        BatchReportDialog(self._view, title, report, on_restart=self._on_request_restart)

    def _fail(self, exc: Exception) -> None:
        self.panel.hide()
        InfoDialog(self._view, "Erro inesperado", f"A operação foi interrompida: {exc}")

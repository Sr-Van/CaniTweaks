"""Diálogos modais reutilizáveis: informação, confirmação, relatório de lote e reinício."""
from typing import Callable, List, Optional, Sequence

import customtkinter as ctk

from app.domain.batch_report import BatchReport
from app.domain.enums import OutcomeKind
from app.domain.result import Result
from app.ui import theme

_OUTCOME_ICON = {OutcomeKind.DONE: "✅", OutcomeKind.SKIPPED: "⏭", OutcomeKind.FAILED: "❌"}
_OUTCOME_COLOR = {
    OutcomeKind.DONE: theme.COLOR_SUCCESS,
    OutcomeKind.SKIPPED: theme.MUTED_TEXT,
    OutcomeKind.FAILED: theme.COLOR_ERROR,
}


class _ModalDialog(ctk.CTkToplevel):
    """Base: janela modal centralizada sobre a janela pai."""

    def __init__(self, parent, title: str, width: int, height: int):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self._center(parent, width, height)
        self.after(100, self._take_focus)  # O grab imediato falha no Windows com CTkToplevel.

    def _center(self, parent, width: int, height: int) -> None:
        root = parent.winfo_toplevel()
        x = root.winfo_rootx() + (root.winfo_width() - width) // 2
        y = root.winfo_rooty() + (root.winfo_height() - height) // 3
        self.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")

    def _take_focus(self) -> None:
        if self.winfo_exists():
            self.grab_set()
            self.focus_set()

    def _title_label(self, text: str) -> None:
        ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(18, 8), padx=20)

    def _button_row(self) -> ctk.CTkFrame:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(side="bottom", pady=16)
        return row

    @staticmethod
    def _button(parent, text: str, command: Callable[[], None], color: str = theme.NEUTRAL, hover: str = theme.NEUTRAL_HOVER):
        button = ctk.CTkButton(parent, text=text, width=140, fg_color=color, hover_color=hover, command=command)
        button.pack(side="left", padx=8)
        return button


class InfoDialog(_ModalDialog):
    """Mensagem simples com botão OK."""

    def __init__(self, parent, title: str, message: str):
        super().__init__(parent, title, 420, 190)
        self._title_label(title)
        ctk.CTkLabel(self, text=message, wraplength=370, justify="center", font=ctk.CTkFont(size=12)).pack(padx=20)
        self._button(self._button_row(), "OK", self.destroy, theme.ACCENT, theme.ACCENT_HOVER)


class ConfirmDialog(_ModalDialog):
    """Pergunta de confirmação com lista opcional de itens afetados."""

    def __init__(
        self,
        parent,
        title: str,
        message: str,
        items: Sequence[str],
        confirm_text: str,
        on_confirm: Callable[[], None],
    ):
        height = 250 + min(len(items), 8) * 22
        super().__init__(parent, title, 520, height)
        self._on_confirm = on_confirm

        self._title_label(title)
        ctk.CTkLabel(self, text=message, wraplength=470, justify="left", font=ctk.CTkFont(size=12)).pack(padx=24, anchor="w")

        buttons = self._button_row()  # Empacotado antes da lista para ficar sempre visível.
        if items:
            box = ctk.CTkScrollableFrame(self, fg_color=theme.PANEL_BG, height=min(len(items), 8) * 22)
            box.pack(fill="both", expand=True, padx=24, pady=(10, 0))
            for item in items:
                ctk.CTkLabel(box, text=f"• {item}", anchor="w", font=ctk.CTkFont(size=12)).pack(fill="x")

        self._button(buttons, "Cancelar", self.destroy)
        self._button(buttons, confirm_text, self._confirm, theme.ACCENT, theme.ACCENT_HOVER)

    def _confirm(self) -> None:
        self.destroy()
        self._on_confirm()


class BatchReportDialog(_ModalDialog):
    """Resumo de uma execução em lote com o resultado de cada tweak."""

    def __init__(self, parent, title: str, report: BatchReport, on_restart: Optional[Callable[[], None]]):
        super().__init__(parent, title, 600, 520)
        self._on_restart = on_restart

        self._title_label(title)
        ctk.CTkLabel(
            self, text=self._summary_line(report), font=ctk.CTkFont(size=12, weight="bold"),
            text_color=theme.COLOR_ERROR if report.failed else theme.COLOR_SUCCESS,
        ).pack(padx=24, anchor="w")
        for note in self._notes(report):
            ctk.CTkLabel(self, text=note, wraplength=550, justify="left", anchor="w",
                         font=ctk.CTkFont(size=11), text_color=theme.COLOR_WARNING).pack(padx=24, anchor="w", pady=(4, 0))

        buttons = self._button_row()
        details = ctk.CTkScrollableFrame(self, fg_color=theme.PANEL_BG)
        details.pack(fill="both", expand=True, padx=24, pady=(10, 0))
        for outcome in report.outcomes:
            self._add_outcome_row(details, outcome)

        self._button(buttons, "Fechar", self.destroy)
        if report.restart_required and on_restart:
            self._button(buttons, "🔄 Reiniciar...", self._restart, theme.DANGER, theme.DANGER_HOVER)

    @staticmethod
    def _summary_line(report: BatchReport) -> str:
        parts = [f"{len(report.done)} concluído(s)"]
        if report.skipped:
            parts.append(f"{len(report.skipped)} ignorado(s)")
        if report.failed:
            parts.append(f"{len(report.failed)} com falha")
        if report.cancelled:
            parts.append("cancelado pelo usuário")
        return " · ".join(parts)

    @staticmethod
    def _notes(report: BatchReport) -> List[str]:
        notes = []
        if report.restore_point is not None and not report.restore_point.ok:
            notes.append(f"⚠ Ponto de restauração não criado: {report.restore_point.error}")
        if report.restart_required:
            notes.append(f"🔄 Reinicie o Windows para concluir: {', '.join(report.restart_required)}.")
        return notes

    @staticmethod
    def _add_outcome_row(parent, outcome) -> None:
        text = f"{_OUTCOME_ICON[outcome.kind]}  {outcome.tweak.name}"
        detail = outcome.result.error if outcome.kind == OutcomeKind.FAILED else outcome.result.message
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        ctk.CTkLabel(row, text=text, anchor="w", font=ctk.CTkFont(size=12)).pack(fill="x")
        if detail:
            ctk.CTkLabel(row, text=detail, anchor="w", wraplength=500, justify="left",
                         font=ctk.CTkFont(size=11), text_color=_OUTCOME_COLOR[outcome.kind]).pack(fill="x", padx=(26, 0))

    def _restart(self) -> None:
        self.destroy()
        self._on_restart()


class RestartDialog(_ModalDialog):
    """Confirma o reinício e, após agendado, permite cancelá-lo."""

    def __init__(
        self,
        parent,
        pending: Sequence[str],
        on_restart: Callable[[], Result],
        on_cancel_restart: Callable[[], Result],
        delay_seconds: int,
    ):
        super().__init__(parent, "Reiniciar o Windows", 460, 250)
        self._on_restart = on_restart
        self._on_cancel_restart = on_cancel_restart
        self._delay = delay_seconds

        self._title_label("🔄 Reinicialização")
        pending_text = f"\n\nPendentes: {', '.join(pending)}." if pending else ""
        self._message = ctk.CTkLabel(
            self, wraplength=410, justify="center", font=ctk.CTkFont(size=12),
            text=f"Salve seu trabalho antes de continuar. Algumas otimizações só têm efeito total após reiniciar.{pending_text}",
        )
        self._message.pack(padx=20)

        self._buttons = self._button_row()
        self._later_button = self._button(self._buttons, "Mais tarde", self.destroy)
        self._action_button = self._button(self._buttons, "Reiniciar agora", self._restart, theme.DANGER, theme.DANGER_HOVER)

    def _restart(self) -> None:
        result = self._on_restart()
        if not result.ok:
            self._message.configure(text=f"Não foi possível agendar o reinício: {result.error}", text_color=theme.COLOR_ERROR)
            return
        self._message.configure(
            text=f"O Windows reiniciará em {self._delay} segundos.\nClique em Cancelar reinício para abortar.",
            text_color=theme.COLOR_WARNING,
        )
        self._later_button.configure(text="Fechar")
        self._action_button.configure(text="Cancelar reinício", command=self._cancel,
                                      fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER)

    def _cancel(self) -> None:
        result = self._on_cancel_restart()
        text = "Reinício cancelado." if result.ok else f"Não foi possível cancelar: {result.error}"
        self._message.configure(text=text, text_color=theme.COLOR_SUCCESS if result.ok else theme.COLOR_ERROR)
        self._action_button.configure(state="disabled")

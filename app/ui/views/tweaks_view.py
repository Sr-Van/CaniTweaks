"""Aba principal de Otimizações: busca, filtros, ações individuais e em lote."""
from datetime import datetime
from pathlib import Path
from tkinter import filedialog
from typing import Callable, Dict, List

import customtkinter as ctk

from app.domain.entities import SystemInfo, Tweak
from app.domain.enums import TweakCategory, TweakStatus
from app.domain.result import Result
from app.ui import theme
from app.ui.batch_flow import BatchFlow
from app.ui.components.dialogs import ConfirmDialog, InfoDialog
from app.ui.components.tweak_card import TweakCard
from app.ui.task_runner import UiTaskRunner
from app.use_cases.batch_runner import BatchRunner
from app.use_cases.status_report import build_status_report
from app.use_cases.tweak_manager import TweakManager

_SEARCH_DEBOUNCE_MS = 150
_CONFIRM_LIST_LIMIT = 12


class TweaksView(ctk.CTkFrame):
    """Lista de tweaks com busca, filtro por categoria e aplicação individual ou em lote."""

    def __init__(
        self,
        master,
        tweak_manager: TweakManager,
        batch_runner: BatchRunner,
        tasks: UiTaskRunner,
        info: SystemInfo,
        on_restart_needed: Callable[[List[str]], None],
        on_request_restart: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._tweaks = tweak_manager
        self._batch = batch_runner
        self._tasks = tasks
        self._info = info
        self._on_restart_needed = on_restart_needed

        self._category = TweakCategory.ALL
        self._query = ""
        self._search_job = None
        self._statuses: Dict[str, TweakStatus] = {}
        self._visible: List[Tweak] = []
        self._cards: Dict[str, TweakCard] = {}
        self._loading_statuses = False

        self._flow = BatchFlow(self, tasks, on_restart_needed, on_request_restart)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self._build_header()
        self._build_toolbar()
        self._build_filter()
        self._flow.panel.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 8))
        self._flow.panel.hide()
        self._build_card_list()

        tasks.subscribe_busy(self._on_busy_changed)
        self._apply_filter()

    # --- Construção da interface ------------------------------------------------------------

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        ctk.CTkLabel(header, text="Otimizações do sistema", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")

        self._export_button = ctk.CTkButton(
            header, text="Exportar relatório", width=150, height=30, fg_color=theme.NEUTRAL, text_color=theme.COBRA_YELLOW,
            hover_color=theme.NEUTRAL_HOVER, command=self._export_report,
        )
        self._export_button.pack(side="right")
        self._stats_label = ctk.CTkLabel(header, text="Verificando...", font=ctk.CTkFont(size=12), text_color=theme.MUTED_TEXT)
        self._stats_label.pack(side="right", padx=14)

    def _build_toolbar(self) -> None:
        bar = ctk.CTkFrame(self, fg_color=theme.PANEL_BG, corner_radius=10)
        bar.grid(row=1, column=0, sticky="ew", padx=20, pady=(5, 8))

        self._search = ctk.CTkEntry(bar, placeholder_text="Buscar otimização...", height=36, width=280)
        self._search.pack(side="left", padx=12, pady=10)
        self._search.bind("<KeyRelease>", self._on_search_key)
        self._search.bind("<Escape>", self._clear_search)

        self._apply_button = ctk.CTkButton(
            bar, text="Aplicar visíveis", height=36, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER, command=self._on_apply_visible,
        )
        self._apply_button.pack(side="right", padx=(6, 12), pady=10)
        self._revert_button = ctk.CTkButton(
            bar, text="↩ Reverter ativos", height=36, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=theme.NEUTRAL, text_color=theme.COBRA_YELLOW, hover_color=theme.NEUTRAL_HOVER, command=self._on_revert_visible,
        )
        self._revert_button.pack(side="right", pady=10)

    def _build_filter(self) -> None:
        self._filter = ctk.CTkSegmentedButton(
            self, values=[category.value for category in TweakCategory], command=self._on_category_changed,
            font=ctk.CTkFont(size=11), selected_color="#7a5c00", selected_hover_color=theme.SCALE_GOLD, text_color="#ffffff",
            unselected_color="#2a2a2a", unselected_hover_color="#3a3a3a",
        )
        self._filter.set(TweakCategory.ALL.value)
        self._filter.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 8))

    def _build_card_list(self) -> None:
        self._list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list.grid(row=4, column=0, sticky="nsew", padx=20, pady=(0, 15))
        for tweak in self._tweaks.get_tweaks():
            self._cards[tweak.id] = TweakCard(self._list, tweak, self._apply_single, self._revert_single)
        self._empty_label = ctk.CTkLabel(
            self._list, text="Nenhuma otimização encontrada para este filtro.",
            font=ctk.CTkFont(size=13), text_color=theme.MUTED_TEXT,
        )

    # --- Filtro e busca ---------------------------------------------------------------------

    def _on_category_changed(self, value: str) -> None:
        self._category = next(category for category in TweakCategory if category.value == value)
        self._apply_filter()

    def _on_search_key(self, _event=None) -> None:
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(_SEARCH_DEBOUNCE_MS, self._run_search)

    def _run_search(self) -> None:
        self._search_job = None
        self._query = self._search.get()
        self._apply_filter()

    def _clear_search(self, _event=None) -> None:
        self._search.delete(0, "end")
        self._run_search()

    def _apply_filter(self) -> None:
        """Mostra apenas os cards que passam no filtro, mantendo a ordem do catálogo."""
        self._visible = self._tweaks.get_tweaks(self._category, self._query)
        for card in self._cards.values():
            card.pack_forget()
        self._empty_label.pack_forget()
        for tweak in self._visible:
            self._cards[tweak.id].pack(fill="x", pady=6)
        if not self._visible:
            self._empty_label.pack(pady=40)
        self._update_batch_buttons()

    # --- Estado dos tweaks ------------------------------------------------------------------

    def refresh_statuses(self) -> None:
        """Consulta o estado real dos tweaks em segundo plano e atualiza os cards."""
        if self._loading_statuses or self._tasks.is_busy:
            return
        self._loading_statuses = True
        self._tasks.run(self._tweaks.get_statuses, self._on_statuses_loaded, self._on_statuses_failed)

    def _on_statuses_loaded(self, statuses: Dict[str, TweakStatus]) -> None:
        self._loading_statuses = False
        self._statuses = statuses
        for tweak_id, card in self._cards.items():
            status = statuses.get(tweak_id, TweakStatus.UNKNOWN)
            if card.status != status:  # Evita apagar a mensagem de uma ação recém-concluída.
                card.set_status(status)
        self._update_stats()
        self._update_batch_buttons()

    def _on_statuses_failed(self, _exc: Exception) -> None:
        self._loading_statuses = False
        self._stats_label.configure(text="Não foi possível verificar o estado")

    def _update_stats(self) -> None:
        reversible = [t for t in self._tweaks.get_tweaks() if t.is_reversible]
        active = sum(1 for t in reversible if self._statuses.get(t.id) == TweakStatus.ACTIVE)
        self._stats_label.configure(text=f"{active} de {len(reversible)} otimizações ativas")

    def _on_busy_changed(self, busy: bool) -> None:
        for card in self._cards.values():
            card.set_interaction_enabled(not busy)
        self._update_batch_buttons()
        if not busy and self.winfo_ismapped():
            self.refresh_statuses()

    # --- Ações individuais ------------------------------------------------------------------

    def _apply_single(self, tweak_id: str) -> None:
        self._run_single(tweak_id, apply=True)

    def _revert_single(self, tweak_id: str) -> None:
        self._run_single(tweak_id, apply=False)

    def _run_single(self, tweak_id: str, apply: bool) -> None:
        card = self._cards[tweak_id]
        tweak = card.tweak
        action = self._tweaks.apply_tweak if apply else self._tweaks.revert_tweak

        def work():
            result = action(tweak_id)
            return result, self._tweaks.get_status(tweak_id)

        def done(outcome) -> None:
            self._show_single_result(tweak, *outcome, applied=apply)

        def failed(exc: Exception) -> None:
            card.set_status(TweakStatus.ERROR, note=f"Erro inesperado: {exc}", note_is_error=True)

        if self._tasks.run_exclusive(work, done, failed):
            card.set_status(TweakStatus.PENDING)

    def _show_single_result(self, tweak: Tweak, result: Result, status: TweakStatus, applied: bool) -> None:
        card = self._cards[tweak.id]
        self._statuses[tweak.id] = status
        if not result.ok:
            card.set_status(status, note=result.error, note_is_error=True)
        else:
            card.set_status(status, note=self._success_note(tweak, result, applied))
            if result.needs_restart:
                self._on_restart_needed([tweak.name])
        self._update_stats()
        self._update_batch_buttons()

    @staticmethod
    def _success_note(tweak: Tweak, result: Result, applied: bool) -> str:
        if result.message:
            return result.message
        note = "Aplicado com sucesso" if applied else "Revertido ao estado original"
        return f"{note} — reinicie para concluir" if result.needs_restart else note

    # --- Ações em lote ----------------------------------------------------------------------

    def _apply_targets(self) -> List[Tweak]:
        """Tweaks visíveis ainda não aplicados. Ações de limpeza só entram se o usuário filtrou por elas."""
        include_actions = self._category == TweakCategory.DISK_CLEANUP or bool(self._query.strip())
        return [
            tweak for tweak in self._visible
            if (tweak.is_reversible or include_actions)
            and self._statuses.get(tweak.id) not in (TweakStatus.UNSUPPORTED, TweakStatus.PENDING)
            and not (tweak.is_reversible and self._statuses.get(tweak.id) == TweakStatus.ACTIVE)
        ]

    def _revert_targets(self) -> List[Tweak]:
        return [t for t in self._visible if t.is_reversible and self._statuses.get(t.id) == TweakStatus.ACTIVE]

    def _update_batch_buttons(self) -> None:
        busy = self._tasks.is_busy
        self._apply_button.configure(state="normal" if not busy and self._apply_targets() else "disabled")
        self._revert_button.configure(state="normal" if not busy and self._revert_targets() else "disabled")
        self._export_button.configure(state="disabled" if busy else "normal")

    def _on_apply_visible(self) -> None:
        targets = self._apply_targets()
        if not targets:
            return
        has_reversible = any(t.is_reversible for t in targets)
        has_actions = any(not t.is_reversible for t in targets)
        message = f"Serão aplicadas {len(targets)} otimização(ões)."
        if has_reversible:
            message += " Um ponto de restauração do Windows será criado antes e cada ajuste poderá ser revertido."
        if has_actions:
            message += " As ações de limpeza não podem ser desfeitas."
        self._confirm_batch("Aplicar otimizações", message, targets, "Aplicar", apply=True)

    def _on_revert_visible(self) -> None:
        targets = self._revert_targets()
        if not targets:
            return
        message = f"{len(targets)} otimização(ões) voltarão ao estado em que estavam antes de serem aplicadas."
        self._confirm_batch("Reverter otimizações", message, targets, "Reverter", apply=False)

    def _confirm_batch(self, title: str, message: str, targets: List[Tweak], confirm_text: str, apply: bool) -> None:
        items = [f"{t.name}  (risco {t.risk.value.lower()})" for t in targets[:_CONFIRM_LIST_LIMIT]]
        if len(targets) > _CONFIRM_LIST_LIMIT:
            items.append(f"... e mais {len(targets) - _CONFIRM_LIST_LIMIT}")
        ConfirmDialog(self, title, message, items, confirm_text, lambda: self._start_batch(targets, apply))

    def _start_batch(self, targets: List[Tweak], apply: bool) -> None:
        runner = self._batch.apply_batch if apply else self._batch.revert_batch
        intro = (
            "Criando ponto de restauração (pode levar alguns segundos)..."
            if apply and any(t.is_reversible for t in targets) else "Iniciando..."
        )
        title = "Resultado da aplicação" if apply else "Resultado da reversão"
        self._flow.start(lambda progress, cancel: runner(targets, progress, cancel), title, intro)

    # --- Exportação -------------------------------------------------------------------------

    def _export_report(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self, title="Exportar relatório", defaultextension=".txt",
            initialfile="wintweaks-relatorio.txt", filetypes=[("Texto", "*.txt")],
        )
        if not path:
            return
        report = build_status_report(self._tweaks.get_tweaks(), self._statuses, self._info, datetime.now())
        try:
            Path(path).write_text(report, encoding="utf-8")
        except OSError as exc:
            InfoDialog(self, "Falha ao exportar", f"Não foi possível salvar o arquivo: {exc}")

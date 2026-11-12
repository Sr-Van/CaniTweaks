"""Aba de Presets com perfis prontos de otimização."""
from typing import Callable, Dict, List, Tuple

import customtkinter as ctk

from app.ui import theme
from app.ui.batch_flow import BatchFlow
from app.ui.components.dialogs import ConfirmDialog
from app.ui.components.preset_card import PresetCard
from app.ui.task_runner import UiTaskRunner
from app.use_cases.presets_manager import PresetsManager


class PresetsView(ctk.CTkFrame):
    """Lista de presets com aplicação e reversão em um clique."""

    def __init__(
        self,
        master,
        presets_manager: PresetsManager,
        tasks: UiTaskRunner,
        on_restart_needed: Callable[[List[str]], None],
        on_request_restart: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._presets = presets_manager
        self._tasks = tasks
        self._cards: Dict[str, PresetCard] = {}
        self._loading = False

        self._flow = BatchFlow(self, tasks, on_restart_needed, on_request_restart)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_header()
        self._flow.panel.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))
        self._flow.panel.hide()
        self._build_cards()

        tasks.subscribe_busy(self._on_busy_changed)

    def _build_header(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        ctk.CTkLabel(header, text="🎯 Presets Rápidos", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Aplique conjuntos de otimizações com um clique. Cada preset pode ser revertido depois.",
            font=ctk.CTkFont(size=12), text_color=theme.MUTED_TEXT,
        ).pack(anchor="w", pady=(2, 0))

    def _build_cards(self) -> None:
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 15))
        for preset in self._presets.get_presets():
            names = [tweak.name for tweak in self._presets.get_preset_tweaks(preset.id)]
            card = PresetCard(scroll, preset, names, self._confirm_apply, self._confirm_revert)
            card.pack(fill="x", pady=10)
            self._cards[preset.id] = card

    # --- Estado -----------------------------------------------------------------------------

    def refresh_statuses(self) -> None:
        """Atualiza, em segundo plano, quantos tweaks de cada preset já estão ativos."""
        if self._loading or self._tasks.is_busy:
            return
        self._loading = True
        self._tasks.run(self._presets.get_all_progress, self._on_progress_loaded, self._on_progress_failed)

    def _on_progress_loaded(self, progress: Dict[str, Tuple[int, int]]) -> None:
        self._loading = False
        for preset_id, (active, total) in progress.items():
            self._cards[preset_id].set_progress(active, total)

    def _on_progress_failed(self, _exc: Exception) -> None:
        self._loading = False

    def _on_busy_changed(self, busy: bool) -> None:
        for card in self._cards.values():
            card.set_interaction_enabled(not busy)
        if not busy and self.winfo_ismapped():
            self.refresh_statuses()

    # --- Ações ------------------------------------------------------------------------------

    def _confirm_apply(self, preset_id: str) -> None:
        card = self._cards[preset_id]
        message = (
            f"O preset \"{card.preset.name}\" será aplicado. Um ponto de restauração do Windows "
            "será criado antes e você poderá reverter o preset a qualquer momento."
        )
        ConfirmDialog(self, "Aplicar preset", message, self._tweak_names(preset_id), "Aplicar",
                      lambda: self._start(preset_id, apply=True))

    def _confirm_revert(self, preset_id: str) -> None:
        card = self._cards[preset_id]
        message = f"As otimizações ativas do preset \"{card.preset.name}\" voltarão ao estado original."
        ConfirmDialog(self, "Reverter preset", message, self._tweak_names(preset_id), "Reverter",
                      lambda: self._start(preset_id, apply=False))

    def _tweak_names(self, preset_id: str) -> List[str]:
        return [tweak.name for tweak in self._presets.get_preset_tweaks(preset_id)]

    def _start(self, preset_id: str, apply: bool) -> None:
        run = self._presets.apply_preset if apply else self._presets.revert_preset
        intro = "Criando ponto de restauração (pode levar alguns segundos)..." if apply else "Iniciando..."
        title = "Resultado do preset" if apply else "Resultado da reversão do preset"
        self._flow.start(lambda progress, cancel: run(preset_id, progress, cancel), title, intro)

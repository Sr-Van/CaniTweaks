"""Painel de progresso com botão de cancelamento para operações em lote."""
from typing import Callable

import customtkinter as ctk

from app.ui import theme


class ProgressPanel(ctk.CTkFrame):
    """Barra de progresso, texto do item atual e botão Cancelar.

    Deve ser posicionado com `grid`; `show()` e `hide()` controlam a visibilidade.
    """

    def __init__(self, master, on_cancel: Callable[[], None], **kwargs):
        super().__init__(master, fg_color=theme.PANEL_BG, corner_radius=10, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self._label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12, weight="bold"), anchor="w")
        self._label.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))

        self._bar = ctk.CTkProgressBar(self, height=10)
        self._bar.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))

        self._cancel_button = ctk.CTkButton(
            self, text="Cancelar", width=90, height=28, fg_color=theme.NEUTRAL, text_color=theme.COBRA_YELLOW,
            hover_color=theme.NEUTRAL_HOVER, command=on_cancel,
        )
        self._cancel_button.grid(row=0, column=1, rowspan=2, padx=(0, 14))

    def show(self, message: str) -> None:
        self._bar.set(0)
        self._label.configure(text=message)
        self._cancel_button.configure(state="normal", text="Cancelar")
        self.grid()

    def hide(self) -> None:
        self.grid_remove()

    def update_progress(self, current: int, total: int, item_name: str) -> None:
        """`current` é a posição (1-based) do item que está começando a ser processado."""
        self._bar.set((current - 1) / total if total else 0)
        self._label.configure(text=f"({current}/{total}) {item_name}...")

    def mark_cancelling(self) -> None:
        self._cancel_button.configure(state="disabled", text="Cancelando...")
        self._label.configure(text="Cancelando após o item atual...")

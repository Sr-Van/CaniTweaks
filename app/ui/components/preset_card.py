"""Componente visual de um Preset (perfil de otimizações)."""
from typing import Callable, Sequence

import customtkinter as ctk

from app.domain.entities import Preset
from app.ui import theme

_MIN_WRAP = 300
_WRAP_MARGIN = 36


class PresetCard(ctk.CTkFrame):
    """Card com descrição, progresso de aplicação e botões Aplicar/Reverter do preset."""

    def __init__(
        self,
        master,
        preset: Preset,
        tweak_names: Sequence[str],
        on_apply: Callable[[str], None],
        on_revert: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(master, corner_radius=8, fg_color=theme.CARD_BG, border_width=1,
                         border_color=theme.BORDER, **kwargs)
        self.preset = preset
        self._on_apply = on_apply
        self._on_revert = on_revert
        self._active = 0
        self._enabled = True

        self._build_title_row()
        self._description = self._add_wrapped_label(preset.description, 12, theme.BODY_TEXT, (0, 10))
        self._build_progress_row()
        self._add_wrapped_label(f"Inclui: {' · '.join(tweak_names)}", 11, theme.MUTED_TEXT, (0, 14))
        self.bind("<Configure>", self._on_resize)

    def _build_title_row(self) -> None:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(16, 6))
        ctk.CTkLabel(
            row, text=self.preset.name, font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left")

        self._apply_button = ctk.CTkButton(
            row, text="Aplicar Preset", width=120, height=34, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
            command=lambda: self._on_apply(self.preset.id),
        )
        self._apply_button.pack(side="right")
        self._revert_button = ctk.CTkButton(
            row, text="Reverter", width=90, height=34, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=theme.NEUTRAL, text_color=theme.COBRA_YELLOW, hover_color=theme.NEUTRAL_HOVER,
            command=lambda: self._on_revert(self.preset.id),
        )
        self._revert_button.pack(side="right", padx=(0, 8))

    def _build_progress_row(self) -> None:
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 10))
        self._bar = ctk.CTkProgressBar(row, height=8, width=180)
        self._bar.pack(side="left")
        self._bar.set(0)
        self._progress_label = ctk.CTkLabel(
            row, text="Verificando...", font=ctk.CTkFont(size=11), text_color=theme.MUTED_TEXT
        )
        self._progress_label.pack(side="left", padx=(10, 0))

    def _add_wrapped_label(self, text: str, size: int, color, pady) -> ctk.CTkLabel:
        label = ctk.CTkLabel(
            self, text=text, font=ctk.CTkFont(size=size), text_color=color,
            wraplength=_MIN_WRAP, justify="left", anchor="w",
        )
        label.pack(fill="x", padx=18, pady=pady)
        return label

    def set_progress(self, active: int, total: int) -> None:
        """Mostra quantos tweaks reversíveis do preset já estão ativos."""
        self._active = active
        self._bar.set(active / total if total else 0)
        if total == 0:
            text = "Apenas ações pontuais (sem estado)"
        elif active == total:
            text = f"Totalmente aplicado ({active}/{total})"
        else:
            text = f"{active} de {total} ativos"
        self._progress_label.configure(text=text)
        self._refresh_revert_button()

    def set_interaction_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self._apply_button.configure(state="normal" if enabled else "disabled")
        self._refresh_revert_button()

    def _refresh_revert_button(self) -> None:
        self._revert_button.configure(state="normal" if self._enabled and self._active > 0 else "disabled")

    def _on_resize(self, event) -> None:
        wrap = max(_MIN_WRAP, event.width - _WRAP_MARGIN)
        for child in self.winfo_children():
            if isinstance(child, ctk.CTkLabel):
                child.configure(wraplength=wrap)

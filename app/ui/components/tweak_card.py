"""Componente visual para exibição individual de um Tweak."""
from typing import Callable

import customtkinter as ctk

from app.domain.entities import Tweak
from app.domain.enums import TweakKind, TweakStatus
from app.ui import theme

_MIN_WRAP = 240
_WRAP_MARGIN = 16


class TweakCard(ctk.CTkFrame):
    """Card que exibe as informações de um tweak e o botão de Aplicar/Reverter/Executar."""

    def __init__(
        self,
        master,
        tweak: Tweak,
        on_apply: Callable[[str], None],
        on_revert: Callable[[str], None],
        **kwargs,
    ):
        super().__init__(master, corner_radius=10, fg_color=theme.CARD_BG, **kwargs)
        self.tweak = tweak
        self._on_apply = on_apply
        self._on_revert = on_revert
        self._status = TweakStatus.PENDING
        self._interaction_enabled = True

        self.grid_columnconfigure(0, weight=1)
        self._build_info_column()
        self._build_action_column()
        self.set_status(TweakStatus.PENDING, pending_text="⏳ Verificando...")

    # --- Construção -------------------------------------------------------------------------

    def _build_info_column(self) -> None:
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.grid(row=0, column=0, sticky="nsew", padx=(16, 10), pady=14)

        header = ctk.CTkFrame(info, fg_color="transparent")
        header.pack(fill="x", anchor="w")
        ctk.CTkLabel(
            header, text=self.tweak.name, font=ctk.CTkFont(size=14, weight="bold"), anchor="w"
        ).pack(side="left")
        self._add_badges(header)

        self._summary = ctk.CTkLabel(
            info,
            text=self.tweak.summary,
            font=ctk.CTkFont(size=12),
            text_color=theme.BODY_TEXT,
            wraplength=_MIN_WRAP,
            justify="left",
            anchor="w",
        )
        self._summary.pack(fill="x", anchor="w", pady=(6, 4))
        info.bind("<Configure>", self._on_resize)

        if self.tweak.technical_detail:
            ctk.CTkLabel(
                info,
                text=f"⚙ {self.tweak.technical_detail}",
                font=ctk.CTkFont(size=10),
                text_color=("#888888", "#707070"),
                anchor="w",
            ).pack(fill="x", anchor="w")

        self._note = ctk.CTkLabel(info, text="", font=ctk.CTkFont(size=11, weight="bold"), anchor="w")

    def _add_badges(self, header: ctk.CTkFrame) -> None:
        self._badge(header, f" {self.tweak.category.value} ", theme.CATEGORY_COLORS.get(self.tweak.category, "#4a4a4a"), "#ffffff", 11)
        if self.tweak.risk in theme.RISK_COLORS:
            background, foreground = theme.RISK_COLORS[self.tweak.risk]
            self._badge(header, f" Risco {self.tweak.risk.value.lower()} ", background, foreground, 10)
        if self.tweak.requires_restart:
            self._badge(header, " 🔄 Reinício ", "#4a235a", "#d7bde2", 10)

    @staticmethod
    def _badge(parent, text: str, background: str, foreground: str, size: int) -> None:
        ctk.CTkLabel(
            parent,
            text=text,
            font=ctk.CTkFont(size=size, weight="bold"),
            fg_color=background,
            text_color=foreground,
            corner_radius=6,
            height=20,
        ).pack(side="left", padx=(8, 0))

    def _build_action_column(self) -> None:
        actions = ctk.CTkFrame(self, fg_color="transparent", width=140)
        actions.grid(row=0, column=1, sticky="ns", padx=(10, 16), pady=14)

        self._status_label = ctk.CTkLabel(actions, text="", font=ctk.CTkFont(size=12, weight="bold"))
        self._status_label.pack(pady=(4, 8))

        self._button = ctk.CTkButton(
            actions, text="", width=110, height=32, font=ctk.CTkFont(size=12, weight="bold"), command=self._on_click
        )
        self._button.pack()

    # --- Estado -----------------------------------------------------------------------------

    @property
    def status(self) -> TweakStatus:
        return self._status

    def set_status(
        self,
        status: TweakStatus,
        note: str = "",
        note_is_error: bool = False,
        pending_text: str = "",
    ) -> None:
        """Atualiza o estado exibido, com uma mensagem opcional de sucesso/erro."""
        self._status = status
        text, color = theme.STATUS_STYLE[status]
        if status == TweakStatus.INACTIVE and self.tweak.kind == TweakKind.ACTION:
            text = "Ação pontual"
        self._status_label.configure(text=pending_text or text, text_color=color)
        self._set_note(note, note_is_error)
        self._refresh_button()

    def set_interaction_enabled(self, enabled: bool) -> None:
        """Desabilita o botão enquanto outra operação do app está em andamento."""
        self._interaction_enabled = enabled
        self._refresh_button()

    def _set_note(self, note: str, is_error: bool) -> None:
        if not note:
            self._note.pack_forget()
            return
        self._note.configure(text=note, text_color=theme.COLOR_ERROR if is_error else theme.COLOR_SUCCESS)
        self._note.pack(fill="x", anchor="w", pady=(6, 0))

    def _refresh_button(self) -> None:
        text, color, hover = self._button_style()
        selectable = self._status not in (TweakStatus.PENDING, TweakStatus.UNSUPPORTED)
        self._button.configure(
            text=text,
            fg_color=color,
            hover_color=hover,
            state="normal" if selectable and self._interaction_enabled else "disabled",
        )

    def _button_style(self):
        if self._status == TweakStatus.UNSUPPORTED:
            return "Indisponível", theme.NEUTRAL, theme.NEUTRAL_HOVER
        if self.tweak.kind == TweakKind.ACTION:
            return "Executar", theme.ACCENT, theme.ACCENT_HOVER
        if self._status == TweakStatus.ACTIVE:
            return "Reverter", theme.NEUTRAL, theme.NEUTRAL_HOVER
        return "Aplicar", theme.ACCENT, theme.ACCENT_HOVER

    # --- Eventos ----------------------------------------------------------------------------

    def _on_click(self) -> None:
        if self._status == TweakStatus.ACTIVE and self.tweak.is_reversible:
            self._on_revert(self.tweak.id)
        else:
            self._on_apply(self.tweak.id)

    def _on_resize(self, event) -> None:
        self._summary.configure(wraplength=max(_MIN_WRAP, event.width - _WRAP_MARGIN))

"""Componente visual para exibição individual de um Tweak."""
import customtkinter as ctk
from typing import Callable
from app.domain.entities import Tweak
from app.domain.enums import TweakCategory, TweakStatus


CATEGORY_COLORS = {
    TweakCategory.LATENCY: ("#1f538d", "#2980b9"),        # Azul
    TweakCategory.FPS: ("#6c3483", "#8e44ad"),            # Roxo
    TweakCategory.RAM_PROCESSES: ("#b9770e", "#d68910"),  # Âmbar / Laranja
    TweakCategory.DISK_CLEANUP: ("#196f3d", "#27ae60"),   # Verde
}


class TweakCard(ctk.CTkFrame):
    """Card moderno que exibe as informações e ações de um Tweak."""

    def __init__(
        self,
        master,
        tweak: Tweak,
        on_apply: Callable[[str], None],
        on_revert: Callable[[str], None],
        **kwargs
    ):
        super().__init__(master, corner_radius=10, fg_color=("#2b2b2b", "#1e1e1e"), **kwargs)
        self.tweak = tweak
        self.on_apply = on_apply
        self.on_revert = on_revert

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        # Container esquerdo (Texto e Detalhes)
        left_container = ctk.CTkFrame(self, fg_color="transparent")
        left_container.grid(row=0, column=0, sticky="nsew", padx=(16, 10), pady=14)

        # Linha 1: Título e Tag de Categoria
        header_row = ctk.CTkFrame(left_container, fg_color="transparent")
        header_row.pack(fill="x", anchor="w")

        title_lbl = ctk.CTkLabel(
            header_row,
            text=tweak.name,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        title_lbl.pack(side="left")

        # Badge de categoria
        badge_color = CATEGORY_COLORS.get(tweak.category, ("#4a4a4a", "#4a4a4a"))
        cat_badge = ctk.CTkLabel(
            header_row,
            text=f" {tweak.category.value} ",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=badge_color[1],
            text_color="#ffffff",
            corner_radius=6,
            height=20
        )
        cat_badge.pack(side="left", padx=(10, 0))

        if tweak.requires_restart:
            restart_badge = ctk.CTkLabel(
                header_row,
                text=" 🔄 Reinício ",
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="#78281f",
                text_color="#f5b7b1",
                corner_radius=6,
                height=20
            )
            restart_badge.pack(side="left", padx=(6, 0))

        # Linha 2: Resumo
        summary_lbl = ctk.CTkLabel(
            left_container,
            text=tweak.summary,
            font=ctk.CTkFont(size=12),
            text_color=("#cccccc", "#a0a0a0"),
            wraplength=540,
            justify="left",
            anchor="w"
        )
        summary_lbl.pack(fill="x", anchor="w", pady=(6, 4))

        # Linha 3: Detalhes Técnicos
        if tweak.technical_detail:
            tech_lbl = ctk.CTkLabel(
                left_container,
                text=f"⚙️ {tweak.technical_detail}",
                font=ctk.CTkFont(size=10),
                text_color=("#888888", "#707070"),
                anchor="w"
            )
            tech_lbl.pack(fill="x", anchor="w")

        # Container direito (Status e Ação)
        right_container = ctk.CTkFrame(self, fg_color="transparent", width=140)
        right_container.grid(row=0, column=1, sticky="ns", padx=(10, 16), pady=14)

        # Status badge
        self.status_lbl = ctk.CTkLabel(
            right_container,
            text=self._format_status(tweak.status),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self._get_status_color(tweak.status)
        )
        self.status_lbl.pack(pady=(4, 8))

        # Botão Aplicar / Reverter
        self.action_btn = ctk.CTkButton(
            right_container,
            text="Reverter" if tweak.status == TweakStatus.ACTIVE else "Aplicar",
            width=100,
            height=32,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#34495e" if tweak.status == TweakStatus.ACTIVE else "#1f6aa5",
            hover_color="#2c3e50" if tweak.status == TweakStatus.ACTIVE else "#144870",
            command=self._on_button_click
        )
        self.action_btn.pack()

    def _format_status(self, status: TweakStatus) -> str:
        if status == TweakStatus.ACTIVE:
            return "● Ativo"
        elif status == TweakStatus.INACTIVE:
            return "○ Inativo"
        elif status == TweakStatus.PENDING:
            return "⏳ Processando..."
        return "⚠️ Erro"

    def _get_status_color(self, status: TweakStatus) -> str:
        if status == TweakStatus.ACTIVE:
            return "#2ecc71"  # Verde
        elif status == TweakStatus.INACTIVE:
            return "#95a5a6"  # Cinza
        return "#e74c3c"      # Vermelho

    def _on_button_click(self):
        if self.tweak.status == TweakStatus.ACTIVE:
            self.on_revert(self.tweak.id)
        else:
            self.on_apply(self.tweak.id)

    def update_status(self, status: TweakStatus):
        self.tweak.status = status
        self.status_lbl.configure(
            text=self._format_status(status),
            text_color=self._get_status_color(status)
        )
        is_active = (status == TweakStatus.ACTIVE)
        self.action_btn.configure(
            text="Reverter" if is_active else "Aplicar",
            fg_color="#34495e" if is_active else "#1f6aa5",
            hover_color="#2c3e50" if is_active else "#144870",
            state="normal"
        )

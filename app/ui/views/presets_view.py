"""Aba de Presets com perfis prontos de otimização."""
import threading
import customtkinter as ctk
from typing import Callable, List
from app.domain.entities import Preset
from app.use_cases.presets_manager import PresetsManager


class PresetsView(ctk.CTkFrame):
    """Visualização da aba de Presets de 1 clique."""

    def __init__(self, master, presets_manager: PresetsManager, on_preset_applied: Callable[[], None], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.presets_manager = presets_manager
        self.on_preset_applied = on_preset_applied
        self.is_busy = False

        self._build_header()
        self._build_progress_area()
        self._build_presets_list()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 10))

        title = ctk.CTkLabel(
            header_frame,
            text="🎯 Presets Rápidos",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header_frame,
            text="Aplique configurações otimizadas em lote com apenas um clique para diferentes cenários de uso.",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        subtitle.pack(anchor="w", pady=(2, 0))

    def _build_progress_area(self):
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.progress_lbl = ctk.CTkLabel(
            self.progress_frame,
            text="Aplicando preset...",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.progress_lbl.pack(anchor="w", padx=20, pady=(4, 4))

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=10)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 10))
        self.progress_bar.set(0)

    def _build_presets_list(self):
        scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_area.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        for preset in self.presets_manager.get_presets():
            card = self._create_preset_card(scroll_area, preset)
            card.pack(fill="x", pady=10)

    def _create_preset_card(self, master, preset: Preset) -> ctk.CTkFrame:
        card = ctk.CTkFrame(master, corner_radius=12, fg_color=("#2b2b2b", "#1e1e1e"))

        top_row = ctk.CTkFrame(card, fg_color="transparent")
        top_row.pack(fill="x", padx=18, pady=(16, 6))

        title_lbl = ctk.CTkLabel(
            top_row,
            text=f"{preset.icon}  {preset.name}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_lbl.pack(side="left")

        apply_btn = ctk.CTkButton(
            top_row,
            text="Aplicar Preset",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#1f6aa5",
            hover_color="#144870",
            width=120,
            height=34,
            command=lambda p_id=preset.id: self._apply_preset_threaded(p_id)
        )
        apply_btn.pack(side="right")

        desc_lbl = ctk.CTkLabel(
            card,
            text=preset.description,
            font=ctk.CTkFont(size=12),
            text_color=("#cccccc", "#a0a0a0"),
            wraplength=640,
            justify="left",
            anchor="w"
        )
        desc_lbl.pack(fill="x", padx=18, pady=(0, 10))

        # Tags com lista de tweaks inclusos
        tags_row = ctk.CTkFrame(card, fg_color="transparent")
        tags_row.pack(fill="x", padx=18, pady=(0, 14))

        count_badge = ctk.CTkLabel(
            tags_row,
            text=f" Inclusos ({len(preset.tweak_ids)} tweaks): ",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#888888"
        )
        count_badge.pack(side="left")

        tweaks_summary = ", ".join(preset.tweak_ids[:5])
        if len(preset.tweak_ids) > 5:
            tweaks_summary += f" +{len(preset.tweak_ids) - 5} outros"

        tweaks_names = ctk.CTkLabel(
            tags_row,
            text=tweaks_summary,
            font=ctk.CTkFont(size=11),
            text_color="#2b7de9"
        )
        tweaks_names.pack(side="left", padx=(4, 0))

        return card

    def _apply_preset_threaded(self, preset_id: str):
        if self.is_busy:
            return

        self.is_busy = True
        self.progress_frame.pack(fill="x", before=self.winfo_children()[-1])
        self.progress_bar.set(0)

        def progress_callback(current: int, total: int, tweak_name: str):
            fraction = current / total
            def update():
                self.progress_bar.set(fraction)
                self.progress_lbl.configure(text=f"Aplicando ({current}/{total}): {tweak_name}...")
            self.after(0, update)

        def worker():
            self.presets_manager.apply_preset(preset_id, progress_callback)
            
            def finalize():
                self.progress_frame.pack_forget()
                self.is_busy = False
                self.on_preset_applied()

            self.after(300, finalize)

        threading.Thread(target=worker, daemon=True).start()

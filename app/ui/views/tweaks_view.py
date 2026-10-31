"""Aba principal de Otimizações com filtros, botão Aplicar Todos e lista de cards."""
import threading
import customtkinter as ctk
from typing import Dict, List
from app.domain.entities import Tweak
from app.domain.enums import TweakCategory, TweakStatus
from app.ui.components.tweak_card import TweakCard
from app.use_cases.tweak_manager import TweakManager


class TweaksView(ctk.CTkFrame):
    """Visualização da lista de Tweaks com filtros e aplicação em lote."""

    def __init__(self, master, tweak_manager: TweakManager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.tweak_manager = tweak_manager
        self.current_category = TweakCategory.ALL
        self.card_widgets: Dict[str, TweakCard] = {}
        self.is_busy = False

        self._build_header()
        self._build_action_bar()
        self._build_progress_area()
        self._build_scrollable_list()
        self.refresh_list()

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(15, 5))

        title = ctk.CTkLabel(
            header_frame,
            text="⚡ Central de Otimizações",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title.pack(side="left")

        self.stats_lbl = ctk.CTkLabel(
            header_frame,
            text="Carregando status...",
            font=ctk.CTkFont(size=12),
            text_color="#888888"
        )
        self.stats_lbl.pack(side="right", padx=10)

    def _build_action_bar(self):
        action_bar = ctk.CTkFrame(self, fg_color=("#232323", "#1a1a1a"), corner_radius=10)
        action_bar.pack(fill="x", padx=20, pady=(5, 10))

        # Botão 'Aplicar Todos' em destaque LOGO ANTES da lista
        self.apply_all_btn = ctk.CTkButton(
            action_bar,
            text="⚡ Aplicar Todos os Tweaks",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#1f6aa5",
            hover_color="#144870",
            height=38,
            command=self._on_apply_all
        )
        self.apply_all_btn.pack(side="right", padx=12, pady=10)

        # Filtro de categorias por Segmented Button
        cat_values = [c.value for c in TweakCategory]
        self.seg_filter = ctk.CTkSegmentedButton(
            action_bar,
            values=cat_values,
            command=self._on_category_changed,
            font=ctk.CTkFont(size=11),
            selected_color="#2b7de9"
        )
        self.seg_filter.set(TweakCategory.ALL.value)
        self.seg_filter.pack(side="left", padx=12, pady=10)

    def _build_progress_area(self):
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        
        self.progress_lbl = ctk.CTkLabel(
            self.progress_frame,
            text="Aplicando alterações...",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.progress_lbl.pack(anchor="w", padx=20, pady=(2, 4))

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=10)
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 6))
        self.progress_bar.set(0)

    def _build_scrollable_list(self):
        self.scroll_list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_list.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _on_category_changed(self, selected_value: str):
        for cat in TweakCategory:
            if cat.value == selected_value:
                self.current_category = cat
                break
        self.refresh_list()

    def refresh_list(self):
        """Reconstrói a lista de cards com base no filtro atual."""
        for widget in self.scroll_list.winfo_children():
            widget.destroy()
        self.card_widgets.clear()

        tweaks = self.tweak_manager.get_tweaks(self.current_category)
        all_tweaks = self.tweak_manager.get_tweaks(TweakCategory.ALL)
        active_count = sum(1 for t in all_tweaks if t.status == TweakStatus.ACTIVE)
        self.stats_lbl.configure(text=f"{active_count} de {len(all_tweaks)} otimizações ativas")

        if not tweaks:
            empty_lbl = ctk.CTkLabel(
                self.scroll_list,
                text="Nenhum tweak encontrado nesta categoria.",
                font=ctk.CTkFont(size=13),
                text_color="#888888"
            )
            empty_lbl.pack(pady=40)
            return

        for tweak in tweaks:
            card = TweakCard(
                self.scroll_list,
                tweak=tweak,
                on_apply=self._apply_single_threaded,
                on_revert=self._revert_single_threaded
            )
            card.pack(fill="x", pady=6)
            self.card_widgets[tweak.id] = card

    def _apply_single_threaded(self, tweak_id: str):
        if self.is_busy:
            return
        
        card = self.card_widgets.get(tweak_id)
        if card:
            card.update_status(TweakStatus.PENDING)

        def worker():
            self.tweak_manager.apply_tweak(tweak_id)
            self.after(0, self.refresh_list)

        threading.Thread(target=worker, daemon=True).start()

    def _revert_single_threaded(self, tweak_id: str):
        if self.is_busy:
            return

        card = self.card_widgets.get(tweak_id)
        if card:
            card.update_status(TweakStatus.PENDING)

        def worker():
            self.tweak_manager.revert_tweak(tweak_id)
            self.after(0, self.refresh_list)

        threading.Thread(target=worker, daemon=True).start()

    def _on_apply_all(self):
        if self.is_busy:
            return

        self.is_busy = True
        self.apply_all_btn.configure(state="disabled", text="⚡ Aplicando...")
        self.progress_frame.pack(fill="x", before=self.scroll_list)
        self.progress_bar.set(0)

        tweaks_to_apply = self.tweak_manager.get_tweaks(self.current_category)

        def progress_callback(current: int, total: int, tweak_name: str):
            fraction = current / total
            def update():
                self.progress_bar.set(fraction)
                self.progress_lbl.configure(text=f"Aplicando ({current}/{total}): {tweak_name}...")
            self.after(0, update)

        def worker():
            restarts = self.tweak_manager.apply_batch(tweaks_to_apply, progress_callback)
            
            def finalize():
                self.progress_frame.pack_forget()
                self.apply_all_btn.configure(state="normal", text="⚡ Aplicar Todos os Tweaks")
                self.is_busy = False
                self.refresh_list()
                if restarts:
                    self._show_restart_dialog(restarts)

            self.after(300, finalize)

        threading.Thread(target=worker, daemon=True).start()

    def _show_restart_dialog(self, restart_tweaks: List[str]):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Aviso de Reinicialização")
        dialog.geometry("450x230")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="🔄 Reinicialização Recomendada",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(16, 8))

        ctk.CTkLabel(
            dialog,
            text=f"Alguns tweaks aplicados ({len(restart_tweaks)}) exigem reinício do Windows para surtir efeito total (ex: {restart_tweaks[0]}).\n\nDeseja reiniciar agora ou mais tarde?",
            wraplength=380,
            justify="center",
            font=ctk.CTkFont(size=12)
        ).pack(pady=10)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=15)

        ctk.CTkButton(
            btn_frame,
            text="Reiniciar Depois",
            width=130,
            fg_color="#34495e",
            hover_color="#2c3e50",
            command=dialog.destroy
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Reiniciar Agora",
            width=130,
            fg_color="#c0392b",
            hover_color="#962d22",
            command=dialog.destroy
        ).pack(side="left", padx=10)

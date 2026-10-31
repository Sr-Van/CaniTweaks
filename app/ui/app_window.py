"""Janela Principal da aplicação CustomTkinter."""
import customtkinter as ctk
from app.use_cases.tweak_manager import TweakManager
from app.use_cases.presets_manager import PresetsManager
from app.ui.views.tweaks_view import TweaksView
from app.ui.views.presets_view import PresetsView


class AppWindow(ctk.CTk):
    """Janela principal do utilitário de PC Tweaks."""

    def __init__(self, tweak_manager: TweakManager, presets_manager: PresetsManager):
        super().__init__()
        self.tweak_manager = tweak_manager
        self.presets_manager = presets_manager

        # Configurações gerais da Janela
        self.title("WinTweaks - Gaming & Performance Optimizer")
        self.geometry("1020x700")
        self.minsize(880, 580)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.grid_columnconfigure(0, weight=0)  # Sidebar fixa
        self.grid_columnconfigure(1, weight=1)  # Conteúdo responsivo
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()
        self._select_tab("tweaks")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=("#1f1f1f", "#141414"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        # Logotipo / Título
        app_title = ctk.CTkLabel(
            self.sidebar,
            text="⚡ WinTweaks",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w"
        )
        app_title.grid(row=0, column=0, padx=20, pady=(24, 2), sticky="w")

        app_sub = ctk.CTkLabel(
            self.sidebar,
            text="Gaming Optimizer",
            font=ctk.CTkFont(size=12),
            text_color="#888888",
            anchor="w"
        )
        app_sub.grid(row=1, column=0, padx=20, pady=(0, 24), sticky="w")

        # Botões de Navegação
        self.btn_tweaks = ctk.CTkButton(
            self.sidebar,
            text="⚡  Otimizações",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            anchor="w",
            corner_radius=8,
            command=lambda: self._select_tab("tweaks")
        )
        self.btn_tweaks.grid(row=2, column=0, padx=14, pady=6, sticky="ew")

        self.btn_presets = ctk.CTkButton(
            self.sidebar,
            text="🎯  Presets Rápidos",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40,
            anchor="w",
            corner_radius=8,
            command=lambda: self._select_tab("presets")
        )
        self.btn_presets.grid(row=3, column=0, padx=14, pady=6, sticky="ew")

        # Rodapé da Sidebar
        footer_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer_frame.grid(row=5, column=0, padx=16, pady=20, sticky="s")

        badge = ctk.CTkLabel(
            footer_frame,
            text="🛡️ Modo Pré-visualização",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#f39c12",
            fg_color="#33240a",
            corner_radius=6,
            height=22,
            padx=8
        )
        badge.pack(pady=(0, 4))

        ver_lbl = ctk.CTkLabel(
            footer_frame,
            text="v0.1.0 (Mock Preview)",
            font=ctk.CTkFont(size=10),
            text_color="#666666"
        )
        ver_lbl.pack()

    def _build_content_area(self):
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.tweaks_view = TweaksView(self.content_frame, self.tweak_manager)
        self.presets_view = PresetsView(
            self.content_frame,
            self.presets_manager,
            on_preset_applied=self.tweaks_view.refresh_list
        )

    def _select_tab(self, tab_name: str):
        if tab_name == "tweaks":
            self.presets_view.grid_forget()
            self.tweaks_view.grid(row=0, column=0, sticky="nsew")
            self.btn_tweaks.configure(fg_color="#1f6aa5")
            self.btn_presets.configure(fg_color="transparent")
            self.tweaks_view.refresh_list()
        else:
            self.tweaks_view.grid_forget()
            self.presets_view.grid(row=0, column=0, sticky="nsew")
            self.btn_presets.configure(fg_color="#1f6aa5")
            self.btn_tweaks.configure(fg_color="transparent")

"""Janela principal: barra lateral, avisos globais e troca de abas."""
from pathlib import Path
from typing import List

import customtkinter as ctk
from PIL import Image

from app import __version__
from app.ui import theme
from app.ui.fonts import apply_default_font, load_bundled_fonts
from app.ui.components.dialogs import RestartDialog
from app.ui.task_runner import UiTaskRunner
from app.ui.views.presets_view import PresetsView
from app.ui.views.tweaks_view import TweaksView
from app.use_cases.batch_runner import BatchRunner
from app.use_cases.presets_manager import PresetsManager
from app.use_cases.system_service import RESTART_DELAY_SECONDS, SystemService
from app.use_cases.tweak_manager import TweakManager

_TAB_TWEAKS = "tweaks"
_TAB_PRESETS = "presets"
_ASSETS = Path(__file__).resolve().parent.parent / "assets"


class AppWindow(ctk.CTk):
    """Janela principal do CaniTweaks."""

    def __init__(
        self,
        tweak_manager: TweakManager,
        presets_manager: PresetsManager,
        batch_runner: BatchRunner,
        system_service: SystemService,
    ):
        load_bundled_fonts()
        super().__init__()
        self._system = system_service
        self._info = system_service.get_info()
        self._pending_restart: List[str] = []

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme(str(_ASSETS / "caninana_theme.json"))
        apply_default_font()
        self.title("CaniTweaks - Gaming & Performance Optimizer")
        self.geometry("1100x740")
        self.minsize(940, 600)
        self.configure(fg_color=theme.SERPENT_BLACK)
        self._set_icon()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._tasks = UiTaskRunner(self)
        self._build_sidebar()
        self._build_content(tweak_manager, presets_manager, batch_runner)
        self._select_tab(_TAB_TWEAKS)

    # --- Construção -------------------------------------------------------------------------

    def _build_sidebar(self) -> None:
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=theme.SIDEBAR_BG)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(4, weight=1)

        ctk.CTkLabel(sidebar, text="CaniTweaks", font=ctk.CTkFont(size=20, weight="bold"), text_color=theme.COBRA_YELLOW, anchor="w").grid(
            row=0, column=0, padx=20, pady=(24, 2), sticky="w")
        ctk.CTkLabel(sidebar, text="Gaming Optimizer", font=ctk.CTkFont(size=12), text_color=theme.MUTED_TEXT,
                     anchor="w").grid(row=1, column=0, padx=20, pady=(0, 24), sticky="w")

        self._nav_buttons = {
            _TAB_TWEAKS: self._nav_button(sidebar, "Otimizações", _TAB_TWEAKS, row=2),
            _TAB_PRESETS: self._nav_button(sidebar, "Presets rápidos", _TAB_PRESETS, row=3),
        }
        self._build_sidebar_logo(sidebar)
        self._build_sidebar_footer(sidebar)

    def _set_icon(self) -> None:
        try:
            self.iconbitmap(str(_ASSETS / "caninana.ico"))
        except Exception:  # noqa: BLE001 - ícone é cosmético; nunca impede a abertura
            pass

    def _build_sidebar_logo(self, sidebar: ctk.CTkFrame) -> None:
        try:
            image = Image.open(_ASSETS / "caninana-logo.png")
            self._logo = ctk.CTkImage(light_image=image, dark_image=image, size=(180, 180))
        except Exception:  # noqa: BLE001 - sem logo a interface continua funcional
            return
        ctk.CTkLabel(sidebar, text="", image=self._logo, corner_radius=10).grid(
            row=4, column=0, padx=14, pady=10, sticky="s")

    def _nav_button(self, parent, text: str, tab: str, row: int) -> ctk.CTkButton:
        button = ctk.CTkButton(
            parent, text=text, font=ctk.CTkFont(size=13, weight="bold"), height=40, anchor="w",
            corner_radius=8, command=lambda: self._select_tab(tab),
        )
        button.grid(row=row, column=0, padx=14, pady=6, sticky="ew")
        return button

    def _build_sidebar_footer(self, sidebar: ctk.CTkFrame) -> None:
        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.grid(row=5, column=0, padx=14, pady=20, sticky="ew")

        text, color, background = (
            ("Administrador", theme.COLOR_SUCCESS, "#12301c") if self._info.is_admin
            else ("Sem administrador", theme.COLOR_WARNING, "#33240a")
        )
        ctk.CTkLabel(footer, text=text, font=ctk.CTkFont(size=11, weight="bold"), text_color=color,
                     fg_color=background, corner_radius=6, height=24).pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(footer, text=self._info.windows_label, font=ctk.CTkFont(size=10),
                     text_color="#666666").pack()
        ctk.CTkLabel(footer, text=f"v{__version__}", font=ctk.CTkFont(size=10), text_color="#666666").pack()

    def _build_content(self, tweak_manager, presets_manager, batch_runner) -> None:
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        self._banners = ctk.CTkFrame(content, fg_color="transparent", height=0)
        self._banners.grid(row=0, column=0, sticky="ew")
        self._build_admin_banner()
        self._build_restart_banner()

        self._tweaks_view = TweaksView(
            content, tweak_manager, batch_runner, self._tasks, self._info,
            self._register_restart_needed, self._open_restart_dialog,
        )
        self._presets_view = PresetsView(
            content, presets_manager, self._tasks, self._register_restart_needed, self._open_restart_dialog
        )
        self._views = {_TAB_TWEAKS: self._tweaks_view, _TAB_PRESETS: self._presets_view}

    def _build_admin_banner(self) -> None:
        if self._info.is_admin:
            return
        banner = ctk.CTkFrame(self._banners, fg_color="#2b2208", corner_radius=8)
        banner.pack(fill="x", padx=20, pady=(12, 0))
        ctk.CTkLabel(
            banner, text="Sem administrador: ajustes de sistema (HKLM, serviços, energia) vão falhar.",
            text_color=theme.COLOR_WARNING, font=ctk.CTkFont(size=12), anchor="w",
        ).pack(side="left", padx=12, pady=8)
        ctk.CTkButton(
            banner, text="Reabrir como admin", width=190, height=28, fg_color=theme.COLOR_WARNING,
            hover_color=theme.SCALE_GOLD, text_color=theme.ON_ACCENT, command=self._elevate,
        ).pack(side="right", padx=12)

    def _build_restart_banner(self) -> None:
        self._restart_banner = ctk.CTkFrame(self._banners, fg_color="#3a2d08", corner_radius=8)
        self._restart_label = ctk.CTkLabel(self._restart_banner, text="", font=ctk.CTkFont(size=12), anchor="w",
                                           text_color=theme.COBRA_YELLOW)
        self._restart_label.pack(side="left", padx=12, pady=8)
        ctk.CTkButton(
            self._restart_banner, text="Reiniciar...", width=110, height=28, fg_color=theme.DANGER,
            hover_color=theme.DANGER_HOVER, command=self._open_restart_dialog,
        ).pack(side="right", padx=12)

    # --- Navegação --------------------------------------------------------------------------

    def _select_tab(self, tab: str) -> None:
        for name, view in self._views.items():
            if name == tab:
                view.grid(row=1, column=0, sticky="nsew")
            else:
                view.grid_forget()
        for name, button in self._nav_buttons.items():
            button.configure(fg_color=theme.ACCENT if name == tab else "transparent",
                             text_color=theme.ON_ACCENT if name == tab else theme.COBRA_YELLOW,
                             hover_color=theme.SCALE_GOLD if name == tab else "#2a2a2a")
        self._views[tab].refresh_statuses()

    # --- Reinício e elevação ----------------------------------------------------------------

    def _register_restart_needed(self, names: List[str]) -> None:
        for name in names:
            if name not in self._pending_restart:
                self._pending_restart.append(name)
        count = len(self._pending_restart)
        self._restart_label.configure(text=f"Reinício pendente para concluir {count} otimização(ões).")
        self._restart_banner.pack(fill="x", padx=20, pady=(12, 0))

    def _open_restart_dialog(self) -> None:
        RestartDialog(
            self, self._pending_restart, self._system.restart_computer,
            self._system.cancel_restart, RESTART_DELAY_SECONDS,
        )

    def _elevate(self) -> None:
        if self._system.relaunch_as_admin():
            self.destroy()

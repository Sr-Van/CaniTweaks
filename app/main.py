"""Ponto de entrada principal da aplicação."""
import sys
from app.adapters.fake_tweak_adapter import FakeTweakAdapter
from app.use_cases.tweak_manager import TweakManager
from app.use_cases.presets_manager import PresetsManager
from app.ui.app_window import AppWindow


def main():
    # Instanciação das camadas de acordo com Clean Architecture
    tweak_adapter = FakeTweakAdapter()
    tweak_manager = TweakManager(tweak_adapter)
    presets_manager = PresetsManager(tweak_manager)

    # Inicialização da interface gráfica
    app = AppWindow(tweak_manager, presets_manager)
    app.mainloop()


if __name__ == "__main__":
    main()

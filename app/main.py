"""Ponto de entrada principal da aplicação."""
import sys

from app.bootstrap import build_application, configure_logging
from app.ui.app_window import AppWindow


def main() -> None:
    configure_logging()
    application = build_application()
    system = application.system_service

    # Pede elevação logo na abertura. Se o usuário recusar, o app segue em modo limitado
    # (a interface exibe um aviso e permite tentar novamente).
    if not system.get_info().is_admin and system.relaunch_as_admin():
        sys.exit(0)

    AppWindow(
        application.tweak_manager,
        application.presets_manager,
        application.batch_runner,
        system,
    ).mainloop()


if __name__ == "__main__":
    main()

"""Utilitários de verificação e elevação de privilégios de Administrador no Windows."""
import ctypes
import logging
import os
import subprocess
import sys

logger = logging.getLogger(__name__)

_SW_SHOWNORMAL = 1
_SHELL_EXECUTE_SUCCESS_THRESHOLD = 32  # ShellExecute retorna > 32 em caso de sucesso.


def is_admin() -> bool:
    """Verifica se o processo atual possui privilégios de Administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except (AttributeError, OSError):
        return False


def relaunch_as_admin() -> bool:
    """Reinicia o aplicativo pedindo elevação (UAC).

    Retorna True se o usuário aceitou — o chamador deve então encerrar o processo atual.
    Retorna False se a elevação foi recusada ou falhou.
    """
    executable, arguments = _build_launch_command()
    try:
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", executable, arguments, None, _SW_SHOWNORMAL
        )
    except (AttributeError, OSError):
        logger.exception("Falha ao solicitar elevação")
        return False
    return result > _SHELL_EXECUTE_SUCCESS_THRESHOLD


def _build_launch_command() -> tuple:
    """Monta (executável, argumentos) para relançar o app, em modo script ou PyInstaller."""
    if getattr(sys, "frozen", False):
        return sys.executable, subprocess.list2cmdline(sys.argv[1:])
    script = os.path.abspath(sys.argv[0])
    return sys.executable, subprocess.list2cmdline([script, *sys.argv[1:]])

"""Adaptador para consulta e controle de serviços do Windows."""
import logging
import re
from typing import Optional

from app.adapters.errors import SystemOperationError
from app.adapters.process_runner import CommandRunner
from app.adapters.registry_adapter import WindowsRegistryAdapter

logger = logging.getLogger(__name__)

_SERVICES_KEY = "HKLM\\SYSTEM\\CurrentControlSet\\Services"
_START_VALUE_TO_MODE = {2: "auto", 3: "demand", 4: "disabled"}
_SETTABLE_MODES = {"auto", "delayed-auto", "demand", "disabled"}

_STATE_RE = re.compile(r"STATE\s*:\s*(\d+)")
_SC_RUNNING = "4"
_ERROR_SERVICE_NOT_ACTIVE = 1062
_ERROR_SERVICE_ALREADY_RUNNING = 1056


class WindowsServiceAdapter:
    """Lê o modo de inicialização pelo registro (independe de idioma) e controla via sc.exe."""

    def __init__(self, registry: WindowsRegistryAdapter, runner: CommandRunner):
        self._registry = registry
        self._runner = runner

    def get_start_mode(self, name: str) -> Optional[str]:
        """Retorna 'auto', 'delayed-auto', 'demand', 'disabled', 'other' ou None se não existir."""
        service_key = f"{_SERVICES_KEY}\\{name}"
        start = self._registry.read(service_key, "Start")
        if start is None:
            return None
        mode = _START_VALUE_TO_MODE.get(start.value, "other")
        if mode == "auto":
            delayed = self._registry.read(service_key, "DelayedAutostart")
            if delayed is not None and delayed.value == 1:
                return "delayed-auto"
        return mode

    def is_running(self, name: str) -> bool:
        result = self._runner.run(["sc", "query", name])
        match = _STATE_RE.search(result.stdout)
        return bool(match) and match.group(1) == _SC_RUNNING

    def set_start_mode(self, name: str, mode: str) -> None:
        if mode not in _SETTABLE_MODES:
            raise SystemOperationError(f"Modo de inicialização inválido para '{name}': {mode}")
        result = self._runner.run(["sc", "config", name, "start=", mode])
        if not result.ok:
            raise SystemOperationError(self._failure_message("configurar", name, result.output))

    def stop(self, name: str) -> bool:
        """Tenta parar o serviço. Retorna False se não foi possível (não é tratado como erro fatal)."""
        result = self._runner.run(["sc", "stop", name])
        ok = result.ok or result.returncode == _ERROR_SERVICE_NOT_ACTIVE
        if not ok:
            logger.warning("Não foi possível parar o serviço %s: %s", name, result.output)
        return ok

    def start(self, name: str) -> bool:
        result = self._runner.run(["sc", "start", name])
        ok = result.ok or result.returncode == _ERROR_SERVICE_ALREADY_RUNNING
        if not ok:
            logger.warning("Não foi possível iniciar o serviço %s: %s", name, result.output)
        return ok

    @staticmethod
    def _failure_message(action: str, name: str, detail: str) -> str:
        return f"Falha ao {action} o serviço '{name}': {detail or 'verifique se está como Administrador'}"

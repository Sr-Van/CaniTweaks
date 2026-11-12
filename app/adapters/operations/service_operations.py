"""Operações sobre serviços do Windows."""
from typing import Any, Dict

from app.adapters.operations.base import SystemOperation
from app.adapters.services_adapter import WindowsServiceAdapter

_DISABLED = "disabled"


class DisableServiceOperation(SystemOperation):
    """Desativa e para um serviço. Serviço inexistente é considerado já otimizado."""

    def __init__(self, services: WindowsServiceAdapter, service_name: str, default_mode: str = "demand"):
        self._services = services
        self._name = service_name
        self._default_mode = default_mode

    @property
    def key(self) -> str:
        return f"service::{self._name}"

    def is_applied(self) -> bool:
        mode = self._services.get_start_mode(self._name)
        return mode is None or mode == _DISABLED

    def snapshot(self) -> Dict[str, Any]:
        mode = self._services.get_start_mode(self._name)
        if mode is None:
            return {"exists": False}
        return {"exists": True, "mode": mode, "running": self._services.is_running(self._name)}

    def apply(self) -> None:
        if self._services.get_start_mode(self._name) is None:
            return
        self._services.set_start_mode(self._name, _DISABLED)
        self._services.stop(self._name)

    def restore(self, snapshot: Dict[str, Any]) -> None:
        if not snapshot.get("exists"):
            return
        mode = snapshot["mode"]
        if mode != "other":
            self._services.set_start_mode(self._name, mode)
        if snapshot.get("running"):
            self._services.start(self._name)

    def reset_to_default(self) -> None:
        if self._services.get_start_mode(self._name) is not None:
            self._services.set_start_mode(self._name, self._default_mode)

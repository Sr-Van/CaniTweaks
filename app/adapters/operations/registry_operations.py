"""Operações baseadas em valores do Registro do Windows."""
import winreg
from typing import Any, Dict, List, Optional

from app.adapters.operations.base import SystemOperation
from app.adapters.registry_adapter import WindowsRegistryAdapter


class RegistryValueOperation(SystemOperation):
    """Define um único valor de registro e sabe restaurá-lo ao estado anterior."""

    def __init__(
        self,
        registry: WindowsRegistryAdapter,
        path: str,
        name: str,
        value: Any,
        default: Optional[Any] = None,
        reg_type: int = winreg.REG_DWORD,
    ):
        self._registry = registry
        self._path = path
        self._name = name
        self._value = value
        self._default = default  # None significa "remover o valor" (padrão do Windows).
        self._reg_type = reg_type

    @property
    def key(self) -> str:
        return f"{self._path}::{self._name}"

    def is_applied(self) -> bool:
        entry = self._registry.read(self._path, self._name)
        return entry is not None and entry.value == self._value

    def snapshot(self) -> Dict[str, Any]:
        entry = self._registry.read(self._path, self._name)
        if entry is None:
            return {"exists": False}
        return {"exists": True, "value": entry.value, "type": entry.reg_type}

    def apply(self) -> None:
        self._registry.write(self._path, self._name, self._value, self._reg_type)

    def restore(self, snapshot: Dict[str, Any]) -> None:
        if snapshot.get("exists"):
            self._registry.write(self._path, self._name, snapshot["value"], snapshot["type"])
        else:
            self._registry.delete(self._path, self._name)

    def reset_to_default(self) -> None:
        if self._default is None:
            self._registry.delete(self._path, self._name)
        else:
            self._registry.write(self._path, self._name, self._default, self._reg_type)


class InterfaceValuesOperation(SystemOperation):
    """Aplica os mesmos valores de registro em todas as subchaves de um caminho.

    Usado para ajustes por interface de rede (ex.: TcpAckFrequency / TCPNoDelay).
    """

    def __init__(self, registry: WindowsRegistryAdapter, parent_path: str, values: Dict[str, int]):
        self._registry = registry
        self._parent_path = parent_path
        self._values = values

    @property
    def key(self) -> str:
        return f"{self._parent_path}::*"

    def _children(self) -> List[RegistryValueOperation]:
        subkeys = self._registry.list_subkeys(self._parent_path)
        return [
            RegistryValueOperation(self._registry, f"{self._parent_path}\\{subkey}", name, value)
            for subkey in subkeys
            for name, value in self._values.items()
        ]

    def is_applied(self) -> bool:
        children = self._children()
        return bool(children) and all(child.is_applied() for child in children)

    def snapshot(self) -> Dict[str, Any]:
        return {child.key: child.snapshot() for child in self._children()}

    def apply(self) -> None:
        for child in self._children():
            child.apply()

    def restore(self, snapshot: Dict[str, Any]) -> None:
        for child in self._children():
            if child.key in snapshot:
                child.restore(snapshot[child.key])
            else:
                child.reset_to_default()  # Interface criada depois do backup.

    def reset_to_default(self) -> None:
        for child in self._children():
            child.reset_to_default()

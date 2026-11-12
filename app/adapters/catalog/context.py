"""Tipos e dependências compartilhados pelos módulos do catálogo de tweaks."""
import winreg
from dataclasses import dataclass, field
from typing import Any, List, Optional

from app.adapters.disk_clean_adapter import DiskCleanAdapter
from app.adapters.operations.base import ActionOperation, SystemOperation
from app.adapters.operations.registry_operations import RegistryValueOperation
from app.adapters.powercfg_adapter import PowerCfgAdapter
from app.adapters.registry_adapter import WindowsRegistryAdapter
from app.adapters.services_adapter import WindowsServiceAdapter
from app.domain.entities import Tweak


@dataclass(frozen=True)
class CatalogEntry:
    """Associa o tweak (metadados) às operações que o implementam no sistema."""

    tweak: Tweak
    operations: List[SystemOperation] = field(default_factory=list)
    action: Optional[ActionOperation] = None


@dataclass(frozen=True)
class CatalogContext:
    """Gateways do sistema usados para montar as operações do catálogo."""

    registry: WindowsRegistryAdapter
    services: WindowsServiceAdapter
    powercfg: PowerCfgAdapter
    cleaner: DiskCleanAdapter

    def reg(
        self,
        path: str,
        name: str,
        value: Any,
        default: Optional[Any] = None,
        reg_type: int = winreg.REG_DWORD,
    ) -> RegistryValueOperation:
        """Atalho para declarar um valor de registro. `default=None` remove o valor ao reverter."""
        return RegistryValueOperation(self.registry, path, name, value, default, reg_type)

    def reg_sz(self, path: str, name: str, value: str, default: str) -> RegistryValueOperation:
        """Atalho para valores de texto (REG_SZ)."""
        return self.reg(path, name, value, default, winreg.REG_SZ)

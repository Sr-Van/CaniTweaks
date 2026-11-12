"""Operações sobre planos e configurações de energia (powercfg)."""
from typing import Any, Dict

from app.adapters.operations.base import SystemOperation
from app.adapters.powercfg_adapter import PowerCfgAdapter

ULTIMATE_PERFORMANCE_GUID = "e9a42b02-d5df-448d-aa00-03f14749eb61"
# GUID fixo da nossa cópia do plano, para detectar e remover o plano de forma determinística.
WINTWEAKS_ULTIMATE_GUID = "e9a42b02-d5df-448d-aa00-03f14749eb62"
BALANCED_GUID = "381b4222-f694-41f0-9685-ff5bb260df2e"


class UltimatePerformancePlanOperation(SystemOperation):
    """Cria (se necessário) e ativa o plano oculto 'Desempenho Máximo'."""

    def __init__(self, powercfg: PowerCfgAdapter):
        self._powercfg = powercfg

    @property
    def key(self) -> str:
        return "powerplan::ultimate"

    def is_applied(self) -> bool:
        return self._powercfg.get_active_scheme() in (ULTIMATE_PERFORMANCE_GUID, WINTWEAKS_ULTIMATE_GUID)

    def snapshot(self) -> Dict[str, Any]:
        return {"previous": self._powercfg.get_active_scheme()}

    def apply(self) -> None:
        if WINTWEAKS_ULTIMATE_GUID not in self._powercfg.list_schemes():
            self._powercfg.duplicate_scheme(ULTIMATE_PERFORMANCE_GUID, WINTWEAKS_ULTIMATE_GUID)
        self._powercfg.set_active(WINTWEAKS_ULTIMATE_GUID)

    def restore(self, snapshot: Dict[str, Any]) -> None:
        self._activate_and_cleanup(snapshot.get("previous", BALANCED_GUID))

    def reset_to_default(self) -> None:
        self._activate_and_cleanup(BALANCED_GUID)

    def _activate_and_cleanup(self, target_guid: str) -> None:
        schemes = self._powercfg.list_schemes()
        if target_guid in schemes:
            self._powercfg.set_active(target_guid)
        if WINTWEAKS_ULTIMATE_GUID in schemes and target_guid != WINTWEAKS_ULTIMATE_GUID:
            self._powercfg.delete_scheme(WINTWEAKS_ULTIMATE_GUID)


class PowerSettingOperation(SystemOperation):
    """Altera uma configuração do plano de energia ativo (somente energia da tomada)."""

    def __init__(
        self,
        powercfg: PowerCfgAdapter,
        subgroup_guid: str,
        setting_guid: str,
        value: int,
        default: int,
    ):
        self._powercfg = powercfg
        self._subgroup = subgroup_guid
        self._setting = setting_guid
        self._value = value
        self._default = default

    @property
    def key(self) -> str:
        return f"powersetting::{self._subgroup}::{self._setting}"

    def is_applied(self) -> bool:
        return self._powercfg.get_ac_value(self._subgroup, self._setting) == self._value

    def snapshot(self) -> Dict[str, Any]:
        return {"value": self._powercfg.get_ac_value(self._subgroup, self._setting)}

    def apply(self) -> None:
        self._powercfg.set_ac_value(self._subgroup, self._setting, self._value)

    def restore(self, snapshot: Dict[str, Any]) -> None:
        self._powercfg.set_ac_value(self._subgroup, self._setting, snapshot["value"])

    def reset_to_default(self) -> None:
        self._powercfg.set_ac_value(self._subgroup, self._setting, self._default)

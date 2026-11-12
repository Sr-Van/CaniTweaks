"""Adaptador para o utilitário powercfg (planos e configurações de energia)."""
import re
from typing import List

from app.adapters.errors import SystemOperationError
from app.adapters.process_runner import CommandRunner

_GUID_RE = re.compile(r"[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}")
_HEX_RE = re.compile(r"0x[0-9a-fA-F]+")
_CURRENT_SCHEME = "SCHEME_CURRENT"


class PowerCfgAdapter:
    """Encapsula as chamadas ao powercfg, independentes do idioma do Windows."""

    def __init__(self, runner: CommandRunner):
        self._runner = runner

    def get_active_scheme(self) -> str:
        output = self._run("/getactivescheme")
        match = _GUID_RE.search(output)
        if not match:
            raise SystemOperationError("Não foi possível identificar o plano de energia ativo.")
        return match.group(0).lower()

    def list_schemes(self) -> List[str]:
        return [guid.lower() for guid in _GUID_RE.findall(self._run("/list"))]

    def duplicate_scheme(self, source_guid: str, target_guid: str) -> None:
        self._run("/duplicatescheme", source_guid, target_guid)

    def set_active(self, guid: str) -> None:
        self._run("/setactive", guid)

    def delete_scheme(self, guid: str) -> None:
        self._run("/delete", guid)

    def get_ac_value(self, subgroup_guid: str, setting_guid: str) -> int:
        """Lê o índice atual (energia da tomada) de uma configuração do plano ativo.

        A saída é localizada, então usa-se o penúltimo valor hexadecimal (CA), pois o
        último é o de bateria (CC).
        """
        output = self._run("/query", _CURRENT_SCHEME, subgroup_guid, setting_guid)
        values = _HEX_RE.findall(output)
        if len(values) < 2:
            raise SystemOperationError("Configuração de energia indisponível neste computador.")
        return int(values[-2], 16)

    def set_ac_value(self, subgroup_guid: str, setting_guid: str, value: int) -> None:
        self._run("/setacvalueindex", _CURRENT_SCHEME, subgroup_guid, setting_guid, str(value))
        self._run("/setactive", _CURRENT_SCHEME)  # Reaplica o plano para efetivar a mudança.

    def _run(self, *args: str) -> str:
        result = self._runner.run(["powercfg", *args])
        if not result.ok:
            raise SystemOperationError(f"powercfg {args[0]} falhou: {result.output or 'sem detalhes'}")
        return result.stdout

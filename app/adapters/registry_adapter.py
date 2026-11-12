"""Adaptador para leitura e escrita no Registro do Windows (HKLM / HKCU)."""
import logging
import winreg
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from app.adapters.errors import SystemOperationError

logger = logging.getLogger(__name__)

_HIVES = {
    "HKLM": winreg.HKEY_LOCAL_MACHINE,
    "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
    "HKCU": winreg.HKEY_CURRENT_USER,
    "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
}

# Garante a visão 64-bit do registro mesmo se o processo for 32-bit.
_VIEW_64 = winreg.KEY_WOW64_64KEY

_DWORD_MAX = 0xFFFFFFFF


@dataclass(frozen=True)
class RegistryEntry:
    """Valor lido do registro junto com seu tipo (REG_DWORD, REG_SZ...)."""

    value: Any
    reg_type: int


class WindowsRegistryAdapter:
    """Operações utilitárias sobre o Registro. Erros viram SystemOperationError."""

    def read(self, full_path: str, name: str) -> Optional[RegistryEntry]:
        """Lê um valor. Retorna None se a chave ou o valor não existirem."""
        hive, sub_key = self._split(full_path)
        try:
            with winreg.OpenKey(hive, sub_key, 0, winreg.KEY_READ | _VIEW_64) as key:
                value, reg_type = winreg.QueryValueEx(key, name)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise self._wrap("ler", full_path, name, exc) from exc
        return RegistryEntry(value, reg_type)

    def write(self, full_path: str, name: str, value: Any, reg_type: int = winreg.REG_DWORD) -> None:
        """Cria ou atualiza um valor, criando a chave se necessário."""
        self._validate(value, reg_type)
        hive, sub_key = self._split(full_path)
        try:
            with winreg.CreateKeyEx(hive, sub_key, 0, winreg.KEY_SET_VALUE | _VIEW_64) as key:
                winreg.SetValueEx(key, name, 0, reg_type, value)
        except OSError as exc:
            raise self._wrap("gravar", full_path, name, exc) from exc

    def delete(self, full_path: str, name: str) -> None:
        """Remove um valor. É idempotente: não falha se ele já não existir."""
        hive, sub_key = self._split(full_path)
        try:
            with winreg.OpenKey(hive, sub_key, 0, winreg.KEY_SET_VALUE | _VIEW_64) as key:
                winreg.DeleteValue(key, name)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise self._wrap("remover", full_path, name, exc) from exc

    def list_subkeys(self, full_path: str) -> List[str]:
        """Lista os nomes das subchaves. Retorna lista vazia se a chave não existir."""
        hive, sub_key = self._split(full_path)
        try:
            with winreg.OpenKey(hive, sub_key, 0, winreg.KEY_READ | _VIEW_64) as key:
                count = winreg.QueryInfoKey(key)[0]
                return [winreg.EnumKey(key, index) for index in range(count)]
        except FileNotFoundError:
            return []
        except OSError as exc:
            raise self._wrap("listar", full_path, "", exc) from exc

    @staticmethod
    def _split(full_path: str) -> Tuple[int, str]:
        hive_name, _, sub_key = full_path.partition("\\")
        hive = _HIVES.get(hive_name.upper())
        if hive is None:
            raise SystemOperationError(f"Hive do registro não suportada: {hive_name}")
        return hive, sub_key

    @staticmethod
    def _validate(value: Any, reg_type: int) -> None:
        if reg_type == winreg.REG_DWORD:
            valid = isinstance(value, int) and 0 <= value <= _DWORD_MAX
        elif reg_type == winreg.REG_SZ:
            valid = isinstance(value, str)
        else:
            raise SystemOperationError(f"Tipo de registro não suportado: {reg_type}")
        if not valid:
            raise SystemOperationError(f"Valor inválido para o tipo de registro: {value!r}")

    @staticmethod
    def _wrap(action: str, full_path: str, name: str, exc: OSError) -> SystemOperationError:
        target = f"{full_path}\\{name}" if name else full_path
        if isinstance(exc, PermissionError):
            message = f"Permissão negada ao {action} '{target}'. Execute como Administrador."
        else:
            message = f"Falha ao {action} '{target}': {exc}"
        logger.warning(message)
        return SystemOperationError(message)

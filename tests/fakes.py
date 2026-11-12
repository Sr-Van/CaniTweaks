"""Dublês de teste que substituem registro, serviços, powercfg e demais gateways do SO."""
from typing import Dict, List, Optional, Tuple

from app.adapters.catalog.context import CatalogContext
from app.adapters.disk_clean_adapter import CleanSummary
from app.adapters.errors import SystemOperationError
from app.adapters.process_runner import CommandResult
from app.adapters.registry_adapter import RegistryEntry
from app.domain.entities import Tweak
from app.domain.enums import TweakStatus
from app.domain.result import Result
from app.ports.restore_port import RestorePointPort
from app.ports.tweak_port import TweakPort

REG_DWORD = 4


class FakeRegistry:
    """Registro em memória com a mesma interface de WindowsRegistryAdapter."""

    def __init__(self):
        self.values: Dict[Tuple[str, str], RegistryEntry] = {}
        self.fail_writes_for: set = set()

    def read(self, path: str, name: str) -> Optional[RegistryEntry]:
        return self.values.get((path, name))

    def write(self, path: str, name: str, value, reg_type: int = REG_DWORD) -> None:
        if name in self.fail_writes_for:
            raise SystemOperationError(f"Permissão negada ao gravar '{name}'")
        self.values[(path, name)] = RegistryEntry(value, reg_type)

    def delete(self, path: str, name: str) -> None:
        self.values.pop((path, name), None)

    def list_subkeys(self, path: str) -> List[str]:
        prefix = path + "\\"
        return sorted({key[0][len(prefix):].split("\\")[0] for key in self.values if key[0].startswith(prefix)})

    def seed(self, path: str, name: str, value, reg_type: int = REG_DWORD) -> None:
        self.values[(path, name)] = RegistryEntry(value, reg_type)


class FakeServices:
    """Serviços do Windows em memória."""

    def __init__(self, services: Optional[Dict[str, dict]] = None):
        self.services = services if services is not None else {}

    def get_start_mode(self, name: str) -> Optional[str]:
        service = self.services.get(name)
        return service["mode"] if service else None

    def is_running(self, name: str) -> bool:
        return self.services[name]["running"]

    def set_start_mode(self, name: str, mode: str) -> None:
        self.services[name]["mode"] = mode

    def stop(self, name: str) -> bool:
        self.services[name]["running"] = False
        return True

    def start(self, name: str) -> bool:
        self.services[name]["running"] = True
        return True


class FakePowerCfg:
    """powercfg em memória."""

    def __init__(self, active: str = "381b4222-f694-41f0-9685-ff5bb260df2e"):
        self.active = active
        self.schemes = [active]
        self.ac_values: Dict[Tuple[str, str], int] = {}

    def get_active_scheme(self) -> str:
        return self.active

    def list_schemes(self) -> List[str]:
        return list(self.schemes)

    def duplicate_scheme(self, source: str, target: str) -> None:
        self.schemes.append(target)

    def set_active(self, guid: str) -> None:
        self.active = guid

    def delete_scheme(self, guid: str) -> None:
        self.schemes.remove(guid)

    def get_ac_value(self, subgroup: str, setting: str) -> int:
        return self.ac_values.get((subgroup, setting), 1)

    def set_ac_value(self, subgroup: str, setting: str, value: int) -> None:
        self.ac_values[(subgroup, setting)] = value


class FakeCleaner:
    """Limpador de disco que registra os diretórios recebidos."""

    def __init__(self, freed_bytes: int = 2048, failed_files: int = 0):
        self.calls: List[list] = []
        self._summary = CleanSummary(freed_bytes, failed_files)

    def clean(self, directories) -> CleanSummary:
        self.calls.append(list(directories))
        return self._summary


class FakeRunner:
    """CommandRunner que devolve uma resposta fixa e registra os comandos recebidos."""

    def __init__(self, stdout: str = "", returncode: int = 0, stderr: str = ""):
        self.commands: List[list] = []
        self._result = CommandResult(returncode, stdout, stderr)

    def run(self, args, timeout: float = 60) -> CommandResult:
        self.commands.append(list(args))
        return self._result


def make_context(registry=None, services=None, powercfg=None, cleaner=None) -> CatalogContext:
    """Cria um CatalogContext com dublês (cada argumento omitido vira um fake novo)."""
    return CatalogContext(
        registry=registry or FakeRegistry(),
        services=services or FakeServices(),
        powercfg=powercfg or FakePowerCfg(),
        cleaner=cleaner or FakeCleaner(),
    )


class InMemoryTweakPort(TweakPort):
    """TweakPort simples para testar casos de uso sem o catálogo real."""

    def __init__(self, tweaks: List[Tweak]):
        self._tweaks = tweaks
        self.statuses: Dict[str, TweakStatus] = {t.id: TweakStatus.INACTIVE for t in tweaks}
        self.fail_ids: set = set()
        self.calls: List[Tuple[str, str]] = []

    def get_all_tweaks(self) -> List[Tweak]:
        return list(self._tweaks)

    def check_status(self, tweak_id: str) -> TweakStatus:
        return self.statuses[tweak_id]

    def apply(self, tweak_id: str) -> Result:
        self.calls.append(("apply", tweak_id))
        if tweak_id in self.fail_ids:
            return Result.failure("falhou")
        self.statuses[tweak_id] = TweakStatus.ACTIVE
        tweak = next(t for t in self._tweaks if t.id == tweak_id)
        return Result.success(needs_restart=tweak.requires_restart)

    def revert(self, tweak_id: str) -> Result:
        self.calls.append(("revert", tweak_id))
        self.statuses[tweak_id] = TweakStatus.INACTIVE
        return Result.success()


class RecordingRestorePort(RestorePointPort):
    """Ponto de restauração falso que registra as descrições recebidas."""

    def __init__(self, result: Optional[Result] = None):
        self.descriptions: List[str] = []
        self._result = result or Result.success()

    def create_restore_point(self, description: str) -> Result:
        self.descriptions.append(description)
        return self._result

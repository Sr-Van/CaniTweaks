"""Raiz de composição: instancia e conecta adapters, casos de uso e configuração de log."""
import logging
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler

from app.adapters.app_paths import data_directory
from app.adapters.catalog import CatalogContext, build_catalog
from app.adapters.catalog_tweak_adapter import CatalogTweakAdapter
from app.adapters.disk_clean_adapter import DiskCleanAdapter
from app.adapters.powercfg_adapter import PowerCfgAdapter
from app.adapters.process_runner import CommandRunner
from app.adapters.registry_adapter import WindowsRegistryAdapter
from app.adapters.restore_adapter import SystemRestoreAdapter
from app.adapters.services_adapter import WindowsServiceAdapter
from app.adapters.state_backup import JsonStateBackup
from app.adapters.windows_system_adapter import WindowsSystemAdapter
from app.domain.presets import DEFAULT_PRESETS
from app.use_cases.batch_runner import BatchRunner
from app.use_cases.presets_manager import PresetsManager
from app.use_cases.system_service import SystemService
from app.use_cases.tweak_manager import TweakManager

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_LOG_MAX_BYTES = 512 * 1024
_LOG_BACKUP_COUNT = 2


@dataclass(frozen=True)
class Application:
    """Conjunto de casos de uso prontos para serem consumidos pela interface."""

    tweak_manager: TweakManager
    presets_manager: PresetsManager
    batch_runner: BatchRunner
    system_service: SystemService


def configure_logging() -> None:
    """Registra logs em %LOCALAPPDATA%/WinTweaks/wintweaks.log com rotação."""
    handler = RotatingFileHandler(
        data_directory() / "wintweaks.log",
        maxBytes=_LOG_MAX_BYTES,
        backupCount=_LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    logging.basicConfig(level=logging.INFO, handlers=[handler])


def build_application() -> Application:
    """Conecta todas as camadas seguindo Ports & Adapters."""
    runner = CommandRunner()
    registry = WindowsRegistryAdapter()
    system_port = WindowsSystemAdapter(runner)

    context = CatalogContext(
        registry=registry,
        services=WindowsServiceAdapter(registry, runner),
        powercfg=PowerCfgAdapter(runner),
        cleaner=DiskCleanAdapter(),
    )
    backup = JsonStateBackup(data_directory() / "state_backup.json")
    tweak_port = CatalogTweakAdapter(build_catalog(context), backup, system_port.get_info().windows_build)

    tweak_manager = TweakManager(tweak_port)
    batch_runner = BatchRunner(tweak_manager, SystemRestoreAdapter(runner))
    presets_manager = PresetsManager(DEFAULT_PRESETS, tweak_manager, batch_runner)
    return Application(tweak_manager, presets_manager, batch_runner, SystemService(system_port))

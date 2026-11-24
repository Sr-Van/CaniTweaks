"""Valida o catálogo de tweaks contra o Windows real.

Modos:
  (padrão)   Somente leitura: consulta o estado e o snapshot de cada operação e aponta falhas.
  --ciclo    Exige administrador. Para cada tweak inativo: aplica, confere, reverte e confirma
             que o estado original foi restaurado. Tweaks já ativos e ações são puladas.

Uso (na raiz do projeto):
  python -m scripts.validar_sistema
  python -m scripts.validar_sistema --ciclo
"""
import argparse
import sys
from typing import Any, Dict, List, Tuple

from app.adapters.catalog import CatalogContext, build_catalog
from app.adapters.catalog.context import CatalogEntry
from app.adapters.catalog_tweak_adapter import CatalogTweakAdapter
from app.adapters.disk_clean_adapter import DiskCleanAdapter
from app.adapters.errors import SystemOperationError
from app.adapters.powercfg_adapter import PowerCfgAdapter
from app.adapters.process_runner import CommandRunner
from app.adapters.registry_adapter import WindowsRegistryAdapter
from app.adapters.services_adapter import WindowsServiceAdapter
from app.adapters.state_backup import JsonStateBackup
from app.adapters.app_paths import data_directory
from app.adapters.windows_system_adapter import WindowsSystemAdapter
from app.domain.enums import TweakKind, TweakStatus

OK, FAIL, SKIP = "OK  ", "FALHA", "PULA"


def _build() -> Tuple[List[CatalogEntry], CatalogTweakAdapter, WindowsSystemAdapter]:
    runner = CommandRunner()
    registry = WindowsRegistryAdapter()
    system = WindowsSystemAdapter(runner)
    context = CatalogContext(
        registry=registry,
        services=WindowsServiceAdapter(registry, runner),
        powercfg=PowerCfgAdapter(runner),
        cleaner=DiskCleanAdapter(),
    )
    entries = build_catalog(context)
    backup = JsonStateBackup(data_directory() / "state_backup.json")
    return entries, CatalogTweakAdapter(entries, backup, system.get_info().windows_build), system


def _read_only(entry: CatalogEntry, port: CatalogTweakAdapter) -> List[str]:
    """Lê status e snapshot de cada operação. Retorna a lista de problemas encontrados."""
    problems: List[str] = []
    status = port.check_status(entry.tweak.id)
    if status == TweakStatus.UNKNOWN:
        problems.append("status UNKNOWN (leitura falhou; veja o log)")
    if status == TweakStatus.UNSUPPORTED or entry.tweak.kind == TweakKind.ACTION:
        return problems
    for operation in entry.operations:
        try:
            operation.is_applied()
            operation.snapshot()
        except (SystemOperationError, OSError) as exc:
            problems.append(f"{operation.key}: {exc}")
    return problems


def _snapshots(entry: CatalogEntry) -> Dict[str, Any]:
    return {operation.key: operation.snapshot() for operation in entry.operations}


def _cycle(entry: CatalogEntry, port: CatalogTweakAdapter) -> Tuple[str, str]:
    """Aplica e reverte um tweak. Retorna (resultado, detalhe)."""
    tweak = entry.tweak
    if tweak.kind == TweakKind.ACTION:
        return SKIP, "ação pontual"
    status = port.check_status(tweak.id)
    if status == TweakStatus.UNSUPPORTED:
        return SKIP, "indisponível nesta versão do Windows"
    if status != TweakStatus.INACTIVE:
        return SKIP, f"estado inicial {status.name}; não alterado para preservar sua configuração"

    before = _snapshots(entry)
    applied = port.apply(tweak.id)
    if not applied.ok:
        return FAIL, f"aplicar: {applied.error}"
    detail = ""
    if port.check_status(tweak.id) != TweakStatus.ACTIVE:
        detail = "aplicou mas o status não ficou ATIVO; "
    reverted = port.revert(tweak.id)
    if not reverted.ok:
        return FAIL, f"{detail}reverter: {reverted.error}"
    after = _snapshots(entry)
    if after != before:
        return FAIL, f"{detail}estado após reverter difere do original: {before} -> {after}"
    if detail:
        return FAIL, detail.rstrip("; ")
    return OK, "aplicou, ativou e restaurou o estado original"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ciclo", action="store_true", help="aplica e reverte cada tweak (exige administrador)")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")  # Acentos corretos mesmo em consoles cp1252.

    entries, port, system = _build()
    info = system.get_info()
    print(f"{info.windows_label} | administrador: {'sim' if info.is_admin else 'não'}")

    if args.ciclo and not info.is_admin:
        print("O modo --ciclo precisa de um terminal elevado (Executar como administrador).")
        return 2

    failures = 0
    for entry in entries:
        if args.ciclo:
            outcome, detail = _cycle(entry, port)
        else:
            problems = _read_only(entry, port)
            outcome, detail = (FAIL, "; ".join(problems)) if problems else (OK, port.check_status(entry.tweak.id).name)
        failures += outcome == FAIL
        print(f"[{outcome}] {entry.tweak.id}: {detail}")

    print(f"\n{len(entries)} tweaks, {failures} falha(s).")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

"""Catálogo declarativo de todos os tweaks suportados."""
from typing import List

from app.adapters.catalog.context import CatalogContext, CatalogEntry
from app.adapters.catalog.disk_cleanup import build_cleanup_entries
from app.adapters.catalog.fps import build_fps_entries
from app.adapters.catalog.input_devices import build_input_entries
from app.adapters.catalog.latency import build_latency_entries
from app.adapters.catalog.ram_processes import build_ram_entries


def build_catalog(ctx: CatalogContext) -> List[CatalogEntry]:
    """Monta o catálogo completo, na ordem em que os tweaks aparecem na interface."""
    return [
        *build_latency_entries(ctx),
        *build_fps_entries(ctx),
        *build_input_entries(ctx),
        *build_ram_entries(ctx),
        *build_cleanup_entries(ctx),
    ]


__all__ = ["CatalogContext", "CatalogEntry", "build_catalog"]

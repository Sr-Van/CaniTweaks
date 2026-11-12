"""Tweaks (ações pontuais) da categoria LIMPEZA DE DISCO."""
from typing import List

from app.adapters.catalog.context import CatalogContext, CatalogEntry
from app.adapters.operations.cleanup_action import CleanDirectoriesAction
from app.domain.entities import Tweak
from app.domain.enums import TweakCategory, TweakKind


def build_cleanup_entries(ctx: CatalogContext) -> List[CatalogEntry]:
    return [
        CatalogEntry(
            Tweak(
                id="clean_temp_files",
                name="Limpar Arquivos Temporários",
                summary="Remove arquivos obsoletos de instaladores, caches de jogos e logs antigos "
                        "das pastas temporárias do usuário e do sistema.",
                category=TweakCategory.DISK_CLEANUP,
                kind=TweakKind.ACTION,
                technical_detail="Pastas: %TEMP% e %SystemRoot%\\Temp (arquivos em uso são ignorados)",
            ),
            action=CleanDirectoriesAction(ctx.cleaner, ["%TEMP%", "%SystemRoot%\\Temp"]),
        ),
        CatalogEntry(
            Tweak(
                id="clean_prefetch_dumps",
                name="Limpar Prefetch, Relatórios de Erro e Dumps",
                summary="Esvazia o cache de pré-carregamento, relatórios de falha (WER) e dumps de "
                        "travamento. O Windows recria o Prefetch automaticamente.",
                category=TweakCategory.DISK_CLEANUP,
                kind=TweakKind.ACTION,
                technical_detail="Pastas: Prefetch, ProgramData\\...\\WER e Minidump",
            ),
            action=CleanDirectoriesAction(
                ctx.cleaner,
                [
                    "%SystemRoot%\\Prefetch",
                    "%ProgramData%\\Microsoft\\Windows\\WER\\ReportQueue",
                    "%ProgramData%\\Microsoft\\Windows\\WER\\ReportArchive",
                    "%SystemRoot%\\Minidump",
                ],
            ),
        ),
        CatalogEntry(
            Tweak(
                id="clean_shader_cache",
                name="Limpar Cache de Shaders",
                summary="Apaga caches de shaders do DirectX, NVIDIA e AMD. Resolve artefatos e "
                        "travamentos após atualizar drivers; o primeiro jogo recompila os shaders.",
                category=TweakCategory.DISK_CLEANUP,
                kind=TweakKind.ACTION,
                technical_detail="Pastas: %LOCALAPPDATA%\\D3DSCache, NVIDIA\\DXCache e AMD\\DxCache",
            ),
            action=CleanDirectoriesAction(
                ctx.cleaner,
                [
                    "%LOCALAPPDATA%\\D3DSCache",
                    "%LOCALAPPDATA%\\NVIDIA\\DXCache",
                    "%LOCALAPPDATA%\\NVIDIA\\GLCache",
                    "%LOCALAPPDATA%\\AMD\\DxCache",
                ],
            ),
        ),
    ]

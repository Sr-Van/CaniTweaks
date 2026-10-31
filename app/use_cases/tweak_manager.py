"""Caso de Uso para Gerenciamento e Execução de Tweaks."""
from typing import Callable, List, Optional
from app.domain.entities import Tweak
from app.domain.enums import TweakCategory, TweakStatus
from app.ports.tweak_port import TweakPort


class TweakManager:
    """Orquestra a consulta e aplicação de tweaks."""

    def __init__(self, port: TweakPort):
        self._port = port

    def get_tweaks(self, category_filter: TweakCategory = TweakCategory.ALL) -> List[Tweak]:
        """Retorna os tweaks aplicando o filtro de categoria se selecionado."""
        all_tweaks = self._port.get_all_tweaks()
        if category_filter == TweakCategory.ALL:
            return all_tweaks
        return [t for t in all_tweaks if t.category == category_filter]

    def apply_tweak(self, tweak_id: str) -> bool:
        """Aplica um tweak individual."""
        return self._port.apply(tweak_id)

    def revert_tweak(self, tweak_id: str) -> bool:
        """Reverte um tweak individual."""
        return self._port.revert(tweak_id)

    def apply_batch(
        self,
        tweaks: List[Tweak],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[str]:
        """
        Aplica uma lista de tweaks sequencialmente disparando callbacks de progresso.
        Retorna lista de IDs que necessitam de reinicialização.
        """
        total = len(tweaks)
        restart_needed: List[str] = []

        for idx, tweak in enumerate(tweaks, start=1):
            if progress_callback:
                progress_callback(idx, total, tweak.name)

            success = self._port.apply(tweak.id)
            if success and tweak.requires_restart:
                restart_needed.append(tweak.name)

        return restart_needed

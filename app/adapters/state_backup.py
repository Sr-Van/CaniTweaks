"""Persistência em JSON do estado original do usuário antes de cada tweak."""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

Snapshot = Dict[str, Any]


class JsonStateBackup:
    """Guarda, por tweak, os valores originais para que a reversão restaure o que o usuário tinha."""

    def __init__(self, file_path: Path):
        self._file_path = file_path

    def get(self, tweak_id: str) -> Optional[Snapshot]:
        return self._load().get(tweak_id)

    def save(self, tweak_id: str, snapshot: Snapshot) -> None:
        data = self._load()
        data[tweak_id] = snapshot
        self._write(data)

    def delete(self, tweak_id: str) -> None:
        data = self._load()
        if data.pop(tweak_id, None) is not None:
            self._write(data)

    def _load(self) -> Dict[str, Snapshot]:
        try:
            with open(self._file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError:
            return {}
        except (OSError, json.JSONDecodeError):
            logger.exception("Backup de estado ilegível; será recriado: %s", self._file_path)
            return {}
        return data if isinstance(data, dict) else {}

    def _write(self, data: Dict[str, Snapshot]) -> None:
        """Escrita atômica: grava em arquivo temporário e substitui o original."""
        temp_path = self._file_path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        os.replace(temp_path, self._file_path)

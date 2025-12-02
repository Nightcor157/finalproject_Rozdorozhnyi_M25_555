
from __future__ import annotations

import json
import os
from json import JSONDecodeError
from typing import Any

from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:

    _instance: "DatabaseManager | None" = None

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_paths()
        return cls._instance

    def _init_paths(self) -> None:
        settings = SettingsLoader()
        data_dir = settings.get("DATA_DIR")
        os.makedirs(data_dir, exist_ok=True)
        self.data_dir = data_dir

    def load_json(self, path: str, default: Any) -> Any:
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, JSONDecodeError):
            return default

    def save_json(self, path: str, data: Any) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)


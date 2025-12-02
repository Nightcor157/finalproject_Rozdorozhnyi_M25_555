
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


class SettingsLoader:

    _instance: Optional["SettingsLoader"] = None

    def __new__(cls) -> "SettingsLoader":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_settings()
        return cls._instance

    def _init_settings(self) -> None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(os.path.dirname(base_dir))
        config_path = os.path.join(base_dir, "config.json")

        defaults: Dict[str, Any] = {
            "DATA_DIR": os.path.join(base_dir, "data"),
            "RATES_TTL_SECONDS": 31536000,  # 1 год — кэш почти не протухает
            "BASE_CURRENCY": "USD",
            "LOG_DIR": os.path.join(base_dir, "logs"),
            "LOG_FILE": os.path.join(base_dir, "logs", "actions.log"),
            "LOG_LEVEL": "INFO",
        }

        self._settings: Dict[str, Any] = defaults

        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as file:
                    loaded = json.load(file)
                self._settings.update(loaded)
            except Exception:
                pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def reload(self) -> None:
        self._init_settings()


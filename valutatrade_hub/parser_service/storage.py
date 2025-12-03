
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List

from .config import ParserConfig


def _atomic_write(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


class RatesStorage:

    def __init__(self, config: ParserConfig) -> None:
        self.rates_path = config.RATES_FILE_PATH
        self.history_path = config.HISTORY_FILE_PATH

    # ---------- snapshot (rates.json) ----------

    def load_snapshot(self) -> Dict[str, Any]:
        try:
            with open(self.rates_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_snapshot(
        self,
        pairs_rates: Dict[str, float],
        sources: Dict[str, str],
    ) -> str:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        data: Dict[str, Any] = {"pairs": {}, "last_refresh": now}
        for pair, rate in pairs_rates.items():
            src = sources.get(pair, "ParserService")
            data["pairs"][pair] = {
                "rate": rate,
                "updated_at": now,
                "source": src,
            }
        _atomic_write(self.rates_path, data)
        return now


    def append_history(
        self,
        pairs_rates: Dict[str, float],
        source: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        try:
            with open(self.history_path, "r", encoding="utf-8") as file:
                history: List[Dict[str, Any]] = json.load(file)
                if not isinstance(history, list):
                    history = []
        except (FileNotFoundError, json.JSONDecodeError):
            history = []

        for pair, rate in pairs_rates.items():
            try:
                from_code, to_code = pair.split("_", 1)
            except ValueError:
                continue
            entry_id = f"{from_code}_{to_code}_{now}"
            history.append(
                {
                    "id": entry_id,
                    "from_currency": from_code,
                    "to_currency": to_code,
                    "rate": float(rate),
                    "timestamp": now,
                    "source": source,
                    "meta": {
                        "source_client": source,
                    },
                },
            )

        _atomic_write(self.history_path, history)


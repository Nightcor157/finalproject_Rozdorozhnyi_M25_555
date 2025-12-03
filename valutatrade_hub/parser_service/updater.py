from __future__ import annotations

from typing import Dict, Iterable, Tuple

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.logging_config import get_logger

from .api_clients import BaseApiClient
from .storage import RatesStorage


class RatesUpdater:
    def __init__(
        self,
        clients: Iterable[BaseApiClient],
        storage: RatesStorage,
    ) -> None:
        self.clients = list(clients)
        self.storage = storage
        self.logger = get_logger()

    def run_update(self) -> Tuple[str, int, str]:
        self.logger.info("Starting rates update...")

        all_pairs: Dict[str, float] = {}
        sources: Dict[str, str] = {}
        errors: Dict[str, str] = {}

        for client in self.clients:
            self.logger.info("Fetching from %s...", client.name)
            try:
                rates = client.fetch_rates()
                self.logger.info(
                    "Fetching from %s... OK (%d rates)",
                    client.name,
                    len(rates),
                )
                for pair, rate in rates.items():
                    all_pairs[pair] = rate
                    sources[pair] = client.name
            except ApiRequestError as exc:
                msg = str(exc)
                errors[client.name] = msg
                self.logger.error(
                    "Failed to fetch from %s: %s",
                    client.name,
                    msg,
                )

        if not all_pairs and errors:
            raise ApiRequestError("Не удалось получить курсы ни от одного источника.")

        last_refresh = self.storage.save_snapshot(all_pairs, sources)

        for client_name in set(sources.values()):
            client_pairs = {
                pair: rate
                for pair, rate in all_pairs.items()
                if sources.get(pair) == client_name
            }
            if client_pairs:
                self.storage.append_history(client_pairs, client_name)

        total = len(all_pairs)
        if errors:
            message = (
                "Update completed with errors. "
                "Проверьте логи для деталей."
            )
        else:
            message = "Update successful."

        self.logger.info(
            "Rates update finished: %d pairs, last_refresh=%s",
            total,
            last_refresh,
        )
        return message, total, last_refresh


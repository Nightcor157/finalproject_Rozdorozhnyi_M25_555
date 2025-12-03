
from __future__ import annotations

import time

from .updater import RatesUpdater


def run_periodic(updater: RatesUpdater, interval_seconds: int) -> None:
    while True:
        updater.run_update()
        time.sleep(interval_seconds)


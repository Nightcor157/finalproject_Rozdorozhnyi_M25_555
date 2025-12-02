
from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler

from valutatrade_hub.infra.settings import SettingsLoader

_LOGGER_NAME = "valutatrade"


def _setup_logging() -> logging.Logger:
    settings = SettingsLoader()
    log_dir = settings.get("LOG_DIR")
    log_file = settings.get("LOG_FILE")
    log_level_str = settings.get("LOG_LEVEL", "INFO")

    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(_LOGGER_NAME)
    if logger.handlers:
        return logger  # уже настроен

    level = getattr(logging, log_level_str.upper(), logging.INFO)
    logger.setLevel(level)

    handler = RotatingFileHandler(
        log_file,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(levelname)s %(asctime)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger


def get_logger() -> logging.Logger:
    return _setup_logging()


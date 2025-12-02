
from __future__ import annotations

from datetime import datetime
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from valutatrade_hub.logging_config import get_logger

F = TypeVar("F", bound=Callable[..., Any])


def log_action(action: str, verbose: bool = False) -> Callable[[F], F]:

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = get_logger()
            timestamp = datetime.now().isoformat()
            username = None
            currency = None
            amount = None

            for arg in list(args) + list(kwargs.values()):
                if hasattr(arg, "username"):
                    username = getattr(arg, "username")
                if isinstance(arg, str) and len(arg) <= 5:
                    # может быть код валюты
                    currency = arg.upper()
                if isinstance(arg, (int, float)) and amount is None:
                    amount = float(arg)

            try:
                result = func(*args, **kwargs)
                logger.info(
                    "%s %s user=%r currency=%r amount=%r result=OK",
                    action,
                    timestamp,
                    username,
                    currency,
                    amount,
                )
                if verbose:
                    logger.debug("Result: %r", result)
                return result
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "%s %s user=%r currency=%r amount=%r result=ERROR "
                    "error_type=%s error_message=%s",
                    action,
                    timestamp,
                    username,
                    currency,
                    amount,
                    type(exc).__name__,
                    str(exc),
                )
                raise

        return cast(F, wrapper)

    return decorator


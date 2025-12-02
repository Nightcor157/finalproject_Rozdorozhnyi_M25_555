
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

from .exceptions import CurrencyNotFoundError


@dataclass
class Currency(ABC):

    name: str
    code: str

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Имя валюты не может быть пустым.")
        normalized = self.code.upper()
        if not (2 <= len(normalized) <= 5) or " " in normalized:
            raise ValueError("Код валюты должен быть 2–5 символов без пробелов.")
        self.code = normalized

    @abstractmethod
    def get_display_info(self) -> str:
        raise NotImplementedError


@dataclass
class FiatCurrency(Currency):

    issuing_country: str

    def get_display_info(self) -> str:
        return (
            f"[FIAT] {self.code} — {self.name} "
            f"(Issuing: {self.issuing_country})"
        )


@dataclass
class CryptoCurrency(Currency):

    algorithm: str
    market_cap: float

    def get_display_info(self) -> str:
        return (
            f"[CRYPTO] {self.code} — {self.name} "
            f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})"
        )



_CURRENCY_REGISTRY: Dict[str, Currency] = {
    "USD": FiatCurrency(name="US Dollar", code="USD", issuing_country="United States"),
    "EUR": FiatCurrency(name="Euro", code="EUR", issuing_country="Eurozone"),
    "RUB": FiatCurrency(name="Russian Ruble", code="RUB", issuing_country="Russia"),
    "BTC": CryptoCurrency(
        name="Bitcoin",
        code="BTC",
        algorithm="SHA-256",
        market_cap=1.12e12,
    ),
    "ETH": CryptoCurrency(
        name="Ethereum",
        code="ETH",
        algorithm="Ethash",
        market_cap=4.80e11,
    ),
}


def get_currency(code: str) -> Currency:
    if not code:
        raise CurrencyNotFoundError(code="") 
    normalized = code.upper()
    try:
        return _CURRENCY_REGISTRY[normalized]
    except KeyError:
        raise CurrencyNotFoundError(normalized)


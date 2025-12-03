from abc import ABC, abstractmethod
from typing import Dict

import requests

from valutatrade_hub.core.exceptions import ApiRequestError

from .config import ParserConfig


class BaseApiClient(ABC):
    def __init__(self, config: ParserConfig) -> None:
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        raise NotImplementedError


class CoinGeckoClient(BaseApiClient):
    @property
    def name(self) -> str:
        return "CoinGecko"

    def fetch_rates(self) -> Dict[str, float]:
        ids = ",".join(self.config.CRYPTO_ID_MAP.values())
        vs_currency = self.config.BASE_CURRENCY.lower()
        params = {"ids": ids, "vs_currencies": vs_currency}

        try:
            response = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT,
            )
        except requests.exceptions.RequestException as exc:  # noqa: TRY003
            raise ApiRequestError(f"CoinGecko: ошибка сети: {exc}") from exc

        if response.status_code != 200:
            raise ApiRequestError(f"CoinGecko: HTTP {response.status_code}")

        try:
            data = response.json()
        except ValueError as exc:
            raise ApiRequestError("CoinGecko: некорректный JSON") from exc

        rates: Dict[str, float] = {}
        for code, coin_id in self.config.CRYPTO_ID_MAP.items():
            coin_info = data.get(coin_id)
            if not isinstance(coin_info, dict):
                continue
            price = coin_info.get(vs_currency)
            if price is None:
                continue
            try:
                price_f = float(price)
            except (TypeError, ValueError):
                continue
            pair = f"{code.upper()}_{self.config.BASE_CURRENCY}"
            rates[pair] = price_f

        return rates


class ExchangeRateApiClient(BaseApiClient):
    @property
    def name(self) -> str:
        return "ExchangeRate-API"

    def fetch_rates(self) -> Dict[str, float]:
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("Ключ EXCHANGERATE_API_KEY не задан.")

        url = (
            f"{self.config.EXCHANGERATE_API_URL}/"
            f"{self.config.EXCHANGERATE_API_KEY}/latest/"
            f"{self.config.BASE_CURRENCY}"
        )

        try:
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
        except requests.exceptions.RequestException as exc:  # noqa: TRY003
            raise ApiRequestError(f"ExchangeRate-API: ошибка сети: {exc}") from exc

        if response.status_code != 200:
            raise ApiRequestError(
                f"ExchangeRate-API: HTTP {response.status_code}",
            )

        try:
            data = response.json()
        except ValueError as exc:
            raise ApiRequestError("ExchangeRate-API: некорректный JSON") from exc

        if data.get("result") != "success":
            raise ApiRequestError(
                f"ExchangeRate-API: результат {data.get('result')}",
            )

        rates_data = data.get("rates") or data.get("conversion_rates") or {}
        rates: Dict[str, float] = {}

        for code in self.config.FIAT_CURRENCIES:
            value = rates_data.get(code)
            if value is None:
                continue
            try:
                rate_f = float(value)
            except (TypeError, ValueError):
                continue
            pair = f"{code}_{self.config.BASE_CURRENCY}"
            rates[pair] = rate_f

        return rates

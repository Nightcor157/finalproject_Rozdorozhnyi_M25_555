
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Dict, Optional


class User:

    def __init__(
        self,
        user_id: int,
        username: str,
        hashed_password: str,
        salt: str,
        registration_date: datetime,
    ) -> None:
        self._user_id = user_id
        self.username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date


    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        value = f"{password}{salt}".encode("utf-8")
        return hashlib.sha256(value).hexdigest()


    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = value

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date


    def get_user_info(self) -> dict:
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
        }

    def change_password(self, new_password: str) -> None:
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        self._hashed_password = self._hash_password(new_password, self._salt)

    def verify_password(self, password: str) -> bool:
        expected = self._hash_password(password, self._salt)
        return expected == self._hashed_password


class Wallet:

    def __init__(self, currency_code: str, balance: float = 0.0) -> None:
        self.currency_code = currency_code.upper()
        self.balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if not isinstance(value, (int, float)):
            raise ValueError("Баланс должен быть числом.")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = float(value)


    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        self._balance += float(amount)

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")
        if amount > self._balance:
            raise ValueError("Недостаточно средств для списания.")
        self._balance -= float(amount)

    def get_balance_info(self) -> str:
        return f"{self.currency_code}: {self._balance:.4f}"


class Portfolio:

    def __init__(
        self,
        user_id: int,
        wallets: Optional[Dict[str, Wallet]] = None,
    ) -> None:
        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = wallets or {}


    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        return dict(self._wallets)


    def add_currency(self, currency_code: str) -> Wallet:
        code = currency_code.upper()
        if code in self._wallets:
            raise ValueError(f"Кошелёк '{code}' уже существует.")
        wallet = Wallet(code, 0.0)
        self._wallets[code] = wallet
        return wallet

    def get_wallet(self, currency_code: str) -> Optional[Wallet]:
        return self._wallets.get(currency_code.upper())

    def get_total_value(
        self,
        exchange_rates: Dict[str, float],
        base_currency: str = "USD",
    ) -> float:
        base = base_currency.upper()
        if base != "USD":
            raise ValueError(f"Неизвестная базовая валюта '{base}'")

        total = 0.0
        for code, wallet in self._wallets.items():
            if code == base:
                total += wallet.balance
            else:
                pair = f"{code}_{base}"
                rate = exchange_rates.get(pair)
                if rate is None:
                    continue
                total += wallet.balance * rate
        return total


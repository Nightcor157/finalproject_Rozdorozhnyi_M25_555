
from __future__ import annotations

import json
import os
from datetime import datetime
from json import JSONDecodeError
from typing import Any, Dict, List, Optional

from .models import Portfolio, User, Wallet

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PORTFOLIOS_FILE = os.path.join(DATA_DIR, "portfolios.json")
RATES_FILE = os.path.join(DATA_DIR, "rates.json")


def _ensure_data_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)




def load_users() -> List[Dict[str, Any]]:
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, JSONDecodeError):
        return []


def save_users(users: List[Dict[str, Any]]) -> None:
    _ensure_data_dir()
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=2)


def next_user_id(users: List[Dict[str, Any]]) -> int:
    if not users:
        return 1
    return max(user["user_id"] for user in users) + 1


def find_user_by_username(
    users: List[Dict[str, Any]],
    username: str,
) -> Optional[Dict[str, Any]]:
    for user in users:
        if user["username"] == username:
            return user
    return None


def user_from_record(record: Dict[str, Any]) -> User:
    return User(
        user_id=record["user_id"],
        username=record["username"],
        hashed_password=record["hashed_password"],
        salt=record["salt"],
        registration_date=datetime.fromisoformat(record["registration_date"]),
    )




def load_portfolios() -> List[Dict[str, Any]]:
    try:
        with open(PORTFOLIOS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, JSONDecodeError):
        return []


def save_portfolios(portfolios: List[Dict[str, Any]]) -> None:
    _ensure_data_dir()
    with open(PORTFOLIOS_FILE, "w", encoding="utf-8") as file:
        json.dump(portfolios, file, ensure_ascii=False, indent=2)


def find_portfolio_record(
    portfolios: List[Dict[str, Any]],
    user_id: int,
) -> Optional[Dict[str, Any]]:
    for record in portfolios:
        if record["user_id"] == user_id:
            return record
    return None


def portfolio_from_record(record: Dict[str, Any]) -> Portfolio:
    wallets_data = record.get("wallets", {})
    wallets: Dict[str, Wallet] = {}
    for code, w_data in wallets_data.items():
        balance = float(w_data.get("balance", 0.0))
        wallets[code] = Wallet(currency_code=code, balance=balance)
    return Portfolio(user_id=record["user_id"], wallets=wallets)


def portfolio_to_record(portfolio: Portfolio) -> Dict[str, Any]:
    wallets_dict: Dict[str, Dict[str, Any]] = {}
    for code, wallet in portfolio.wallets.items():
        wallets_dict[code] = {
            "currency_code": wallet.currency_code,
            "balance": wallet.balance,
        }
    return {
        "user_id": portfolio.user_id,
        "wallets": wallets_dict,
    }




def load_rates() -> Dict[str, Any]:
    try:
        with open(RATES_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, JSONDecodeError):
        return {}


def save_rates(rates: Dict[str, Any]) -> None:
    _ensure_data_dir()
    with open(RATES_FILE, "w", encoding="utf-8") as file:
        json.dump(rates, file, ensure_ascii=False, indent=2)


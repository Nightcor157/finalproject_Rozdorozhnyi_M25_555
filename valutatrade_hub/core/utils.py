from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader

from .models import Portfolio, User, Wallet

settings = SettingsLoader()
db = DatabaseManager()

DATA_DIR = settings.get("DATA_DIR")
USERS_FILE = f"{DATA_DIR}/users.json"
PORTFOLIOS_FILE = f"{DATA_DIR}/portfolios.json"
RATES_FILE = f"{DATA_DIR}/rates.json"




def load_users() -> List[Dict[str, Any]]:
    return db.load_json(USERS_FILE, default=[])


def save_users(users: List[Dict[str, Any]]) -> None:
    db.save_json(USERS_FILE, users)


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
    return db.load_json(PORTFOLIOS_FILE, default=[])


def save_portfolios(portfolios: List[Dict[str, Any]]) -> None:
    db.save_json(PORTFOLIOS_FILE, portfolios)


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
    return db.load_json(RATES_FILE, default={})


def save_rates(rates: Dict[str, Any]) -> None:
    db.save_json(RATES_FILE, rates)


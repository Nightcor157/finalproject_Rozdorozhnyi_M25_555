
from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.settings import SettingsLoader

from .currencies import get_currency
from .exceptions import ApiRequestError
from .models import Portfolio, User
from .utils import (
    find_portfolio_record,
    find_user_by_username,
    load_portfolios,
    load_rates,
    load_users,
    next_user_id,
    portfolio_from_record,
    portfolio_to_record,
    save_portfolios,
    save_users,
    user_from_record,
)

settings = SettingsLoader()



def register_user(username: str, password: str) -> str:
    if len(password) < 4:
        return "Пароль должен быть не короче 4 символов"

    users = load_users()
    if find_user_by_username(users, username) is not None:
        return f"Имя пользователя '{username}' уже занято"

    user_id = next_user_id(users)
    salt = secrets.token_hex(8)
    tmp_user = User(
        user_id=user_id,
        username=username,
        hashed_password="",
        salt=salt,
        registration_date=datetime.now(),
    )
    tmp_user.change_password(password)

    record = {
        "user_id": user_id,
        "username": username,
        "hashed_password": tmp_user.hashed_password,
        "salt": salt,
        "registration_date": tmp_user.registration_date.isoformat(),
    }
    users.append(record)
    save_users(users)

    portfolios = load_portfolios()
    portfolio_record = {
        "user_id": user_id,
        "wallets": {},
    }
    portfolios.append(portfolio_record)
    save_portfolios(portfolios)

    return (
        f"Пользователь '{username}' зарегистрирован (id={user_id}). "
        "Войдите: login --username alice --password ****"
    )


def login_user(username: str, password: str) -> Tuple[Optional[User], str]:
    users = load_users()
    record = find_user_by_username(users, username)
    if record is None:
        return None, f"Пользователь '{username}' не найден"

    user = user_from_record(record)
    if not user.verify_password(password):
        return None, "Неверный пароль"

    return user, f"Вы вошли как '{username}'"


def load_user_portfolio(user: User) -> Portfolio:
    portfolios = load_portfolios()
    record = find_portfolio_record(portfolios, user.user_id)
    if record is None:
        portfolio = Portfolio(user_id=user.user_id, wallets={})
        portfolios.append(portfolio_to_record(portfolio))
        save_portfolios(portfolios)
        return portfolio
    return portfolio_from_record(record)


def save_user_portfolio(portfolio: Portfolio) -> None:
    portfolios = load_portfolios()
    record = find_portfolio_record(portfolios, portfolio.user_id)
    new_record = portfolio_to_record(portfolio)

    if record is None:
        portfolios.append(new_record)
    else:
        idx = portfolios.index(record)
        portfolios[idx] = new_record

    save_portfolios(portfolios)


def show_portfolio(user: User, base_currency: str = "USD") -> str:
    portfolio = load_user_portfolio(user)
    wallets = portfolio.wallets

    if not wallets:
        return f"Портфель пользователя '{user.username}' пуст."

    base = base_currency.upper()
    rates = load_rates()
    exchange_rates: Dict[str, float] = {}
    for key, value in rates.items():
        if key.endswith("_USD") and isinstance(value, dict):
            rate = value.get("rate")
            if isinstance(rate, (int, float)):
                exchange_rates[key] = float(rate)

    try:
        total = portfolio.get_total_value(exchange_rates, base_currency=base)
    except ValueError:
        return f"Неизвестная базовая валюта '{base}'"

    lines = [f"Портфель пользователя '{user.username}' (база: {base}):"]
    for code, wallet in wallets.items():
        if code == base:
            value_base = wallet.balance
        else:
            pair = f"{code}_{base}"
            rate = exchange_rates.get(pair)
            if rate is None:
                value_base = 0.0
            else:
                value_base = wallet.balance * rate
        lines.append(
            f"- {code}: {wallet.balance:.4f}  → {value_base:.2f} {base}",
        )

    lines.append("---------------------------------")
    lines.append(f"ИТОГО: {total:,.2f} {base}".replace(",", " "))

    return "\n".join(lines)


def get_rate_pair(from_code: str, to_code: str) -> Tuple[Optional[float], str]:
    get_currency(from_code)
    get_currency(to_code)

    from_c = from_code.upper()
    to_c = to_code.upper()

    rates = load_rates()
    ttl = settings.get("RATES_TTL_SECONDS", 31536000)

    last_refresh_str = rates.get("last_refresh")
    if last_refresh_str:
        try:
            last_refresh = datetime.fromisoformat(
                last_refresh_str.replace("Z", "+00:00"),
            )
            now_utc = datetime.now(timezone.utc)
            age_seconds = (now_utc - last_refresh).total_seconds()
            if age_seconds > float(ttl):
                raise ApiRequestError("источник курсов недоступен (кеш устарел)")
        except ValueError:
            pass

    pairs = rates.get("pairs", {})

    direct_key = f"{from_c}_{to_c}"
    record = pairs.get(direct_key)
    if isinstance(record, dict) and "rate" in record:
        rate = float(record["rate"])
        updated_at = record.get("updated_at", "")
        msg = (
            f"Курс {from_c}→{to_c}: {rate:.8f} "
            f"(обновлено: {updated_at})"
        )
        return rate, msg

    reverse_key = f"{to_c}_{from_c}"
    record = pairs.get(reverse_key)
    if isinstance(record, dict) and "rate" in record:
        rev_rate = float(record["rate"])
        if rev_rate == 0:
            raise ApiRequestError("получен нулевой курс из кеша")
        rate = 1.0 / rev_rate
        updated_at = record.get("updated_at", "")
        msg = (
            f"Курс {from_c}→{to_c}: {rate:.8f} "
            f"(обновлено: {updated_at})"
        )
        return rate, msg

    return None, f"Курс {from_c}→{to_c} недоступен. Повторите попытку позже."


    
@log_action("BUY")
def buy_currency(
    user: User,
    currency_code: str,
    amount: float,
) -> str:
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    get_currency(currency_code)

    code = currency_code.upper()
    portfolio = load_user_portfolio(user)
    wallet = portfolio.get_wallet(code)
    if wallet is None:
        wallet = portfolio.add_currency(code)

    rate, _msg = get_rate_pair(code, "USD")
    if rate is None:
        raise ApiRequestError(f"Не удалось получить курс для {code}→USD")

    before = wallet.balance
    wallet.deposit(amount)
    after = wallet.balance
    estimated_cost = amount * rate

    save_user_portfolio(portfolio)

    return (
        f"Покупка выполнена: {amount:.4f} {code} по курсу {rate:.2f} USD/{code}\n"
        f"Изменения в портфеле:\n"
        f"- {code}: было {before:.4f} → стало {after:.4f}\n"
        f"Оценочная стоимость покупки: {estimated_cost:,.2f} USD".replace(
            ",",
            " ",
        )
    )


@log_action("SELL")
def sell_currency(
    user: User,
    currency_code: str,
    amount: float,
) -> str:
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    get_currency(currency_code)

    code = currency_code.upper()
    portfolio = load_user_portfolio(user)
    wallet = portfolio.get_wallet(code)
    if wallet is None:
        return (
            f"У вас нет кошелька '{code}'. Добавьте валюту: "
            "она создаётся автоматически при первой покупке."
        )

    rate, _msg = get_rate_pair(code, "USD")
    if rate is None:
        raise ApiRequestError(f"Не удалось получить курс для {code}→USD")

    before = wallet.balance
    wallet.withdraw(amount)
    after = wallet.balance
    revenue = amount * rate

    save_user_portfolio(portfolio)

    return (
        f"Продажа выполнена: {amount:.4f} {code} по курсу {rate:.2f} USD/{code}\n"
        f"Изменения в портфеле:\n"
        f"- {code}: было {before:.4f} → стало {after:.4f}\n"
        f"Оценочная выручка: {revenue:,.2f} USD".replace(",", " ")
    )


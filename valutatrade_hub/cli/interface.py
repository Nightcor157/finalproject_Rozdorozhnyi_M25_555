
from __future__ import annotations

import shlex
from typing import Dict, Optional

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.models import User
from valutatrade_hub.core.usecases import (
    buy_currency,
    get_rate_pair,
    login_user,
    register_user,
    sell_currency,
    show_portfolio,
)


def _parse_options(args: list[str]) -> Dict[str, str]:
    options: Dict[str, str] = {}
    i = 0
    while i < len(args):
        token = args[i]
        if token.startswith("--"):
            key = token[2:]
            value = ""
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                value = args[i + 1]
                i += 1
            options[key] = value
        i += 1
    return options


def _print_help() -> None:
    print("\nДоступные команды:")
    print("  register --username <str> --password <str>")
    print("  login --username <str> --password <str>")
    print("  show-portfolio [--base <str>]")
    print("  buy --currency <str> --amount <float>")
    print("  sell --currency <str> --amount <float>")
    print("  get-rate --from <str> --to <str>")
    print("  help")
    print("  exit\n")




def run_cli() -> None:
    current_user: Optional[User] = None
    print("*** Платформа валютного кошелька ***")
    _print_help()

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nВыход.")
            break

        if not raw:
            continue

        try:
            parts = shlex.split(raw)
        except ValueError:
            print(f"Некорректная командная строка: {raw}")
            continue

        command = parts[0]
        args = parts[1:]
        options = _parse_options(args)

        try:
            if command == "exit":
                print("Выход.")
                break

            if command == "help":
                _print_help()
                continue

            if command == "register":
                username = options.get("username", "")
                password = options.get("password", "")

                if not username:
                    print("Требуется параметр --username")
                    continue
                if not password:
                    print("Требуется параметр --password")
                    continue

                message = register_user(username, password)
                print(message)
                continue

            if command == "login":
                username = options.get("username", "")
                password = options.get("password", "")

                if not username:
                    print("Требуется параметр --username")
                    continue
                if not password:
                    print("Требуется параметр --password")
                    continue

                user, message = login_user(username, password)
                print(message)
                if user is not None:
                    current_user = user
                continue

            if command in {"show-portfolio", "buy", "sell"} and current_user is None:
                print("Сначала выполните login")
                continue

            if command == "show-portfolio":
                base = options.get("base", "USD")
                text = show_portfolio(
                    current_user,  # type: ignore[arg-type]
                    base_currency=base,
                )
                print(text)
                continue

            if command == "buy":
                currency = options.get("currency", "").upper()
                amount_str = options.get("amount", "")

                if not currency:
                    print("Требуется параметр --currency")
                    continue
                if not amount_str:
                    print("Требуется параметр --amount")
                    continue

                try:
                    amount = float(amount_str)
                except ValueError:
                    print("'amount' должен быть положительным числом")
                    continue

                message = buy_currency(
                    current_user,  # type: ignore[arg-type]
                    currency,
                    amount,
                )
                print(message)
                continue

            if command == "sell":
                currency = options.get("currency", "").upper()
                amount_str = options.get("amount", "")

                if not currency:
                    print("Требуется параметр --currency")
                    continue
                if not amount_str:
                    print("Требуется параметр --amount")
                    continue

                try:
                    amount = float(amount_str)
                except ValueError:
                    print("'amount' должен быть положительным числом")
                    continue

                message = sell_currency(
                    current_user,  # type: ignore[arg-type]
                    currency,
                    amount,
                )
                print(message)
                continue

            if command == "get-rate":
                from_code = options.get("from", "").upper()
                to_code = options.get("to", "").upper()

                if not from_code or not to_code:
                    print("Нужно указать --from и --to")
                    continue

                rate, msg = get_rate_pair(from_code, to_code)
                print(msg)
                if rate is not None:
                    rev_rate, _ = get_rate_pair(to_code, from_code)
                    if rev_rate is not None:
                        print(
                            f"Обратный курс {to_code}→{from_code}: "
                            f"{rev_rate:.8f}",
                        )
                continue

            print(f"Неизвестная команда: {command}. Введите 'help' для списка.")

        except InsufficientFundsError as exc:
            print(str(exc))
        except CurrencyNotFoundError as exc:
            print(str(exc))
            print(
                "Проверьте код валюты или используйте команду "
                "get-rate для поддерживаемых пар.",
            )
        except ApiRequestError as exc:
            print(str(exc))
            print("Повторите попытку позже или проверьте подключение к сети.")
        except ValueError as exc:
            print(str(exc))



from __future__ import annotations

import shlex
from typing import Optional

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.usecases import (
    buy_currency,
    get_rate_pair,
    login_user,
    register_user,
    sell_currency,
    show_portfolio,
)
from valutatrade_hub.core.utils import load_rates
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


def _print_help() -> None:
    print("\n*** Платформа валютного кошелька ***\n")
    print("Доступные команды:")
    print("  register --username <str> --password <str>")
    print("  login --username <str> --password <str>")
    print("  show-portfolio [--base <str>]")
    print("  buy --currency <str> --amount <float>")
    print("  sell --currency <str> --amount <float>")
    print("  get-rate --from <str> --to <str>")
    print(
        "  update-rates [--source <coingecko|exchangerate>] "
        "- обновить курсы",
    )
    print(
        "  show-rates [--currency <str>] [--top <int>] "
        "[--base <str>] - показать кеш курсов",
    )
    print("  help")
    print("  exit\n")


def run_cli() -> None:
    current_user: Optional[str] = None
    print("*** Платформа валютного кошелька ***")
    _print_help()

    while True:
        try:
            raw = input("> ").strip()
            if not raw:
                continue

            try:
                tokens = shlex.split(raw)
            except ValueError:
                print("Не удалось разобрать команду. Попробуйте снова.")
                continue

            command = tokens[0]


            if command == "help":
                _print_help()
                continue

            if command == "exit":
                print("Выход из программы.")
                return


            if command == "update-rates":
                source_filter: Optional[str] = None
                i = 1
                while i < len(tokens):
                    if tokens[i] == "--source" and i + 1 < len(tokens):
                        source_filter = tokens[i + 1].lower()
                        i += 2
                    else:
                        i += 1

                config = ParserConfig()
                storage = RatesStorage(config)

                clients = []
                if source_filter in (None, "coingecko"):
                    clients.append(CoinGeckoClient(config))
                if source_filter in (None, "exchangerate", "exchange-rate"):
                    clients.append(ExchangeRateApiClient(config))

                if not clients:
                    print(
                        "Неизвестный источник. Используйте "
                        "coingecko или exchangerate.",
                    )
                    continue

                updater = RatesUpdater(clients, storage)
                message, total, last_refresh = updater.run_update()
                print(
                    f"{message} Total rates updated: {total}. "
                    f"Last refresh: {last_refresh}",
                )
                continue


            if command == "show-rates":
                currency_code: Optional[str] = None
                base_code: Optional[str] = None
                top_n: Optional[int] = None

                i = 1
                while i < len(tokens):
                    if tokens[i] == "--currency" and i + 1 < len(tokens):
                        currency_code = tokens[i + 1].upper()
                        i += 2
                    elif tokens[i] == "--base" and i + 1 < len(tokens):
                        base_code = tokens[i + 1].upper()
                        i += 2
                    elif tokens[i] == "--top" and i + 1 < len(tokens):
                        try:
                            top_n = int(tokens[i + 1])
                        except ValueError:
                            print("'--top' должно быть целым числом")
                            top_n = None
                        i += 2
                    else:
                        i += 1

                rates = load_rates()
                pairs = rates.get("pairs", {})
                last_refresh = rates.get("last_refresh", "")

                if not pairs:
                    print(
                        "Локальный кеш курсов пуст. "
                        "Выполните 'update-rates', чтобы загрузить данные.",
                    )
                    continue

                items = list(pairs.items())

                if currency_code:
                    items = [
                        (pair, info)
                        for pair, info in items
                        if pair.startswith(f"{currency_code}_")
                    ]

                if base_code:
                    items = [
                        (pair, info)
                        for pair, info in items
                        if pair.endswith(f"_{base_code}")
                    ]

                if not items:
                    if currency_code:
                        print(
                            f"Курс для '{currency_code}' не найден в кеше.",
                        )
                    else:
                        print("Подходящих записей не найдено.")
                    continue

                if top_n is not None:
                    items.sort(
                        key=lambda kv: float(kv[1].get("rate", 0.0)),
                        reverse=True,
                    )
                    items = items[:top_n]
                else:
                    items.sort(key=lambda kv: kv[0])

                print(
                    f"Rates from cache (updated at {last_refresh}):",
                )
                for pair, info in items:
                    rate = info.get("rate", 0.0)
                    print(f"- {pair}: {rate}")
                continue


            if command == "register":
                username: Optional[str] = None
                password: Optional[str] = None

                i = 1
                while i < len(tokens):
                    if tokens[i] == "--username" and i + 1 < len(tokens):
                        username = tokens[i + 1]
                        i += 2
                    elif tokens[i] == "--password" and i + 1 < len(tokens):
                        password = tokens[i + 1]
                        i += 2
                    else:
                        i += 1

                if not username or not password:
                    print(
                        "Укажите --username и --password "
                        "для регистрации.",
                    )
                    continue

                message = register_user(username, password)
                print(message)
                continue


            if command == "login":
                username = None
                password = None

                i = 1
                while i < len(tokens):
                    if tokens[i] == "--username" and i + 1 < len(tokens):
                        username = tokens[i + 1]
                        i += 2
                    elif tokens[i] == "--password" and i + 1 < len(tokens):
                        password = tokens[i + 1]
                        i += 2
                    else:
                        i += 1

                if not username or not password:
                    print(
                        "Укажите --username и --password "
                        "для входа.",
                    )
                    continue

                message, ok = login_user(username, password)
                print(message)
                if ok:
                    current_user = username
                continue


            if command == "show-portfolio":
                if current_user is None:
                    print("Сначала выполните login.")
                    continue

                base = "USD"
                i = 1
                while i < len(tokens):
                    if tokens[i] == "--base" and i + 1 < len(tokens):
                        base = tokens[i + 1].upper()
                        i += 2
                    else:
                        i += 1

                message = show_portfolio(current_user, base)
                print(message)
                continue


            if command == "buy":
                if current_user is None:
                    print("Сначала выполните login.")
                    continue

                currency = None
                amount_str = None

                i = 1
                while i < len(tokens):
                    if tokens[i] == "--currency" and i + 1 < len(tokens):
                        currency = tokens[i + 1].upper()
                        i += 2
                    elif tokens[i] == "--amount" and i + 1 < len(tokens):
                        amount_str = tokens[i + 1]
                        i += 2
                    else:
                        i += 1

                if currency is None or amount_str is None:
                    print(
                        "Укажите --currency и --amount "
                        "для покупки.",
                    )
                    continue

                try:
                    amount = float(amount_str)
                except ValueError:
                    print("'amount' должен быть числом.")
                    continue

                message = buy_currency(current_user, currency, amount)
                print(message)
                continue


            if command == "sell":
                if current_user is None:
                    print("Сначала выполните login.")
                    continue

                currency = None
                amount_str = None

                i = 1
                while i < len(tokens):
                    if tokens[i] == "--currency" and i + 1 < len(tokens):
                        currency = tokens[i + 1].upper()
                        i += 2
                    elif tokens[i] == "--amount" and i + 1 < len(tokens):
                        amount_str = tokens[i + 1]
                        i += 2
                    else:
                        i += 1

                if currency is None or amount_str is None:
                    print(
                        "Укажите --currency и --amount "
                        "для продажи.",
                    )
                    continue

                try:
                    amount = float(amount_str)
                except ValueError:
                    print("'amount' должен быть числом.")
                    continue

                message = sell_currency(current_user, currency, amount)
                print(message)
                continue


            if command == "get-rate":
                from_code = None
                to_code = None

                i = 1
                while i < len(tokens):
                    if tokens[i] == "--from" and i + 1 < len(tokens):
                        from_code = tokens[i + 1].upper()
                        i += 2
                    elif tokens[i] == "--to" and i + 1 < len(tokens):
                        to_code = tokens[i + 1].upper()
                        i += 2
                    else:
                        i += 1

                if from_code is None or to_code is None:
                    print(
                        "Укажите --from и --to "
                        "для получения курса.",
                    )
                    continue

                _, msg = get_rate_pair(from_code, to_code)
                print(msg)
                continue


            print(f"Неизвестная команда '{command}'. Введите 'help'.")

        except InsufficientFundsError as exc:
            print(str(exc))
        except CurrencyNotFoundError as exc:
            print(str(exc))
        except ApiRequestError as exc:
            print(str(exc))
        except KeyboardInterrupt:
            print("\nВыход из программы.")
            return


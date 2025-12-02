

class InsufficientFundsError(Exception):

    def __init__(self, available: float, required: float, code: str) -> None:
        self.available = float(available)
        self.required = float(required)
        self.code = code.upper()
        message = (
            f"Недостаточно средств: доступно {self.available:.4f} {self.code}, "
            f"требуется {self.required:.4f} {self.code}"
        )
        super().__init__(message)


class CurrencyNotFoundError(Exception):

    def __init__(self, code: str) -> None:
        self.code = code.upper()
        message = f"Неизвестная валюта '{self.code}'"
        super().__init__(message)


class ApiRequestError(Exception):

    def __init__(self, reason: str) -> None:
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)
        self.reason = reason


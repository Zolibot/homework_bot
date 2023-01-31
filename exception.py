class UnexpectedServerError(Exception):
    """Некорректный ответ сервера."""

    pass


class ResponseCodeNotCorrect(Exception):
    """Некорректный код ответа сервера."""

    pass


class RequestUnclear(Exception):
    """Неясный запрос сервиса."""

    pass


class DateInResponseNotExist(Exception):
    """Не даты в ответе."""

    pass


class UnknownTaskStatus(Exception):
    """Неизвестный статус задания."""

    pass

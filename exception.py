class ResponseCodeNotCorrect(Exception):
    """Некорректный ответ сервер."""

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

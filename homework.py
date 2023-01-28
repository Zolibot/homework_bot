import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_PERIOD = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    logging.debug("Проверяем доступность переменных окружения")
    return all([PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN])


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    logging.debug("Отправляем сообщение в Telegram")

    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as error:
        logging.error(f"Ошибка Отправки сообщения: {error}")
    else:
        logging.debug(
            f"Отправлено на chat_id:{TELEGRAM_CHAT_ID},сообщениe: {message}"
        )


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    logging.debug("Отправляем запрос к эндпоинту API-сервиса")
    timestamp = current_timestamp or int(time.time())
    try:
        homework_statuses = requests.get(
            url=ENDPOINT, headers=HEADERS, params={"from_date": timestamp}
        )
    except homework_statuses.raise_for_status() as error:
        msg = f"'API возвращает код, отличный от 200': {error}"
        logging.error(msg)
        raise Exception(msg)
    except requests.RequestException:
        logging.error("Нет соединения c сервером")
    else:
        logging.info("Запрос к API выполнен успешно")

    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    logging.info("началo проверки ответа сервера")

    if type(response) is not dict:
        raise TypeError("Нет словоря в ответе API")

    if "homeworks" not in response:
        raise KeyError("Ошибка словаря по ключу homeworks")

    if type(response["homeworks"]) is not list:
        raise TypeError("Нет списка в ответе API")
    return response["homeworks"]


def parse_status(homework):
    """Извлекает статус из конкретной домашней работы."""
    homework_name = homework.get("homework_name")
    homework_status = homework.get("status")

    if homework_name is None:
        raise KeyError('Отсутствует ключ "homework_name" в ответе API')

    if homework_status is None:
        raise KeyError('Отсутствует ключ "status" в ответе API')

    if homework_status not in HOMEWORK_VERDICTS:
        raise Exception(f"Неизвестный статус работы: {homework_status}")

    verdict = HOMEWORK_VERDICTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    logging.info("Проверка переменных")

    if not check_tokens():
        logging.critical("Отсутствуют одна или несколько переменных окружения")
        sys.exit("Отсутствуют одна или несколько переменных окружения")

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    cache_message = ""
    cache_error_message = ""

    while True:
        try:
            response = get_api_answer(timestamp)
            logging.info(response)
            homework = check_response(response)
            if homework:
                message = parse_status(homework[0])
                if message != cache_message:
                    send_message(bot, message)
                cache_message = message
            else:
                logging.info("Список домашних работ пустой")
        except Exception as error:
            message_error = f"Сбой в работе программы: {error}"
            logging.error(error)
            if message_error != cache_error_message:
                send_message(bot, message_error)
                cache_error_message = message_error
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s, %(levelname)s, %(message)s",
    )
    main()

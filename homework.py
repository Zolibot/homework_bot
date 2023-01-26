import os
import logging
import requests

import telegram
from http import HTTPStatus
from time import sleep, time
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s',
)
logger = logging.getLogger(__name__)

ENV_VARS = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
PRACTICUM_TOKEN = os.getenv(ENV_VARS[0])
TELEGRAM_TOKEN = os.getenv(ENV_VARS[1])
TELEGRAM_CHAT_ID = os.getenv(ENV_VARS[2])

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    for var in ENV_VARS:
        if var not in os.environ:
            raise EnvironmentError("Failed because {} is not set.".format(var))
    return True

def send_message(bot, message):
    ...


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)

    if homework_statuses.status_code != HTTPStatus.OK:
        logger.error("API возвращает код, отличный от 200")
        raise Exception(
            "API возвращает код, отличный от 200"
        )

    homework_json = homework_statuses.json()
    return homework_json


def check_response(response):
    ...


def parse_status(homework):
    ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    ...

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    ...

    while True:
        try:

            ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ...


if __name__ == '__main__':
    main()

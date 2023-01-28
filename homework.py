import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exception import (
    DateInResponseNotExist,
    RequestUnclear,
    ResponseCodeNotCorrect,
    UnknownTaskStatus
)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    logging.debug('Проверяем доступность переменных окружения')
    return all([PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN])


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    logging.debug('Отправляем сообщение в Telegram')

    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.TelegramError as error:
        logging.error(f'Ошибка Отправки сообщения: {error}')
    else:
        logging.debug(
            f'Отправлено на chat_id:{TELEGRAM_CHAT_ID},сообщениe: {message}'
        )


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    logging.debug('Отправляем запрос к эндпоинту API-сервиса')
    params_request = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp},
    }
    logging.info('Начат запрос к API-сервиса')

    try:
        response = requests.get(**params_request)
        if response.status_code != HTTPStatus.OK:
            raise ResponseCodeNotCorrect('API возвращает код, отличный от 200')
    except requests.RequestException as error:
        raise RequestUnclear(f'Нет соединения c сервером: {error}')
    except Exception as error:
        raise ResponseCodeNotCorrect(
            f'API возвращает код, отличный от 200: {error}'
        )
    else:
        logging.info('Запрос к API выполнен успешно')

    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    logging.info('началo проверки ответа сервера')

    if not isinstance(response, dict):
        raise TypeError('Нет словоря в ответе API')

    if not response.get('current_date'):
        raise DateInResponseNotExist('Нет даты в ответе')

    if not isinstance(response.get('homeworks'), list):
        raise TypeError('Нет списка в ответе API')
    return response['homeworks']


def parse_status(homework):
    """Извлекает статус из конкретной домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    for attribute in [homework_name, homework_status]:
        if attribute is None:
            raise KeyError(f'Отсутствует ключ {attribute} в ответе API')

    if homework_status not in HOMEWORK_VERDICTS:
        logging.error('Неизвестный статус задания')
        raise UnknownTaskStatus(
            f'Неизвестный статус задания: {homework_status}'
        )

    verdict = HOMEWORK_VERDICTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    logging.info('Проверка переменных')

    if not check_tokens():
        exit_message = 'Отсутствуют одна или несколько переменных окружения'
        logging.critical(exit_message)
        sys.exit(exit_message)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    cache_message = ''
    cache_error_message = ''

    while True:
        try:
            response = get_api_answer(int(time.time()))
            logging.info(response)
            homework = check_response(response)
            if homework:
                message = parse_status(homework[0])
                if message != cache_message:
                    send_message(bot, message)
                cache_message = message
            else:
                logging.info('Список домашних работ пустой')
        except Exception as error:
            message_error = f'Сбой в работе программы: {error}'
            logging.error(error)
            if message_error != cache_error_message:
                send_message(bot, message_error)
                cache_error_message = message_error
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s, %(levelname)s, %(message)s',
    )
    main()

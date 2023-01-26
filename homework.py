import os
import sys
import time
import logging
import requests

import telegram
from http import HTTPStatus
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s',
)

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler(sys.stdout))

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
    logger.debug("Проверяем доступность переменных окружения")
    if PRACTICUM_TOKEN and TELEGRAM_CHAT_ID and TELEGRAM_TOKEN:
        return True
    else:
        return False


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    logger.debug("Отправляем сообщение в Telegram")
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(
            f'Отправлено на chat_id:{TELEGRAM_CHAT_ID},сообщениe: {message}'
        )
    except telegram.TelegramError as error:
        message = f'Ошибка Отправки сообщения: {error}'
        logger.error('Ошибка Отправки сообщения')


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    logger.debug("Отправляем запрос к эндпоинту API-сервиса")
    try:
        homework_statuses = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if homework_statuses.status_code != HTTPStatus.OK:
            logger.error('API возвращает код, отличный от 200')
            raise Exception('API возвращает код, отличный от 200')
    except requests.RequestException:
        logger.error('Нет соединения c сервером')
    else:
        logger.info("Запрос к API выполнен успешно")

    return homework_statuses.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    logger.info("началo проверки ответа сервера")
    if type(response) is not dict:
        raise TypeError('Нет словоря в ответе API')

    if 'homeworks' not in response:
        raise KeyError('Ошибка словаря по ключу homeworks')

    if type(response['homeworks']) is not list:
        raise TypeError('Нет списка в ответе API')
    return response['homeworks']


def parse_status(homework):
    """Извлекает статус из конкретной домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_name is None:
        raise KeyError(
            'Отсутствует ключ "homework_name" в ответе API'
        )

    if homework_status is None:
        raise KeyError(
            'Отсутствует ключ "status" в ответе API'
        )

    if homework_status not in HOMEWORK_VERDICTS:
        raise Exception(
            f'Неизвестный статус работы: {homework_status}'
        )

    verdict = HOMEWORK_VERDICTS.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    logger.info('Проверка переменных')
    if not check_tokens():
        logger.critical('Отсутствуют одна или несколько переменных окружения')
        sys.exit('Отсутствуют одна или несколько переменных окружения')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    cache_message = ''
    cache_error_message = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            logger.info(response)
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
            logger.error(error)
            if message_error != cache_error_message:
                send_message(bot, message_error)
                cache_error_message = message_error
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()

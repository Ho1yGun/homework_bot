import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


class BotError(Exception):
    """Ошибки в работе бота."""
    pass


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Удачная отправка сообщения в Telegram')
    except Exception as error:
        logger.error(error, exc_info=True)


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code != 200:
        logger.error(
            f'Недоступен эндпоинт API-сервиса,'
            f' текущий статус код: {homework_statuses.status_code}'
        )
        raise BotError('Недоступен эндпоинт API-сервиса')
    homework_statuses = homework_statuses.json()
    return homework_statuses


def check_response(response):
    """Проверяет ответ API на корректность."""
    homeworks = response['homeworks']
    if type(homeworks) == list:
        return homeworks
    else:
        logger.error(
            f'Формат ответа API отличается от'
            f' ожидаемоего,{type(homeworks)} != list'
        )


def parse_status(homework):
    """Извлекает из информации о домашней работе статус этой работы."""
    if 'homework_name' not in homework:
        raise KeyError('homework_name отсутствует в homework')
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as error:
        error_message = f'ошибка в статусе домашней работы: {error}'
        send_message(telegram.Bot(token=TELEGRAM_TOKEN), error_message)
        logger.critical(error_message)
        raise BotError(error_message)


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if TELEGRAM_CHAT_ID and PRACTICUM_TOKEN and TELEGRAM_TOKEN is not None:
        return True
    else:
        logger.critical('Отсутствие обязательных переменных окружения')
        return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if check_tokens() is False:
        raise Exception('Недоступна переменная окружения')
    old_verdict = ''
    old_error_message = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            message = check_response(response)
            if message:
                verdict = parse_status(message[0])
                if verdict != old_verdict:
                    send_message(bot, verdict)
                    old_verdict = verdict
                else:
                    logger.debug('Нет новых статусов')
            time.sleep(RETRY_TIME)

        except KeyboardInterrupt:
            logger.error('Работа программы прервана с клавиатуры компьютера')

        except Exception as error:
            logger.error(error, exc_info=True)
            new_error_message = f'Сбой в работе программы: {error} '
            if new_error_message not in old_error_message:
                old_error_message += new_error_message
                send_message(bot, new_error_message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()

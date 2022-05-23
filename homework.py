import logging
import sys
import time
from http import HTTPStatus

import requests
import telegram

from config import (ENDPOINT, HEADERS, HOMEWORK_STATUSES, PRACTICUM_TOKEN,
                    RETRY_TIME, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN)
from exceptions import BotMessageError, YandexAPIError


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info('Удачная отправка сообщения в Telegram')
    except Exception as error:
        logger.error(error, exc_info=True)
        raise BotMessageError('Бот не смог отправить сообщение')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if homework_statuses.status_code != HTTPStatus.OK:
        logger.error(
            f'Недоступен эндпоинт API-сервиса,'
            f' текущий статус код: {homework_statuses.status_code}'
        )
        raise YandexAPIError('Недоступен эндпоинт API-сервиса')
    homework_statuses = homework_statuses.json()
    return homework_statuses


def check_response(response):
    """Проверяет ответ API на корректность."""
    homeworks = response.get('homeworks')
    if isinstance(homeworks, list):
        return homeworks

    logger.error(
        f'Формат ответа API отличается от'
        f' ожидаемоего,{type(homeworks)} != list'
    )


def parse_status(homework):
    """Извлекает из информации о домашней работе статус этой работы."""
    if 'homework_name' not in homework:
        raise KeyError('homework_name отсутствует в homework')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        logger.error(
            f'статус {homework_status} домашней работы'
            f' не найден в списке HOMEWORK_STATUSES')
        raise YandexAPIError('Неизвестный статус домашней работы')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    all([TELEGRAM_CHAT_ID, PRACTICUM_TOKEN, TELEGRAM_TOKEN])


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    if check_tokens() is False:
        logger.critical('Отсутствие обязательных переменных окружения')
        sys.exit('Недоступна переменная окружения')
    old_verdict = ''
    old_error_message = []

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

        except Exception as error:
            logger.error(error, exc_info=True)
            new_error_message = f'Сбой в работе программы: {error} '
            if new_error_message not in old_error_message:
                old_error_message.append(new_error_message)
                send_message(bot, new_error_message)

        finally:
            time.sleep(RETRY_TIME)
            current_timestamp = response.get('current_date')


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    try:
        main()
    except KeyboardInterrupt:
        logger.error('Работа программы прервана с клавиатуры компьютера')
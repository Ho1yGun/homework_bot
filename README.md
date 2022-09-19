# homework_bot
## Telegram bot для запросов к API Yandex.Practicum.
### Возможности:
#### • Раз в заданный интервал времени опрашивать API сервиса Практикум.Домашка и проверять статус отправленной на ревью домашней работы
#### • При обновлении статуса анализировать ответ API и отправлять вам соответствующее уведомление в Telegram.
#### • Логировать свою работу и сообщать вам о важных проблемах сообщением в Telegram.

### Как запустить проект:

#### Клонировать репозиторий и перейти в него в командной строке:

```
HTTPS: git clone https://github.com/Ho1yGun/homework_bot.git
SSH: git clone git@github.com:Ho1yGun/homework_bot.git
```

```
cd homework_bot
```

#### Cоздать и активировать виртуальное окружение:

```
python3 -m venv env
или 
python -m venv env для windows, далее так же
```

```
source env/bin/activate
```

#### Установить зависимости из файла requirements.txt:

```
pip install -r requirements.txt
```
#### Создать файл .env в корне проекта и прописать в нём:
```
PRACTICUM_TOKEN=практикум токен без пробелов
TELEGRAM_TOKEN=ваш токен телеграма без пробелов
TELEGRAM_CHAT_ID=ваш ID телеграмм чата без пробелов
```

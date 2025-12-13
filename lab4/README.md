# Telegram TGWall

Меняет фон Telegram-канала по реальному времени рассвета и заката (OpenWeatherMap). Работает как CLI и как systemd-сервис. Использует Telethon (user session, SQLiteSession; не бот).

## Возможности
- Фазы суток: night → dawn → morning → day → evening → sunset → night
- Получение рассвета/заката и timezone из OpenWeatherMap
- Автоматический выбор обоев по текущей фазе
- Применение обоев в Telegram канал: только официальный MTProto-метод `messages.SetChatWallPaper` (без фолбэков)
- CLI-команды: login, run, daemon
- Логирование в stdout и `logs/app.log` (ротация)

## Установка
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Настройка
1) Создайте файлы в `config/` и заполните:

```ini
# config/.env.core
TZ=Europe/Moscow
CITY=Moscow
INTERVAL_MINUTES=30
LOG_LEVEL=INFO
```

```ini
# config/.env.telegram
TELEGRAM_API_ID=xxxxx
TELEGRAM_API_HASH=xxxxx
TELEGRAM_SESSION=tgwall.session
TELEGRAM_CHAT=@your_channel
ALLOW_SET_CHANNEL_PHOTO=false
```

```ini
# config/.env.weather
OPENWEATHER_API_KEY=xxxxx
OPENWEATHER_LANG=ru
OPENWEATHER_UNITS=metric
```

2) Укажите изображения и правила в `config/config.json` и положите файлы в `backgrounds/`:
Подробная схема и примеры: см. `docs/config.md`.

## Первый вход (создание сессии)
```bash
python -m app.cli login --phone +79990000000
```
Следуйте инструкциям; будет создан бинарный SQLite `.session` файл по пути `TELEGRAM_SESSION`.

## Запуск
- Разовый запуск:
```bash
python -m app.cli run --city Moscow
```
- Демон:
```bash
python -m app.cli daemon --city Moscow
```

## systemd
Смотрите `service/tgwall.service`. Пример установки:
```bash
sudo cp service/tgwall.service /etc/systemd/system/tgwall.service
sudo systemctl daemon-reload
sudo systemctl enable tgwall
sudo systemctl start tgwall
```

## Примечания по Telegram API
- Смена обоев (SetChatWallPaperRequest) требует права администратора и достаточный уровень бустов канала (channel_custom_wallpaper_level_min)
- При ошибках (например, WALLPAPER_INVALID, CHAT_ADMIN_REQUIRED) команда завершается с ошибкой (без скрытых фолбэков)

## Диагностика
- Проверка установки обоев вручную:
```bash
python -m app.cli test-wallpaper --image backgrounds/day.jpg --log-level DEBUG
```
Логи покажут ход установки, в т.ч. использование UploadWallPaperRequest и результат SetChatWallPaper.

## Безопасность
- Не коммитьте `.session` файлы и ключи
- Ограничьте доступ к `config/` и `logs/`

## Лицензия
MIT

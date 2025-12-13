# Документация по config/config.json

Файл `config/config.json` управляет режимом работы, вероятностями погодных инстансов и картой соответствия фаз суток/погоды к файлам обоев.

## Структура

- flags
  - mode: "time_only" | "weather_based" | "weather_no_fog" | "random_mode"
    - time_only: игнорировать погоду, всегда брать `clear` для фазы
    - weather_based: учитывать погоду и вероятности (fog/thunder)
    - weather_no_fog: полностью игнорировать туман (и коды 7xx):
      - прямой туман/мгла/haze не используются; подбирается `overcast`/`cloudy`/`clear` по облачности
      - вероятность `fogChance` отключена
    - random_mode: выбрать случайный доступный инстанс фазы
  - cache_enabled: true/false — пропуск обновления, если состояние не изменилось
  - use_random_selection: true/false — при нескольких файлах выбирать случайно/первый
  - log_details: true/false — подробные DEBUG-логи выбора
  - apply_fog_for_all_phases: true/false — legacy; игнорируется, туман применяется только на фазе `dawn`

- probabilities
  - fogChance: число [0..1] — шанс тумана (см. правила ниже)
  - thunderChance: число [0..1] — шанс грозы как модификатора heavy_rain

- update
  - interval_minutes: период обновления цикла
  - timezone: TZ, например `Europe/Moscow`

- matrix: объект фаз → объект инстансов → массив путей
  - Фазы: `night`, `dawn`, `morning`, `day`, `evening`, `sunset`
  - Инстансы: `clear`, `cloudy`, `overcast`, `rain`, `heavy_rain`, `thunderstorm`, `fog`
  - Туман: только для `dawn` и только ключи `fog_clear`, `fog_cloudy`
  - Значение — строка (один файл) или массив строк (несколько файлов)

## Правила выбора погоды

1) Базовая категоризация по OpenWeather:
- `thunderstorm` | код 2xx → `heavy_rain`
- `drizzle` → `rain`
- `rain` | 5xx → `heavy_rain` для 502,503,504,522,531; иначе `rain`
- `snow` | 6xx → `heavy_rain` для 602,622; иначе `rain`
- `mist`/`fog`/`haze` | 7xx → `fog`
- `clear` | 800 → `clear`
- `clouds` | 80x → `overcast` (clouds>=85), `cloudy` (clouds>=40), иначе `clear`

2) Вероятности-модификаторы:
- `fog`: применяется только при фазе `dawn` и только если базовый инстанс в {clear, cloudy}; при `rand < fogChance` выбирается `fog_clear` или `fog_cloudy` (если определены в матрице фазы `dawn`)
- `thunderstorm`: если базовый инстанс `heavy_rain` и `rand < thunderChance` → `thunderstorm`

3) Замены совместимости: `snow` → `rain`, `blizzard` → `heavy_rain` (если провайдер так вернёт)

## Выбор файла обоев

- Если под инстансом несколько файлов и `use_random_selection=true` — равновероятный случайный выбор, иначе берётся первый.
- Если для пары (фаза, инстанс) нет записей — пробуем `clear`, затем первый доступный инстанс фазы.
- Несуществующие файлы логируются как `WARNING`, приложение не падает.

## Кэш состояния

- Кэш хранится в `.cache/last_state.json`:
```json
{
  "phase": "dawn",
  "weather": "fog_clear",
  "file": "backgrounds/dawn_fog_clear.jpg"
}
```
- Если кэш совпадает по (phase, weather, file), обновление пропускается и обращений к Telegram нет.

## Пример минимальной конфигурации

```json
{
  "flags": {
    "mode": "weather_based",
    "cache_enabled": true,
    "use_random_selection": true,
    "log_details": false,
    "apply_fog_for_all_phases": false
  },
  "probabilities": {
    "fogChance": 0.3,
    "thunderChance": 0.5
  },
  "update": {
    "interval_minutes": 30,
    "timezone": "Europe/Moscow"
  },
  "matrix": {
    "dawn": {
      "clear": [
        "backgrounds/dawn_clear.jpg"
      ],
      "fog_clear": [
        "backgrounds/dawn_fog_clear.jpg"
      ],
      "fog_cloudy": [
        "backgrounds/dawn_fog_cloudy.jpg"
      ]
    }
  }
}
```

## MIGRATION (wallpapers.json → config.json)

- Переименуйте `config/wallpapers.json` в `config/config.json` и расширьте по структуре выше.
- На время перехода проект поддерживает старый `wallpapers.json` (с предупреждением), но рекомендуется перейти на `config.json`.

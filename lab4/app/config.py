from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict
import json
import os
import logging

from dotenv import dotenv_values, load_dotenv


logger = logging.getLogger(__name__)

# Paths
ROOT_DIR = Path(__file__).resolve().parents[1]
ENV_CORE = ROOT_DIR / "config" / ".env.core"
ENV_TG = ROOT_DIR / "config" / ".env.telegram"
ENV_WEATHER = ROOT_DIR / "config" / ".env.weather"
CONFIG_JSON = ROOT_DIR / "config" / "config.json"


def _load_envs_in_order() -> None:
    """Загрузить .env-файлы в строгом порядке: core, weather, telegram.

    Поздние файлы перекрывают значения ранних.
    """
    for p in (ENV_CORE, ENV_WEATHER, ENV_TG):
        if p.exists():
            load_dotenv(p, override=True)
            logger.info("Загружен env-файл: %s", p)
        else:
            logger.warning("Env-файл не найден: %s", p)


@dataclass(frozen=True)
class CoreConfig:
    tz: str
    city: str
    interval_minutes: int
    log_level: str


@dataclass(frozen=True)
class TelegramConfig:
    api_id: int
    api_hash: str
    session_file: Path
    chat: str
    allow_set_channel_photo: bool


@dataclass(frozen=True)
class WeatherConfig:
    api_key: str
    lang: str
    units: str


class Config:
    """Загружает конфигурацию из .env и JSON."""

    def __init__(self, config_dir: Path) -> None:
        # Устаревшая инициализация; используйте Config.load().
        self.config_dir = config_dir
        self.core = self._load_core()
        self.telegram = self._load_telegram()
        self.weather = self._load_weather()
        self.wallpaper_matrix = self._load_wallpapers()

    @classmethod
    def load(cls, base_dir: Path | None = None) -> "Config":
        """Загрузить конфигурацию из .env и переменных окружения.

        Parameters
        ----------
        base_dir:
            Optional project base directory. Defaults to the parent of this
            file's directory (project root), with "config" subdirectory.

        Returns
        -------
        Config
            Fully initialized configuration object.
        """
        if base_dir is None:
            base_dir = ROOT_DIR
        config_dir = base_dir / "config"

        # Загружаем .env в строгом порядке с логированием
        _load_envs_in_order()

        # Проверяем обязательные переменные
        required_keys = [
            "TELEGRAM_API_ID",
            "TELEGRAM_API_HASH",
            "TELEGRAM_SESSION",
            "TELEGRAM_CHAT",
            "OPENWEATHER_API_KEY",
        ]
        missing = [k for k in required_keys if not os.getenv(k)]
        if missing:
            raise ValueError(
                "Отсутствуют обязательные переменные окружения: "
                + ", ".join(missing)
                + ". Заполните файлы config/.env.*."
            )

        # Формируем dataclass-объекты из os.environ
        core = CoreConfig(
            tz=os.getenv("TZ", "UTC"),
            city=os.getenv("CITY", "Moscow"),
            interval_minutes=int(os.getenv("INTERVAL_MINUTES", "30")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

        session_raw = os.getenv("TELEGRAM_SESSION", "")
        session_file = Path(session_raw).expanduser()
        if not session_file.is_absolute():
            session_file = session_file.resolve()
        if not session_file.exists():
            logger.warning("ENV Telegram: файл сессии не существует: %s", session_file)

        tg = TelegramConfig(
            api_id=int(os.getenv("TELEGRAM_API_ID", "0")),
            api_hash=os.getenv("TELEGRAM_API_HASH", ""),
            session_file=session_file,
            chat=os.getenv("TELEGRAM_CHAT", ""),
            allow_set_channel_photo=cls._to_bool(os.getenv("ALLOW_SET_CHANNEL_PHOTO", "false")),
        )

        weather = WeatherConfig(
            api_key=os.getenv("OPENWEATHER_API_KEY", ""),
            lang=os.getenv("OPENWEATHER_LANG", "ru"),
            units=os.getenv("OPENWEATHER_UNITS", "metric"),
        )

        # Сводка загруженных значений
        masked_api_id = cls._mask_api_id(tg.api_id)
        masked_hash = (tg.api_hash[:-6] + "******") if len(tg.api_hash) > 6 else "******"
        logger.info("ENV Core: TZ=%s CITY=%s INTERVAL_MINUTES=%s LOG_LEVEL=%s", core.tz, core.city, core.interval_minutes, core.log_level)
        logger.info("ENV Telegram: API_ID=%s API_HASH=%s SESSION=%s CHAT=%s ALLOW_SET_CHANNEL_PHOTO=%s",
                    masked_api_id, masked_hash, tg.session_file, tg.chat, tg.allow_set_channel_photo)
        logger.info("ENV Weather: KEY=*** LANG=%s UNITS=%s", weather.lang, weather.units)

        # Load config.json (fallback to legacy wallpapers.json)
        config_path = CONFIG_JSON
        if not config_path.exists():
            legacy = ROOT_DIR / "config" / "wallpapers.json"
            if legacy.exists():
                logger.warning("config.json не найден; используем устаревший wallpapers.json")
                config_path = legacy
            else:
                raise FileNotFoundError("Отсутствует файл конфигурации config/config.json")
        with config_path.open("r", encoding="utf-8") as f:
            matrix = json.load(f)

        cfg = cls.__new__(cls)  # обходим __init__
        cfg.config_dir = config_dir
        cfg.core = core
        cfg.telegram = tg
        cfg.weather = weather
        cfg.wallpaper_matrix = matrix
        return cfg

    def _load_core(self) -> CoreConfig:
        env = self._read_env(".env.core")
        tz = self._require(env, "TZ")
        city = env.get("CITY", "Moscow")
        interval_minutes = int(env.get("INTERVAL_MINUTES", "30"))
        log_level = env.get("LOG_LEVEL", "INFO")
        core = CoreConfig(tz=tz, city=city, interval_minutes=interval_minutes, log_level=log_level)
        logger.info("ENV Core: TZ=%s CITY=%s INTERVAL_MINUTES=%s LOG_LEVEL=%s", core.tz, core.city, core.interval_minutes, core.log_level)
        return core

    def _load_telegram(self) -> TelegramConfig:
        env = self._read_env(".env.telegram")
        api_id = int(self._require(env, "TELEGRAM_API_ID"))
        api_hash = self._require(env, "TELEGRAM_API_HASH")
        session_file = Path(self._require(env, "TELEGRAM_SESSION")).expanduser()
        chat = self._require(env, "TELEGRAM_CHAT")
        allow_set_channel_photo = self._to_bool(env.get("ALLOW_SET_CHANNEL_PHOTO", "false"))
        if not session_file.is_absolute():
            raise ValueError(f"TELEGRAM_SESSION должен быть абсолютным путём: {session_file}")
        if not session_file.exists():
            logger.warning("ENV Telegram: файл сессии не существует: %s", session_file)
        masked_api = self._mask_api_id(api_id)
        logger.info(
            "ENV Telegram: API_ID=%s SESSION=%s CHAT=%s ALLOW_SET_CHANNEL_PHOTO=%s",
            masked_api,
            session_file,
            chat,
            allow_set_channel_photo,
        )
        return TelegramConfig(
            api_id=api_id,
            api_hash=api_hash,
            session_file=session_file,
            chat=chat,
            allow_set_channel_photo=allow_set_channel_photo,
        )

    def _load_weather(self) -> WeatherConfig:
        env = self._read_env(".env.weather")
        api_key = self._require(env, "OPENWEATHER_API_KEY")
        lang = env.get("OPENWEATHER_LANG", "ru")
        units = env.get("OPENWEATHER_UNITS", "metric")
        logger.info("ENV Weather: KEY=*** LANG=%s UNITS=%s", lang, units)
        return WeatherConfig(api_key=api_key, lang=lang, units=units)

    def _load_wallpapers(self) -> Dict[str, Any]:
        file = self.config_dir / "config.json"
        try:
            logger.debug("📥 Чтение config.json: %s", file)
            if file.exists():
                with file.open("r", encoding="utf-8") as f:
                    data: Dict[str, Any] = json.load(f)
                if "matrix" not in data or not isinstance(data["matrix"], dict):
                    raise ValueError("Некорректный config.json: отсутствует объект 'matrix'")
                return data
            legacy = self.config_dir / "wallpapers.json"
            if legacy.exists():
                logger.warning("config.json не найден; используем устаревший wallpapers.json: %s", legacy)
                with legacy.open("r", encoding="utf-8") as f:
                    return json.load(f)
            raise FileNotFoundError("Отсутствует файл конфигурации config.json")
        except Exception as exc:  # noqa: BLE001
            logger.error("Не удалось прочитать config.json %s: %s", file, exc)
            raise

    def _read_env(self, name: str) -> Dict[str, str]:
        file_path = self.config_dir / name
        if not file_path.exists():
            raise FileNotFoundError(f"Отсутствует файл конфигурации: {file_path}")
        logger.debug("📥 Загружаем env-файл: %s", file_path)
        env = dotenv_values(str(file_path))
        # Merge with OS env as fallback (do not override explicit file values)
        result: Dict[str, str] = {}
        for k, v in os.environ.items():
            result[k] = v
        for k, v in env.items():
            if v is not None:
                result[k] = v
        return result

    @staticmethod
    def _require(env: Dict[str, str], key: str) -> str:
        value = env.get(key)
        if not value:
            raise KeyError(f"Required key '{key}' is missing in configuration")
        return value

    @staticmethod
    def _to_bool(value: str | bool) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _mask_api_id(api_id: int) -> str:
        s = str(api_id)
        if len(s) <= 2:
            return "*" * len(s)
        return "*" * (len(s) - 2) + s[-2:]
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]


def _bool(v: str | bool) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"1", "true", "yes", "on"}


def _load_envs(base: Path) -> None:
    for name in (".env.core", ".env.weather", ".env.telegram"):
        p = base / "config" / name
        if p.exists():
            load_dotenv(p, override=True)


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
    @classmethod
    def load(cls, base_dir: Path | None = None) -> "Config":
        base_dir = base_dir or ROOT_DIR
        _load_envs(base_dir)
        need = ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_SESSION", "TELEGRAM_CHAT", "OPENWEATHER_API_KEY"]
        if any(not os.getenv(k) for k in need):
            raise ValueError("Missing required env keys")
        core = CoreConfig(
            tz=os.getenv("TZ", "UTC"),
            city=os.getenv("CITY", "Moscow"),
            interval_minutes=int(os.getenv("INTERVAL_MINUTES", "30")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )
        tg = TelegramConfig(
            api_id=int(os.getenv("TELEGRAM_API_ID", "0")),
            api_hash=os.getenv("TELEGRAM_API_HASH", ""),
            session_file=Path(os.getenv("TELEGRAM_SESSION", "")).expanduser().resolve(),
            chat=os.getenv("TELEGRAM_CHAT", ""),
            allow_set_channel_photo=_bool(os.getenv("ALLOW_SET_CHANNEL_PHOTO", "false")),
        )
        weather = WeatherConfig(
            api_key=os.getenv("OPENWEATHER_API_KEY", ""),
            lang=os.getenv("OPENWEATHER_LANG", "ru"),
            units=os.getenv("OPENWEATHER_UNITS", "metric"),
        )
        with (base_dir / "config" / "config.json").open("r", encoding="utf-8") as f:
            matrix: dict[str, Any] = json.load(f)
        cfg = cls.__new__(cls)
        cfg.config_dir = base_dir / "config"
        cfg.core = core
        cfg.telegram = tg
        cfg.weather = weather
        cfg.wallpaper_matrix = matrix
        return cfg



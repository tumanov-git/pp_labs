from __future__ import annotations

from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

__all__ = ["setup_logging"]


def _level(name: str) -> int:
    return getattr(logging, name.upper(), logging.INFO)


def _handler(path: Path, max_bytes: int, backups: int, level: int) -> RotatingFileHandler:
    h = RotatingFileHandler(filename=str(path), maxBytes=max_bytes, backupCount=backups, encoding="utf-8")
    h.setLevel(level)
    h.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S"))
    return h


def setup_logging(log_level: str = "INFO", log_dir: Path | None = None) -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    level = _level(log_level)
    root.setLevel(level)
    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", "%Y-%m-%d %H:%M:%S"))
    root.addHandler(sh)
    if log_dir is None:
        return
    log_dir.mkdir(parents=True, exist_ok=True)
    root.addHandler(_handler(log_dir / "app.log", 5 * 1024 * 1024, 3, level))
    weather = logging.getLogger("weather")
    weather.setLevel(level)
    weather.addHandler(_handler(log_dir / "weather.log", 2 * 1024 * 1024, 2, level))
    logging.getLogger("telethon").setLevel(logging.INFO)
    logging.getLogger("telethon.network.mtprotosender").setLevel(logging.INFO)



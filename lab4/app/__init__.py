"""Пакет Telegram TGWall.

CLI и сервис для смены обоев канала Telegram в зависимости от фаз
суток (рассвет/закат из OpenWeatherMap).
"""

from __future__ import annotations

from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

__all__ = [
    "setup_logging",
]


def setup_logging(log_level: str = "INFO", log_dir: Path | None = None) -> None:
    """Настроить логирование в stdout и файл с ротацией.

    Parameters
    ----------
    log_level:
        Уровень логирования (например, "DEBUG", "INFO").
    log_dir:
        Каталог для лог-файла ("logs/app.log"). Если не указан,
        файловый обработчик не добавляется.
    """

    root_logger = logging.getLogger()
    if root_logger.handlers:
        # Предотвращаем дубли обработчиков при повторной инициализации
        return

    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.setLevel(level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    if log_dir is not None:
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                filename=str(log_dir / "app.log"),
                maxBytes=5 * 1024 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception:  # noqa: BLE001 - best-effort file logging
            # Если файловый обработчик не инициализировался — продолжаем с stdout
            logging.getLogger(__name__).warning(
                "Не удалось инициализировать файловое логирование; продолжаем только stdout",
                exc_info=True,
            )

    # Отдельный лог для погоды
    if log_dir is not None:
        try:
            weather_logger = logging.getLogger("weather")
            if not any(isinstance(h, RotatingFileHandler) and getattr(h, 'baseFilename', '').endswith('weather.log') for h in weather_logger.handlers):
                weather_fh = RotatingFileHandler(
                    filename=str(log_dir / "weather.log"),
                    maxBytes=2 * 1024 * 1024,
                    backupCount=2,
                    encoding="utf-8",
                )
                weather_fh.setLevel(level)
                weather_fh.setFormatter(formatter)
                weather_logger.setLevel(level)
                weather_logger.addHandler(weather_fh)
        except Exception:
            logging.getLogger(__name__).warning("Не удалось настроить weather.log", exc_info=True)

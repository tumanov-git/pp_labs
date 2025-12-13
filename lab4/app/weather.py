from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging

import requests


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WeatherData:
    """Данные о времени рассвета/заката и погодных условиях.

    Attributes
    ----------
    sunrise:
        Localized datetime of sunrise (tzinfo set to the location offset).
    sunset:
        Localized datetime of sunset (tzinfo set to the location offset).
    timezone_offset:
        Offset in seconds from UTC for the location.
    Дополнительно включены упрощённые погодные поля для выбора обоев.
    """

    sunrise: datetime
    sunset: datetime
    timezone_offset: int
    weather_main: Optional[str] = None  # пример: "Clear", "Clouds", "Rain", "Thunderstorm", "Snow", "Fog"
    weather_id: Optional[int] = None    # код OpenWeather (2xx, 3xx, 5xx, 6xx, 7xx, 800, 80x)
    clouds_percent: Optional[int] = None


class WeatherProvider:
    """Получает sunrise/sunset и базовые погодные признаки из OpenWeatherMap current weather API."""

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: str, units: str = "metric", lang: str = "en") -> None:
        self.api_key = api_key
        self.units = units
        self.lang = lang

    def fetch(self, city: str, timeout_s: int = 10) -> Optional[WeatherData]:
        """Запросить погоду для города. При ошибке вернуть None (вызовущий решит, что делать)."""
        params = {
            "q": city,
            "appid": self.api_key,
            "units": self.units,
            "lang": self.lang,
        }
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=timeout_s)
            resp.raise_for_status()
            data = resp.json()
            sys = data.get("sys", {})
            tz_offset = int(data.get("timezone", 0))
            sunrise_ts = int(sys.get("sunrise"))
            sunset_ts = int(sys.get("sunset"))

            tz = timezone(timedelta(seconds=tz_offset))
            sunrise = datetime.fromtimestamp(sunrise_ts, tz)
            sunset = datetime.fromtimestamp(sunset_ts, tz)

            weather_list = data.get("weather") or []
            main = None
            wid = None
            if weather_list:
                w0 = weather_list[0] or {}
                main = w0.get("main")
                try:
                    wid = int(w0.get("id")) if w0.get("id") is not None else None
                except Exception:
                    wid = None
            clouds = None
            try:
                clouds = int((data.get("clouds") or {}).get("all"))
            except Exception:
                clouds = None

            return WeatherData(
                sunrise=sunrise,
                sunset=sunset,
                timezone_offset=tz_offset,
                weather_main=main,
                weather_id=wid,
                clouds_percent=clouds,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch weather: %s", exc, exc_info=True)
            return None
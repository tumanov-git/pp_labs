from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional
import logging
import requests

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WeatherData:
    sunrise: datetime
    sunset: datetime
    timezone_offset: int
    weather_main: Optional[str] = None
    weather_id: Optional[int] = None
    clouds_percent: Optional[int] = None


class WeatherProvider:
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def __init__(self, api_key: str, units: str = "metric", lang: str = "en") -> None:
        self.api_key = api_key
        self.units = units
        self.lang = lang

    def fetch(self, city: str, timeout_s: int = 10) -> Optional[WeatherData]:
        params = {"q": city, "appid": self.api_key, "units": self.units, "lang": self.lang}
        try:
            r = requests.get(self.BASE_URL, params=params, timeout=timeout_s)
            r.raise_for_status()
            data = r.json()
            sys = data.get("sys", {})
            tz_offset = int(data.get("timezone", 0))
            tz = timezone(timedelta(seconds=tz_offset))
            sunrise = datetime.fromtimestamp(int(sys.get("sunrise")), tz)
            sunset = datetime.fromtimestamp(int(sys.get("sunset")), tz)
            w0 = (data.get("weather") or [{}])[0] or {}
            main = w0.get("main")
            wid = int(w0.get("id")) if w0.get("id") is not None else None
            clouds = int((data.get("clouds") or {}).get("all")) if (data.get("clouds") or {}).get("all") is not None else None
            return WeatherData(sunrise=sunrise, sunset=sunset, timezone_offset=tz_offset, weather_main=main, weather_id=wid, clouds_percent=clouds)
        except Exception as exc:
            logger.error("weather fetch failed: %s", exc)
            return None



from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal
import logging

from .weather import WeatherData


logger = logging.getLogger(__name__)

Phase = Literal["night", "dawn", "morning", "day", "evening", "sunset"]


@dataclass(frozen=True)
class TimeSelector:
    """Определяет текущую фазу суток на основе времени рассвета/заката.

    Правила (локальное время):
    - dawn:    [sunrise - 30m, sunrise + 30m)
    - morning: [sunrise + 30m, sunrise + 2h)
    - day:     [sunrise + 2h,  sunset - 2h)
    - evening: [sunset - 2h,   sunset - 30m)
    - sunset:  [sunset - 30m,  sunset + 30m)
    - night:   иначе
    """

    weather: WeatherData

    def get_phase(self, now: datetime) -> Phase:
        sunrise = self.weather.sunrise
        sunset = self.weather.sunset

        dawn_start = sunrise - timedelta(minutes=30)
        dawn_end = sunrise + timedelta(minutes=30)

        morning_start = dawn_end
        morning_end = sunrise + timedelta(hours=2)

        day_start = morning_end
        day_end = sunset - timedelta(hours=2)

        evening_start = day_end
        evening_end = sunset - timedelta(minutes=30)

        sunset_start = evening_end
        sunset_end = sunset + timedelta(minutes=30)

        # Normalize 'now' to the same tz as weather datetimes if missing
        if now.tzinfo is None:
            now = now.replace(tzinfo=self.weather.sunrise.tzinfo)

        if dawn_start <= now < dawn_end:
            return "dawn"
        if morning_start <= now < morning_end:
            return "morning"
        if day_start <= now < day_end:
            return "day"
        if evening_start <= now < evening_end:
            return "evening"
        if sunset_start <= now < sunset_end:
            return "sunset"
        return "night"

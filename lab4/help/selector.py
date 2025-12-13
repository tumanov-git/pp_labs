from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from .weather import WeatherData

Phase = Literal["night", "dawn", "morning", "day", "evening", "sunset"]


def _bounds(sunrise: datetime, sunset: datetime) -> dict[str, datetime]:
    return {
        "dawn_start": sunrise - timedelta(minutes=30),
        "dawn_end": sunrise + timedelta(minutes=30),
        "morning_end": sunrise + timedelta(hours=2),
        "day_end": sunset - timedelta(hours=2),
        "evening_end": sunset - timedelta(minutes=30),
        "sunset_end": sunset + timedelta(minutes=30),
    }


@dataclass(frozen=True)
class TimeSelector:
    weather: WeatherData

    def get_phase(self, now: datetime) -> Phase:
        sr, ss = self.weather.sunrise, self.weather.sunset
        if now.tzinfo is None:
            now = now.replace(tzinfo=sr.tzinfo)
        b = _bounds(sr, ss)
        if now < b["dawn_start"]:
            return "night"
        if now < b["dawn_end"]:
            return "dawn"
        if now < b["morning_end"]:
            return "morning"
        if now < b["day_end"]:
            return "day"
        if now < b["evening_end"]:
            return "evening"
        if now < b["sunset_end"]:
            return "sunset"
        return "night"


def phase_at(weather: WeatherData, dt: datetime) -> Phase:
    return TimeSelector(weather).get_phase(dt)



from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from .config import Config
from .selector import TimeSelector
from .weather import WeatherProvider, WeatherData
from .wallpapers import WallpaperMatrix
from .log_utils import trim_logs, update_weather_stats


@dataclass
class AppService:
    config: Config

    def __post_init__(self) -> None:
        w = self.config.weather
        self.weather_provider = WeatherProvider(api_key=w.api_key, units=w.units, lang=w.lang)
        t = self.config.telegram
        from .telegram_client import TelegramAuth, TelegramClientWrapper
        self.telegram = TelegramClientWrapper(TelegramAuth(t.api_id, t.api_hash, t.session_file))
        self.wallpapers = WallpaperMatrix.from_json(self.config.config_dir.parent, self.config.wallpaper_matrix)
        self._app_log = (self.config.config_dir.parent / "logs" / "app.log").resolve()
        self._max_lines = int((self.config.wallpaper_matrix.get("logs") or {}).get("max_entries", 50))
        stats = self.config.wallpaper_matrix.get("stats") or {}
        self._stats_on = bool(stats.get("enabled", True))
        self._stats_path = (self.config.config_dir.parent / str(stats.get("file", ".cache/weather_stats.json"))).resolve()

    async def run_once(self, city: str | None = None) -> None:
        city = city or self.config.core.city
        wd = self.weather_provider.fetch(city)
        phase = "day"
        if wd:
            phase = TimeSelector(wd).get_phase(datetime.now(tz=wd.sunrise.tzinfo))
        inst = self.wallpapers.pick_instance(phase, wd.weather_main if wd else None, wd.weather_id if wd else None, wd.clouds_percent if wd else None)
        fp = self.wallpapers.pick_wallpaper(phase, inst)
        if not fp or not fp.exists():
            return
        if self.wallpapers.should_skip_by_cache(phase, inst, fp):
            return
        await self.telegram.apply_wallpaper(self.config.telegram.chat, fp, self.config.telegram.allow_set_channel_photo)
        self.wallpapers.save_cache(phase, inst, fp)
        trim_logs(self._app_log, self._max_lines)
        update_weather_stats(self._stats_path, inst, self._stats_on)
        await self.telegram.close()

    async def run_daemon(self, interval_minutes: int | None = None, city: str | None = None) -> None:
        fallback = float((interval_minutes or self.wallpapers.update.interval_minutes or self.config.core.interval_minutes) * 60)
        while True:
            try:
                await self.run_once(city=city)
            finally:
                sec = fallback
                try:
                    c = city or self.config.core.city
                    wd = self.weather_provider.fetch(c)
                    if wd:
                        now = datetime.now(tz=wd.sunrise.tzinfo)
                        nxt, _ = self._next(wd, now)
                        sec = max(1.0, (nxt - now).total_seconds())
                except Exception:
                    sec = fallback
                await asyncio.sleep(sec)

    def _next(self, wd: WeatherData, now: datetime) -> tuple[datetime, str]:
        sr, ss = wd.sunrise, wd.sunset
        pts = [
            (sr - timedelta(minutes=30), "dawn"),
            (sr + timedelta(minutes=30), "morning"),
            (sr + timedelta(hours=2), "day"),
            (ss - timedelta(hours=2), "evening"),
            (ss - timedelta(minutes=30), "sunset"),
            (ss + timedelta(minutes=30), "night"),
        ]
        for t, ph in pts:
            if now < t:
                return t, ph
        return (sr + timedelta(days=1) - timedelta(minutes=30)), "dawn"



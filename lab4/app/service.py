from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from .config import Config
from .weather import WeatherProvider, WeatherData
from .selector import TimeSelector
from .wallpapers import WallpaperMatrix
from .log_utils import trim_logs, update_weather_stats


logger = logging.getLogger(__name__)


@dataclass
class AppService:
    """Координирует получение погоды, выбор фазы и применение обоев."""

    config: Config

    def __post_init__(self) -> None:  # type: ignore[override]
        wcfg = self.config.weather
        self.weather_provider = WeatherProvider(api_key=wcfg.api_key, units=wcfg.units, lang=wcfg.lang)
        tcfg = self.config.telegram
        from .telegram_client import TelegramClientWrapper, TelegramAuth
        self.telegram = TelegramClientWrapper(TelegramAuth(tcfg.api_id, tcfg.api_hash, tcfg.session_file))
        self.wallpapers = WallpaperMatrix.from_json(
            base_dir=self.config.config_dir.parent,  # относительные пути от корня проекта
            data=self.config.wallpaper_matrix,
        )
        # Настройки ротации логов из config.json
        raw = self.config.wallpaper_matrix or {}
        logs_cfg = raw.get("logs") or {}
        try:
            self._log_max_entries = int(logs_cfg.get("max_entries", 50))
        except Exception:
            self._log_max_entries = 50
        self._app_log_path = (self.config.config_dir.parent / "logs" / "app.log").expanduser().resolve()
        # Настройки статистики погоды
        stats_cfg = raw.get("stats") or {}
        self._stats_enabled = bool(stats_cfg.get("enabled", True))
        stats_file = str(stats_cfg.get("file", ".cache/weather_stats.json"))
        self._stats_path = (self.config.config_dir.parent / stats_file).expanduser().resolve()

    async def run_once(self, city: str | None = None) -> None:
        city_to_use = city or self.config.core.city
        logger.info("Запуск обновления tgwall для города=%s", city_to_use)

        logger.debug("Получаем погоду для города=%s", city_to_use)
        weather = self.weather_provider.fetch(city_to_use)
        if weather is None:
            logger.warning("Погода недоступна; используем фазу 'day' по умолчанию")
            phase = "day"
        else:
            selector = TimeSelector(weather)
            now_local = datetime.now(tz=weather.sunrise.tzinfo)
            phase = selector.get_phase(now_local)
            logger.debug("Вычислена фаза=%s на момент=%s (sunrise=%s sunset=%s)", phase, now_local, weather.sunrise, weather.sunset)

        # 1) инстанс
        instance = self.wallpapers.pick_instance(
            phase=phase,
            weather_main=(weather.weather_main.lower() if weather and weather.weather_main else None) if weather else None,
            weather_id=(weather.weather_id if weather else None),
            clouds=(weather.clouds_percent if weather else None),
        )
        # 2) файл
        wallpaper_path = self.wallpapers.pick_wallpaper(phase, instance)
        if wallpaper_path is None:
            logger.error("Не удалось определить файл обоев для фазы=%s инстанса=%s", phase, instance)
            return

        tcfg = self.config.telegram
        logger.debug("Применяем обои: чат=%s путь=%s", tcfg.chat, wallpaper_path)
        if not wallpaper_path.exists():
            logger.warning("Файл обоев отсутствует; пропускаем обновление Telegram: %s", wallpaper_path)
            return

        # 3) кэш-пропуск
        if self.wallpapers.should_skip_by_cache(phase, instance, wallpaper_path):
            logger.info("Phase=%s Weather=%s — изменений нет, пропускаем", phase, instance)
            return

        # 4) применить
        await self.telegram.apply_wallpaper(tcfg.chat, wallpaper_path, tcfg.allow_set_channel_photo)
        logger.info("Phase=%s Weather=%s Wallpaper=%s", phase, instance, wallpaper_path)
        # 5) сохранить кэш
        self.wallpapers.save_cache(phase, instance, wallpaper_path)
        # 6) ротация логов по количеству записей
        try:
            trim_logs(self._app_log_path, self._log_max_entries)
        except Exception:  # noqa: BLE001
            logger.debug("Ошибка ротации логов", exc_info=True)
        # 7) статистика погодных состояний
        try:
            update_weather_stats(self._stats_path, instance, self._stats_enabled)
        except Exception:  # noqa: BLE001
            logger.debug("Ошибка обновления статистики погоды", exc_info=True)
        # Всегда закрываем клиент в одиночном режиме
        try:
            await self.telegram.close()
        except Exception:  # noqa: BLE001
            logger.warning("Не удалось корректно закрыть Telegram-клиент после run_once", exc_info=True)

    async def run_daemon(self, interval_minutes: int | None = None, city: str | None = None) -> None:
        fallback_interval = interval_minutes or self.wallpapers.update.interval_minutes or self.config.core.interval_minutes
        logger.info("Запускаем демон по контрольным точкам фаз (резервный интервал=%s мин)", fallback_interval)
        try:
            while True:
                # Выполнить обновление сейчас (актуализировать обои)
                try:
                    await self.run_once(city=city)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Итерация обновления завершилась ошибкой: %s", exc, exc_info=True)

                # Рассчитать следующую контрольную точку
                try:
                    city_to_use = city or self.config.core.city
                    weather = self.weather_provider.fetch(city_to_use)
                    if weather is None:
                        raise RuntimeError("Погода недоступна для расчёта контрольной точки")

                    now_local = datetime.now(tz=weather.sunrise.tzinfo)
                    selector = TimeSelector(weather)
                    current_phase = selector.get_phase(now_local)
                    next_time, next_phase = self._compute_next_checkpoint(weather, now_local)

                    seconds = max(1.0, (next_time - now_local).total_seconds())
                    logger.info(
                        "Scheduler: now=%s phase=%s -> next=%s at %s (in %.0fs)",
                        now_local,
                        current_phase,
                        next_phase,
                        next_time,
                        seconds,
                    )
                except Exception as exc:  # noqa: BLE001
                    seconds = max(1.0, float(fallback_interval * 60))
                    logger.warning(
                        "Не удалось вычислить следующую контрольную точку; используем резерв %s минут. Ошибка: %s",
                        fallback_interval,
                        exc,
                        exc_info=True,
                    )

                # Спим до следующего события (на 1-2 секунды раньше смысла нет; оставим минимальный дрейф)
                await asyncio.sleep(seconds)
        finally:
            try:
                await self.telegram.close()
            except Exception:  # noqa: BLE001
                logger.warning("Не удалось закрыть Telegram-клиент при остановке демона", exc_info=True)

    def _compute_next_checkpoint(self, weather: WeatherData, now: datetime) -> tuple[datetime, str]:
        """Рассчитать ближайшую временную контрольную точку и целевую фазу.

        Контрольные точки привязаны к границам фаз TimeSelector.
        """
        sunrise = weather.sunrise
        sunset = weather.sunset

        dawn_start = sunrise - timedelta(minutes=30)
        dawn_end = sunrise + timedelta(minutes=30)          # -> morning
        morning_end = sunrise + timedelta(hours=2)          # -> day
        day_end = sunset - timedelta(hours=2)               # -> evening
        evening_end = sunset + timedelta(minutes=20)        # -> twilight
        twilight_end = sunset + timedelta(minutes=50)       # -> night

        if now < dawn_start:
            return dawn_start, "dawn"
        if now < dawn_end:
            return dawn_end, "morning"
        if now < morning_end:
            return morning_end, "day"
        if now < day_end:
            return day_end, "evening"
        if now < evening_end:
            return evening_end, "twilight"
        if now < twilight_end:
            return twilight_end, "night"

        # После завершения twilight — ждём следующего рассвета следующего дня
        next_sunrise = sunrise + timedelta(days=1)
        next_dawn_start = next_sunrise - timedelta(minutes=30)
        return next_dawn_start, "dawn"

    # (логика инстансов и кэша перенесена в WallpaperMatrix)
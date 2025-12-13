from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import random
import json


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MatrixFlags:
    mode: str = "weather_no_fog"          # "time_only" | "weather_based" | "weather_no_fog" | "random_mode"
    cache_enabled: bool = True
    use_random_selection: bool = True
    log_details: bool = False
    apply_fog_for_all_phases: bool = False


@dataclass(frozen=True)
class MatrixProbabilities:
    fogChance: float = 0.3
    thunderChance: float = 0.5


@dataclass(frozen=True)
class MatrixUpdate:
    interval_minutes: int = 30
    timezone: str = "UTC"


@dataclass(frozen=True)
class WallpaperMatrix:
    """Резолвер путей обоев по фазе и погодным инстансам.

    Поддерживает обратную совместимость со старым форматом (phase -> path).
    """

    base_dir: Path
    flags: MatrixFlags
    probabilities: MatrixProbabilities
    update: MatrixUpdate
    # matrix: phase -> instance -> list[path]
    matrix: Dict[str, Dict[str, List[str]]]

    @classmethod
    def from_json(cls, base_dir: Path, data: Dict[str, Any]) -> "WallpaperMatrix":
        raw_matrix = data.get("matrix")
        if not isinstance(raw_matrix, dict):
            raise ValueError("Некорректный wallpapers.json: отсутствует объект 'matrix'")

        # Разбор флагов
        raw_flags = data.get("flags") or {}
        flags = MatrixFlags(
            mode=str(raw_flags.get("mode", "time_only")),
            cache_enabled=bool(raw_flags.get("cache_enabled", True)),
            use_random_selection=bool(raw_flags.get("use_random_selection", True)),
            log_details=bool(raw_flags.get("log_details", False)),
            apply_fog_for_all_phases=bool(raw_flags.get("apply_fog_for_all_phases", False)),
        )

        # Вероятности
        raw_probs = data.get("probabilities") or {}
        probs = MatrixProbabilities(
            fogChance=float(raw_probs.get("fogChance", 0.3)),
            thunderChance=float(raw_probs.get("thunderChance", 0.5)),
        )

        # Обновление
        raw_upd = data.get("update") or {}
        upd = MatrixUpdate(
            interval_minutes=int(raw_upd.get("interval_minutes", 30)),
            timezone=str(raw_upd.get("timezone", "UTC")),
        )

        # Нормализация матрицы
        norm: Dict[str, Dict[str, List[str]]] = {}
        for phase, value in raw_matrix.items():
            if isinstance(value, str):
                # Старый формат: phase -> path
                norm[phase] = {"clear": [value]}
            elif isinstance(value, dict):
                inst_map: Dict[str, List[str]] = {}
                for inst, files in value.items():
                    if isinstance(files, list):
                        inst_map[str(inst)] = [str(p) for p in files]
                    elif isinstance(files, str):
                        inst_map[str(inst)] = [str(files)]
                norm[phase] = inst_map
            else:
                logger.warning("Игнорируем некорректную запись матрицы для фазы %s", phase)

        obj = cls(base_dir=base_dir, flags=flags, probabilities=probs, update=upd, matrix=norm)
        # Инициализация кэша при создании
        try:
            obj.init_cache()
        except Exception:
            logger.debug("Не удалось инициализировать кэш", exc_info=True)
        return obj

    def resolve_file(self, phase: str, instance: str) -> Optional[Path]:
        """Выбрать файл для пары (фаза, инстанс) с учётом настроек.

        Возвращает None, если ничего не найдено.
        """
        phase_map = self.matrix.get(phase)
        if not phase_map:
            logger.warning("Для фазы %s нет записей в матрице", phase)
            return None
        candidates = phase_map.get(instance)
        if not candidates or not len(candidates):
            # Пытаемся взять clear как базовый
            candidates = phase_map.get("clear")
        if not candidates:
            # Берём любые доступные
            for _, files in phase_map.items():
                if files:
                    candidates = files
                    break
        if not candidates:
            return None

        if self.flags.use_random_selection:
            choice = random.choice(candidates)
            if self.flags.log_details:
                try:
                    idx = candidates.index(choice) + 1
                    total = len(candidates)
                    logger.debug("Выбран случайный вариант #%s из %s для %s/%s -> %s", idx, total, phase, instance, choice)
                except Exception:
                    logger.debug("Выбран случайный вариант для %s/%s -> %s", phase, instance, choice)
        else:
            choice = candidates[0]
        path = (self.base_dir / choice).expanduser().resolve()
        if not path.exists():
            logger.warning("Файл обоев не существует: %s", path)
        if self.flags.log_details:
            logger.debug("Выбран файл для фазы=%s инстанса=%s -> %s", phase, instance, path)
        return path

    # -------------------- Работа с кэшем --------------------
    def _cache_dir(self) -> Path:
        return (self.base_dir / ".cache").expanduser().resolve()

    def _cache_file(self) -> Path:
        return self._cache_dir() / "last_state.json"

    def init_cache(self) -> None:
        d = self._cache_dir()
        d.mkdir(parents=True, exist_ok=True)
        f = self._cache_file()
        if not f.exists():
            f.write_text('{"phase":"","weather":"","file":""}', encoding="utf-8")

    def load_cache(self) -> Dict[str, Any]:
        try:
            f = self._cache_file()
            if f.exists():
                return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            logger.debug("Не удалось прочитать кэш", exc_info=True)
        return {"phase": "", "weather": "", "file": ""}

    def save_cache(self, phase: str, weather: str, file_path: Path) -> None:
        try:
            payload = {"phase": phase, "weather": weather, "file": str(file_path)}
            self._cache_file().write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            logger.debug("Не удалось сохранить кэш", exc_info=True)

    def should_skip_by_cache(self, phase: str, instance: str, file_path: Path) -> bool:
        if not self.flags.cache_enabled:
            return False
        try:
            data = self.load_cache()
            return data.get("phase") == phase and data.get("weather") == instance and data.get("file") == str(file_path)
        except Exception:
            return False

    # -------------------- Выбор инстансов и файлов --------------------
    def instances_for_phase(self, phase: str) -> List[str]:
        phase_map = self.matrix.get(phase) or {}
        return list(phase_map.keys())

    def pick_instance(
        self,
        phase: str,
        weather_main: Optional[str],
        weather_id: Optional[int],
        clouds: Optional[int],
    ) -> str:
        # Режим только по времени
        if self.flags.mode == "time_only":
            return "clear"

        main = (weather_main or "").lower()
        wid = int(weather_id or 0)
        clouds_pct = int(clouds or 0)

        # Базовая категоризация
        if main == "thunderstorm" or 200 <= wid <= 232:
            base = "heavy_rain"
        elif main in ("drizzle",):
            base = "rain"
        elif main == "rain" or 500 <= wid <= 531:
            base = "heavy_rain" if wid in (502, 503, 504, 522, 531) else "rain"
        elif main == "snow" or 600 <= wid <= 622:
            base = "heavy_rain" if wid in (602, 622) else "rain"
        elif main in ("mist", "fog", "haze") or 700 <= wid < 800:
            # Туман как погода: никогда не возвращаем прямой инстанс "fog".
            # Выбираем ближний по ощущению вариант; собственно fog применяется позже только для dawn.
            base = "overcast" if clouds_pct >= 85 else ("cloudy" if clouds_pct >= 40 else "clear")
        elif main == "clear" or wid == 800:
            base = "clear"
        elif main == "clouds" or 801 <= wid <= 804:
            base = "overcast" if clouds_pct >= 85 else ("cloudy" if clouds_pct >= 40 else "clear")
        else:
            base = "clear"

        if self.flags.mode == "random_mode":
            # случайный доступный инстанс для фазы
            insts = self.instances_for_phase(phase)
            if insts:
                return random.choice(insts) if self.flags.use_random_selection else insts[0]
            return base

        # Вероятностные модификаторы
        probs = self.probabilities
        details = self.flags.log_details
        weather_logger = logging.getLogger("weather")
        try:
            # Базовая запись в отдельный файл погоды (учитываем туман, даже если выключен)
            weather_logger.info(
                "Mode=%s Phase=%s Base=%s Main=%s Wid=%s Clouds=%s",
                self.flags.mode,
                phase,
                base,
                main,
                wid,
                clouds_pct,
            )
        except Exception:
            pass

        # Туман только на рассвете (dawn). Для остальных фаз вероятность тумана = 0.
        # Применяется только к базам clear/cloudy и только в dawn, цель — fog_clear/fog_cloudy.
        fog_allowed_general = (phase == "dawn") and base in ("clear", "cloudy")
        fog_rand = None
        fog_applied = False
        fog_target = None
        if fog_allowed_general:
            fog_rand = random.random()
            # Подбираем только fog_clear / fog_cloudy (если они существуют в матрице)
            phase_map = self.matrix.get(phase) or {}
            preferred = f"fog_{base}"  # fog_clear или fog_cloudy
            alt = "fog_cloudy" if preferred == "fog_clear" else "fog_clear"
            if phase_map.get(preferred):
                fog_target = preferred
            elif phase_map.get(alt):
                fog_target = alt
            else:
                fog_target = None
            # Логируем возможный туман в отдельный файл даже если режим без тумана
            try:
                weather_logger.info(
                    "FogCandidate phase=%s base=%s target=%s rand=%.2f<th=%.2f",
                    phase,
                    base,
                    fog_target or "n/a",
                    fog_rand,
                    probs.fogChance,
                )
            except Exception:
                pass
            # Применяем туман только если режим не weather_no_fog
            if fog_target and self.flags.mode != "weather_no_fog" and fog_rand < probs.fogChance:
                old_base = base
                base = fog_target
                fog_applied = True
                if details:
                    logger.debug(
                        "Туман активирован: %s → %s (phase=%s rand=%.2f < %.2f)",
                        old_base,
                        base,
                        phase,
                        fog_rand,
                        probs.fogChance,
                    )

        # Гроза как модификатор ливня
        if base == "heavy_rain":
            r = random.random()
            if details:
                logger.debug("thunderChance=%.2f rand=%.2f", probs.thunderChance, r)
            if r < probs.thunderChance:
                base = "thunderstorm"

        if details:
            logger.debug("Выбран инстанс для фазы=%s -> %s (main=%s id=%s clouds=%s)", phase, base, main, wid, clouds_pct)
        try:
            weather_logger.info(
                "Final phase=%s instance=%s (mode=%s fog_applied=%s)",
                phase,
                base,
                self.flags.mode,
                fog_applied,
            )
        except Exception:
            pass
        return base

    def pick_wallpaper(self, phase: str, instance: str) -> Optional[Path]:
        return self.resolve_file(phase, instance)
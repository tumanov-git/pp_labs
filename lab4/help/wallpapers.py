from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import random


@dataclass(frozen=True)
class MatrixFlags:
    mode: str = "weather_no_fog"
    cache_enabled: bool = True
    use_random_selection: bool = True


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
    base_dir: Path
    flags: MatrixFlags
    probabilities: MatrixProbabilities
    update: MatrixUpdate
    matrix: Dict[str, Dict[str, List[str]]]

    @classmethod
    def from_json(cls, base_dir: Path, data: Dict[str, Any]) -> "WallpaperMatrix":
        raw = data.get("matrix") or {}
        flags = MatrixFlags(**(data.get("flags") or {}))
        probs = MatrixProbabilities(**(data.get("probabilities") or {}))
        upd = MatrixUpdate(**(data.get("update") or {}))
        norm: Dict[str, Dict[str, List[str]]] = {}
        for ph, val in raw.items():
            if isinstance(val, str):
                norm[ph] = {"clear": [val]}
            elif isinstance(val, dict):
                norm[ph] = {str(k): ([str(x) for x in v] if isinstance(v, list) else [str(v)]) for k, v in val.items()}
        obj = cls(base_dir=base_dir, flags=flags, probabilities=probs, update=upd, matrix=norm)
        obj._cache_dir().mkdir(parents=True, exist_ok=True)
        if not obj._cache_file().exists():
            obj._cache_file().write_text('{"phase":"","weather":"","file":""}', encoding="utf-8")
        return obj

    def _cache_dir(self) -> Path:
        return (self.base_dir / ".cache").expanduser().resolve()

    def _cache_file(self) -> Path:
        return self._cache_dir() / "last_state.json"

    def load_cache(self) -> Dict[str, Any]:
        try:
            return json.loads(self._cache_file().read_text(encoding="utf-8"))
        except Exception:
            return {"phase": "", "weather": "", "file": ""}

    def save_cache(self, phase: str, weather: str, file_path: Path) -> None:
        self._cache_file().write_text(json.dumps({"phase": phase, "weather": weather, "file": str(file_path)}, ensure_ascii=False), encoding="utf-8")

    def should_skip_by_cache(self, phase: str, weather: str, file_path: Path) -> bool:
        if not self.flags.cache_enabled:
            return False
        c = self.load_cache()
        return c.get("phase") == phase and c.get("weather") == weather and c.get("file") == str(file_path)

    def resolve_file(self, phase: str, instance: str) -> Optional[Path]:
        phase_map = self.matrix.get(phase) or {}
        files = phase_map.get(instance) or phase_map.get("clear") or next(iter(phase_map.values()), None)
        if not files:
            return None
        choice = random.choice(files) if self.flags.use_random_selection else files[0]
        return (self.base_dir / choice).expanduser().resolve()

    def pick_instance(self, phase: str, weather_main: Optional[str], weather_id: Optional[int], clouds: Optional[int]) -> str:
        if self.flags.mode == "time_only":
            return "clear"
        main = (weather_main or "").lower(); wid = int(weather_id or 0); cl = int(clouds or 0)
        if main == "thunderstorm" or 200 <= wid <= 232:
            base = "heavy_rain"
        elif main == "rain" or 500 <= wid <= 531:
            base = "rain"
        elif main == "clouds" or 801 <= wid <= 804:
            base = "overcast" if cl >= 85 else ("cloudy" if cl >= 40 else "clear")
        else:
            base = "clear"
        if base == "heavy_rain" and random.random() < self.probabilities.thunderChance:
            base = "thunderstorm"
        return base

    def pick_wallpaper(self, phase: str, instance: str) -> Optional[Path]:
        return self.resolve_file(phase, instance)



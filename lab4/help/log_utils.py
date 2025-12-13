from __future__ import annotations

from pathlib import Path
import json


def trim_logs(file_path: Path, max_lines: int) -> None:
    if max_lines <= 0:
        return
    p = file_path.expanduser().resolve()
    if not p.exists():
        return
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines(True)
    if len(lines) > max_lines:
        p.write_text("".join(lines[-max_lines:]), encoding="utf-8")


def update_weather_stats(file_path: Path, instance: str, enabled: bool) -> None:
    if not enabled:
        return
    p = file_path.expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    base = {"clear": 0, "cloudy": 0, "overcast": 0, "rain": 0, "heavy_rain": 0, "thunderstorm": 0, "fog": 0}
    data = base.copy()
    if p.exists():
        try:
            raw = json.loads(p.read_text(encoding="utf-8")) or {}
            if isinstance(raw, dict):
                for k, v in raw.items():
                    if isinstance(k, str) and isinstance(v, int):
                        data[k] = v
        except Exception:
            data = base.copy()
    key = "fog" if instance.startswith("fog") else instance
    data[key] = int(data.get(key, 0)) + 1
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def rebuild_weather_stats_from_log(log_file: Path, out_file: Path) -> None:
    lf = log_file.expanduser().resolve()
    text = lf.read_text(encoding="utf-8", errors="ignore")
    counts = {"clear": 0, "cloudy": 0, "overcast": 0, "rain": 0, "heavy_rain": 0, "thunderstorm": 0, "fog": 0}
    for line in text.splitlines():
        if "Final" in line and " instance=" in line:
            part = line.split(" instance=", 1)[1]
            inst = part.split(" ", 1)[0].split(")", 1)[0].strip()
            key = "fog" if inst.startswith("fog") else inst
            if key in counts:
                counts[key] += 1
    of = out_file.expanduser().resolve()
    of.parent.mkdir(parents=True, exist_ok=True)
    of.write_text(json.dumps(counts, ensure_ascii=False, indent=2), encoding="utf-8")



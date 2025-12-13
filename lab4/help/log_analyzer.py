from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt


@dataclass
class WeatherLogEntry:
    timestamp: datetime
    phase: str
    base: str
    main: str
    weather_id: int
    clouds_percent: int


def parse_log_file(log_path: Path) -> list[WeatherLogEntry]:
    pat = re.compile(
        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| INFO \| weather \| "
        r"Mode=\w+ Phase=(\w+) Base=(\w+) Main=(\w+) Wid=(\d+) Clouds=(\d+)"
    )
    out: list[WeatherLogEntry] = []
    for line in log_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = pat.search(line)
        if not m:
            continue
        out.append(
            WeatherLogEntry(
                timestamp=datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"),
                phase=m.group(2),
                base=m.group(3),
                main=m.group(4),
                weather_id=int(m.group(5)),
                clouds_percent=int(m.group(6)),
            )
        )
    return out


def plot_counts(entries: list[WeatherLogEntry], out_dir: Path) -> None:
    c = Counter(e.base for e in entries)
    labels = list(c.keys()); values = list(c.values())
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(labels, values)
    ax.set_title("Weather counts")
    fig.savefig(out_dir / "weather_distribution.png", dpi=120, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    base = Path(__file__).parent.parent
    log_path = base / "logs" / "weather.log"
    out_dir = base / "graphs"
    out_dir.mkdir(exist_ok=True)
    entries = parse_log_file(log_path)
    if entries:
        plot_counts(entries, out_dir)


if __name__ == "__main__":
    main()



"""
Анализатор логов погоды с визуализацией.

Парсит weather.log и создаёт красивые графики:
- Timeline облачности
- Распределение погодных условий (pie chart)
- Распределение фаз дня
- Heatmap облачности по дням/часам
- Статистика по типам погоды
"""

from __future__ import annotations

import os
import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

_BASE_DIR = Path(__file__).parent.parent
_MPL_DIR = (_BASE_DIR / ".cache" / "matplotlib").resolve()
_MPL_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_DIR))

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Wedge
from matplotlib.colors import LinearSegmentedColormap

# Настройка стиля
plt.style.use('dark_background')

# Цветовые палитры
PHASE_COLORS = {
    'night': '#1a1a2e',
    'dawn': '#ff7b54',
    'morning': '#ffb26b',
    'day': '#ffd56f',
    'evening': '#939b62',
    'sunset': '#e94560',
}

WEATHER_COLORS = {
    'clear': '#4fc3f7',
    'cloudy': '#90a4ae',
    'overcast': '#546e7a',
    'rain': '#1565c0',
    'snow': '#e1f5fe',
    'thunderstorm': '#6a1b9a',
    'fog': '#b0bec5',
    'mist': '#cfd8dc',
}

# Кастомная colormap для облачности
CLOUDS_CMAP = LinearSegmentedColormap.from_list(
    'clouds', 
    ['#4fc3f7', '#81d4fa', '#b3e5fc', '#90a4ae', '#607d8b', '#455a64', '#263238']
)


@dataclass
class WeatherLogEntry:
    """Одна запись из лога погоды."""
    timestamp: datetime
    phase: str
    base: str
    main: str
    weather_id: int
    clouds_percent: int


def parse_log_file(log_path: Path) -> list[WeatherLogEntry]:
    """Парсит лог-файл и возвращает список записей."""
    entries = []
    
    # Паттерн для строк с Mode=weather_based
    pattern = re.compile(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| INFO \| weather \| '
        r'Mode=\w+ Phase=(\w+) Base=(\w+) Main=(\w+) Wid=(\d+) Clouds=(\d+)'
    )
    
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                entries.append(WeatherLogEntry(
                    timestamp=timestamp,
                    phase=match.group(2),
                    base=match.group(3),
                    main=match.group(4),
                    weather_id=int(match.group(5)),
                    clouds_percent=int(match.group(6)),
                ))
    
    return entries


def entries_to_df(entries: list[WeatherLogEntry]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": [e.timestamp for e in entries],
            "phase": [e.phase for e in entries],
            "clouds": [e.clouds_percent for e in entries],
            "base": [e.base for e in entries],
        }
    )


def permutation_test_mean_diff(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    a: str,
    b: str,
    n_perm: int = 5000,
    seed: int = 7,
) -> tuple[float, float]:
    sub = df[df[group_col].isin([a, b])][[group_col, value_col]].dropna().copy()
    if sub.empty:
        return float("nan"), float("nan")
    g = (sub[group_col] == a).to_numpy(dtype=bool)
    x = sub[value_col].to_numpy(dtype=float)
    obs = float(x[g].mean() - x[~g].mean())
    rng = np.random.default_rng(seed)
    n = len(x)
    count = 0
    for _ in range(n_perm):
        idx = rng.permutation(n)
        gp = g[idx]
        diff = float(x[gp].mean() - x[~gp].mean())
        if diff >= obs:
            count += 1
    p_value = (count + 1) / (n_perm + 1)
    return obs, float(p_value)


def setup_figure_style(fig, ax, title: str):
    """Применяет единый стиль к графику."""
    fig.patch.set_facecolor('#0d1117')
    ax.set_facecolor('#161b22')
    ax.set_title(title, fontsize=16, fontweight='bold', color='#f0f6fc', pad=15)
    ax.tick_params(colors='#8b949e', labelsize=10)
    for spine in ax.spines.values():
        spine.set_color('#30363d')


def plot_clouds_timeline(entries: list[WeatherLogEntry], output_dir: Path):
    """График изменения облачности по времени."""
    fig, ax = plt.subplots(figsize=(14, 6))
    setup_figure_style(fig, ax, 'Облачность по времени')
    
    timestamps = [e.timestamp for e in entries]
    clouds = [e.clouds_percent for e in entries]
    
    # Градиентная заливка под линией
    ax.fill_between(timestamps, clouds, alpha=0.3, color='#4fc3f7')
    ax.plot(timestamps, clouds, color='#4fc3f7', linewidth=1.5, alpha=0.9)
    
    # Scatter точки с цветом по облачности
    scatter = ax.scatter(timestamps, clouds, c=clouds, cmap=CLOUDS_CMAP, 
                         s=15, alpha=0.7, edgecolors='none')
    
    ax.set_xlabel('Дата', fontsize=12, color='#8b949e')
    ax.set_ylabel('Облачность (%)', fontsize=12, color='#8b949e')
    ax.set_ylim(0, 105)
    
    # Форматирование дат
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    fig.autofmt_xdate()
    
    # Colorbar
    cbar = plt.colorbar(scatter, ax=ax, pad=0.02)
    cbar.set_label('Облачность %', color='#8b949e')
    cbar.ax.tick_params(colors='#8b949e')
    
    ax.grid(True, alpha=0.2, color='#30363d')
    
    plt.tight_layout()
    fig.savefig(output_dir / 'clouds_timeline.png', dpi=150, facecolor='#0d1117', 
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f'Сохранено: clouds_timeline.png')


def plot_weather_distribution(entries: list[WeatherLogEntry], output_dir: Path):
    """Круговая диаграмма распределения погодных условий."""
    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('#0d1117')
    
    # Подсчёт базовых погодных условий
    base_counts = Counter(e.base for e in entries)
    labels = list(base_counts.keys())
    sizes = list(base_counts.values())
    colors = [WEATHER_COLORS.get(label, '#607d8b') for label in labels]
    
    # Красивый donut chart
    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=None,
        colors=colors,
        autopct='%1.1f%%',
        startangle=90,
        pctdistance=0.75,
        wedgeprops=dict(width=0.5, edgecolor='#0d1117', linewidth=2),
        textprops=dict(color='#f0f6fc', fontsize=11, fontweight='bold')
    )
    
    # Центральный текст
    total = sum(sizes)
    ax.text(0, 0, f'{total}\nзаписей', ha='center', va='center', 
            fontsize=18, fontweight='bold', color='#f0f6fc')
    
    # Легенда
    legend_labels = [f'{label.capitalize()} ({count})' for label, count in zip(labels, sizes)]
    ax.legend(wedges, legend_labels, title='Погода', loc='center left', 
              bbox_to_anchor=(1, 0, 0.5, 1), fontsize=11, 
              title_fontsize=13, facecolor='#161b22', edgecolor='#30363d',
              labelcolor='#8b949e')
    
    ax.set_title('Распределение погодных условий', fontsize=16, 
                 fontweight='bold', color='#f0f6fc', pad=20)
    
    plt.tight_layout()
    fig.savefig(output_dir / 'weather_distribution.png', dpi=150, facecolor='#0d1117',
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f'Сохранено: weather_distribution.png')


def plot_phase_distribution(entries: list[WeatherLogEntry], output_dir: Path):
    """Горизонтальная диаграмма распределения фаз дня."""
    fig, ax = plt.subplots(figsize=(10, 6))
    setup_figure_style(fig, ax, 'Распределение фаз дня')
    
    phase_counts = Counter(e.phase for e in entries)
    
    # Сортировка по хронологии дня
    phase_order = ['night', 'dawn', 'morning', 'day', 'evening', 'sunset']
    phases = [p for p in phase_order if p in phase_counts]
    counts = [phase_counts[p] for p in phases]
    colors = [PHASE_COLORS.get(p, '#607d8b') for p in phases]
    
    # Русские названия
    phase_names = {
        'night': 'Ночь',
        'dawn': 'Рассвет', 
        'morning': 'Утро',
        'day': 'День',
        'evening': 'Вечер',
        'sunset': 'Закат'
    }
    labels = [phase_names.get(p, p) for p in phases]
    
    bars = ax.barh(labels, counts, color=colors, edgecolor='#0d1117', linewidth=2)
    
    # Добавляем значения на бары
    for bar, count in zip(bars, counts):
        width = bar.get_width()
        ax.text(width + max(counts)*0.02, bar.get_y() + bar.get_height()/2,
                f'{count}', ha='left', va='center', color='#f0f6fc', 
                fontsize=11, fontweight='bold')
    
    ax.set_xlabel('Количество записей', fontsize=12, color='#8b949e')
    ax.set_xlim(0, max(counts) * 1.15)
    ax.grid(True, axis='x', alpha=0.2, color='#30363d')
    
    plt.tight_layout()
    fig.savefig(output_dir / 'phase_distribution.png', dpi=150, facecolor='#0d1117',
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f'Сохранено: phase_distribution.png')


def plot_clouds_heatmap(entries: list[WeatherLogEntry], output_dir: Path):
    """Тепловая карта облачности по дням недели и часам."""
    fig, ax = plt.subplots(figsize=(12, 8))
    setup_figure_style(fig, ax, 'Облачность по часам и дням недели')
    
    # Создаём матрицу: часы (0-23) x дни недели (0-6)
    heatmap_data = np.full((7, 24), np.nan)
    counts = np.zeros((7, 24))
    
    for entry in entries:
        day = entry.timestamp.weekday()
        hour = entry.timestamp.hour
        if np.isnan(heatmap_data[day, hour]):
            heatmap_data[day, hour] = 0
        heatmap_data[day, hour] += entry.clouds_percent
        counts[day, hour] += 1
    
    # Среднее значение
    with np.errstate(divide='ignore', invalid='ignore'):
        heatmap_data = np.where(counts > 0, heatmap_data / counts, np.nan)
    
    im = ax.imshow(heatmap_data, cmap=CLOUDS_CMAP, aspect='auto', vmin=0, vmax=100)
    
    # Оси
    days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    hours = [f'{h:02d}:00' for h in range(24)]
    
    ax.set_yticks(range(7))
    ax.set_yticklabels(days)
    ax.set_xticks(range(24))
    ax.set_xticklabels(hours, rotation=45, ha='right')
    
    ax.set_xlabel('Час', fontsize=12, color='#8b949e')
    ax.set_ylabel('День недели', fontsize=12, color='#8b949e')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax, pad=0.02)
    cbar.set_label('Средняя облачность %', color='#8b949e')
    cbar.ax.tick_params(colors='#8b949e')
    
    plt.tight_layout()
    fig.savefig(output_dir / 'clouds_heatmap.png', dpi=150, facecolor='#0d1117',
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f'Сохранено: clouds_heatmap.png')


def plot_daily_summary(entries: list[WeatherLogEntry], output_dir: Path):
    """Сводный график по дням: средняя облачность + преобладающая погода."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), 
                                    gridspec_kw={'height_ratios': [2, 1]})
    fig.patch.set_facecolor('#0d1117')
    
    # Группируем по дням
    daily_data = {}
    for entry in entries:
        date = entry.timestamp.date()
        if date not in daily_data:
            daily_data[date] = {'clouds': [], 'weather': []}
        daily_data[date]['clouds'].append(entry.clouds_percent)
        daily_data[date]['weather'].append(entry.base)
    
    dates = sorted(daily_data.keys())
    avg_clouds = [np.mean(daily_data[d]['clouds']) for d in dates]
    min_clouds = [np.min(daily_data[d]['clouds']) for d in dates]
    max_clouds = [np.max(daily_data[d]['clouds']) for d in dates]
    
    # Преобладающая погода за день
    dominant_weather = [Counter(daily_data[d]['weather']).most_common(1)[0][0] for d in dates]
    weather_colors = [WEATHER_COLORS.get(w, '#607d8b') for w in dominant_weather]
    
    # График 1: Облачность
    ax1.set_facecolor('#161b22')
    ax1.fill_between(dates, min_clouds, max_clouds, alpha=0.2, color='#4fc3f7', 
                     label='Диапазон')
    ax1.plot(dates, avg_clouds, color='#4fc3f7', linewidth=2, marker='o', 
             markersize=4, label='Средняя')
    
    ax1.set_ylabel('Облачность (%)', fontsize=12, color='#8b949e')
    ax1.set_ylim(0, 105)
    ax1.legend(loc='upper right', facecolor='#161b22', edgecolor='#30363d', 
               labelcolor='#8b949e')
    ax1.set_title('Ежедневная сводка', fontsize=16, fontweight='bold', 
                  color='#f0f6fc', pad=15)
    ax1.tick_params(colors='#8b949e')
    ax1.grid(True, alpha=0.2, color='#30363d')
    for spine in ax1.spines.values():
        spine.set_color('#30363d')
    
    # График 2: Преобладающая погода
    ax2.set_facecolor('#161b22')
    ax2.bar(dates, [1]*len(dates), color=weather_colors, edgecolor='#0d1117', linewidth=1)
    
    ax2.set_xlabel('Дата', fontsize=12, color='#8b949e')
    ax2.set_ylabel('Преобладающая\nпогода', fontsize=10, color='#8b949e')
    ax2.set_yticks([])
    ax2.tick_params(colors='#8b949e')
    for spine in ax2.spines.values():
        spine.set_color('#30363d')
    
    # Легенда для погоды
    unique_weather = list(set(dominant_weather))
    legend_patches = [plt.Rectangle((0, 0), 1, 1, facecolor=WEATHER_COLORS.get(w, '#607d8b')) 
                      for w in unique_weather]
    ax2.legend(legend_patches, [w.capitalize() for w in unique_weather], 
               loc='upper right', facecolor='#161b22', edgecolor='#30363d',
               labelcolor='#8b949e', ncol=len(unique_weather))
    
    # Форматирование дат
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
    ax2.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    fig.autofmt_xdate()
    
    plt.tight_layout()
    fig.savefig(output_dir / 'daily_summary.png', dpi=150, facecolor='#0d1117',
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f'Сохранено: daily_summary.png')


def plot_weather_by_phase(entries: list[WeatherLogEntry], output_dir: Path):
    """Stacked bar chart: погода в разрезе фаз дня."""
    fig, ax = plt.subplots(figsize=(12, 7))
    setup_figure_style(fig, ax, 'Погода по фазам дня')
    
    # Сортировка фаз по хронологии
    phase_order = ['night', 'dawn', 'morning', 'day', 'evening', 'sunset']
    
    # Собираем данные
    phase_weather = {}
    all_weathers = set()
    
    for entry in entries:
        if entry.phase not in phase_weather:
            phase_weather[entry.phase] = Counter()
        phase_weather[entry.phase][entry.base] += 1
        all_weathers.add(entry.base)
    
    phases = [p for p in phase_order if p in phase_weather]
    weather_types = sorted(all_weathers)
    
    # Русские названия фаз
    phase_names = {
        'night': 'Ночь', 'dawn': 'Рассвет', 'morning': 'Утро',
        'day': 'День', 'evening': 'Вечер', 'sunset': 'Закат'
    }
    
    x = np.arange(len(phases))
    width = 0.7
    bottom = np.zeros(len(phases))
    
    for weather in weather_types:
        values = [phase_weather[p].get(weather, 0) for p in phases]
        color = WEATHER_COLORS.get(weather, '#607d8b')
        ax.bar(x, values, width, label=weather.capitalize(), bottom=bottom, 
               color=color, edgecolor='#0d1117', linewidth=1)
        bottom += values
    
    ax.set_xticks(x)
    ax.set_xticklabels([phase_names.get(p, p) for p in phases])
    ax.set_xlabel('Фаза дня', fontsize=12, color='#8b949e')
    ax.set_ylabel('Количество записей', fontsize=12, color='#8b949e')
    ax.legend(loc='upper right', facecolor='#161b22', edgecolor='#30363d',
              labelcolor='#8b949e')
    ax.grid(True, axis='y', alpha=0.2, color='#30363d')
    
    plt.tight_layout()
    fig.savefig(output_dir / 'weather_by_phase.png', dpi=150, facecolor='#0d1117',
                edgecolor='none', bbox_inches='tight')
    plt.close(fig)
    print(f'Сохранено: weather_by_phase.png')


def main():
    """Главная функция."""
    # Пути
    base_dir = Path(__file__).parent.parent
    log_path = base_dir / 'logs' / 'weather.log'
    output_dir = base_dir / 'graphs'
    
    # Создаём папку для графиков
    output_dir.mkdir(exist_ok=True)
    
    print(f'Анализ файла: {log_path}')
    print(f'Графики сохраняются в: {output_dir}\n')
    
    # Парсим лог
    entries = parse_log_file(log_path)
    
    if not entries:
        print('Не найдено записей в логе!')
        return
    
    print(f'Найдено {len(entries)} записей')
    print(f'Период: {entries[0].timestamp.date()} — {entries[-1].timestamp.date()}\n')
    
    # Генерируем графики
    print('Генерация графиков...\n')
    
    plot_clouds_timeline(entries, output_dir)
    plot_weather_distribution(entries, output_dir)
    plot_phase_distribution(entries, output_dir)
    plot_clouds_heatmap(entries, output_dir)
    plot_daily_summary(entries, output_dir)
    plot_weather_by_phase(entries, output_dir)

    df = entries_to_df(entries)
    obs, p = permutation_test_mean_diff(df, "phase", "clouds", a="night", b="day", n_perm=5000, seed=7)
    print("\nH0: mean_clouds(night) <= mean_clouds(day)")
    print("H1: mean_clouds(night) >  mean_clouds(day)")
    print(f"obs_diff = {obs:.3f}")
    print(f"p_value  = {p:.5f}")
    
    print(f'\nГотово! Все графики сохранены в {output_dir}')


if __name__ == '__main__':
    main()


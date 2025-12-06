"""Конфигурация приложения"""
from pathlib import Path
from dataclasses import dataclass


# Базовый путь к проекту
BASE_DIR = Path(__file__).parent.parent
UI_DIR = BASE_DIR / "UI"


@dataclass
class UIConfig:
    """Конфигурация UI элементов"""
    # Пути к изображениям
    aphex_image: Path = UI_DIR / "aphex.png"
    close_button: Path = UI_DIR / "close.png"
    minimize_button: Path = UI_DIR / "minimize.png"
    play_button: Path = UI_DIR / "play.png"
    pause_button: Path = UI_DIR / "pause.png"
    stop_button: Path = UI_DIR / "stop.png"
    progress_bar_empty: Path = UI_DIR / "progress_bar_empty.png"
    progress_bar_filled: Path = UI_DIR / "progress_bar_filled.png"
    progress_button: Path = UI_DIR / "button_prog.png"
    
    # Координаты кнопок управления окном (относительно aphex.png)
    window_buttons_y: int = 15
    close_button_x: int = 395
    window_buttons_spacing: int = 5
    
    # Координаты кнопок управления воспроизведением
    play_pause_x: int = 365
    play_pause_y: int = 75
    control_buttons_gap: int = 10
    
    # Координаты прогресс-бара
    progress_bar_x: int = 278
    progress_bar_y: int = 560
    time_label_gap: int = 10  # Отступ таймера от прогресс-бара
    time_font_size: int = 20  # Размер шрифта при 100%
    time_text_color: str = "#d7a910"  # Цвет текста времени
    
    # Область аудиовизуализатора (px относительно оригинальной aphex.png)
    viz_x: int = 197
    viz_y: int = 175
    viz_width: int = 458   # 655 - 197
    viz_height: int = 337  # 512 - 175
    viz_background: str = "#000000"
    viz_color: str = "#d7a910"  # базовый цвет полос/колец
    viz_bar_count: int = 64  # число столбиков в спектре
    viz_fft_window_ms: int = 80  # длина окна для FFT
    viz_wave_downsample: int = 1024  # длина волновой формы после даунсэмплинга
    viz_spec_smooth_alpha: float = 0.65  # сглаживание спектра (0..1, ближе к 1 — быстрее)
    viz_wave_smooth_alpha: float = 0.5   # сглаживание волновой формы
    viz_autogain_decay: float = 0.995    # эксп. затухание автогейна (0..1)
    viz_db_floor: float = -60.0          # минимальный dB уровень для баров


# Глобальный объект конфигурации
config = UIConfig()


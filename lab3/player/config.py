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
    
    # Координаты кнопок управления окном (относительно aphex.png)
    window_buttons_y: int = 15
    close_button_x: int = 400
    window_buttons_spacing: int = 5
    
    # Координаты кнопок управления воспроизведением
    play_pause_x: int = 362
    play_pause_y: int = 75
    control_buttons_gap: int = 10


# Глобальный объект конфигурации
config = UIConfig()


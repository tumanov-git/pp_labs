"""Конфигурация приложения"""
import os
from pathlib import Path

# Базовый путь к проекту
BASE_DIR = Path(__file__).parent.parent

# Пути к UI файлам
UI_DIR = BASE_DIR / "UI"
APHEX_IMAGE = UI_DIR / "aphex.png"
CLOSE_BUTTON = UI_DIR / "close.png"
MINIMIZE_BUTTON = UI_DIR / "minimize.png"

# Координаты кнопок (относительно изображения aphex.png)
BUTTONS_Y = 15
CLOSE_BUTTON_X = 400
BUTTON_SPACING = 5  # Расстояние между кнопками


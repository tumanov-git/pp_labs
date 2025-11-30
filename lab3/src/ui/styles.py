"""
Стили и константы для UI в стиле Windows XP
"""

from PyQt5.QtGui import QColor, QLinearGradient


# Цвета для шапки окна
class TitleBarColors:
    """Цвета для кастомной шапки"""
    
    # Градиент шапки (из HTML)
    GRADIENT_STOPS = [
        (0.07, QColor(61, 149, 255)),   # #3D95FF
        (0.10, QColor(3, 114, 255)),    # #0372FF
        (0.14, QColor(3, 101, 241)),    # #0365F1
        (0.26, QColor(0, 83, 225)),     # #0053E1
        (0.56, QColor(0, 88, 238)),     # #0058EE
        (0.74, QColor(2, 106, 254)),    # #026AFE
        (0.85, QColor(2, 106, 254)),    # #026AFE
        (0.91, QColor(0, 96, 252)),     # #0060FC
        (0.96, QColor(0, 67, 207)),     # #0043CF
    ]
    
    # Рамка
    BORDER_COLOR = QColor(0, 32, 200)  # #0020C8
    BORDER_COLOR_ALT = QColor(0, 89, 232)  # #0059E8
    
    # Текст
    TEXT_COLOR = QColor(255, 255, 255)  # white
    TEXT_SHADOW = QColor(0, 0, 0, 128)  # rgba(0, 0, 0, 0.5)


# Высота шапки
TITLE_BAR_HEIGHT = 29


def get_title_bar_gradient(height):
    """
    Создает градиент для шапки окна
    
    Args:
        height: Высота шапки
        
    Returns:
        QLinearGradient: Градиент для отрисовки
    """
    gradient = QLinearGradient(0, 0, 0, height)
    
    for stop, color in TitleBarColors.GRADIENT_STOPS:
        gradient.setColorAt(stop, color)
    
    return gradient


# Стили для кнопок шапки
BUTTON_STYLES = {
    'help': """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #245FF5, stop:0.33 #245FF5, stop:0.66 #256BF8, stop:1 #256BF8);
            border: 1px solid rgba(0, 20, 200, 0.5);
            border-radius: 2px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #2D6AFF, stop:0.33 #2D6AFF, stop:0.66 #2E76FF, stop:1 #2E76FF);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #1D4FE5, stop:0.33 #1D4FE5, stop:0.66 #1E5BE8, stop:1 #1E5BE8);
        }
    """,
    'close': """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #E46446, stop:1 #E65D32);
            border: 1px solid rgba(228, 95, 62, 0.5);
            border-radius: 2px;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #F47456, stop:1 #F46D42);
        }
        QPushButton:pressed {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 #D45436, stop:1 #D44D22);
        }
    """
}


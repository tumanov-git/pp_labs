"""
Кастомная шапка окна в стиле Windows XP
"""

import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QPainter, QColor, QIcon
from .styles import (
    get_title_bar_gradient,
    TitleBarColors,
    TITLE_BAR_HEIGHT,
    BUTTON_STYLES
)


class TitleBar(QWidget):
    """Кастомная шапка окна в стиле Windows XP"""

    def __init__(self, parent=None, title="Аудиоплеер"):
        super().__init__(parent)
        self.parent_window = parent
        self.title_text = title
        self.setFixedHeight(TITLE_BAR_HEIGHT)
        self.setMinimumWidth(200)
        self.drag_position = QPoint()

        # Layout для шапки
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(4)

        # Заголовок
        self.title_label = QLabel(self.title_text)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 13px;
                font-weight: 700;
                font-family: Arial, sans-serif;
                background: transparent;
            }
        """)
        layout.addWidget(self.title_label)
        layout.addStretch()

        # Кнопка справки
        self.help_button = QPushButton()
        self.help_button.setFixedSize(21, 21)
        self.help_button.setStyleSheet(BUTTON_STYLES['help'])
        self.help_button.setIconSize(QSize(16, 16))
        self.help_button.clicked.connect(self.show_help)
        layout.addWidget(self.help_button)

        # Кнопка закрытия
        self.close_button = QPushButton()
        self.close_button.setFixedSize(21, 21)
        self.close_button.setStyleSheet(BUTTON_STYLES['close'])
        self.close_button.setIconSize(QSize(16, 16))
        self.close_button.clicked.connect(self.close_window)
        layout.addWidget(self.close_button)

        self.setLayout(layout)
        
        # Загрузка иконок
        self.load_icons()

    def load_icons(self):
        """Загрузка SVG иконок для кнопок"""
        try:
            # Путь к иконкам относительно корня проекта
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            help_icon_path = os.path.join(base_path, 'assets', 'icons', 'Help.svg')
            close_icon_path = os.path.join(base_path, 'assets', 'icons', 'Close.svg')
            
            if os.path.exists(help_icon_path):
                self.help_button.setIcon(QIcon(help_icon_path))
            
            if os.path.exists(close_icon_path):
                self.close_button.setIcon(QIcon(close_icon_path))
        except Exception as e:
            # Если иконки не загрузились, кнопки будут без иконок
            print(f"Не удалось загрузить иконки: {e}")

    def paintEvent(self, event):
        """Отрисовка градиентного фона шапки"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Основной градиент
        gradient = get_title_bar_gradient(self.height())
        painter.fillRect(self.rect(), gradient)

        # Рамка
        painter.setPen(TitleBarColors.BORDER_COLOR)
        # Верхняя и нижняя линии
        painter.drawLine(0, 0, self.width(), 0)
        painter.drawLine(0, self.height() - 1, self.width(), self.height() - 1)
        # Боковые линии
        painter.drawLine(0, 0, 0, self.height())
        painter.drawLine(self.width() - 1, 0, self.width() - 1, self.height())

    def mousePressEvent(self, event):
        """Обработка нажатия мыши для перетаскивания окна"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Обработка перемещения мыши для перетаскивания окна"""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.parent_window.move(event.globalPos() - self.drag_position)
            event.accept()

    def show_help(self):
        """Показ справки"""
        if self.parent_window:
            self.parent_window.show_about()

    def close_window(self):
        """Закрытие окна"""
        if self.parent_window:
            self.parent_window.close()

    def set_title(self, title):
        """Установка заголовка"""
        self.title_text = title
        self.title_label.setText(title)


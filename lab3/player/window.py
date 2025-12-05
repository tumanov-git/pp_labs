"""Главное окно приложения"""
from PyQt6.QtWidgets import QWidget, QLabel, QMenu
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QMouseEvent, QCursor, QAction
from .config import APHEX_IMAGE, CLOSE_BUTTON, MINIMIZE_BUTTON, CLOSE_BUTTON_X, BUTTONS_Y, BUTTON_SPACING


class CustomButton(QLabel):
    """Кастомная кнопка из PNG изображения"""
    
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        if pixmap.isNull():
            raise ValueError("Передан пустой pixmap")
        self.setPixmap(pixmap)
        self.setFixedSize(pixmap.size())
        self.setScaledContents(False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # Устанавливаем курсор-указатель при наведении
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
    def mousePressEvent(self, event: QMouseEvent):
        """Обработка нажатия на кнопку"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent().button_clicked(self)


class MainWindow(QWidget):
    """Главное окно с прозрачным фоном и изображением Aphex Twin"""
    
    def __init__(self):
        super().__init__()
        # Исходные размеры изображения
        self.original_aphex_pixmap = None
        self.original_close_pixmap = None
        self.original_minimize_pixmap = None
        # Текущий масштаб (в процентах)
        self.scale = 100
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        # Загружаем исходные изображения
        self.original_aphex_pixmap = QPixmap(str(APHEX_IMAGE))
        if self.original_aphex_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {APHEX_IMAGE}")
        
        self.original_close_pixmap = QPixmap(str(CLOSE_BUTTON))
        if self.original_close_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {CLOSE_BUTTON}")
            
        self.original_minimize_pixmap = QPixmap(str(MINIMIZE_BUTTON))
        if self.original_minimize_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {MINIMIZE_BUTTON}")
        
        # Убираем стандартный интерфейс окна (frameless)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Делаем окно прозрачным
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Создаем фон с изображением Aphex Twin
        self.background_label = QLabel(self)
        self.background_label.setScaledContents(False)
        
        # Создаем кнопки (будут пересозданы при масштабировании)
        self.close_button = None
        self.minimize_button = None
        
        # Включаем отслеживание мыши для перетаскивания окна
        self.setMouseTracking(True)
        self.drag_position = QPoint()
        
        # Применяем начальный масштаб
        self.apply_scale(100)
        
    def button_clicked(self, button):
        """Обработка нажатия на кнопку"""
        if button == self.close_button:
            self.close()
        elif button == self.minimize_button:
            self.showMinimized()
            
    def mousePressEvent(self, event: QMouseEvent):
        """Обработка нажатия мыши для перетаскивания окна и контекстного меню"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            # Показываем контекстное меню с масштабированием
            self.show_context_menu(event.globalPosition().toPoint())
            event.accept()
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """Обработка движения мыши для перетаскивания окна"""
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            
    def apply_scale(self, scale_percent: int):
        """Применение масштаба к окну и элементам"""
        self.scale = scale_percent
        scale_factor = scale_percent / 100.0
        
        # Масштабируем изображение Aphex Twin
        scaled_width = int(self.original_aphex_pixmap.width() * scale_factor)
        scaled_height = int(self.original_aphex_pixmap.height() * scale_factor)
        scaled_aphex = self.original_aphex_pixmap.scaled(
            scaled_width, scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Устанавливаем размер окна
        self.setFixedSize(scaled_width, scaled_height)
        
        # Обновляем фон
        self.background_label.setPixmap(scaled_aphex)
        self.background_label.setGeometry(0, 0, scaled_width, scaled_height)
        
        # Масштабируем кнопки
        scaled_close = self.original_close_pixmap.scaled(
            int(self.original_close_pixmap.width() * scale_factor),
            int(self.original_close_pixmap.height() * scale_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        scaled_minimize = self.original_minimize_pixmap.scaled(
            int(self.original_minimize_pixmap.width() * scale_factor),
            int(self.original_minimize_pixmap.height() * scale_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Обновляем существующие кнопки или создаем новые, если их нет
        if self.close_button:
            self.close_button.setPixmap(scaled_close)
            self.close_button.setFixedSize(scaled_close.size())
        else:
            self.close_button = CustomButton(scaled_close, self)
            
        if self.minimize_button:
            self.minimize_button.setPixmap(scaled_minimize)
            self.minimize_button.setFixedSize(scaled_minimize.size())
        else:
            self.minimize_button = CustomButton(scaled_minimize, self)
        
        # Пересчитываем позиции кнопок с учетом масштаба
        scaled_close_x = int(CLOSE_BUTTON_X * scale_factor)
        scaled_close_y = int(BUTTONS_Y * scale_factor)
        scaled_spacing = int(BUTTON_SPACING * scale_factor)
        
        self.close_button.move(scaled_close_x, scaled_close_y)
        self.minimize_button.move(
            scaled_close_x + scaled_close.width() + scaled_spacing,
            scaled_close_y
        )
        
        # Показываем кнопки, если они были скрыты
        self.close_button.show()
        self.minimize_button.show()
        
    def show_context_menu(self, position):
        """Показать контекстное меню с опциями масштабирования"""
        menu = QMenu(self)
        
        scale_options = [10, 25, 50, 75, 100, 150, 200]
        
        for scale_value in scale_options:
            action = QAction(f"{scale_value}%", self)
            action.setCheckable(True)
            action.setChecked(scale_value == self.scale)
            action.triggered.connect(lambda checked, s=scale_value: self.apply_scale(s))
            menu.addAction(action)
        
        menu.exec(position)
        
    def paintEvent(self, event):
        """Перерисовка окна"""
        super().paintEvent(event)


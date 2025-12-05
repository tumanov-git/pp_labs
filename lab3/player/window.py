"""Главное окно приложения"""
from PyQt6.QtWidgets import QWidget, QLabel, QMenu, QFileDialog
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QMouseEvent, QCursor, QAction
from .config import config
from .audio_player import AudioPlayer


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
            event.accept()  # Предотвращаем распространение события
            self.parent().button_clicked(self)


class MainWindow(QWidget):
    """Главное окно с прозрачным фоном и изображением Aphex Twin"""
    
    def __init__(self):
        super().__init__()
        # Исходные размеры изображения
        self.original_aphex_pixmap = None
        self.original_close_pixmap = None
        self.original_minimize_pixmap = None
        self.original_play_pixmap = None
        self.original_pause_pixmap = None
        self.original_stop_pixmap = None
        # Текущий масштаб (в процентах)
        self.scale = 100
        # Аудиоплеер
        self.audio_player = AudioPlayer()
        # Подключаем сигналы для автоматического обновления состояния
        self.audio_player.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        # Состояние воспроизведения (True = играет, False = на паузе/остановлено)
        self.is_playing = False
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        # Загружаем исходные изображения
        self.original_aphex_pixmap = QPixmap(str(config.aphex_image))
        if self.original_aphex_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {config.aphex_image}")
        
        self.original_close_pixmap = QPixmap(str(config.close_button))
        if self.original_close_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {config.close_button}")
            
        self.original_minimize_pixmap = QPixmap(str(config.minimize_button))
        if self.original_minimize_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {config.minimize_button}")
        
        self.original_play_pixmap = QPixmap(str(config.play_button))
        if self.original_play_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {config.play_button}")
            
        self.original_pause_pixmap = QPixmap(str(config.pause_button))
        if self.original_pause_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {config.pause_button}")
            
        self.original_stop_pixmap = QPixmap(str(config.stop_button))
        if self.original_stop_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {config.stop_button}")
        
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
        self.play_pause_button = None
        self.stop_button = None
        
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
        elif button == self.play_pause_button:
            self.toggle_play_pause()
        elif button == self.stop_button:
            self.stop_playback()
    
    def toggle_play_pause(self):
        """Переключение между воспроизведением и паузой"""
        if not self.audio_player.current_file:
            # Если файл не загружен, открываем диалог выбора файла
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Выберите аудиофайл",
                "",
                "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a *.aac);;All Files (*)"
            )
            if file_path:
                try:
                    self.audio_player.load_file(file_path)
                    self.audio_player.play()
                    self.is_playing = True
                    self.update_play_pause_button()
                except Exception as e:
                    print(f"Ошибка загрузки файла: {e}")
            return
        
        if self.is_playing:
            self.audio_player.pause()
            self.is_playing = False
        else:
            self.audio_player.play()
            self.is_playing = True
        self.update_play_pause_button()
    
    def stop_playback(self):
        """Остановка воспроизведения"""
        self.audio_player.stop()
        self.is_playing = False
        self.update_play_pause_button()
    
    def on_playback_state_changed(self, state):
        """Обработка изменения состояния воспроизведения"""
        from PyQt6.QtMultimedia import QMediaPlayer
        self.is_playing = (state == QMediaPlayer.PlaybackState.PlayingState)
        self.update_play_pause_button()
    
    def update_play_pause_button(self):
        """Обновление внешнего вида кнопки play/pause в зависимости от состояния"""
        if not self.play_pause_button:
            return
        
        scale_factor = self.scale / 100.0
        if self.is_playing:
            # Показываем pause
            scaled_pause = self.original_pause_pixmap.scaled(
                int(self.original_pause_pixmap.width() * scale_factor),
                int(self.original_pause_pixmap.height() * scale_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.play_pause_button.setPixmap(scaled_pause)
            self.play_pause_button.setFixedSize(scaled_pause.size())
        else:
            # Показываем play
            scaled_play = self.original_play_pixmap.scaled(
                int(self.original_play_pixmap.width() * scale_factor),
                int(self.original_play_pixmap.height() * scale_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.play_pause_button.setPixmap(scaled_play)
            self.play_pause_button.setFixedSize(scaled_play.size())
        
        # Обновляем позицию stop кнопки после изменения размера play/pause
        self.update_stop_button_position()
    
    def update_stop_button_position(self):
        """Обновление позиции кнопки stop относительно play/pause"""
        if not self.play_pause_button or not self.stop_button:
            return
        
        scale_factor = self.scale / 100.0
        scaled_play_pause_x = int(config.play_pause_x * scale_factor)
        scaled_play_pause_y = int(config.play_pause_y * scale_factor)
        scaled_control_gap = int(config.control_buttons_gap * scale_factor)
        
        play_pause_width = self.play_pause_button.width()
        stop_x = scaled_play_pause_x + play_pause_width + scaled_control_gap
        self.stop_button.move(stop_x, scaled_play_pause_y)
            
    def mousePressEvent(self, event: QMouseEvent):
        """Обработка нажатия мыши для перетаскивания окна и контекстного меню"""
        # Проверяем, не нажали ли мы на кнопку или её дочерний элемент
        click_pos = event.position().toPoint()
        child = self.childAt(click_pos)
        
        # Проверяем, является ли клик по кнопке (включая дочерние элементы)
        if child:
            # Поднимаемся по иерархии виджетов, чтобы найти кнопку
            widget = child
            while widget and widget != self:
                if isinstance(widget, CustomButton):
                    # Если клик по кнопке, не обрабатываем перетаскивание
                    return
                widget = widget.parent()
        
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
        scaled_close_x = int(config.close_button_x * scale_factor)
        scaled_close_y = int(config.window_buttons_y * scale_factor)
        scaled_spacing = int(config.window_buttons_spacing * scale_factor)
        
        self.close_button.move(scaled_close_x, scaled_close_y)
        self.minimize_button.move(
            scaled_close_x + scaled_close.width() + scaled_spacing,
            scaled_close_y
        )
        
        # Масштабируем кнопки управления воспроизведением
        scaled_play = self.original_play_pixmap.scaled(
            int(self.original_play_pixmap.width() * scale_factor),
            int(self.original_play_pixmap.height() * scale_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        scaled_pause = self.original_pause_pixmap.scaled(
            int(self.original_pause_pixmap.width() * scale_factor),
            int(self.original_pause_pixmap.height() * scale_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        scaled_stop = self.original_stop_pixmap.scaled(
            int(self.original_stop_pixmap.width() * scale_factor),
            int(self.original_stop_pixmap.height() * scale_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Обновляем или создаем кнопку play/pause
        if self.play_pause_button:
            # Обновляем в зависимости от состояния
            if self.is_playing:
                self.play_pause_button.setPixmap(scaled_pause)
                self.play_pause_button.setFixedSize(scaled_pause.size())
            else:
                self.play_pause_button.setPixmap(scaled_play)
                self.play_pause_button.setFixedSize(scaled_play.size())
        else:
            # Создаем новую кнопку (по умолчанию play)
            self.play_pause_button = CustomButton(scaled_play, self)
        
        # Обновляем или создаем кнопку stop
        if self.stop_button:
            self.stop_button.setPixmap(scaled_stop)
            self.stop_button.setFixedSize(scaled_stop.size())
        else:
            self.stop_button = CustomButton(scaled_stop, self)
        
        # Пересчитываем позиции кнопок управления с учетом масштаба
        scaled_play_pause_x = int(config.play_pause_x * scale_factor)
        scaled_play_pause_y = int(config.play_pause_y * scale_factor)
        scaled_control_gap = int(config.control_buttons_gap * scale_factor)
        
        self.play_pause_button.move(scaled_play_pause_x, scaled_play_pause_y)
        
        # Обновляем позицию stop кнопки относительно play/pause
        self.update_stop_button_position()
        
        # Показываем кнопки, если они были скрыты
        self.close_button.show()
        self.minimize_button.show()
        self.play_pause_button.show()
        self.stop_button.show()
        
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


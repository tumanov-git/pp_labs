"""Главное окно приложения"""
from PyQt6.QtWidgets import QWidget, QLabel, QMenu, QFileDialog, QMenuBar, QApplication
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QPainter, QMouseEvent, QCursor, QAction, QFont, QPalette
from .config import config
from .audio_player import AudioPlayer
from .viz import VisualizerWidget, decode_file_to_mono
import numpy as np


class CustomButton(QLabel):
    """Кастомная кнопка из PNG изображения"""
    
    clicked = pyqtSignal()  # Сигнал нажатия
    
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
            event.accept()
            self.clicked.emit()


class ProgressButton(QLabel):
    """Кнопка ползунка прогресс-бара с поддержкой перетаскивания."""
    
    drag_started = pyqtSignal()
    drag_moved = pyqtSignal(QPoint)  # Передаём глобальную позицию мыши
    drag_finished = pyqtSignal(QPoint)
    
    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.setPixmap(pixmap)
        self.setFixedSize(pixmap.size())
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._dragging = False
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging = True
            self.drag_started.emit()
            event.accept()
    
    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging:
            self.drag_moved.emit(event.globalPosition().toPoint())
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and self._dragging:
            self._dragging = False
            self.drag_finished.emit(event.globalPosition().toPoint())
            event.accept()


class MarqueeLabel(QLabel):
    """Метка с бегущей строкой, если текст не помещается."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = ""
        self._offset = 0
        self._speed_px = 2
        self._interval_ms = 50
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_marquee_params(self, speed_px: int, interval_ms: int):
        self._speed_px = max(1, speed_px)
        self._interval_ms = max(10, interval_ms)
        self._timer.setInterval(self._interval_ms)

    def set_paused(self, paused: bool):
        """
        Управляет анимацией бегущей строки.
        При паузе останавливаем таймер, при возобновлении — запускаем,
        если текст длиннее области.
        """
        if paused:
            if self._timer.isActive():
                self._timer.stop()
        else:
            if self._need_scroll() and not self._timer.isActive():
                self._timer.start(self._interval_ms)

    def set_text(self, text: str):
        new_text = text or ""
        # Сбрасываем offset только если текст изменился
        if new_text != self._text:
            self._text = new_text
            self._offset = 0
            if self._need_scroll():
                if not self._timer.isActive():
                    self._timer.start(self._interval_ms)
            else:
                self._timer.stop()
            self.update()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Проверяем, нужно ли прокручивать после изменения размера
        if self._need_scroll():
            if not self._timer.isActive():
                self._timer.start(self._interval_ms)
        else:
            self._timer.stop()
            self._offset = 0

    def _need_scroll(self) -> bool:
        fm = self.fontMetrics()
        return fm.horizontalAdvance(self._text) > self.width()

    def _tick(self):
        if not self._need_scroll():
            self._timer.stop()
            self._offset = 0
            return
        step = self._speed_px
        fm = self.fontMetrics()
        unit = fm.horizontalAdvance(self._text + "   ")
        if unit <= 0:
            return
        self._offset = (self._offset + step) % unit
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        color = self.palette().color(QPalette.ColorRole.WindowText)
        painter.setPen(color)
        fm = painter.fontMetrics()
        rect = self.rect()
        baseline = rect.y() + (rect.height() + fm.ascent() - fm.descent()) // 2

        if not self._need_scroll():
            text_width = fm.horizontalAdvance(self._text)
            x = rect.x() + (rect.width() - text_width) // 2
            painter.drawText(x, baseline, self._text)
            painter.end()
            return

        text_unit = self._text + "   "
        unit_w = fm.horizontalAdvance(text_unit)
        x = -self._offset
        # Дублируем текст, чтобы заполнить весь прямоугольник
        while x < rect.width():
            painter.drawText(rect.x() + x, baseline, text_unit)
            x += unit_w
        painter.end()


class MainWindow(QWidget):
    """Главное окно с прозрачным фоном и изображением Aphex Twin"""
    
    def __init__(self):
        super().__init__()
        # Применяем глобальный шрифт приложения сразу ко всему окну
        self.setFont(QApplication.font())
        # Исходные размеры изображения
        self.original_aphex_pixmap = None
        self.original_close_pixmap = None
        self.original_minimize_pixmap = None
        self.original_play_pixmap = None
        self.original_pause_pixmap = None
        self.original_stop_pixmap = None
        self.original_progress_empty_pixmap = None
        self.original_progress_filled_pixmap = None
        self.original_progress_button_pixmap = None
        self.original_file_button_pixmap = None
        self.original_viz_wave_active = None
        self.original_viz_wave_inactive = None
        self.original_viz_2d_active = None
        self.original_viz_2d_inactive = None
        self.original_viz_3d_active = None
        self.original_viz_3d_inactive = None
        # Текущий масштаб (в процентах)
        self.scale = 50
        # Флаг перетаскивания ползунка прогресс-бара
        self.is_dragging_progress = False
        # Флаг перетаскивания окна
        self.is_dragging_window = False
        # Аудиоплеер
        self.audio_player = AudioPlayer()
        # Подключаем сигналы для автоматического обновления состояния
        self.audio_player.media_player.playbackStateChanged.connect(self.on_playback_state_changed)
        # Состояние воспроизведения (True = играет, False = на паузе/остановлено)
        self.is_playing = False
        # Виджет аудиовизуализатора
        self.visualizer: VisualizerWidget | None = None
        # Текущий режим визуализатора
        self.viz_mode = "wave"
        # Кнопки режимов
        self.viz_mode_buttons = {}
        # Кнопка выбора файла
        self.file_button = None
        # Буфер для визуализации
        self._viz_audio: np.ndarray | None = None
        self._viz_samplerate: int = 0
        self._viz_timer = QTimer(self)
        self._viz_timer.timeout.connect(self.update_visualizer_frame)
        self._viz_timer.start(33)  # ~30 FPS
        self.init_ui()
        
    def init_ui(self):
        """Инициализация интерфейса"""
        # Разрешаем обработку горячих клавиш
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
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
        
        self.original_progress_empty_pixmap = QPixmap(str(config.progress_bar_empty))
        if self.original_progress_empty_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {config.progress_bar_empty}")
            
        self.original_progress_filled_pixmap = QPixmap(str(config.progress_bar_filled))
        if self.original_progress_filled_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {config.progress_bar_filled}")
            
        self.original_progress_button_pixmap = QPixmap(str(config.progress_button))
        if self.original_progress_button_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {config.progress_button}")
        # Кнопка выбора файла
        self.original_file_button_pixmap = QPixmap(str(config.file_button))
        if self.original_file_button_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {config.file_button}")
        # Кнопки режимов визуализатора
        self.original_viz_wave_active = QPixmap(str(config.viz_button_wave_active))
        self.original_viz_wave_inactive = QPixmap(str(config.viz_button_wave_inactive))
        self.original_viz_2d_active = QPixmap(str(config.viz_button_2d_active))
        self.original_viz_2d_inactive = QPixmap(str(config.viz_button_2d_inactive))
        self.original_viz_3d_active = QPixmap(str(config.viz_button_3d_active))
        self.original_viz_3d_inactive = QPixmap(str(config.viz_button_3d_inactive))
        if any(p.isNull() for p in [
            self.original_viz_wave_active,
            self.original_viz_wave_inactive,
            self.original_viz_2d_active,
            self.original_viz_2d_inactive,
            self.original_viz_3d_active,
            self.original_viz_3d_inactive,
        ]):
            raise FileNotFoundError("Не удалось загрузить изображения кнопок режимов визуализатора")
        
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
        
        # Создаем элементы прогресс-бара
        self.progress_empty = None
        self.progress_filled = None
        self.progress_button = None
        self.time_label = None
        # Строка состояния
        self.status_label: MarqueeLabel | None = None
        self.status_text: str = "Файл не загружен"
        
        # Таймер для обновления прогресс-бара
        self.progress_timer = QTimer(self)
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(100)  # Обновление каждые 100мс
        
        # Создаем менюбар
        self.create_menu_bar()
        
        # Включаем отслеживание мыши для перетаскивания окна
        self.setMouseTracking(True)
        self.drag_position = QPoint()
        
        # Применяем начальный масштаб
        self.apply_scale(50)
    
    def create_menu_bar(self):
        """Создание меню приложения (только для macOS)"""
        self.menu_bar = QMenuBar(self)
        self.menu_bar.setFont(self._app_font(config.ui_font_size))
        
        # На Windows/Linux прячем меню (будет контекстным по ПКМ), на Mac оно нативное
        import sys
        if sys.platform != 'darwin':
            # На Windows/Linux меню не будет видимым, только для контекстного меню
            self.menu_bar.hide()
        else:
            # На macOS показываем нативное меню в системной строке
            self.menu_bar.show()
        
        # === МЕНЮ "ФАЙЛ" ===
        file_menu = self.menu_bar.addMenu("Файл")
        
        open_action = QAction("Открыть...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(lambda: self.select_and_load_file(auto_play=False))
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction("Выход", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # === МЕНЮ "ВОСПРОИЗВЕДЕНИЕ" ===
        playback_menu = self.menu_bar.addMenu("Воспроизведение")
        
        play_pause_action = QAction("Play/Pause", self)
        play_pause_action.setShortcut("Space")
        play_pause_action.triggered.connect(self.toggle_play_pause)
        playback_menu.addAction(play_pause_action)
        
        stop_action = QAction("Стоп", self)
        stop_action.setShortcut("S")
        stop_action.triggered.connect(self.stop_playback)
        playback_menu.addAction(stop_action)
        
        # === МЕНЮ "ВИД" ===
        view_menu = self.menu_bar.addMenu("Вид")
        
        # Подменю "Визуализация"
        viz_menu = view_menu.addMenu("Визуализация")
        
        self.viz_actions = {}
        viz_modes = [
            ("wave", "Волна", "1"),
            ("3d", "3D спектр", "2"),
            ("2d", "2D (кот)", "3"),
        ]
        
        for mode, name, shortcut in viz_modes:
            action = QAction(name, self)
            action.setShortcut(shortcut)
            action.setCheckable(True)
            action.setChecked(mode == self.viz_mode)
            action.triggered.connect(lambda checked, m=mode: self.set_viz_mode(m))
            viz_menu.addAction(action)
            self.viz_actions[mode] = action
        
        view_menu.addSeparator()
        
        # Подменю "Масштаб"
        scale_menu = view_menu.addMenu("Масштаб")
        
        scale_options = [10, 25, 50, 75, 100, 150, 200]
        self.scale_actions = {}
        
        for scale_value in scale_options:
            action = QAction(f"{scale_value}%", self)
            action.setCheckable(True)
            action.setChecked(scale_value == 50)
            action.triggered.connect(lambda checked, s=scale_value: self.apply_scale(s))
            scale_menu.addAction(action)
            self.scale_actions[scale_value] = action
        
    def _connect_button(self, button: CustomButton, handler):
        """Подключить сигнал clicked кнопки к обработчику."""
        button.clicked.connect(handler)
    
    def toggle_play_pause(self):
        """Переключение между воспроизведением и паузой"""
        if not self.audio_player.current_file:
            # Если файл не загружен, открываем диалог выбора файла
            self.select_and_load_file(auto_play=True)
            return
        
        if self.is_playing:
            self.audio_player.pause()
            self.is_playing = False
        else:
            self.audio_player.play()
            self.is_playing = True
        self._update_visualizer_play_state()
        self.update_play_pause_button()
        self.update_status_marquee_state()
    
    def stop_playback(self):
        """Остановка воспроизведения"""
        self.audio_player.stop()
        self.is_playing = False
        self._update_visualizer_play_state()
        self.update_play_pause_button()
        self.update_progress()  # Сбросить прогресс-бар
        self.update_status_text()
        self.update_status_marquee_state()
    
    def on_playback_state_changed(self, state):
        """Обработка изменения состояния воспроизведения"""
        from PyQt6.QtMultimedia import QMediaPlayer
        self.is_playing = (state == QMediaPlayer.PlaybackState.PlayingState)
        self._update_visualizer_play_state()
        self.update_play_pause_button()
        # состояние файла не меняется, но статус перерисуем (пауза/плей)
        self.update_status_text()
        self.update_status_marquee_state()
    
    def update_play_pause_button(self):
        """Обновление внешнего вида кнопки play/pause в зависимости от состояния"""
        if not self.play_pause_button:
            return
        
        scale_factor = self.scale / 100.0
        if self.is_playing:
            scaled = self._scale_pixmap(self.original_pause_pixmap, scale_factor)
        else:
            scaled = self._scale_pixmap(self.original_play_pixmap, scale_factor)
        
        self.play_pause_button.setPixmap(scaled)
        self.play_pause_button.setFixedSize(scaled.size())
        
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
    
    def update_progress(self):
        """Обновление прогресс-бара и времени"""
        if not self.progress_empty or not self.progress_filled or not self.progress_button:
            return
        
        # Если перетаскиваем ползунок, не обновляем автоматически
        if self.is_dragging_progress:
            return
        
        duration = self.audio_player.get_duration()
        position = self.audio_player.get_position()
        
        if duration <= 0:
            if self.time_label:
                self.time_label.hide()
            return
        
        # Вычисляем прогресс (0.0 - 1.0)
        progress = position / duration if duration > 0 else 0.0
        
        self.set_progress_position(progress)
        self.update_time_label(position, duration)
    
    def set_progress_position(self, progress: float):
        """Установка позиции прогресс-бара (0.0 - 1.0)"""
        if not self.progress_empty or not self.progress_filled or not self.progress_button:
            return
        
        scale_factor = self.scale / 100.0
        progress = max(0.0, min(1.0, progress))
        
        # Ширина прогресс-бара
        bar_width = self.progress_empty.width()
        button_width = self.progress_button.width()
        button_height = self.progress_button.height()
        bar_height = self.progress_empty.height()
        
        # Позиция прогресс-бара
        bar_x = int(config.progress_bar_x * scale_factor)
        bar_y = int(config.progress_bar_y * scale_factor)
        
        # Вычисляем ширину заполненной части
        filled_width = int(bar_width * progress)
        
        # Обновляем ширину заполненной части (обрезаем справа)
        if filled_width > 0:
            # Берем исходное изображение и обрезаем
            scaled_filled = self.original_progress_filled_pixmap.scaled(
                bar_width, bar_height,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            # Создаем обрезанный pixmap
            cropped = scaled_filled.copy(0, 0, filled_width, bar_height)
            self.progress_filled.setPixmap(cropped)
            self.progress_filled.setFixedSize(filled_width, bar_height)
            self.progress_filled.move(bar_x, bar_y)
            self.progress_filled.show()
        else:
            self.progress_filled.hide()
        
        # Позиция ползунка (центр ползунка на позиции прогресса)
        button_x = bar_x + int((bar_width - button_width) * progress)
        button_y = bar_y + (bar_height - button_height) // 2  # Центрируем по вертикали
        self.progress_button.move(button_x, button_y)
    
    def update_time_label(self, position_ms: int, duration_ms: int):
        """Обновление метки времени"""
        if not self.time_label:
            return
        
        def format_time(ms, show_hours: bool):
            total_seconds = ms // 1000
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            if show_hours:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            return f"{minutes:02d}:{seconds:02d}"
        
        show_hours = duration_ms >= 3_600_000
        current = format_time(position_ms, show_hours)
        total = format_time(duration_ms, show_hours)
        self.time_label.setText(f"{current}/{total}")
        self.time_label.show()
        
        # Центрируем метку под прогресс-баром
        scale_factor = self.scale / 100.0
        bar_x = int(config.progress_bar_x * scale_factor)
        bar_y = int(config.progress_bar_y * scale_factor)
        bar_width = self.progress_empty.width() if self.progress_empty else 0
        bar_height = self.progress_empty.height() if self.progress_empty else 0
        gap = int(config.time_label_gap * scale_factor)
        
        label_width = self.time_label.sizeHint().width()
        label_x = bar_x + (bar_width - label_width) // 2
        label_y = bar_y + bar_height + gap
        self.time_label.move(label_x, label_y)
    
    def on_progress_drag_started(self):
        """Начало перетаскивания ползунка"""
        self.is_dragging_progress = True
        self.is_dragging_window = False
    
    def on_progress_drag_moved(self, global_pos: QPoint):
        """Перетаскивание ползунка"""
        self.is_dragging_window = False
        
        scale_factor = self.scale / 100.0
        bar_x = int(config.progress_bar_x * scale_factor)
        bar_width = self.progress_empty.width() if self.progress_empty else 0
        button_width = self.progress_button.width() if self.progress_button else 0
        
        local_pos = self.mapFromGlobal(global_pos)
        
        # Вычисляем прогресс из позиции мыши
        progress = (local_pos.x() - bar_x - button_width // 2) / (bar_width - button_width)
        progress = max(0.0, min(1.0, progress))
        
        # Обновляем визуальную позицию
        self.set_progress_position(progress)
        
        # Обновляем время в метке
        duration = self.audio_player.get_duration()
        position = int(duration * progress)
        self.update_time_label(position, duration)
    
    def on_progress_drag_finished(self, global_pos: QPoint):
        """Окончание перетаскивания ползунка"""
        self.is_dragging_progress = False
        
        scale_factor = self.scale / 100.0
        bar_x = int(config.progress_bar_x * scale_factor)
        bar_width = self.progress_empty.width() if self.progress_empty else 0
        button_width = self.progress_button.width() if self.progress_button else 0
        
        local_pos = self.mapFromGlobal(global_pos)
        
        progress = (local_pos.x() - bar_x - button_width // 2) / (bar_width - button_width)
        progress = max(0.0, min(1.0, progress))
        
        # Перематываем аудио
        duration = self.audio_player.get_duration()
        new_position = int(duration * progress)
        self.audio_player.set_position(new_position)
    
    def seek_to_click_position(self, click_pos: QPoint):
        """Перемотка к позиции клика на прогресс-баре"""
        scale_factor = self.scale / 100.0
        bar_x = int(config.progress_bar_x * scale_factor)
        bar_width = self.progress_empty.width() if self.progress_empty else 0
        
        # Вычисляем прогресс из позиции клика
        progress = (click_pos.x() - bar_x) / bar_width
        progress = max(0.0, min(1.0, progress))
        
        # Перематываем аудио
        duration = self.audio_player.get_duration()
        new_position = int(duration * progress)
        self.audio_player.set_position(new_position)
        
        # Обновляем визуальную позицию
        self.set_progress_position(progress)
        self.update_time_label(new_position, duration)
            
    def is_interactive_widget(self, widget):
        """Проверка, является ли виджет интерактивным (кнопка, прогресс-бар, менюбар)"""
        if widget is None:
            return False
        
        # Проверяем все интерактивные элементы
        interactive_widgets = [
            self.close_button,
            self.minimize_button,
            self.play_pause_button,
            self.stop_button,
            self.file_button,
            self.progress_button,
            self.progress_empty,
            self.progress_filled,
            self.time_label,
            self.menu_bar
        ]
        
        # Проверяем сам виджет и поднимаемся по иерархии
        current = widget
        while current and current != self:
            if current in interactive_widgets:
                return True
            if isinstance(current, CustomButton):
                return True
            if isinstance(current, QMenuBar):
                return True
            current = current.parent()
        
        return False
    
    def mousePressEvent(self, event: QMouseEvent):
        """Обработка нажатия мыши для перетаскивания окна и контекстного меню"""
        click_pos = event.position().toPoint()
        child = self.childAt(click_pos)
        
        # Проверяем, не кликнули ли мы по интерактивному элементу
        if self.is_interactive_widget(child):
            # Если клик по прогресс-бару (не по кнопке), обрабатываем перемотку
            if child == self.progress_empty or child == self.progress_filled:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.seek_to_click_position(click_pos)
                    event.accept()
                    return
            # Для всех остальных интерактивных элементов не обрабатываем перетаскивание
            return
        
        # Если клик не по интерактивному элементу, обрабатываем перетаскивание окна
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging_window = True
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        elif event.button() == Qt.MouseButton.RightButton:
            # Показываем контекстное меню (только на Windows/Linux)
            import sys
            if sys.platform != 'darwin':
                self.show_context_menu(event.globalPosition().toPoint())
            event.accept()
            
    def mouseMoveEvent(self, event: QMouseEvent):
        """Обработка движения мыши для перетаскивания окна"""
        # Если перетаскиваем прогресс-бар, не двигаем окно
        if self.is_dragging_progress:
            return
        
        # Если перетаскиваем окно и зажата левая кнопка
        if self.is_dragging_window and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Обработка отпускания кнопки мыши"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging_window = False
            
    def apply_scale(self, scale_percent: int):
        """Применение масштаба к окну и элементам"""
        self.scale = scale_percent
        scale_factor = scale_percent / 100.0
        
        # Обновляем состояние чекбоксов в меню
        if hasattr(self, 'scale_actions'):
            for scale_value, action in self.scale_actions.items():
                action.setChecked(scale_value == scale_percent)
        
        # Масштабируем изображение Aphex Twin
        scaled_aphex = self._scale_pixmap(self.original_aphex_pixmap, scale_factor)
        scaled_width = scaled_aphex.width()
        scaled_height = scaled_aphex.height()
        
        # Устанавливаем размер окна
        self.setFixedSize(scaled_width, scaled_height)
        
        # Обновляем фон
        self.background_label.setPixmap(scaled_aphex)
        self.background_label.setGeometry(0, 0, scaled_width, scaled_height)

        # Создаем/масштабируем визуализатор
        if not self.visualizer:
            self.visualizer = VisualizerWidget(self)
        self.visualizer.set_scale(scale_percent)
        self.visualizer.show()
        self.visualizer.raise_()
        
        # Масштабируем кнопки
        scaled_close = self._scale_pixmap(self.original_close_pixmap, scale_factor)
        scaled_minimize = self._scale_pixmap(self.original_minimize_pixmap, scale_factor)
        
        # Обновляем существующие кнопки или создаем новые, если их нет
        if self.close_button:
            self.close_button.setPixmap(scaled_close)
            self.close_button.setFixedSize(scaled_close.size())
        else:
            self.close_button = CustomButton(scaled_close, self)
            self._connect_button(self.close_button, self.close)
            
        if self.minimize_button:
            self.minimize_button.setPixmap(scaled_minimize)
            self.minimize_button.setFixedSize(scaled_minimize.size())
        else:
            self.minimize_button = CustomButton(scaled_minimize, self)
            self._connect_button(self.minimize_button, self.showMinimized)
        
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
        scaled_play = self._scale_pixmap(self.original_play_pixmap, scale_factor)
        scaled_pause = self._scale_pixmap(self.original_pause_pixmap, scale_factor)
        scaled_stop = self._scale_pixmap(self.original_stop_pixmap, scale_factor)
        
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
            self._connect_button(self.play_pause_button, self.toggle_play_pause)
        
        # Обновляем или создаем кнопку stop
        if self.stop_button:
            self.stop_button.setPixmap(scaled_stop)
            self.stop_button.setFixedSize(scaled_stop.size())
        else:
            self.stop_button = CustomButton(scaled_stop, self)
            self._connect_button(self.stop_button, self.stop_playback)
        
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
        
        # Кнопка выбора файла
        scaled_file_btn = self._scale_pixmap(self.original_file_button_pixmap, scale_factor)
        if self.file_button:
            self.file_button.setPixmap(scaled_file_btn)
            self.file_button.setFixedSize(scaled_file_btn.size())
        else:
            self.file_button = CustomButton(scaled_file_btn, self)
            self._connect_button(self.file_button, lambda: self.select_and_load_file(auto_play=False))
        self.file_button.move(
            int(config.file_button_x * scale_factor),
            int(config.file_button_y * scale_factor)
        )
        self.file_button.show()
        self.file_button.raise_()
        
        # Кнопки режимов визуализатора
        self.scale_viz_mode_buttons(scale_factor)
        
        # Строка состояния
        self.scale_status_label(scale_factor)
        
        # Масштабируем прогресс-бар
        self.scale_progress_bar(scale_factor)
        
    def scale_progress_bar(self, scale_factor: float):
        """Масштабирование прогресс-бара"""
        # Масштабируем изображения прогресс-бара
        scaled_empty = self._scale_pixmap(self.original_progress_empty_pixmap, scale_factor)
        scaled_button = self._scale_pixmap(self.original_progress_button_pixmap, scale_factor)
        
        # Позиция прогресс-бара
        bar_x = int(config.progress_bar_x * scale_factor)
        bar_y = int(config.progress_bar_y * scale_factor)
        
        # Создаем или обновляем пустой прогресс-бар (фон)
        if self.progress_empty:
            self.progress_empty.setPixmap(scaled_empty)
            self.progress_empty.setFixedSize(scaled_empty.size())
        else:
            self.progress_empty = QLabel(self)
            self.progress_empty.setPixmap(scaled_empty)
            self.progress_empty.setFixedSize(scaled_empty.size())
            self.progress_empty.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.progress_empty.move(bar_x, bar_y)
        
        # Создаем или обновляем заполненную часть
        if not self.progress_filled:
            self.progress_filled = QLabel(self)
            self.progress_filled.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.progress_filled.move(bar_x, bar_y)
        
        # Создаем или обновляем кнопку прогресса
        if self.progress_button:
            self.progress_button.setPixmap(scaled_button)
            self.progress_button.setFixedSize(scaled_button.size())
        else:
            self.progress_button = ProgressButton(scaled_button, self)
            # Подключаем сигналы для перетаскивания
            self.progress_button.drag_started.connect(self.on_progress_drag_started)
            self.progress_button.drag_moved.connect(self.on_progress_drag_moved)
            self.progress_button.drag_finished.connect(self.on_progress_drag_finished)
        
        # Центрируем кнопку по вертикали относительно прогресс-бара
        bar_height = scaled_empty.height()
        button_height = scaled_button.height()
        button_y = bar_y + (bar_height - button_height) // 2
        self.progress_button.move(bar_x, button_y)
        
        # Создаем или обновляем метку времени
        font_size = int(config.time_font_size * scale_factor)
        if not self.time_label:
            self.time_label = QLabel("00:00:00/00:00:00", self)
            self.time_label.setStyleSheet(f"color: {config.time_text_color};")
            self.time_label.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        else:
            self.time_label.setStyleSheet(f"color: {config.time_text_color};")
        
        font = self._app_font(font_size)
        self.time_label.setFont(font)
        self.time_label.adjustSize()
        
        # Позиционируем метку времени под прогресс-баром
        gap = int(config.time_label_gap * scale_factor)
        label_width = self.time_label.sizeHint().width()
        label_x = bar_x + (scaled_empty.width() - label_width) // 2
        label_y = bar_y + bar_height + gap
        self.time_label.move(label_x, label_y)
        
        # Показываем элементы
        self.progress_empty.show()
        self.progress_filled.show()
        self.progress_button.show()
        self.time_label.show()
        
        # Поднимаем кнопку наверх
        self.progress_button.raise_()
        
        # Обновляем позицию прогресса
        self.update_progress()
    
    def scale_viz_mode_buttons(self, scale_factor: float):
        """Масштабирование и позиционирование кнопок режимов визуализатора."""
        buttons_def = [
            ("wave", config.viz_btn_wave_x, config.viz_btn_wave_y,
             self.original_viz_wave_active, self.original_viz_wave_inactive),
            # Меняем местами функционал 2 и 3: кнопка "2" теперь режим 3d
            ("3d", config.viz_btn_2d_x, config.viz_btn_2d_y,
             self.original_viz_2d_active, self.original_viz_2d_inactive),
            # Кнопка "3" теперь режим 2d (кот)
            ("2d", config.viz_btn_3d_x, config.viz_btn_3d_y,
             self.original_viz_3d_active, self.original_viz_3d_inactive),
        ]
        for mode, base_x, base_y, pix_active, pix_inactive in buttons_def:
            pixmap = pix_active if self.viz_mode == mode else pix_inactive
            scaled = self._scale_pixmap(pixmap, scale_factor)
            btn = self.viz_mode_buttons.get(mode)
            if btn:
                btn.setPixmap(scaled)
                btn.setFixedSize(scaled.size())
            else:
                btn = CustomButton(scaled, self)
                self.viz_mode_buttons[mode] = btn
                # Захватываем mode в lambda через параметр по умолчанию
                self._connect_button(btn, lambda m=mode: self.set_viz_mode(m))
            btn.move(int(base_x * scale_factor), int(base_y * scale_factor))
            btn.show()
            btn.raise_()

    def scale_status_label(self, scale_factor: float):
        """Масштабирование и позиционирование строки состояния."""
        if not self.status_label:
            self.status_label = MarqueeLabel(self)
        w = int(config.status_width * scale_factor)
        h = int(config.status_height * scale_factor)
        x = int(config.status_x * scale_factor)
        y = int(config.status_y * scale_factor)
        self.status_label.setGeometry(x, y, w, h)
        font = self._app_font(int(config.status_font_size * scale_factor))
        self.status_label.setFont(font)
        self.status_label.setStyleSheet(f"color: {config.status_color};")
        self.status_label.set_marquee_params(config.status_marquee_speed_px, config.status_marquee_interval_ms)
        self.status_label.set_text(self.status_text)
        self.status_label.show()
        self.status_label.raise_()
        self.update_status_marquee_state()
    
    def show_context_menu(self, position):
        """Показать нативное контекстное меню (для Windows/Linux)"""
        menu = QMenu(self)
        
        # === ФАЙЛ ===
        open_action = QAction("Открыть...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(lambda: self.select_and_load_file(auto_play=False))
        menu.addAction(open_action)
        
        menu.addSeparator()
        
        # === ВОСПРОИЗВЕДЕНИЕ ===
        playback_menu = menu.addMenu("Воспроизведение")
        
        play_pause_action = QAction("Play/Pause", self)
        play_pause_action.setShortcut("Space")
        play_pause_action.triggered.connect(self.toggle_play_pause)
        playback_menu.addAction(play_pause_action)
        
        stop_action = QAction("Стоп", self)
        stop_action.setShortcut("S")
        stop_action.triggered.connect(self.stop_playback)
        playback_menu.addAction(stop_action)
        
        menu.addSeparator()
        
        # === ВИЗУАЛИЗАЦИЯ ===
        viz_menu = menu.addMenu("Визуализация")
        
        viz_modes = [
            ("wave", "Волна", "1"),
            ("3d", "3D спектр", "2"),
            ("2d", "2D (кот)", "3"),
        ]
        
        for mode, name, shortcut in viz_modes:
            action = QAction(name, self)
            action.setShortcut(shortcut)
            action.setCheckable(True)
            action.setChecked(mode == self.viz_mode)
            action.triggered.connect(lambda checked, m=mode: self.set_viz_mode(m))
            viz_menu.addAction(action)
        
        menu.addSeparator()
        
        # === МАСШТАБ ===
        scale_menu = menu.addMenu("Масштаб")
        
        scale_options = [10, 25, 50, 75, 100, 150, 200]
        
        for scale_value in scale_options:
            action = QAction(f"{scale_value}%", self)
            action.setCheckable(True)
            action.setChecked(scale_value == self.scale)
            action.triggered.connect(lambda checked, s=scale_value: self.apply_scale(s))
            scale_menu.addAction(action)
        
        menu.addSeparator()
        
        # === ВЫХОД ===
        quit_action = QAction("Выход", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        menu.addAction(quit_action)
        
        # Показываем меню
        menu.exec(position)
        
        # Обновляем состояние в менюбаре после выбора в контекстном меню (для macOS)
        if hasattr(self, 'scale_actions'):
            for scale_value, action in self.scale_actions.items():
                action.setChecked(scale_value == self.scale)
        if hasattr(self, 'viz_actions'):
            for mode, action in self.viz_actions.items():
                action.setChecked(mode == self.viz_mode)
    
    def keyPressEvent(self, event):
        """Горячие клавиши для смены режима визуализатора."""
        if not self.visualizer:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key == Qt.Key.Key_1:
            self.set_viz_mode("wave")
            event.accept()
            return
        if key == Qt.Key.Key_2:
            # Меняем местами функционал: 2 -> 3d
            self.set_viz_mode("3d")
            event.accept()
            return
        if key == Qt.Key.Key_3:
            # 3 -> 2d (кот)
            self.set_viz_mode("2d")
            event.accept()
            return
        super().keyPressEvent(event)

    def select_and_load_file(self, auto_play: bool = False):
        """Открыть диалог выбора файла, загрузить и при необходимости запустить."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите аудиофайл",
            "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a *.aac);;All Files (*)"
        )
        if not file_path:
            return
        try:
            self.audio_player.load_file(file_path)
            self.load_visualizer_audio(file_path)
            if auto_play:
                self.audio_player.play()
                self.is_playing = True
            else:
                # Явно сбрасываем флаг проигрывания, если не автозапуск
                self.is_playing = False
            self._update_visualizer_play_state()
            self.update_play_pause_button()
            self.update_status_text()
            self.update_status_marquee_state()
        except Exception as e:
            print(f"Ошибка загрузки файла: {e}")

    def set_viz_mode(self, mode: str):
        """Установить режим визуализатора и обновить кнопки."""
        if mode not in ("wave", "2d", "3d"):
            return
        self.viz_mode = mode
        if self.visualizer:
            self.visualizer.set_mode(mode)
            self._update_visualizer_play_state()
        # Обновить галочки в меню
        if hasattr(self, 'viz_actions'):
            for m, action in self.viz_actions.items():
                action.setChecked(m == mode)
        # Обновить кнопки (переиспользуем масштабирование для смены спрайта)
        scale_factor = self.scale / 100.0
        self.scale_viz_mode_buttons(scale_factor)
        # Обновить строку состояния (текст может не меняться, но перерисуем)
        self.scale_status_label(scale_factor)
        self.update_status_text()

    def _app_font(self, size: int | None = None) -> QFont:
        """Возвращает шрифт приложения с заданным размером."""
        base = QApplication.font()
        return QFont(base.family(), size if size is not None else base.pointSize())

    def _scale_pixmap(self, pixmap: QPixmap, scale_factor: float) -> QPixmap:
        """Масштабирует pixmap с сохранением пропорций и сглаживанием."""
        return pixmap.scaled(
            int(pixmap.width() * scale_factor),
            int(pixmap.height() * scale_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

    def _update_visualizer_play_state(self):
        """Синхронизировать визуализатор с состоянием плеера."""
        if self.visualizer:
            self.visualizer.set_playing(self.is_playing)

    # --- Визуализатор и аудиоданные (декод из файла) ---
    def load_visualizer_audio(self, file_path: str):
        """Декодировать аудио в память для визуализации."""
        data, samplerate = decode_file_to_mono(file_path)
        if samplerate <= 0 or data.size == 0:
            self._viz_audio = None
            self._viz_samplerate = 0
            return
        self._viz_audio = data.astype(np.float32)
        self._viz_samplerate = samplerate

    def update_visualizer_frame(self):
        """Периодический апдейт визуализатора по позиции плеера."""
        if not self.visualizer or self._viz_audio is None or self._viz_samplerate <= 0:
            return
        pos_ms = self.audio_player.get_position()
        if pos_ms < 0:
            return
        # Окно вокруг текущей позиции
        window_ms = config.viz_fft_window_ms
        center = int(pos_ms * self._viz_samplerate / 1000)
        half = int(window_ms * self._viz_samplerate / 1000 / 2)
        start = max(0, center - half)
        end = min(len(self._viz_audio), start + 2048)
        seg = self._viz_audio[start:end]
        if seg.size == 0:
            return
        # FFT
        win = np.hanning(seg.size)
        spec = np.abs(np.fft.rfft(seg * win))
        # Волновая форма (даунсемплинг для скорости)
        waveform = seg
        downsample = max(8, config.viz_wave_downsample)
        if waveform.size > downsample:
            idx = np.linspace(0, waveform.size - 1, downsample).astype(int)
            waveform = waveform[idx]
        self.visualizer.feed_features(spec, waveform)
        # Синхронизируем состояние строки (например, при старте/стопе)
        self.update_status_text()

    def update_status_text(self):
        """Обновление текста строки состояния и бегущей строки."""
        if not self.status_label:
            return
        if not self.audio_player.current_file:
            text = "Файл не загружен"
        else:
            artist, title = self._get_track_meta()
            text = f'Играет: "{artist}" — "{title}"'
        self.status_text = text
        self.status_label.set_text(text)
        self.update_status_marquee_state()

    def _get_track_meta(self):
        """Пытаемся получить автора и название трека из метаданных плеера."""
        artist = ""
        title = ""
        try:
            from PyQt6.QtMultimedia import QMediaMetaData
            meta = self.audio_player.media_player.metaData()
            if meta:
                artist = meta.get(QMediaMetaData.Key.Author) or meta.get(QMediaMetaData.Key.AlbumArtist) or ""
                title = meta.get(QMediaMetaData.Key.Title) or ""
        except Exception:
            pass
        if self.audio_player.current_file:
            if not title:
                title = self.audio_player.current_file.stem
        if not artist:
            artist = "Unknown"
        return artist, title

    def update_status_marquee_state(self):
        """Остановить или запустить бегущую строку в зависимости от воспроизведения."""
        if not self.status_label:
            return
        paused = not self.is_playing
        self.status_label.set_paused(paused)
        
    def paintEvent(self, event):
        """Перерисовка окна"""
        super().paintEvent(event)


"""
Аудиоплеер на PyQt5 в стиле Windows Media Player 9
Использует PNG-ассеты из папки ui2/pngassets
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QLabel,
                             QMessageBox, QSlider, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QUrl, QSize, QTimer, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QColor, QFont, QPalette, QBrush
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent


# Путь к PNG-ассетам
ASSETS_PATH = Path(__file__).parent / 'ui2' / 'pngassets'


def get_asset(name: str) -> str:
    """Получить путь к PNG-ассету"""
    return str(ASSETS_PATH / name)


class ImageButton(QPushButton):
    """
    Кнопка с изображениями для разных состояний (normal, hover, down, disabled)
    Аналог BUTTON из Corona.wms
    """
    
    def __init__(self, normal: str, hover: str = None, down: str = None, 
                 disabled: str = None, parent=None):
        super().__init__(parent)
        self.normal_img = normal
        self.hover_img = hover or normal
        self.down_img = down or normal
        self.disabled_img = disabled or normal
        
        self.setFlat(True)
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()
        
        # Устанавливаем размер по изображению
        pixmap = QPixmap(normal)
        if not pixmap.isNull():
            self.setFixedSize(pixmap.size())
            self.setIconSize(pixmap.size())
    
    def update_style(self):
        """Обновление стиля кнопки"""
        self.setStyleSheet(f"""
            QPushButton {{
                border: none;
                background: transparent;
                background-image: url({self.normal_img});
                background-repeat: no-repeat;
            }}
            QPushButton:hover {{
                background-image: url({self.hover_img});
            }}
            QPushButton:pressed {{
                background-image: url({self.down_img});
            }}
            QPushButton:disabled {{
                background-image: url({self.disabled_img});
            }}
        """)


class ToggleImageButton(ImageButton):
    """Кнопка-переключатель с двумя состояниями"""
    
    toggled_state = pyqtSignal(bool)
    
    def __init__(self, normal: str, hover: str = None, down: str = None,
                 disabled: str = None, parent=None):
        super().__init__(normal, hover, down, disabled, parent)
        self._is_toggled = False
        self.clicked.connect(self._on_click)
    
    def _on_click(self):
        self._is_toggled = not self._is_toggled
        self.toggled_state.emit(self._is_toggled)
        self._update_appearance()
    
    def _update_appearance(self):
        if self._is_toggled:
            self.setStyleSheet(f"""
                QPushButton {{
                    border: none;
                    background: transparent;
                    background-image: url({self.down_img});
                    background-repeat: no-repeat;
                }}
                QPushButton:hover {{
                    background-image: url({self.hover_img});
                }}
            """)
        else:
            self.update_style()
    
    def set_toggled(self, state: bool):
        self._is_toggled = state
        self._update_appearance()
    
    def is_toggled(self) -> bool:
        return self._is_toggled


class VisualizerWidget(QWidget):
    """
    Виджет визуализации аудио
    Аналог WMPEFFECTS из Corona.wms
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 240)
        self.bars = [0] * 32  # 32 столбика визуализатора
        self.is_playing = False
        
        # Таймер для анимации
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_bars)
        
        self.setStyleSheet("background-color: #000000;")
    
    def start(self):
        """Запуск визуализации"""
        self.is_playing = True
        self.timer.start(50)  # 20 FPS
    
    def stop(self):
        """Остановка визуализации"""
        self.is_playing = False
        self.timer.stop()
        self.bars = [0] * 32
        self.update()
    
    def update_bars(self):
        """Обновление значений столбиков (псевдо-визуализация)"""
        import random
        for i in range(len(self.bars)):
            # Плавное изменение высоты столбиков
            target = random.randint(20, 100) if self.is_playing else 0
            self.bars[i] = self.bars[i] * 0.7 + target * 0.3
        self.update()
    
    def paintEvent(self, event):
        """Отрисовка визуализатора"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Фон
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        if not self.is_playing and all(b < 1 for b in self.bars):
            # Показываем текст когда не играет
            painter.setPen(QColor(0, 255, 0))
            painter.setFont(QFont('Arial', 12))
            painter.drawText(self.rect(), Qt.AlignCenter, 'Windows Media Player')
            return
        
        # Рисуем столбики
        bar_width = self.width() // len(self.bars) - 2
        for i, height in enumerate(self.bars):
            x = i * (bar_width + 2) + 2
            bar_height = int(height * self.height() / 100)
            y = self.height() - bar_height
            
            # Градиент от зелёного к красному
            for j in range(bar_height):
                ratio = j / max(bar_height, 1)
                if ratio < 0.6:
                    color = QColor(0, 255, 0)  # Зелёный
                elif ratio < 0.8:
                    color = QColor(255, 255, 0)  # Жёлтый
                else:
                    color = QColor(255, 0, 0)  # Красный
                painter.setPen(color)
                painter.drawLine(x, self.height() - j, x + bar_width, self.height() - j)


class TransportPanel(QWidget):
    """
    Панель управления воспроизведением
    Аналог bgTransports из Corona.wms
    """
    
    # Сигналы
    play_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    prev_clicked = pyqtSignal()
    next_clicked = pyqtSignal()
    mute_toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Используем transports.png как фон группы кнопок
        # Но для простоты создадим отдельные кнопки
        
        # Кнопка Previous
        self.prev_btn = ImageButton(
            get_asset('seekbutton_left.png'),
            get_asset('seekbutton_left_hover.png'),
            get_asset('seekbutton_left_down.png'),
            get_asset('seekbutton_left_disabled.png')
        )
        self.prev_btn.setToolTip('Предыдущий')
        self.prev_btn.clicked.connect(self.prev_clicked.emit)
        layout.addWidget(self.prev_btn)
        
        # Кнопка Play/Pause (используем transports.png)
        self.play_btn = ImageButton(
            get_asset('transports.png'),
            get_asset('transports_hover.png'),
            get_asset('transports_down.png'),
            get_asset('transports_disabled.png')
        )
        self.play_btn.setToolTip('Воспроизвести')
        self.play_btn.clicked.connect(self.play_clicked.emit)
        layout.addWidget(self.play_btn)
        
        # Кнопка Next
        self.next_btn = ImageButton(
            get_asset('seekbutton_right.png'),
            get_asset('seekbutton_right_hover.png'),
            get_asset('seekbutton_right_down.png'),
            get_asset('seekbutton_right_disabled.png')
        )
        self.next_btn.setToolTip('Следующий')
        self.next_btn.clicked.connect(self.next_clicked.emit)
        layout.addWidget(self.next_btn)
        
        layout.addStretch()


class SeekSlider(QSlider):
    """
    Слайдер прогресса воспроизведения
    Аналог SEEKSLIDER из Corona.wms
    """
    
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setMinimumWidth(200)
        
        # Стилизация слайдера
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #999999;
                height: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d2d2d, stop:1 #1a1a1a);
                margin: 2px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #5c5c5c, stop:1 #3d3d3d);
                border: 1px solid #5c5c5c;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #7c7c7c, stop:1 #5d5d5d);
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00ff00, stop:1 #008800);
                border-radius: 4px;
            }
        """)


class VolumeSlider(QSlider):
    """
    Слайдер громкости
    Аналог VOLUMESLIDER из Corona.wms
    """
    
    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setRange(0, 100)
        self.setValue(70)
        self.setFixedWidth(80)
        
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #666;
                height: 6px;
                background: #2d2d2d;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #888;
                border: 1px solid #666;
                width: 12px;
                margin: -3px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #aaa;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #004400, stop:1 #00aa00);
                border-radius: 3px;
            }
        """)


class TopPanel(QWidget):
    """
    Верхняя панель с кнопками управления
    Аналог svTop из Corona.wms
    """
    
    open_file = pyqtSignal()
    toggle_playlist = pyqtSignal()
    toggle_visualizer = pyqtSignal()
    toggle_equalizer = pyqtSignal()
    minimize_clicked = pyqtSignal()
    close_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(33)
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 3, 10, 3)
        layout.setSpacing(5)
        
        # Левая часть - кнопки управления плеером
        left_layout = QHBoxLayout()
        left_layout.setSpacing(3)
        
        # Кнопка открытия файла
        self.open_btn = ImageButton(
            get_asset('file_open_button.png'),
            get_asset('file_open_button_hover.png'),
            get_asset('file_open_button_down.png'),
            get_asset('file_open_button_disabled.png')
        )
        self.open_btn.setToolTip('Открыть файл')
        self.open_btn.clicked.connect(self.open_file.emit)
        left_layout.addWidget(self.open_btn)
        
        layout.addLayout(left_layout)
        layout.addStretch()
        
        # Правая часть - системные кнопки
        right_layout = QHBoxLayout()
        right_layout.setSpacing(3)
        
        # Кнопка минимизации
        self.min_btn = ImageButton(
            get_asset('minimize_button.png'),
            get_asset('minimize_button_hover.png'),
            get_asset('minimize_button_down.png'),
            get_asset('minimize_button_disabled.png')
        )
        self.min_btn.setToolTip('Свернуть')
        self.min_btn.clicked.connect(self.minimize_clicked.emit)
        right_layout.addWidget(self.min_btn)
        
        layout.addLayout(right_layout)
    
    def paintEvent(self, event):
        """Отрисовка фона панели"""
        painter = QPainter(self)
        
        # Загружаем фоновые изображения
        left_bg = QPixmap(get_asset('player_top_left.png'))
        middle_bg = QPixmap(get_asset('player_top_middle.png'))
        right_bg = QPixmap(get_asset('player_top_right.png'))
        
        # Рисуем левую часть
        if not left_bg.isNull():
            painter.drawPixmap(0, 0, left_bg)
        
        # Рисуем среднюю часть (тайлим)
        if not middle_bg.isNull():
            x = left_bg.width() if not left_bg.isNull() else 0
            end_x = self.width() - (right_bg.width() if not right_bg.isNull() else 0)
            while x < end_x:
                painter.drawPixmap(x, 0, middle_bg)
                x += middle_bg.width()
        
        # Рисуем правую часть
        if not right_bg.isNull():
            painter.drawPixmap(self.width() - right_bg.width(), 0, right_bg)


class BottomPanel(QWidget):
    """
    Нижняя панель с метаданными и временем
    Аналог svBottom из Corona.wms
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.metadata_text = ''
        self.time_text = '00:00'
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 5, 20, 5)
        
        # Метаданные (название трека)
        self.metadata_label = QLabel('Windows Media Player')
        self.metadata_label.setStyleSheet("""
            QLabel {
                color: #00FF00;
                font-family: Arial;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.metadata_label)
        
        layout.addStretch()
        
        # Время воспроизведения
        self.time_label = QLabel('00:00')
        self.time_label.setStyleSheet("""
            QLabel {
                color: #00FF00;
                font-family: Arial;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.time_label)
    
    def set_metadata(self, text: str):
        self.metadata_label.setText(text)
    
    def set_time(self, time_str: str):
        self.time_label.setText(time_str)
    
    def paintEvent(self, event):
        """Отрисовка фона панели"""
        painter = QPainter(self)
        
        # Загружаем фоновые изображения
        left_bg = QPixmap(get_asset('player_bottom_left.png'))
        middle_bg = QPixmap(get_asset('player_bottom_middle.png'))
        right_bg = QPixmap(get_asset('player_bottom_right.png'))
        
        # Рисуем левую часть
        if not left_bg.isNull():
            painter.drawPixmap(0, 0, left_bg)
        
        # Рисуем среднюю часть (тайлим)
        if not middle_bg.isNull():
            x = left_bg.width() if not left_bg.isNull() else 0
            end_x = self.width() - (right_bg.width() if not right_bg.isNull() else 0)
            while x < end_x:
                painter.drawPixmap(x, 0, middle_bg)
                x += middle_bg.width()
        
        # Рисуем правую часть
        if not right_bg.isNull():
            painter.drawPixmap(self.width() - right_bg.width(), 0, right_bg)


class ControlsPanel(QWidget):
    """
    Панель с элементами управления (transport + seek + volume)
    Аналог svEqualizerBottom из Corona.wms
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(5)
        
        # Слайдер прогресса
        self.seek_slider = SeekSlider()
        main_layout.addWidget(self.seek_slider)
        
        # Панель с кнопками и громкостью
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        # Транспортные кнопки
        self.transport = TransportPanel()
        controls_layout.addWidget(self.transport)
        
        controls_layout.addStretch()
        
        # Громкость
        volume_layout = QHBoxLayout()
        volume_label = QLabel('🔊')
        volume_label.setStyleSheet("color: #888; font-size: 14px;")
        volume_layout.addWidget(volume_label)
        
        self.volume_slider = VolumeSlider()
        volume_layout.addWidget(self.volume_slider)
        
        controls_layout.addLayout(volume_layout)
        
        main_layout.addLayout(controls_layout)
    
    def paintEvent(self, event):
        """Отрисовка фона панели"""
        painter = QPainter(self)
        
        # Загружаем фоновые изображения
        left_bg = QPixmap(get_asset('equalizer_left.png'))
        middle_bg = QPixmap(get_asset('equalizer_middle.png'))
        right_bg = QPixmap(get_asset('equalizer_right.png'))
        
        # Рисуем левую часть
        if not left_bg.isNull():
            # Масштабируем по высоте
            scaled = left_bg.scaledToHeight(self.height(), Qt.SmoothTransformation)
            painter.drawPixmap(0, 0, scaled)
        
        # Рисуем среднюю часть (тайлим)
        if not middle_bg.isNull():
            x = left_bg.width() if not left_bg.isNull() else 0
            end_x = self.width() - (right_bg.width() if not right_bg.isNull() else 0)
            scaled = middle_bg.scaledToHeight(self.height(), Qt.SmoothTransformation)
            while x < end_x:
                painter.drawPixmap(x, 0, scaled)
                x += scaled.width()
        
        # Рисуем правую часть
        if not right_bg.isNull():
            scaled = right_bg.scaledToHeight(self.height(), Qt.SmoothTransformation)
            painter.drawPixmap(self.width() - scaled.width(), 0, scaled)


class AudioPlayer(QMainWindow):
    """
    Главное окно аудиоплеера в стиле Windows Media Player 9
    """

    def __init__(self):
        super().__init__()
        self.current_file = None
        self.media_player = QMediaPlayer()
        self.init_ui()
        self.setup_media_player()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle('Аудиоплеер')
        self.setGeometry(100, 100, 600, 450)
        self.setMinimumSize(500, 400)
        
        # Тёмный фон в стиле WMP
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a2e;
            }
        """)

        # Центральный виджет
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #1a1a2e;")
        self.setCentralWidget(central_widget)

        # Главный layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)

        # Создание меню
        self.create_menu_bar()

        # Верхняя панель
        self.top_panel = TopPanel()
        self.top_panel.open_file.connect(self.open_file)
        self.top_panel.minimize_clicked.connect(self.showMinimized)
        main_layout.addWidget(self.top_panel)

        # Визуализатор
        self.visualizer = VisualizerWidget()
        self.visualizer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.visualizer)

        # Нижняя панель с метаданными
        self.bottom_panel = BottomPanel()
        main_layout.addWidget(self.bottom_panel)

        # Панель управления
        self.controls_panel = ControlsPanel()
        self.controls_panel.transport.play_clicked.connect(self.play_audio)
        self.controls_panel.transport.prev_clicked.connect(self.rewind)
        self.controls_panel.transport.next_clicked.connect(self.fast_forward)
        self.controls_panel.seek_slider.sliderMoved.connect(self.set_position)
        self.controls_panel.volume_slider.valueChanged.connect(self.set_volume)
        main_layout.addWidget(self.controls_panel)

    def create_menu_bar(self):
        """Создание меню приложения"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2d2d44;
                color: #ffffff;
                border-bottom: 1px solid #444;
            }
            QMenuBar::item:selected {
                background-color: #3d3d5c;
            }
            QMenu {
                background-color: #2d2d44;
                color: #ffffff;
                border: 1px solid #444;
            }
            QMenu::item:selected {
                background-color: #3d3d5c;
            }
        """)

        # Меню "Файл"
        file_menu = menubar.addMenu('Файл')
        
        open_action = file_menu.addAction('Открыть')
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction('Выход')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)

        # Меню "Воспроизведение"
        play_menu = menubar.addMenu('Воспроизведение')
        
        play_action = play_menu.addAction('Воспроизвести/Пауза')
        play_action.setShortcut('Space')
        play_action.triggered.connect(self.play_audio)
        
        stop_action = play_menu.addAction('Стоп')
        stop_action.triggered.connect(self.stop_audio)

        # Меню "Вид"
        view_menu = menubar.addMenu('Вид')
        
        fullscreen_action = view_menu.addAction('Полный экран')
        fullscreen_action.setShortcut('F11')
        fullscreen_action.triggered.connect(self.toggle_fullscreen)

        # Меню "Справка"
        help_menu = menubar.addMenu('Справка')
        
        about_action = help_menu.addAction('О программе')
        about_action.triggered.connect(self.show_about)

    def setup_media_player(self):
        """Настройка медиаплеера"""
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        self.media_player.stateChanged.connect(self.state_changed)
        self.media_player.error.connect(self.handle_error)

    def open_file(self):
        """Открытие аудиофайла"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                'Выберите аудиофайл',
                '',
                'Audio Files (*.mp3 *.wav *.ogg *.m4a *.flac);;All Files (*)'
            )

            if file_path:
                self.current_file = file_path
                url = QUrl.fromLocalFile(file_path)
                content = QMediaContent(url)
                self.media_player.setMedia(content)
                
                # Обновляем метаданные
                filename = Path(file_path).stem
                self.bottom_panel.set_metadata(filename)
                
                # Автовоспроизведение
                self.media_player.play()
                
        except Exception as e:
            QMessageBox.critical(
                self,
                'Ошибка',
                f'Не удалось открыть файл:\n{str(e)}'
            )

    def play_audio(self):
        """Воспроизведение/пауза аудио"""
        try:
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.media_player.pause()
            else:
                self.media_player.play()
        except Exception as e:
            QMessageBox.critical(
                self,
                'Ошибка',
                f'Ошибка воспроизведения:\n{str(e)}'
            )

    def stop_audio(self):
        """Остановка воспроизведения"""
        try:
            self.media_player.stop()
            self.visualizer.stop()
        except Exception as e:
            QMessageBox.critical(
                self,
                'Ошибка',
                f'Ошибка остановки:\n{str(e)}'
            )

    def rewind(self):
        """Перемотка назад"""
        pos = self.media_player.position()
        self.media_player.setPosition(max(0, pos - 10000))  # -10 сек

    def fast_forward(self):
        """Перемотка вперёд"""
        pos = self.media_player.position()
        duration = self.media_player.duration()
        self.media_player.setPosition(min(duration, pos + 10000))  # +10 сек

    def set_position(self, position):
        """Установка позиции воспроизведения"""
        try:
            self.media_player.setPosition(position)
        except Exception as e:
            QMessageBox.critical(
                self,
                'Ошибка',
                f'Ошибка установки позиции:\n{str(e)}'
            )

    def set_volume(self, value):
        """Установка громкости"""
        self.media_player.setVolume(value)

    def position_changed(self, position):
        """Обновление позиции слайдера"""
        self.controls_panel.seek_slider.setValue(position)
        
        # Обновляем время
        seconds = position // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        self.bottom_panel.set_time(f'{minutes:02d}:{seconds:02d}')

    def duration_changed(self, duration):
        """Обновление длительности слайдера"""
        self.controls_panel.seek_slider.setRange(0, duration)

    def state_changed(self, state):
        """Обработка изменения состояния плеера"""
        if state == QMediaPlayer.PlayingState:
            self.visualizer.start()
        elif state == QMediaPlayer.PausedState:
            self.visualizer.stop()
        elif state == QMediaPlayer.StoppedState:
            self.visualizer.stop()
            self.bottom_panel.set_time('00:00')

    def handle_error(self, error):
        """Обработка ошибок медиаплеера"""
        error_string = self.media_player.errorString()
        if error_string:
            QMessageBox.critical(
                self,
                'Ошибка медиаплеера',
                f'Ошибка: {error_string}'
            )

    def toggle_fullscreen(self):
        """Переключение полноэкранного режима"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def show_about(self):
        """Показ информации о программе"""
        QMessageBox.about(
            self,
            'О программе',
            'Аудиоплеер в стиле Windows Media Player 9\n\n'
            'Создан с использованием PyQt5\n'
            'Лабораторная работа №3'
        )

    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        if event.key() == Qt.Key_Space:
            self.play_audio()
        elif event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
        else:
            super().keyPressEvent(event)


def main():
    """Точка входа в приложение"""
    app = QApplication(sys.argv)
    
    # Устанавливаем стиль Fusion для лучшей совместимости
    app.setStyle('Fusion')
    
    player = AudioPlayer()
    player.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

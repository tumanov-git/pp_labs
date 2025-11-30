"""
Аудиоплеер на PyQt5 - точная реализация структуры Corona.wms
Переписан с использованием PNG-ассетов из ui2/pngassets
"""

import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QLabel,
                             QMessageBox, QSlider, QFrame, QSizePolicy, QListWidget,
                             QAbstractItemView)
from PyQt5.QtCore import Qt, QUrl, QSize, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QColor, QFont, QPalette, QBrush, QPen
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent


# Путь к PNG-ассетам
ASSETS_PATH = Path(__file__).parent / 'ui2' / 'pngassets'


def get_asset(name: str) -> str:
    """Получить путь к PNG-ассету"""
    return str(ASSETS_PATH / name)


class ImageButton(QPushButton):
    """Кнопка с изображениями для разных состояний"""
    
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
    """Кнопка-переключатель"""
    
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


class TiledBackgroundWidget(QWidget):
    """Виджет с тайлируемым фоном"""
    
    def __init__(self, bg_image: str, transparency_color: str = None, parent=None):
        super().__init__(parent)
        self.bg_image = bg_image
        self.transparency_color = transparency_color
        self.pixmap = QPixmap(bg_image) if bg_image else None
    
    def paintEvent(self, event):
        """Отрисовка тайлируемого фона"""
        if not self.pixmap or self.pixmap.isNull():
            return
        
        painter = QPainter(self)
        x = 0
        y = 0
        
        # Тайлим изображение
        while y < self.height():
            while x < self.width():
                painter.drawPixmap(x, y, self.pixmap)
                x += self.pixmap.width()
            x = 0
            y += self.pixmap.height()


class VisualizerWidget(QWidget):
    """Визуализатор аудио (WMPEFFECTS)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(320, 240)
        self.bars = [0] * 32
        self.is_playing = False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_bars)
        self.setStyleSheet("background-color: #000000;")
    
    def start(self):
        """Запуск визуализации"""
        self.is_playing = True
        self.timer.start(50)
    
    def stop(self):
        """Остановка визуализации"""
        self.is_playing = False
        self.timer.stop()
        self.bars = [0] * 32
        self.update()
    
    def update_bars(self):
        """Обновление значений столбиков"""
        import random
        for i in range(len(self.bars)):
            target = random.randint(20, 100) if self.is_playing else 0
            self.bars[i] = self.bars[i] * 0.7 + target * 0.3
        self.update()
    
    def paintEvent(self, event):
        """Отрисовка визуализатора"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        if not self.is_playing and all(b < 1 for b in self.bars):
            painter.setPen(QColor(0, 255, 0))
            painter.setFont(QFont('Arial', 12))
            painter.drawText(self.rect(), Qt.AlignCenter, 'Windows Media Player')
            return
        
        bar_width = self.width() // len(self.bars) - 2
        for i, height in enumerate(self.bars):
            x = i * (bar_width + 2) + 2
            bar_height = int(height * self.height() / 100)
            y = self.height() - bar_height
            
            for j in range(bar_height):
                ratio = j / max(bar_height, 1)
                if ratio < 0.6:
                    color = QColor(0, 255, 0)
                elif ratio < 0.8:
                    color = QColor(255, 255, 0)
                else:
                    color = QColor(255, 0, 0)
                painter.setPen(color)
                painter.drawLine(x, self.height() - j, x + bar_width, self.height() - j)


class SubViewTop(QWidget):
    """SUBVIEW svTop - верхняя панель (346x33)"""
    
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # svTopLeft (299x33)
        top_left = QWidget()
        top_left.setFixedWidth(299)
        top_left_layout = QHBoxLayout(top_left)
        top_left_layout.setContentsMargins(116, 3, 0, 0)
        top_left_layout.setSpacing(0)
        
        # Кнопка открытия файла
        self.open_btn = ImageButton(
            get_asset('file_open_button.png'),
            get_asset('file_open_button_hover.png'),
            get_asset('file_open_button_down.png'),
            get_asset('file_open_button_disabled.png')
        )
        self.open_btn.setToolTip('Открыть файл')
        self.open_btn.clicked.connect(self.open_file.emit)
        top_left_layout.addWidget(self.open_btn)
        
        # Кнопка плейлиста
        self.playlist_btn = ToggleImageButton(
            get_asset('player_top_controls_left.png'),
            get_asset('player_top_controls_left_hover.png'),
            get_asset('player_top_controls_left_down.png'),
            get_asset('player_top_controls_left_disabled.png')
        )
        self.playlist_btn.setToolTip('Показать плейлист')
        self.playlist_btn.toggled_state.connect(self.toggle_playlist.emit)
        top_left_layout.addWidget(self.playlist_btn)
        
        layout.addWidget(top_left)
        
        # svTopMiddle (1px, тайлится)
        top_middle = TiledBackgroundWidget(get_asset('player_top_middle.png'))
        top_middle.setFixedWidth(1)
        layout.addWidget(top_middle, 1)  # stretch
        
        # svTopRight (46x33)
        top_right = QWidget()
        top_right.setFixedWidth(46)
        top_right_layout = QHBoxLayout(top_right)
        top_right_layout.setContentsMargins(0, 3, 0, 0)
        top_right_layout.setSpacing(0)
        
        # Кнопка минимизации
        self.min_btn = ImageButton(
            get_asset('minimize_button.png'),
            get_asset('minimize_button_hover.png'),
            get_asset('minimize_button_down.png'),
            get_asset('minimize_button_disabled.png')
        )
        self.min_btn.setToolTip('Свернуть')
        self.min_btn.clicked.connect(self.minimize_clicked.emit)
        top_right_layout.addWidget(self.min_btn)
        
        layout.addWidget(top_right)
    
    def paintEvent(self, event):
        """Отрисовка фона"""
        painter = QPainter(self)
        
        # Левая часть
        left_bg = QPixmap(get_asset('player_top_left.png'))
        if not left_bg.isNull():
            painter.drawPixmap(0, 0, left_bg)
        
        # Правая часть
        right_bg = QPixmap(get_asset('player_top_right.png'))
        if not right_bg.isNull():
            painter.drawPixmap(self.width() - right_bg.width(), 0, right_bg)


class SubViewBottom(QWidget):
    """SUBVIEW svBottom - нижняя панель (346x23)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(23)
        self.init_ui()
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # svBottomLeft (286x23)
        bottom_left = QWidget()
        bottom_left.setFixedWidth(286)
        bottom_left_layout = QHBoxLayout(bottom_left)
        bottom_left_layout.setContentsMargins(63, 2, 0, 0)
        
        self.metadata_label = QLabel('Windows Media Player')
        self.metadata_label.setStyleSheet("""
            QLabel {
                color: #00FF00;
                font-family: Arial;
                font-size: 8px;
                font-weight: bold;
            }
        """)
        bottom_left_layout.addWidget(self.metadata_label)
        
        layout.addWidget(bottom_left)
        
        # svBottomMiddle (1px, тайлится)
        bottom_middle = TiledBackgroundWidget(get_asset('player_bottom_middle.png'))
        bottom_middle.setFixedWidth(1)
        layout.addWidget(bottom_middle, 1)
        
        # svBottomRight (59x23)
        bottom_right = QWidget()
        bottom_right.setFixedWidth(59)
        bottom_right_layout = QHBoxLayout(bottom_right)
        bottom_right_layout.setContentsMargins(0, 2, 10, 0)
        bottom_right_layout.addStretch()
        
        self.time_label = QLabel('00:00')
        self.time_label.setStyleSheet("""
            QLabel {
                color: #00FF00;
                font-family: Arial;
                font-size: 8px;
                font-weight: bold;
            }
        """)
        bottom_right_layout.addWidget(self.time_label)
        
        layout.addWidget(bottom_right)
    
    def set_metadata(self, text: str):
        self.metadata_label.setText(text)
    
    def set_time(self, time_str: str):
        self.time_label.setText(time_str)
    
    def paintEvent(self, event):
        """Отрисовка фона"""
        painter = QPainter(self)
        
        left_bg = QPixmap(get_asset('player_bottom_left.png'))
        if not left_bg.isNull():
            painter.drawPixmap(0, 0, left_bg)
        
        right_bg = QPixmap(get_asset('player_bottom_right.png'))
        if not right_bg.isNull():
            painter.drawPixmap(self.width() - right_bg.width(), 0, right_bg)


class EqualizerPanel(QWidget):
    """SUBVIEW svEqualizer - панель эквалайзера (334x183)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(334, 183)
        self.is_visible = False
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # svEqualizerTop (334x123)
        top_panel = QWidget()
        top_panel.setFixedHeight(123)
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(0)
        
        # Левая граница
        left_border = QWidget()
        left_border.setFixedWidth(3)
        left_border.setStyleSheet(f"background-image: url({get_asset('equalizer_pane_left.png')});")
        top_layout.addWidget(left_border)
        
        # Средняя часть с эквалайзером
        middle = QWidget()
        middle.setStyleSheet(f"background-image: url({get_asset('equalizer_pane_middle.png')});")
        top_layout.addWidget(middle, 1)
        
        # Правая граница
        right_border = QWidget()
        right_border.setFixedWidth(4)
        right_border.setStyleSheet(f"background-image: url({get_asset('equalizer_pane_right.png')});")
        top_layout.addWidget(right_border)
        
        layout.addWidget(top_panel)
        
        # svEqualizerBottom (334x60) - панель управления
        bottom_panel = QWidget()
        bottom_panel.setFixedHeight(60)
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(40, 1, 0, 0)
        bottom_layout.setSpacing(5)
        
        # Слайдер прогресса
        self.seek_slider = QSlider(Qt.Horizontal)
        self.seek_slider.setFixedHeight(13)
        self.seek_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 13px;
                background: transparent;
            }
            QSlider::handle:horizontal {
                background: transparent;
                width: 14px;
                height: 13px;
            }
            QSlider::sub-page:horizontal {
                background: transparent;
            }
        """)
        bottom_layout.addWidget(self.seek_slider)
        
        # Панель с транспортом
        transport_layout = QHBoxLayout()
        transport_layout.setContentsMargins(8, 0, 0, 0)
        
        # Кнопка Rewind
        self.rew_btn = ImageButton(
            get_asset('seekbutton_left.png'),
            get_asset('seekbutton_left_hover.png'),
            get_asset('seekbutton_left_down.png'),
            get_asset('seekbutton_left_disabled.png')
        )
        self.rew_btn.setToolTip('Перемотка назад')
        transport_layout.addWidget(self.rew_btn)
        
        # Кнопки транспорта (Play/Pause/Stop/Prev/Next/Mute)
        self.play_btn = ImageButton(
            get_asset('transports.png'),
            get_asset('transports_hover.png'),
            get_asset('transports_down.png'),
            get_asset('transports_disabled.png')
        )
        self.play_btn.setFixedSize(136, 30)
        self.play_btn.setToolTip('Воспроизвести')
        transport_layout.addWidget(self.play_btn)
        
        # Громкость
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedSize(68, 18)
        transport_layout.addWidget(self.volume_slider)
        
        transport_layout.addStretch()
        
        # Кнопка Fast Forward
        self.ffwd_btn = ImageButton(
            get_asset('seekbutton_right.png'),
            get_asset('seekbutton_right_hover.png'),
            get_asset('seekbutton_right_down.png'),
            get_asset('seekbutton_right_disabled.png')
        )
        self.ffwd_btn.setToolTip('Перемотка вперёд')
        transport_layout.addWidget(self.ffwd_btn)
        
        bottom_layout.addLayout(transport_layout)
        layout.addWidget(bottom_panel)
    
    def paintEvent(self, event):
        """Отрисовка фона"""
        painter = QPainter(self)
        
        # Левая часть
        left_bg = QPixmap(get_asset('equalizer_left.png'))
        if not left_bg.isNull():
            scaled = left_bg.scaledToHeight(60, Qt.SmoothTransformation)
            painter.drawPixmap(0, 123, scaled)
        
        # Правая часть
        right_bg = QPixmap(get_asset('equalizer_right.png'))
        if not right_bg.isNull():
            scaled = right_bg.scaledToHeight(60, Qt.SmoothTransformation)
            painter.drawPixmap(self.width() - scaled.width(), 123, scaled)


class PlaylistPanel(QWidget):
    """SUBVIEW svPlaylist - панель плейлиста (263x237)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(263, 237)
        self.is_visible = False
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # svPlaylistTop (263x107)
        top_panel = QWidget()
        top_panel.setFixedHeight(107)
        top_layout = QVBoxLayout(top_panel)
        top_layout.setContentsMargins(26, 34, 0, 0)
        
        # Список плейлиста
        self.playlist = QListWidget()
        self.playlist.setStyleSheet("""
            QListWidget {
                background-color: black;
                color: white;
                border: none;
            }
            QListWidget::item:selected {
                background-color: #333;
            }
        """)
        top_layout.addWidget(self.playlist)
        
        layout.addWidget(top_panel)
        
        # Средняя часть (тайлится)
        middle = TiledBackgroundWidget(get_asset('playlist_middle.png'))
        middle.setFixedHeight(1)
        layout.addWidget(middle)
        
        # Нижняя часть
        bottom = QWidget()
        bottom.setFixedHeight(129)
        layout.addWidget(bottom)
    
    def paintEvent(self, event):
        """Отрисовка фона"""
        painter = QPainter(self)
        
        top_bg = QPixmap(get_asset('playlist_top.png'))
        if not top_bg.isNull():
            painter.drawPixmap(0, 0, top_bg)
        
        bottom_bg = QPixmap(get_asset('playlist_bottom.png'))
        if not bottom_bg.isNull():
            painter.drawPixmap(0, 108, bottom_bg)


class SubViewMain(QWidget):
    """SUBVIEW svMain - основная область (left=250, top=0)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # svTop (346x33)
        self.top_panel = SubViewTop()
        layout.addWidget(self.top_panel)
        
        # svMiddle - область с визуализатором
        middle_wrapper = QWidget()
        middle_layout = QHBoxLayout(middle_wrapper)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        middle_layout.setSpacing(0)
        
        # Левая граница (19px)
        left_border = TiledBackgroundWidget(get_asset('player_left.png'))
        left_border.setFixedWidth(19)
        middle_layout.addWidget(left_border)
        
        # Область визуализации (320x240, но растягивается)
        self.visualizer = VisualizerWidget()
        self.visualizer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        middle_layout.addWidget(self.visualizer)
        
        # Правая граница (7px)
        right_border = TiledBackgroundWidget(get_asset('player_right.png'))
        right_border.setFixedWidth(7)
        middle_layout.addWidget(right_border)
        
        layout.addWidget(middle_wrapper, 1)  # stretch
        
        # svBottom (346x23)
        self.bottom_panel = SubViewBottom()
        layout.addWidget(self.bottom_panel)


class AudioPlayer(QMainWindow):
    """
    VIEW vPlayer - главное окно (859x468, min 859x468)
    Точная реализация структуры из Corona.wms
    """

    def __init__(self):
        super().__init__()
        self.current_file = None
        self.media_player = QMediaPlayer()
        self.g_paneCurrent = 0  # PANE_VIS = 0, PANE_VID = 1
        self.g_vidIsRunning = False
        self.g_playlistIsVisible = False
        self.g_equalizerIsVisible = False
        
        self.init_ui()
        self.setup_media_player()

    def init_ui(self):
        """Инициализация интерфейса согласно Corona.wms"""
        self.setWindowTitle('Аудиоплеер - Windows Media Player 9 Style')
        self.setGeometry(100, 100, 859, 468)
        self.setMinimumSize(859, 468)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        
        # Фон прозрачный (backgroundColor="none")
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ECE9D8;
            }
        """)

        # Центральный виджет
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #ECE9D8;")
        self.setCentralWidget(central_widget)

        # Главный layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        central_widget.setLayout(main_layout)

        # Создание меню
        self.create_menu_bar()

        # SUBVIEW svMain (left=250, top=0)
        self.sv_main = SubViewMain()
        self.sv_main.top_panel.open_file.connect(self.open_file)
        self.sv_main.top_panel.toggle_playlist.connect(self.toggle_playlist)
        self.sv_main.top_panel.minimize_clicked.connect(self.showMinimized)
        main_layout.addSpacing(250)  # left offset
        main_layout.addWidget(self.sv_main, 1)  # stretch

        # SUBVIEW svEqualizer (left=262, top=161) - выдвижная панель
        self.sv_equalizer = EqualizerPanel()
        self.sv_equalizer.seek_slider.sliderMoved.connect(self.set_position)
        self.sv_equalizer.volume_slider.valueChanged.connect(self.set_volume)
        self.sv_equalizer.play_btn.clicked.connect(self.play_audio)
        self.sv_equalizer.rew_btn.clicked.connect(self.rewind)
        self.sv_equalizer.ffwd_btn.clicked.connect(self.fast_forward)
        self.sv_equalizer.hide()  # Скрыта по умолчанию
        main_layout.addWidget(self.sv_equalizer)

        # SUBVIEW svPlaylist (left=250, top=33) - выдвижная панель
        self.sv_playlist = PlaylistPanel()
        self.sv_playlist.hide()  # Скрыта по умолчанию

    def create_menu_bar(self):
        """Создание меню приложения"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #ECE9D8;
                color: #000000;
            }
            QMenuBar::item:selected {
                background-color: #D4D0C8;
            }
            QMenu {
                background-color: #ECE9D8;
                color: #000000;
            }
            QMenu::item:selected {
                background-color: #316AC5;
                color: white;
            }
        """)

        file_menu = menubar.addMenu('Файл')
        open_action = file_menu.addAction('Открыть')
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addSeparator()
        exit_action = file_menu.addAction('Выход')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)

        play_menu = menubar.addMenu('Воспроизведение')
        play_action = play_menu.addAction('Воспроизвести/Пауза')
        play_action.setShortcut('Space')
        play_action.triggered.connect(self.play_audio)
        stop_action = play_menu.addAction('Стоп')
        stop_action.triggered.connect(self.stop_audio)

        view_menu = menubar.addMenu('Вид')
        eq_action = view_menu.addAction('Эквалайзер')
        eq_action.triggered.connect(self.toggle_equalizer)
        playlist_action = view_menu.addAction('Плейлист')
        playlist_action.triggered.connect(self.toggle_playlist)

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
        """Открытие аудиофайла (OpenMedia)"""
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
                
                filename = Path(file_path).stem
                self.sv_main.bottom_panel.set_metadata(filename)
                
                self.media_player.play()
                
        except Exception as e:
            QMessageBox.critical(
                self,
                'Ошибка',
                f'Не удалось открыть файл:\n{str(e)}'
            )

    def play_audio(self):
        """Воспроизведение/пауза"""
        try:
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.media_player.pause()
            else:
                self.media_player.play()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка воспроизведения:\n{str(e)}')

    def stop_audio(self):
        """Остановка воспроизведения"""
        try:
            self.media_player.stop()
            self.sv_main.visualizer.stop()
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка остановки:\n{str(e)}')

    def rewind(self):
        """Перемотка назад"""
        pos = self.media_player.position()
        self.media_player.setPosition(max(0, pos - 10000))

    def fast_forward(self):
        """Перемотка вперёд"""
        pos = self.media_player.position()
        duration = self.media_player.duration()
        self.media_player.setPosition(min(duration, pos + 10000))

    def set_position(self, position):
        """Установка позиции воспроизведения"""
        try:
            self.media_player.setPosition(position)
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f'Ошибка установки позиции:\n{str(e)}')

    def set_volume(self, value):
        """Установка громкости"""
        self.media_player.setVolume(value)

    def position_changed(self, position):
        """Обновление позиции слайдера"""
        self.sv_equalizer.seek_slider.setValue(position)
        
        seconds = position // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        self.sv_main.bottom_panel.set_time(f'{minutes:02d}:{seconds:02d}')

    def duration_changed(self, duration):
        """Обновление длительности слайдера"""
        self.sv_equalizer.seek_slider.setRange(0, duration)

    def state_changed(self, state):
        """Обработка изменения состояния плеера (OnPlayStateChange)"""
        if state == QMediaPlayer.PlayingState:
            self.sv_main.visualizer.start()
        elif state == QMediaPlayer.PausedState:
            self.sv_main.visualizer.stop()
        elif state == QMediaPlayer.StoppedState:
            self.sv_main.visualizer.stop()
            self.sv_main.bottom_panel.set_time('00:00')

    def toggle_playlist(self):
        """TogglePlaylist - переключение видимости плейлиста"""
        self.g_playlistIsVisible = not self.g_playlistIsVisible
        if self.g_playlistIsVisible:
            self.sv_playlist.show()
            self.sv_main.top_panel.playlist_btn.set_toggled(True)
        else:
            self.sv_playlist.hide()
            self.sv_main.top_panel.playlist_btn.set_toggled(False)

    def toggle_equalizer(self):
        """ToggleEqualizer - переключение видимости эквалайзера"""
        self.g_equalizerIsVisible = not self.g_equalizerIsVisible
        if self.g_equalizerIsVisible:
            self.sv_equalizer.show()
        else:
            self.sv_equalizer.hide()

    def handle_error(self, error):
        """Обработка ошибок медиаплеера"""
        error_string = self.media_player.errorString()
        if error_string:
            QMessageBox.critical(self, 'Ошибка медиаплеера', f'Ошибка: {error_string}')

    def show_about(self):
        """Показ информации о программе"""
        QMessageBox.about(
            self,
            'О программе',
            'Аудиоплеер в стиле Windows Media Player 9\n\n'
            'Реализация структуры Corona.wms на PyQt5\n'
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
    app.setStyle('Fusion')
    
    player = AudioPlayer()
    player.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

"""
Аудиоплеер на PyQt5
Базовая реализация с меню, кнопками управления и обработкой исключений
"""

import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QLabel,
                             QMessageBox, QMenuBar, QStatusBar, QSlider)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from ui.title_bar import TitleBar


class AudioPlayer(QMainWindow):
    """Главное окно аудиоплеера"""

    def __init__(self):
        super().__init__()
        self.current_file = None
        self.media_player = QMediaPlayer()
        self.init_ui()
        self.setup_media_player()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        # Убираем стандартную рамку окна для кастомной шапки
        # Оставляем возможность изменения размера окна
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setWindowTitle('Аудиоплеер')
        self.setGeometry(100, 100, 600, 400)
        # Минимальный размер окна
        self.setMinimumSize(400, 300)

        # Главный контейнер с рамкой
        main_container = QWidget()
        main_container.setStyleSheet("""
            QWidget {
                border: 1px solid #0020C8;
                background-color: #ECE9D8;
            }
        """)
        self.setCentralWidget(main_container)

        # Главный layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_container.setLayout(main_layout)

        # Кастомная шапка
        self.title_bar = TitleBar(self, 'Аудиоплеер')
        main_layout.addWidget(self.title_bar)

        # Контейнер для содержимого
        content_widget = QWidget()
        content_widget.setStyleSheet("""
            QWidget {
                background-color: #ECE9D8;
            }
        """)
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)

        # Создание меню (скрыто, но доступно через контекстное меню или хоткеи)
        self.create_menu_bar()
        self.menuBar().hide()  # Скрываем стандартное меню

        # Информация о текущем файле
        self.file_label = QLabel('Файл не выбран')
        self.file_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.file_label)

        # Слайдер прогресса
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 0)
        self.progress_slider.sliderMoved.connect(self.set_position)
        content_layout.addWidget(self.progress_slider)

        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.play_button = QPushButton('Play')
        self.play_button.clicked.connect(self.play_audio)
        buttons_layout.addWidget(self.play_button)

        self.pause_button = QPushButton('Pause')
        self.pause_button.clicked.connect(self.pause_audio)
        buttons_layout.addWidget(self.pause_button)

        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_audio)
        buttons_layout.addWidget(self.stop_button)

        content_layout.addLayout(buttons_layout)
        content_layout.addStretch()

        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Готов')

    def create_menu_bar(self):
        """Создание меню приложения"""
        menubar = self.menuBar()

        # Меню "Файл"
        file_menu = menubar.addMenu('Файл')
        
        open_action = file_menu.addAction('Открыть')
        open_action.triggered.connect(self.open_file)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction('Выход')
        exit_action.triggered.connect(self.close)

        # Меню "Вид"
        view_menu = menubar.addMenu('Вид')
        # Здесь можно добавить настройки вида в будущем

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
                'Audio Files (*.mp3 *.wav *.ogg *.m4a);;All Files (*)'
            )

            if file_path:
                self.current_file = file_path
                url = QUrl.fromLocalFile(file_path)
                content = QMediaContent(url)
                self.media_player.setMedia(content)
                self.file_label.setText(f'Файл: {file_path.split("/")[-1]}')
                self.status_bar.showMessage('Файл загружен')
        except Exception as e:
            QMessageBox.critical(
                self,
                'Ошибка',
                f'Не удалось открыть файл:\n{str(e)}'
            )

    def play_audio(self):
        """Воспроизведение аудио"""
        try:
            if self.media_player.state() == QMediaPlayer.PlayingState:
                self.media_player.pause()
                self.play_button.setText('Play')
            else:
                self.media_player.play()
                self.play_button.setText('Playing')
                self.status_bar.showMessage('Воспроизведение')
        except Exception as e:
            QMessageBox.critical(
                self,
                'Ошибка',
                f'Ошибка воспроизведения:\n{str(e)}'
            )

    def pause_audio(self):
        """Пауза воспроизведения"""
        try:
            self.media_player.pause()
            self.play_button.setText('Play')
            self.status_bar.showMessage('Пауза')
        except Exception as e:
            QMessageBox.critical(
                self,
                'Ошибка',
                f'Ошибка паузы:\n{str(e)}'
            )

    def stop_audio(self):
        """Остановка воспроизведения"""
        try:
            self.media_player.stop()
            self.play_button.setText('Play')
            self.status_bar.showMessage('Остановлено')
        except Exception as e:
            QMessageBox.critical(
                self,
                'Ошибка',
                f'Ошибка остановки:\n{str(e)}'
            )

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

    def position_changed(self, position):
        """Обновление позиции слайдера"""
        self.progress_slider.setValue(position)

    def duration_changed(self, duration):
        """Обновление длительности слайдера"""
        self.progress_slider.setRange(0, duration)

    def state_changed(self, state):
        """Обработка изменения состояния плеера"""
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText('Playing')
        elif state == QMediaPlayer.PausedState:
            self.play_button.setText('Play')
        elif state == QMediaPlayer.StoppedState:
            self.play_button.setText('Play')

    def handle_error(self, error):
        """Обработка ошибок медиаплеера"""
        error_string = self.media_player.errorString()
        QMessageBox.critical(
            self,
            'Ошибка медиаплеера',
            f'Ошибка: {error_string}'
        )
        self.status_bar.showMessage('Ошибка воспроизведения')

    def show_about(self):
        """Показ информации о программе"""
        QMessageBox.about(
            self,
            'О программе',
            'Аудиоплеер на PyQt5\n\n'
            'Базовая версия с поддержкой воспроизведения аудиофайлов.'
        )


def main():
    """Точка входа в приложение"""
    app = QApplication(sys.argv)
    
    player = AudioPlayer()
    player.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()


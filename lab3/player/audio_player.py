"""Модуль для воспроизведения аудио"""
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
from pathlib import Path


class AudioPlayer:
    """Класс для управления воспроизведением аудио"""
    
    # Поддерживаемые форматы
    SUPPORTED_FORMATS = ['.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac']
    
    def __init__(self):
        """Инициализация аудиоплеера"""
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # Текущий файл
        self.current_file = None
        
    def load_file(self, file_path: str | Path):
        """Загрузка аудиофайла"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
            
        if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Неподдерживаемый формат: {file_path.suffix}")
            
        self.current_file = file_path
        url = QUrl.fromLocalFile(str(file_path.absolute()))
        self.media_player.setSource(url)
        
    def play(self):
        """Воспроизведение"""
        if self.current_file:
            self.media_player.play()
            
    def pause(self):
        """Пауза"""
        self.media_player.pause()
        
    def stop(self):
        """Остановка"""
        self.media_player.stop()
        
    def set_volume(self, volume: float):
        """Установка громкости (0.0 - 1.0)"""
        self.audio_output.setVolume(max(0.0, min(1.0, volume)))
        
    def get_duration(self) -> int:
        """Получить длительность в миллисекундах"""
        return self.media_player.duration()
        
    def get_position(self) -> int:
        """Получить текущую позицию в миллисекундах"""
        return self.media_player.position()
        
    def set_position(self, position: int):
        """Установить позицию в миллисекундах"""
        self.media_player.setPosition(position)
        
    def is_playing(self) -> bool:
        """Проверка, играет ли сейчас"""
        return self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState


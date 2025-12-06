"""Простой аудиовизуализатор.

Основан на идеях из open-source проекта Realtime_PyAudio_FFT
(help/audio-viz/Realtime_PyAudio_FFT-master): FFT-аналитика потока
и отрисовка спектра. Здесь оставлена упрощённая версия для встраивания
в PyQt UI; декодер аудио через QtMultimedia встроен здесь же.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Tuple

import numpy as np
from PyQt6.QtCore import Qt, QRect, QEventLoop, QUrl
from PyQt6.QtGui import QColor, QPainter, QPen, QMovie
from PyQt6.QtWidgets import QWidget
from PyQt6.QtMultimedia import QAudioBuffer, QAudioDecoder, QAudioFormat

from .config import config


def buffer_to_mono(buffer: QAudioBuffer) -> np.ndarray:
    """Конвертация QAudioBuffer -> mono float32 [-1..1]."""
    fmt: QAudioFormat = buffer.format()
    channels = fmt.channelCount()
    if channels <= 0:
        return np.array([], dtype=np.float32)

    sample_format = fmt.sampleFormat()
    if sample_format == QAudioFormat.SampleFormat.Float:
        dtype = np.float32
        scale = 1.0
    elif sample_format == QAudioFormat.SampleFormat.Int16:
        dtype = np.int16
        scale = 32768.0
    elif sample_format == QAudioFormat.SampleFormat.Int32:
        dtype = np.int32
        scale = float(2**31)
    elif sample_format == QAudioFormat.SampleFormat.UInt8:
        dtype = np.uint8
        scale = 128.0
    else:
        # Неподдерживаемый формат
        return np.array([], dtype=np.float32)

    data = buffer.data()
    arr = np.frombuffer(data, dtype=dtype)
    if channels > 1:
        arr = arr.reshape(-1, channels).mean(axis=1)
    if scale != 1.0:
        arr = arr.astype(np.float32) / scale
    return arr.astype(np.float32)


def decode_file_to_mono(file_path: str | Path) -> Tuple[np.ndarray, int]:
    """Синхронно декодирует файл в моно массив и sample rate.

    Возвращает (data, samplerate). В случае ошибок — (пустой массив, 0).
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return np.array([], dtype=np.float32), 0

    decoder = QAudioDecoder()
    decoder.setSource(QUrl.fromLocalFile(str(file_path)))

    buffers = []
    loop = QEventLoop()

    def on_ready():
        buf = decoder.read()
        if buf.isValid():
            buffers.append(buf)

    def on_finished():
        loop.quit()

    decoder.bufferReady.connect(on_ready)
    decoder.finished.connect(on_finished)

    decoder.start()
    loop.exec()

    if not buffers:
        return np.array([], dtype=np.float32), 0

    fmt = buffers[0].format()
    samplerate = fmt.sampleRate()
    mono_chunks = [buffer_to_mono(b) for b in buffers]
    data = np.concatenate(mono_chunks) if mono_chunks else np.array([], dtype=np.float32)
    return data, samplerate


class VisualizerWidget(QWidget):
    """Мини-визуализатор со сменой режимов (2D/3D)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.mode = "wave"  # дефолтный третий режим (осциллограф)
        self.scale_percent = 100
        self.spectrum: np.ndarray | None = None
        self.time_domain: np.ndarray | None = None
        self._prev_spec: np.ndarray | None = None
        self._prev_wave: np.ndarray | None = None
        self._ema_peak: float = 1e-3
        self.is_playing: bool = False
        self.cat_movie = QMovie(str(config.cat_gif))
        if self.cat_movie.isValid():
            self.cat_movie.setCacheMode(QMovie.CacheMode.CacheAll)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_mode(self, mode: str):
        """Переключение режима визуализации."""
        if mode not in ("2d", "3d", "wave"):
            return
        self.mode = mode
        self._sync_movie_state()
        self.update()

    def set_scale(self, scale_percent: int):
        """Масштабирование и позиционирование под текущий масштаб окна."""
        self.scale_percent = scale_percent
        k = scale_percent / 100.0
        x = int(config.viz_x * k)
        y = int(config.viz_y * k)
        w = int(config.viz_width * k)
        h = int(config.viz_height * k)
        self.setGeometry(x, y, w, h)
        self.update()

    def feed_features(
        self,
        spectrum: Sequence[float] | np.ndarray | None = None,
        waveform: Sequence[float] | np.ndarray | None = None,
    ):
        """Приём данных извне (FFT + временная область)."""
        if spectrum is not None:
            spec = np.asarray(spectrum, dtype=float)
            # автогейн по эксп. максимуму
            peak = float(np.max(spec)) if spec.size else 0.0
            decay = config.viz_autogain_decay
            self._ema_peak = max(peak, self._ema_peak * decay, 1e-6)
            spec = spec / self._ema_peak
            # сглаживание спектра
            alpha = config.viz_spec_smooth_alpha
            if self._prev_spec is None or self._prev_spec.shape != spec.shape:
                self._prev_spec = spec
            else:
                spec = alpha * spec + (1 - alpha) * self._prev_spec
                self._prev_spec = spec
            self.spectrum = spec

        if waveform is not None:
            wave = np.asarray(waveform, dtype=float)
            alpha_w = config.viz_wave_smooth_alpha
            if self._prev_wave is None or self._prev_wave.shape != wave.shape:
                self._prev_wave = wave
            else:
                wave = alpha_w * wave + (1 - alpha_w) * self._prev_wave
                self._prev_wave = wave
            self.time_domain = wave
        self.update()

    def set_playing(self, is_playing: bool):
        """Установить состояние воспроизведения (для gif режима)."""
        self.is_playing = is_playing
        self._sync_movie_state()
        self.update()

    def _sync_movie_state(self):
        """Старт/стоп анимации кота в зависимости от режима и воспроизведения."""
        if self.mode == "2d" and self.is_playing and self.cat_movie.isValid():
            if self.cat_movie.state() != QMovie.MovieState.Running:
                self.cat_movie.start()
        else:
            if self.cat_movie.state() != QMovie.MovieState.NotRunning:
                self.cat_movie.stop()

    # ---- Rendering ----
    def paintEvent(self, event):
        painter = QPainter(self)
        self._paint_background(painter)
        if self.mode == "2d":
            self._paint_cat(painter)
        elif self.mode == "3d":
            self._paint_rings(painter)
        else:
            self._paint_wave(painter)
        painter.end()

    def _paint_background(self, painter: QPainter):
        painter.fillRect(self.rect(), QColor(config.viz_background))

    def _paint_rings(self, painter: QPainter):
        """Упрощённый 3D-like кольцевой эффект на основе волновой формы."""
        data = self._get_waveform()
        if data.size == 0:
            return
        rect = self.rect()
        cx = rect.center().x()
        cy = rect.center().y()
        radius_base = min(rect.width(), rect.height()) * 0.1
        base_color = QColor(config.viz_color)
        pen = QPen(base_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        samples = min(len(data), 64)
        for idx in range(samples):
            val = data[int(idx * len(data) / samples)]
            amp = (val + 1.0) * 0.5  # normalize -1..1 -> 0..1
            radius = radius_base + amp * min(rect.width(), rect.height()) * 0.35
            alpha = int(150 + 100 * amp)
            ring_color = QColor(base_color)
            ring_color.setAlpha(alpha)
            pen.setColor(ring_color)
            painter.setPen(pen)
            painter.drawEllipse(
                int(cx - radius),
                int(cy - radius),
                int(radius * 2),
                int(radius * 2),
            )

    def _paint_cat(self, painter: QPainter):
        """Рисуем gif с котом по центру, когда играет музыка; иначе фон."""
        if not (self.is_playing and self.cat_movie.isValid()):
            return
        frame = self.cat_movie.currentPixmap()
        if frame.isNull():
            return
        rect = self.rect()
        # масштабируем в разумных пределах, не выходя за канвас
        frame_scaled = frame.scaled(
            rect.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        x = rect.x() + (rect.width() - frame_scaled.width()) // 2
        y = rect.y() + (rect.height() - frame_scaled.height()) // 2
        painter.drawPixmap(x, y, frame_scaled)

    def _paint_wave(self, painter: QPainter):
        """Линейный осциллограф по волновой форме."""
        data = self._get_waveform()
        if data.size == 0:
            return
        rect = self.rect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        base_color = QColor(config.viz_color)
        base_color.setAlpha(200)
        pen = QPen(base_color)
        pen.setWidth(2)
        painter.setPen(pen)
        # нормализация и масштаб
        y_mid = rect.center().y()
        amp = rect.height() * 0.4
        n = len(data)
        for i in range(n - 1):
            x1 = rect.x() + rect.width() * (i / (n - 1))
            x2 = rect.x() + rect.width() * ((i + 1) / (n - 1))
            y1 = y_mid - data[i] * amp
            y2 = y_mid - data[i + 1] * amp
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

    def _get_spectrum(self) -> np.ndarray:
        if self.spectrum is None:
            return np.array([])
        return self.spectrum

    def _get_waveform(self) -> np.ndarray:
        if self.time_domain is None:
            return np.array([])
        return self.time_domain



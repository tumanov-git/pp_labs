from __future__ import annotations

from pathlib import Path
import logging


logger = logging.getLogger(__name__)


def trim_logs(file_path: Path, max_lines: int) -> None:
	"""Обрезать лог-файл, оставив последние max_lines строк.

	Без внешних библиотек; если файла нет — тихо выходим.
	"""
	try:
		if max_lines <= 0:
			return
		file_path = file_path.expanduser().resolve()
		if not file_path.exists():
			return
		# Читаем все строки; для типичного объёма логов этого достаточно.
		with file_path.open("r", encoding="utf-8", errors="ignore") as f:
			lines = f.readlines()
		if len(lines) <= max_lines:
			return
		# Сохраняем только хвост
		tail = lines[-max_lines:]
		with file_path.open("w", encoding="utf-8") as f:
			f.writelines(tail)
		logger.debug("Лог обрезан до последних %s записей", max_lines)
	except Exception:  # noqa: BLE001
		# Не мешаем основному потоку работы
		logger.debug("Не удалось обрезать лог %s", file_path, exc_info=True)

def update_weather_stats(file_path: Path, instance: str, enabled: bool) -> None:
	"""Обновить счётчик погоды в .cache/weather_stats.json.

	- При enabled=False ничего не делает.
	- Создаёт файл при отсутствии.
	- Агрегирует fog_* в ключ 'fog'.
	"""
	if not enabled:
		return
	try:
		file_path = file_path.expanduser().resolve()
		file_path.parent.mkdir(parents=True, exist_ok=True)

		# Базовая структура
		defaults = {
			"clear": 0,
			"cloudy": 0,
			"overcast": 0,
			"rain": 0,
			"heavy_rain": 0,
			"thunderstorm": 0,
			"fog": 0,
		}

		# Читаем существующие данные (если есть)
		data = defaults.copy()
		if file_path.exists():
			try:
				import json as _json
				with file_path.open("r", encoding="utf-8") as f:
					raw = _json.load(f) or {}
				if isinstance(raw, dict):
					for k, v in raw.items():
						if isinstance(k, str) and isinstance(v, int):
							data[k] = v
			except Exception:
				logger.debug("Не удалось прочитать статистику погоды, будет пересоздана", exc_info=True)

		# Агрегируем инстанс
		key = "fog" if instance.startswith("fog") else instance
		data[key] = int(data.get(key, 0)) + 1

		# Запись файла
		try:
			import json as _json
			with file_path.open("w", encoding="utf-8") as f:
				_json.dump(data, f, ensure_ascii=False, indent=2)
			logger.info("✅ Weather stats updated: %s -> %s total", key, data[key])
		except Exception:
			logger.debug("Не удалось записать статистику погоды", exc_info=True)
	except Exception:
		logger.debug("Ошибка обновления статистики погоды", exc_info=True)

def rebuild_weather_stats_from_log(log_file: Path, out_file: Path) -> None:
	"""Полностью пересчитать статистику по всему файлу weather.log."""
	try:
		log_file = log_file.expanduser().resolve()
		if not log_file.exists():
			logger.error("Файл лога не найден: %s", log_file)
			return

		# Базовые ключи
		counts = {
			"clear": 0,
			"cloudy": 0,
			"overcast": 0,
			"rain": 0,
			"heavy_rain": 0,
			"thunderstorm": 0,
			"fog": 0,
		}

		with log_file.open("r", encoding="utf-8", errors="ignore") as f:
			for line in f:
				# Ищем только финальные строки выбора инстанса
				# Пример: "Final phase=day instance=cloudy (mode=weather_no_fog fog_applied=False)"
				if "Final" in line and " instance=" in line:
					try:
						part = line.split(" instance=", 1)[1]
						# instance до пробела или закрывающей скобки
						end_idx = part.find(" ")
						if end_idx == -1:
							end_idx = part.find(")")
						if end_idx == -1:
							inst = part.strip()
						else:
							inst = part[:end_idx].strip()
						key = "fog" if inst.startswith("fog") else inst
						if key in counts:
							counts[key] += 1
					except Exception:
						continue

		out_file = out_file.expanduser().resolve()
		out_file.parent.mkdir(parents=True, exist_ok=True)

		import json as _json
		with out_file.open("w", encoding="utf-8") as f:
			_json.dump(counts, f, ensure_ascii=False, indent=2)
		logger.info("✅ Weather stats rebuilt from log: %s", log_file)
	except Exception:
		logger.error("Не удалось пересчитать статистику из лога", exc_info=True)



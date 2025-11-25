import re
import sys
from pathlib import Path
from typing import Iterable
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

ROMAN_PATTERN = re.compile(
    r"\bM{0,3}(CM|CD|D?C{0,3})"
    r"(XC|XL|L?X{0,3})"
    r"(IX|IV|V?I{0,3})\b"
)


def is_valid_roman(value: str) -> bool:
    return bool(ROMAN_PATTERN.fullmatch(value.strip().upper()))


def _iter_roman(text: str) -> Iterable[str]:
    for match in ROMAN_PATTERN.finditer(text.upper()):
        yield match.group()


def _read_url(url: str) -> str:
    with urlopen(url) as response:
        encoding = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(encoding, errors="replace")


def _read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _ask_mode() -> str:
    print("Выберите режим работы:")
    print("1 — Проверить введённое число")
    print("2 — Найти числа на веб-странице")
    print("3 — Найти числа в локальном файле")
    return input("Ваш выбор: ").strip()


def _handle_single_input() -> None:
    value = input("Введите римское число: ").strip()
    print("Корректно" if is_valid_roman(value) else "Некорректно")


def _handle_text_source(source: str) -> None:
    matches = list(_iter_roman(source))
    if matches:
        print("Найденные римские числа:")
        for value in matches:
            print(f"- {value}")
    else:
        print("Совпадений не найдено.")


def _handle_url_input() -> None:
    url = input("Введите URL: ").strip()
    try:
        text = _read_url(url)
    except (HTTPError, URLError, OSError) as exc:
        print(f"Не удалось загрузить данные: {exc}")
        return
    _handle_text_source(text)


def _handle_file_input() -> None:
    path = Path(input("Введите путь к файлу: ").strip())
    try:
        text = _read_file(path)
    except OSError as exc:
        print(f"Не удалось открыть файл: {exc}")
        return
    _handle_text_source(text)


def main() -> None:
    choice = _ask_mode()
    if choice == "1":
        _handle_single_input()
    elif choice == "2":
        _handle_url_input()
    elif choice == "3":
        _handle_file_input()
    else:
        print("Неизвестный режим.")
        sys.exit(1)


if __name__ == "__main__":
    main()


import ipaddress
import re
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

ROMAN_PATTERN = re.compile(
    r"\bM{0,3}(CM|CD|D?C{0,3})"
    r"(XC|XL|L?X{0,3})"
    r"(IX|IV|V?I{0,3})\b"
)
HOSTNAME_PATTERN = re.compile(
    r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}",
    re.IGNORECASE,
)
ALLOWED_SCHEMES = {"http", "https"}


def is_valid_roman(value: str) -> bool:
    """Возвращает True, если строка — корректное римское число (без учёта регистра)."""
    return bool(ROMAN_PATTERN.fullmatch(value.strip().upper()))


def _extract_text_from_html(html: str) -> str:
    """Удаляет теги без текста и возвращает очищенный текст."""
    soup = BeautifulSoup(html, "html.parser")
    for script in soup(["script", "style", "meta", "link", "noscript"]):
        script.decompose()
    return soup.get_text(separator=" ", strip=True)


def _iter_roman(text: str) -> Iterable[str]:
    """Генерирует римские числа в верхнем регистре, отбрасывая невалидные совпадения."""
    if not text:
        return
    upper_text = text.upper()
    for match in ROMAN_PATTERN.finditer(upper_text):
        value = match.group(0)
        if value and is_valid_roman(value):
            yield value


def _is_valid_hostname(hostname: str) -> bool:
    """Возвращает True для корректных доменов, IP-адресов или localhost."""
    if not hostname:
        return False
    if hostname == "localhost":
        return True
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        pass
    if not HOSTNAME_PATTERN.fullmatch(hostname):
        return False
    return "." in hostname


def _normalize_url(url: str) -> str:
    """Возвращает нормализованный HTTPS/HTTP URL либо пустую строку при ошибке."""
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlparse(raw)
    except ValueError:
        return ""
    if not parsed.scheme:
        raw = f"https://{raw}"
        try:
            parsed = urlparse(raw)
        except ValueError:
            return ""
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        return ""
    if not parsed.netloc:
        return ""
    hostname = parsed.hostname or ""
    if not _is_valid_hostname(hostname):
        return ""
    return parsed.geturl()


def _read_url(url: str) -> str:
    """Загружает страницу, валидирует ошибки и возвращает очищенный текст."""
    normalized = _normalize_url(url)
    if not normalized:
        raise ValueError("Некорректный URL")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,"
            "image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    try:
        response = requests.get(normalized, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()
    except requests.HTTPError as e:
        if response.status_code == 401:
            raise requests.RequestException("Сайт требует авторизацию. Доступ запрещён.")
        elif response.status_code == 403:
            raise requests.RequestException("Доступ к сайту запрещён. Сайт блокирует запросы.")
        elif response.status_code == 404:
            raise requests.RequestException("Страница не найдена.")
        else:
            raise
    response.encoding = response.apparent_encoding or "utf-8"
    html_content = response.text
    return _extract_text_from_html(html_content)


def _read_file(path: Path) -> str:
    """Читает и возвращает содержимое локального файла."""
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
    matches = list(dict.fromkeys(_iter_roman(source)))
    if matches:
        print(", ".join(matches))
    else:
        print("Римских чисел не найдено")


def _handle_url_input() -> None:
    url = input("Введите URL: ").strip()
    try:
        text = _read_url(url)
    except (ValueError, requests.RequestException, OSError) as exc:
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


"""
Иерархия исключений системы курорта.
"""


class ResortError(Exception):
    """Базовое исключение для всех ошибок системы."""
    pass


class EntityNotFoundError(ResortError):
    """Сущность не найдена (CRUD-операции по несуществующему ID)."""
    pass


class ValidationError(ResortError):
    """Невалидные входные данные (некорректные значения, даты и т.п.)."""
    pass


class StorageError(ResortError):
    """Ошибка работы с хранилищем (чтение/запись, парсинг, ввод-вывод)."""
    pass


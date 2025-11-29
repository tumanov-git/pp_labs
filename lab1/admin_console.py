from datetime import datetime
from typing import Optional
import os

from exceptions import EntityNotFoundError, ValidationError, StorageError
from models import ContactInfo, Guest, StaffMember, Location, Service, TimeSlot, Booking
from storage import ResortStorage

# --- Простое состояние файла данных ---
FILE_PATH: Optional[str] = None  # последний загруженный/сохранённый путь
FILE_FORMAT: Optional[str] = None  # 'json' | 'xml' | None
DIRTY: bool = False  # есть несохранённые изменения


def mark_dirty() -> None:
    global DIRTY
    DIRTY = True


def set_loaded(path: str, fmt: str) -> None:
    global FILE_PATH, FILE_FORMAT, DIRTY
    FILE_PATH = path
    FILE_FORMAT = fmt.lower()
    DIRTY = False


def set_saved(path: str, fmt: str) -> None:
    global FILE_PATH, FILE_FORMAT, DIRTY
    FILE_PATH = path
    FILE_FORMAT = fmt.lower()
    DIRTY = False


def current_state_text() -> str:
    src = FILE_PATH if FILE_PATH else "-"
    fmt = FILE_FORMAT.upper() if FILE_FORMAT else "-"
    if FILE_PATH is None and not DIRTY:
        state = "новая (в памяти)"
    elif DIRTY:
        state = "несохранённые изменения"
    else:
        state = "сохранено"
    return f"Источник: {src} | Формат: {fmt} | Состояние: {state}"


def clear_screen() -> None:
    # Самый быстрый вариант: ANSI-очистка и перенос курсора в (0,0)
    print("\033[2J\033[H", end="")


def prompt(message: str) -> str:
    return input(message).strip()


def prompt_optional(message: str) -> Optional[str]:
    value = input(message).strip()
    return value if value != "" else None


def prompt_int(message: str) -> int:
    while True:
        value = input(message).strip()
        try:
            return int(value)
        except ValueError:
            print("Введите целое число.")


def prompt_float(message: str) -> float:
    while True:
        value = input(message).strip()
        try:
            return float(value)
        except ValueError:
            print("Введите число (можно с точкой).")


def prompt_datetime(message: str) -> datetime:
    while True:
        value = input(message + " (формат YYYY-MM-DD HH:MM): ").strip()
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M")
        except ValueError:
            print("Некорректный формат даты/времени.")

# --- Валидации ввода ---
import re
ID_PATTERNS = {
    "guest": re.compile(r"^G\d{3}$"),
    "staff": re.compile(r"^S\d{3}$"),
    "location": re.compile(r"^L\d{3}$"),
    "service": re.compile(r"^SRV\d{3}$"),
    "booking": re.compile(r"^B\d{3}$"),
}
NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁё\s]+$")
EMAIL_RE = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
PHONE_RE = re.compile(r"^\+?\d+$")


def prompt_id(entity: str, label: str) -> str:
    pattern = ID_PATTERNS[entity]
    while True:
        value = prompt(f"{label}: ")
        if not value:
            print("✗ Поле обязательно.")
            continue
        if not pattern.match(value):
            print("✗ Неверный формат ID.")
            continue
        return value


def prompt_name(label: str) -> str:
    while True:
        value = prompt(f"{label}: ")
        if not value:
            print("✗ Поле обязательно.")
            continue
        if not NAME_RE.match(value):
            print("✗ Имя: только буквы и пробелы.")
            continue
        return value


def prompt_email() -> str:
    while True:
        value = prompt("Email: ")
        if not value:
            print("✗ Email обязателен.")
            continue
        if not EMAIL_RE.match(value):
            print("✗ Неверный формат email.")
            continue
        return value


def prompt_phone() -> str:
    while True:
        value = prompt("Телефон: ")
        if not value:
            print("✗ Телефон обязателен.")
            continue
        if not PHONE_RE.match(value):
            print("✗ Телефон: только + и цифры.")
            continue
        return value


def create_guest(storage: ResortStorage) -> None:
    while True:
        try:
            guest_id = prompt_id("guest", "ID гостя (GNNN)")
            try:
                storage.get_guest_by_id(guest_id)
                print("✗ Гость с таким ID уже существует.")
                continue
            except EntityNotFoundError:
                pass
            name = prompt_name("Имя гостя")
            email = prompt_email()
            phone = prompt_phone()
            address = prompt_optional("Адрес (опционально): ")
            arrival_str = prompt_optional("Дата/время прибытия YYYY-MM-DD HH:MM (опционально): ")
            departure_str = prompt_optional("Дата/время отъезда YYYY-MM-DD HH:MM (опционально): ")

            contact = ContactInfo(email=email, phone=phone, address=address)
            guest = Guest(guest_id=guest_id, name=name, contact=contact)
            if arrival_str and departure_str:
                arrival = datetime.strptime(arrival_str, "%Y-%m-%d %H:%M")
                departure = datetime.strptime(departure_str, "%Y-%m-%d %H:%M")
                if departure <= arrival:
                    print("✗ Отъезд должен быть позже прибытия.")
                    continue
                guest.set_stay_dates(arrival, departure)
            storage.create_guest(guest)
            print("✓ Гость создан")
            mark_dirty()
            break
        except (ValidationError, ValueError) as e:
            print(f"✗ Ошибка: {e}")


def list_guests(storage: ResortStorage) -> None:
    guests = storage.list_guests()
    if not guests:
        print("Гостей нет.")
        return
    for g in guests:
        print(f"- {g}")


def create_staff(storage: ResortStorage) -> None:
    while True:
        try:
            staff_id = prompt_id("staff", "ID сотрудника (SNNN)")
            try:
                storage.get_staff_member_by_id(staff_id)
                print("✗ Сотрудник с таким ID уже существует.")
                continue
            except EntityNotFoundError:
                pass
            name = prompt_name("Имя сотрудника")
            role = prompt_name("Роль (должность)")
            email = prompt_email()
            phone = prompt_phone()
            service_ids_str = prompt_optional("ID услуг для привязки (через запятую, опционально): ")

            contact = ContactInfo(email=email, phone=phone)
            staff = StaffMember(staff_id=staff_id, name=name, role=role, contact=contact)
            if service_ids_str:
                ids = [x.strip() for x in service_ids_str.split(",") if x.strip()]
                missing = [sid for sid in ids if sid not in [s.service_id for s in storage.list_services()]]
                if missing:
                    print(f"✗ Не найдены услуги: {', '.join(missing)}")
                    continue
                for sid in ids:
                    staff.assign_service(sid)
            storage.create_staff_member(staff)
            print("✓ Сотрудник создан")
            mark_dirty()
            break
        except ValidationError as e:
            print(f"✗ Ошибка: {e}")


def list_staff(storage: ResortStorage) -> None:
    staff_members = storage.list_staff_members()
    if not staff_members:
        print("Сотрудников нет.")
        return
    for s in staff_members:
        print(f"- {s}")


def create_location(storage: ResortStorage) -> None:
    while True:
        try:
            location_id = prompt_id("location", "ID места (LNNN)")
            try:
                storage.get_location_by_id(location_id)
                print("✗ Место с таким ID уже существует.")
                continue
            except EntityNotFoundError:
                pass
            name = prompt_name("Название")
            location_type = prompt("Тип места (например, массажный_кабинет): ")
            if not location_type:
                print("✗ Тип места обязателен.")
                continue
            description = prompt_optional("Описание (опционально): ")

            loc = Location(location_id=location_id, name=name, location_type=location_type)
            loc.description = description
            storage.create_location(loc)
            print("✓ Место создано")
            mark_dirty()
            break
        except ValidationError as e:
            print(f"✗ Ошибка: {e}")


def list_locations(storage: ResortStorage) -> None:
    locations = storage.list_locations()
    if not locations:
        print("Мест нет.")
        return
    for l in locations:
        print(f"- {l}")


def create_service(storage: ResortStorage) -> None:
    while True:
        try:
            service_id = prompt_id("service", "ID услуги (SRVNNN)")
            try:
                storage.get_service_by_id(service_id)
                print("✗ Услуга с таким ID уже существует.")
                continue
            except EntityNotFoundError:
                pass
            name = prompt_name("Название услуги")
            service_type = prompt("Тип услуги: ")
            if not service_type:
                print("✗ Тип услуги обязателен.")
                continue
            duration = prompt_int("Длительность (мин): ")
            if duration <= 0:
                print("✗ Длительность должна быть положительной.")
                continue
            description = prompt_optional("Описание (опционально): ")
            location_id = prompt_id("location", "ID места для услуги (LNNN)")
            staff_id = prompt_id("staff", "ID сотрудника для услуги (SNNN)")
            # проверка существования
            try:
                storage.get_location_by_id(location_id)
                storage.get_staff_member_by_id(staff_id)
            except EntityNotFoundError as e:
                print(f"✗ {e}")
                continue

            srv = Service(
                service_id=service_id,
                name=name,
                service_type=service_type,
                duration_minutes=duration,
            )
            srv.description = description
            srv.assign_location(location_id)
            srv.assign_staff(staff_id)
            storage.create_service(srv)
            # двунаправленно: привяжем услугу к сотруднику
            staff = storage.get_staff_member_by_id(staff_id)
            staff.assign_service(service_id)
            storage.update_staff_member(staff_id, staff)
            print("✓ Услуга создана")
            mark_dirty()
            break
        except ValidationError as e:
            print(f"✗ Ошибка: {e}")


def list_services(storage: ResortStorage) -> None:
    services = storage.list_services()
    if not services:
        print("Услуг нет.")
        return
    for s in services:
        print(f"- {s}")


def create_booking(storage: ResortStorage) -> None:
    while True:
        try:
            booking_id = prompt_id("booking", "ID бронирования (BNNN)")
            try:
                storage.get_booking_by_id(booking_id)
                print("✗ Бронирование с таким ID уже существует.")
                continue
            except EntityNotFoundError:
                pass
            guest_id = prompt_id("guest", "ID гостя (GNNN)")
            service_id = prompt_id("service", "ID услуги (SRVNNN)")
            start = prompt_datetime("Начало")

            guest = storage.get_guest_by_id(guest_id)
            service = storage.get_service_by_id(service_id)
            if not service.location_id or not service.staff_id:
                print("✗ Услуга должна иметь назначенные место и сотрудника.")
                continue
            location = storage.get_location_by_id(service.location_id)
            staff = storage.get_staff_member_by_id(service.staff_id)
            end = datetime.fromtimestamp(start.timestamp() + service.duration_minutes * 60)
            slot = TimeSlot(start_time=start, end_time=end)

            booking = Booking(
                booking_id=booking_id,
                guest=guest,
                service=service,
                time_slot=slot,
                location=location,
            )
            booking.assign_staff(staff)
            storage.create_booking(booking)
            print("✓ Бронирование создано")
            mark_dirty()
            break
        except (EntityNotFoundError, ValidationError) as e:
            print(f"✗ Ошибка: {e}")


def list_bookings(storage: ResortStorage) -> None:
    bookings = storage.list_bookings()
    if not bookings:
        print("Бронирований нет.")
        return
    for b in bookings:
        print(f"- {b}")


 


def save_data(storage: ResortStorage) -> None:
    path = prompt("Путь к JSON для сохранения (например, lab1/storage_data.json) [Enter — по умолчанию]: ")
    if not path:
        path = "lab1/storage_data.json"
    try:
        storage.save_to_json(path)
        set_saved(path, "json")
        print("✓ Данные сохранены (JSON)")
    except StorageError as e:
        print(f"✗ Ошибка: {e}")


def load_data(storage: ResortStorage) -> None:
    path = prompt("Путь к JSON для загрузки (например, lab1/storage_data.json) [Enter — по умолчанию]: ")
    if not path:
        path = "lab1/storage_data.json"
    try:
        storage.load_from_json(path)
        set_loaded(path, "json")
        print("✓ Данные загружены (JSON)")
    except StorageError as e:
        print(f"✗ Ошибка: {e}")


def save_data_xml(storage: ResortStorage) -> None:
    path = prompt("Путь к XML для сохранения (например, lab1/storage_data.xml) [Enter — по умолчанию]: ")
    if not path:
        path = "lab1/storage_data.xml"
    try:
        storage.save_to_xml(path)
        set_saved(path, "xml")
        print("✓ Данные сохранены (XML)")
    except StorageError as e:
        print(f"✗ Ошибка: {e}")


def load_data_xml(storage: ResortStorage) -> None:
    path = prompt("Путь к XML для загрузки (например, lab1/storage_data.xml) [Enter — по умолчанию]: ")
    if not path:
        path = "lab1/storage_data.xml"
    try:
        storage.load_from_xml(path)
        set_loaded(path, "xml")
        print("✓ Данные загружены (XML)")
    except StorageError as e:
        print(f"✗ Ошибка: {e}")


def print_menu() -> None:
    print("\n=== Консольная админка курорта ===")
    print(current_state_text())
    print("1) Добавить гостя")
    print("2) Список гостей")
    print("3) Добавить сотрудника")
    print("4) Список сотрудников")
    print("5) Добавить место")
    print("6) Список мест")
    print("7) Добавить услугу")
    print("8) Список услуг")
    print("9) Добавить бронирование")
    print("10) Список бронирований")
    print("s) Сохранить в JSON")
    print("l) Загрузить из JSON")
    print("sx) Сохранить в XML")
    print("lx) Загрузить из XML")
    print("q) Выход")


def run_admin() -> None:
    storage = ResortStorage()
    actions = {
        "1": create_guest,
        "2": list_guests,
        "3": create_staff,
        "4": list_staff,
        "5": create_location,
        "6": list_locations,
        "7": create_service,
        "8": list_services,
        "9": create_booking,
        "10": list_bookings,
        "s": save_data,
        "l": load_data,
        "sx": lambda s: save_data_xml(s),
        "lx": lambda s: load_data_xml(s),
    }

    while True:
        clear_screen()
        print_menu()
        try:
            choice = input("> ").strip().lower()
        except EOFError:
            print("\nВыход.")
            break
        if choice == "q":
            print("Выход.")
            break
        action = actions.get(choice)
        if not action:
            print("Неизвестная команда.")
            try:
                input("Нажмите Enter, чтобы продолжить... ")
            except EOFError:
                pass
            continue
        try:
            action(storage)
        except KeyboardInterrupt:
            print("\nОперация прервана пользователем.")
        except Exception as e:
            print(f"✗ Непредвиденная ошибка: {e}")
        # Пауза перед следующим перерисовыванием экрана
        try:
            print()
            input("Нажмите Enter, чтобы вернуться в меню... ")
        except EOFError:
            print("\nВыход.")
            break


if __name__ == "__main__":
    run_admin()


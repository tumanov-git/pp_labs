from datetime import datetime
from typing import Optional

from exceptions import EntityNotFoundError, ValidationError, StorageError
from models import ContactInfo, Guest, StaffMember, Location, Money, Service, TimeSlot, Booking, Invoice
from storage import ResortStorage


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


def create_guest(storage: ResortStorage) -> None:
    try:
        guest_id = prompt("ID гостя (например, G001): ")
        # Предварительная проверка существования
        try:
            storage.get_guest_by_id(guest_id)
            print("✗ Гость с таким ID уже существует.")
            return
        except EntityNotFoundError:
            pass
        name = prompt("Имя гостя: ")
        email = prompt("Email: ")
        phone = prompt("Телефон: ")
        address = prompt_optional("Адрес (опционально): ")
        arrival_str = prompt_optional("Дата/время прибытия YYYY-MM-DD HH:MM (опционально): ")
        departure_str = prompt_optional("Дата/время отъезда YYYY-MM-DD HH:MM (опционально): ")

        contact = ContactInfo(email=email, phone=phone, address=address)
        guest = Guest(guest_id=guest_id, name=name, contact=contact)
        if arrival_str and departure_str:
            arrival = datetime.strptime(arrival_str, "%Y-%m-%d %H:%M")
            departure = datetime.strptime(departure_str, "%Y-%m-%d %H:%M")
            guest.set_stay_dates(arrival, departure)
        storage.create_guest(guest)
        print("✓ Гость создан")
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
    try:
        staff_id = prompt("ID сотрудника (например, S001): ")
        try:
            storage.get_staff_member_by_id(staff_id)
            print("✗ Сотрудник с таким ID уже существует.")
            return
        except EntityNotFoundError:
            pass
        name = prompt("Имя сотрудника: ")
        position = prompt("Должность: ")
        email = prompt("Email: ")
        phone = prompt("Телефон: ")
        specs = prompt_optional("Специализации через запятую (опционально): ")

        contact = ContactInfo(email=email, phone=phone)
        staff = StaffMember(staff_id=staff_id, name=name, position=position, contact=contact)
        if specs:
            for s in [x.strip() for x in specs.split(",") if x.strip()]:
                staff.add_specialization(s)
        storage.create_staff_member(staff)
        print("✓ Сотрудник создан")
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
    try:
        location_id = prompt("ID места (например, L001): ")
        try:
            storage.get_location_by_id(location_id)
            print("✗ Место с таким ID уже существует.")
            return
        except EntityNotFoundError:
            pass
        name = prompt("Название: ")
        capacity = prompt_int("Вместимость (int): ")
        location_type = prompt("Тип места (например, массажный_кабинет): ")
        description = prompt_optional("Описание (опционально): ")

        loc = Location(location_id=location_id, name=name, capacity=capacity, location_type=location_type)
        loc.description = description
        storage.create_location(loc)
        print("✓ Место создано")
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
    try:
        service_id = prompt("ID услуги (например, SRV001): ")
        try:
            storage.get_service_by_id(service_id)
            print("✗ Услуга с таким ID уже существует.")
            return
        except EntityNotFoundError:
            pass
        name = prompt("Название услуги: ")
        service_type = prompt("Тип услуги: ")
        amount = prompt_float("Базовая цена (amount): ")
        currency = prompt("Валюта (например, RUB): ")
        duration = prompt_int("Длительность (мин): ")
        description = prompt_optional("Описание (опционально): ")

        srv = Service(
            service_id=service_id,
            name=name,
            service_type=service_type,
            base_price=Money(amount, currency),
            duration_minutes=duration,
        )
        srv.description = description
        storage.create_service(srv)
        print("✓ Услуга создана")
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
    try:
        booking_id = prompt("ID бронирования (например, B001): ")
        try:
            storage.get_booking_by_id(booking_id)
            print("✗ Бронирование с таким ID уже существует.")
            return
        except EntityNotFoundError:
            pass
        guest_id = prompt("ID гостя: ")
        service_id = prompt("ID услуги: ")
        location_id = prompt("ID места: ")
        start = prompt_datetime("Начало")
        end = prompt_datetime("Конец")
        if end <= start:
            print("✗ Время окончания должно быть позже времени начала.")
            return
        staff_id_opt = prompt_optional("ID сотрудника (опционально): ")

        guest = storage.get_guest_by_id(guest_id)
        service = storage.get_service_by_id(service_id)
        location = storage.get_location_by_id(location_id)
        slot = TimeSlot(start_time=start, end_time=end)

        booking = Booking(
            booking_id=booking_id,
            guest=guest,
            service=service,
            time_slot=slot,
            location=location,
        )
        if staff_id_opt:
            staff = storage.get_staff_member_by_id(staff_id_opt)
            booking.assign_staff(staff)

        storage.create_booking(booking)
        print("✓ Бронирование создано")
    except (EntityNotFoundError, ValidationError) as e:
        print(f"✗ Ошибка: {e}")


def list_bookings(storage: ResortStorage) -> None:
    bookings = storage.list_bookings()
    if not bookings:
        print("Бронирований нет.")
        return
    for b in bookings:
        print(f"- {b}")


def create_invoice(storage: ResortStorage) -> None:
    try:
        invoice_id = prompt("ID счета (например, INV001): ")
        try:
            storage.get_invoice_by_id(invoice_id)
            print("✗ Счёт с таким ID уже существует.")
            return
        except EntityNotFoundError:
            pass
        guest_id = prompt("ID гостя: ")
        issue_date = prompt_datetime("Дата выдачи")
        invoice = Invoice(invoice_id=invoice_id, guest=storage.get_guest_by_id(guest_id), issue_date=issue_date)

        while True:
            service_id = prompt_optional("Добавить позицию: ID услуги (пусто — завершить): ")
            if not service_id:
                break
            try:
                service = storage.get_service_by_id(service_id)
            except EntityNotFoundError as e:
                print(f"  ✗ {e}")
                continue
            discount_str = prompt_optional("Скидка, % (опционально): ")
            discount = float(discount_str) if discount_str else 0.0
            price = service.calculate_price(discount_percent=discount)
            invoice.add_item(service, price)

        if not invoice.items:
            print("✗ Счёт без позиций не создаётся.")
            return
        storage.create_invoice(invoice)
        print("✓ Счёт создан")
    except (EntityNotFoundError, ValidationError, ValueError) as e:
        print(f"✗ Ошибка: {e}")


def list_invoices(storage: ResortStorage) -> None:
    invoices = storage.list_invoices()
    if not invoices:
        print("Счетов нет.")
        return
    for inv in invoices:
        print(f"- {inv}")


def save_data(storage: ResortStorage) -> None:
    path = prompt("Путь к JSON для сохранения (например, lab1/storage_data.json): ")
    try:
        storage.save_to_json(path)
        print("✓ Данные сохранены")
    except StorageError as e:
        print(f"✗ Ошибка: {e}")


def load_data(storage: ResortStorage) -> None:
    path = prompt("Путь к JSON для загрузки (например, lab1/storage_data.json): ")
    try:
        storage.load_from_json(path)
        print("✓ Данные загружены")
    except StorageError as e:
        print(f"✗ Ошибка: {e}")


def print_menu() -> None:
    print("\n=== Консольная админка курорта ===")
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
    print("11) Создать счёт")
    print("12) Список счетов")
    print("s) Сохранить в JSON")
    print("l) Загрузить из JSON")
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
        "11": create_invoice,
        "12": list_invoices,
        "s": save_data,
        "l": load_data,
    }

    while True:
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
            continue
        try:
            action(storage)
        except KeyboardInterrupt:
            print("\nОперация прервана пользователем.")
        except Exception as e:
            print(f"✗ Непредвиденная ошибка: {e}")


if __name__ == "__main__":
    run_admin()


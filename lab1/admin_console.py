from datetime import datetime
from typing import Optional

from exceptions import EntityNotFoundError, ValidationError, StorageError
from classes import ContactInfo, Guest, StaffMember, Location, Service, TimeSlot, Booking
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
    # Если сохранено, показываем, что JSON и XML синхронизированы
    if not DIRTY and FILE_PATH and FILE_FORMAT:
        if FILE_FORMAT == "json":
            return f"Источник: {src} | Формат: JSON+XML (синхронизированы) | Состояние: {state}"
        elif FILE_FORMAT == "xml":
            return f"Источник: {src} | Формат: XML | Состояние: {state}"
    return f"Источник: {src} | Формат: {fmt} | Состояние: {state}"


def clear_screen() -> None:
    # Самый быстрый вариант: ANSI-очистка и перенос курсора в (0,0)
    print("\033[2J\033[H", end="")


class MenuExit(Exception):
    """Исключение для выхода в главное меню."""
    pass


def prompt(message: str, allow_exit: bool = True) -> str:
    """Запросить ввод с возможностью выхода в меню."""
    value = input(message).strip()
    if allow_exit and value.lower() in ("q", "exit", "выход", "отмена"):
        raise MenuExit()
    return value


def prompt_optional(message: str, allow_exit: bool = True) -> Optional[str]:
    """Запросить опциональный ввод с возможностью выхода в меню."""
    value = input(message).strip()
    if allow_exit and value.lower() in ("q", "exit", "выход", "отмена"):
        raise MenuExit()
    return value if value != "" else None


def prompt_int(message: str, allow_exit: bool = True) -> int:
    while True:
        value = input(message).strip()
        if allow_exit and value.lower() in ("q", "exit", "выход", "отмена"):
            raise MenuExit()
        try:
            return int(value)
        except ValueError:
            print("Введите целое число.")


def prompt_datetime(message: str, allow_exit: bool = True) -> datetime:
    while True:
        value = input(message + " (формат YYYY-MM-DD HH:MM): ").strip()
        if allow_exit and value.lower() in ("q", "exit", "выход", "отмена"):
            raise MenuExit()
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


def prompt_id(entity: str, label: str, allow_exit: bool = True) -> str:
    """Запросить ID с проверкой формата для заданного типа сущности."""
    pattern = ID_PATTERNS[entity]
    while True:
        value = prompt(f"{label}: ", allow_exit=allow_exit)
        if not value:
            print("✗ Поле обязательно.")
            continue
        if not pattern.match(value):
            print("✗ Неверный формат ID.")
            continue
        return value


def prompt_name(label: str, allow_exit: bool = True) -> str:
    while True:
        value = prompt(f"{label}: ", allow_exit=allow_exit)
        if not value:
            print("✗ Поле обязательно.")
            continue
        if not NAME_RE.match(value):
            print("✗ Имя: только буквы и пробелы.")
            continue
        return value


def prompt_email(allow_exit: bool = True) -> str:
    while True:
        value = prompt("Email: ", allow_exit=allow_exit)
        if not value:
            print("✗ Email обязателен.")
            continue
        if not EMAIL_RE.match(value):
            print("✗ Неверный формат email.")
            continue
        return value


def prompt_phone(allow_exit: bool = True) -> str:
    while True:
        value = prompt("Телефон: ", allow_exit=allow_exit)
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
            guest_id = storage.generate_guest_id()
            print(f"Автоматически сгенерирован ID: {guest_id}")
            name = prompt_name("Имя гостя")
            email = prompt_email()
            phone = prompt_phone()
            address = prompt_optional("Адрес (опционально): ")

            contact = ContactInfo(email=email, phone=phone, address=address)
            guest = Guest(guest_id=guest_id, name=name, contact=contact)
            storage.create_guest(guest)
            print("✓ Гость создан")
            mark_dirty()
            break
        except MenuExit:
            print("Отмена создания гостя.")
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


def update_guest(storage: ResortStorage) -> None:
    while True:
        try:
            guest_id = prompt_id("guest", "ID гостя для обновления (GNNN)")
            try:
                guest = storage.get_guest_by_id(guest_id)
            except EntityNotFoundError as e:
                print(f"✗ {e}")
                continue
            print(f"Текущий гость: {guest}")
            name = prompt_name("Новое имя гостя")
            email = prompt_email()
            phone = prompt_phone()
            address = prompt_optional("Новый адрес (опционально): ")

            contact = ContactInfo(email=email, phone=phone, address=address)
            updated = Guest(guest_id=guest_id, name=name, contact=contact)
            storage.update_guest(guest_id, updated)
            print("✓ Гость обновлён")
            mark_dirty()
            break
        except MenuExit:
            print("Отмена обновления гостя.")
            break
        except ValidationError as e:
            print(f"✗ Ошибка: {e}")


def delete_guest(storage: ResortStorage) -> None:
    while True:
        try:
            guest_id = prompt_id("guest", "ID гостя для удаления (GNNN)")
            try:
                guest = storage.get_guest_by_id(guest_id)
            except EntityNotFoundError as e:
                print(f"✗ {e}")
                continue
            print(f"Вы действительно хотите удалить гостя: {guest}?")
            confirm = prompt("Введите 'y' для удаления, Enter для отмены: ", allow_exit=False)
            if confirm.lower() == "y":
                storage.delete_guest(guest_id)
                print("✓ Гость удалён")
                mark_dirty()
            else:
                print("Удаление отменено.")
            break
        except MenuExit:
            # здесь MenuExit не ожидается, т.к. allow_exit=False, но оставим для единообразия
            print("Отмена удаления гостя.")
            break
        except EntityNotFoundError as e:
            print(f"✗ Ошибка: {e}")


def create_staff(storage: ResortStorage) -> None:
    while True:
        try:
            staff_id = storage.generate_staff_id()
            print(f"Автоматически сгенерирован ID: {staff_id}")
            name = prompt_name("Имя сотрудника")
            role = prompt_name("Роль (должность)")
            email = prompt_email()
            phone = prompt_phone()
            
            # Показываем доступные услуги
            services = storage.list_services()
            if services:
                print("\nДоступные услуги для привязки:")
                for srv in services:
                    print(f"  - {srv.service_id}: {srv.name} ({srv.duration_minutes} мин)")
            else:
                print("\n⚠ Услуг пока нет. Сначала создайте услуги.")
            print()
            
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
        except MenuExit:
            print("Отмена создания сотрудника.")
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


def update_staff(storage: ResortStorage) -> None:
    while True:
        try:
            staff_id = prompt_id("staff", "ID сотрудника для обновления (SNNN)")
            try:
                staff = storage.get_staff_member_by_id(staff_id)
            except EntityNotFoundError as e:
                print(f"✗ {e}")
                continue
            print(f"Текущий сотрудник: {staff}")
            name = prompt_name("Новое имя сотрудника")
            role = prompt_name("Новая роль (должность)")
            email = prompt_email()
            phone = prompt_phone()
            
            # Показываем доступные услуги
            services = storage.list_services()
            if services:
                print("\nДоступные услуги для привязки:")
                for srv in services:
                    print(f"  - {srv.service_id}: {srv.name} ({srv.duration_minutes} мин)")
            else:
                print("\n⚠ Услуг пока нет. Сначала создайте услуги.")
            print()
            
            service_ids_str = prompt_optional("Новые ID услуг для привязки (через запятую, опционально): ")

            contact = ContactInfo(email=email, phone=phone)
            updated_staff = StaffMember(staff_id=staff_id, name=name, role=role, contact=contact)
            if service_ids_str:
                ids = [x.strip() for x in service_ids_str.split(",") if x.strip()]
                existing_services = [s.service_id for s in storage.list_services()]
                missing = [sid for sid in ids if sid not in existing_services]
                if missing:
                    print(f"✗ Не найдены услуги: {', '.join(missing)}")
                    continue
                for sid in ids:
                    updated_staff.assign_service(sid)
            storage.update_staff_member(staff_id, updated_staff)
            print("✓ Сотрудник обновлён")
            mark_dirty()
            break
        except MenuExit:
            print("Отмена обновления сотрудника.")
            break
        except ValidationError as e:
            print(f"✗ Ошибка: {e}")


def delete_staff(storage: ResortStorage) -> None:
    while True:
        try:
            staff_id = prompt_id("staff", "ID сотрудника для удаления (SNNN)")
            try:
                staff = storage.get_staff_member_by_id(staff_id)
            except EntityNotFoundError as e:
                print(f"✗ {e}")
                continue
            print(f"Вы действительно хотите удалить сотрудника: {staff}?")
            confirm = prompt("Введите 'y' для удаления, Enter для отмены: ", allow_exit=False)
            if confirm.lower() == "y":
                storage.delete_staff_member(staff_id)
                print("✓ Сотрудник удалён")
                mark_dirty()
            else:
                print("Удаление отменено.")
            break
        except MenuExit:
            print("Отмена удаления сотрудника.")
            break
        except EntityNotFoundError as e:
            print(f"✗ Ошибка: {e}")


def create_location(storage: ResortStorage) -> None:
    while True:
        try:
            location_id = storage.generate_location_id()
            print(f"Автоматически сгенерирован ID: {location_id}")
            
            # Показываем существующие места для справки
            existing_locations = storage.list_locations()
            if existing_locations:
                print("\nСуществующие места:")
                for loc in existing_locations:
                    print(f"  - {loc.location_id}: {loc.name}")
                print()
            
            name = prompt_name("Название")

            loc = Location(location_id=location_id, name=name)
            storage.create_location(loc)
            print("✓ Место создано")
            mark_dirty()
            break
        except MenuExit:
            print("Отмена создания места.")
            break
        except ValidationError as e:
            print(f"✗ Ошибка: {e}")


def list_locations(storage: ResortStorage) -> None:
    locations = storage.list_locations()
    if not locations:
        print("Мест нет.")
        return
    for i, loc in enumerate(locations, 1):
        print(f"\n{i}. Место ID={loc.location_id}")
        print(f"   Название: {loc.name}")


def update_location(storage: ResortStorage) -> None:
    while True:
        try:
            location_id = prompt_id("location", "ID места для обновления (LNNN)")
            try:
                loc = storage.get_location_by_id(location_id)
            except EntityNotFoundError as e:
                print(f"✗ {e}")
                continue
            print(f"Текущее место: {loc}")
            name = prompt_name("Новое название")

            updated_loc = Location(location_id=location_id, name=name)
            storage.update_location(location_id, updated_loc)
            print("✓ Место обновлено")
            mark_dirty()
            break
        except MenuExit:
            print("Отмена обновления места.")
            break
        except ValidationError as e:
            print(f"✗ Ошибка: {e}")


def delete_location(storage: ResortStorage) -> None:
    while True:
        try:
            location_id = prompt_id("location", "ID места для удаления (LNNN)")
            try:
                loc = storage.get_location_by_id(location_id)
            except EntityNotFoundError as e:
                print(f"✗ {e}")
                continue
            print(f"Вы действительно хотите удалить место: {loc}?")
            confirm = prompt("Введите 'y' для удаления, Enter для отмены: ", allow_exit=False)
            if confirm.lower() == "y":
                storage.delete_location(location_id)
                print("✓ Место удалено")
                mark_dirty()
            else:
                print("Удаление отменено.")
            break
        except MenuExit:
            print("Отмена удаления места.")
            break
        except EntityNotFoundError as e:
            print(f"✗ Ошибка: {e}")


def create_service(storage: ResortStorage) -> None:
    while True:
        try:
            service_id = storage.generate_service_id()
            print(f"Автоматически сгенерирован ID: {service_id}")
            name = prompt_name("Название услуги")
            duration = prompt_int("Длительность (мин): ")
            if duration <= 0:
                print("✗ Длительность должна быть положительной.")
                continue
            
            # Показываем доступные места
            locations = storage.list_locations()
            if locations:
                print("\nДоступные места:")
                for loc in locations:
                    print(f"  - {loc.location_id}: {loc.name}")
            else:
                print("\n⚠ Мест пока нет. Сначала создайте место.")
            print()
            
            location_id = prompt("ID места для услуги (LNNN): ")
            if not location_id:
                print("✗ ID места обязателен.")
                continue
            
            # Показываем доступных сотрудников
            staff_members = storage.list_staff_members()
            if staff_members:
                print("\nДоступные сотрудники:")
                for staff in staff_members:
                    services_info = f", услуги: {', '.join(staff.service_ids)}" if staff.service_ids else " (нет привязанных услуг)"
                    print(f"  - {staff.staff_id}: {staff.name} ({staff.role}){services_info}")
            else:
                print("\n⚠ Сотрудников пока нет. Сначала создайте сотрудника.")
            print()
            
            staff_id = prompt("ID сотрудника для услуги (SNNN): ")
            if not staff_id:
                print("✗ ID сотрудника обязателен.")
                continue
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
                duration_minutes=duration,
            )
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
        except MenuExit:
            print("Отмена создания услуги.")
            break
        except ValidationError as e:
            print(f"✗ Ошибка: {e}")


def list_services(storage: ResortStorage) -> None:
    services = storage.list_services()
    if not services:
        print("Услуг нет.")
        return
    for i, srv in enumerate(services, 1):
        print(f"\n{i}. Услуга ID={srv.service_id}")
        print(f"   Название: {srv.name}")
        print(f"   Длительность: {srv.duration_minutes} мин")
        if srv.location_id:
            try:
                location = storage.get_location_by_id(srv.location_id)
                print(f"   Место: {srv.location_id} ({location.name})")
            except EntityNotFoundError:
                print(f"   Место: {srv.location_id} (не найдено)")
        else:
            print(f"   Место: (не назначено)")
        if srv.staff_id:
            try:
                staff = storage.get_staff_member_by_id(srv.staff_id)
                print(f"   Сотрудник: {srv.staff_id} ({staff.name}, {staff.role})")
            except EntityNotFoundError:
                print(f"   Сотрудник: {srv.staff_id} (не найден)")
        else:
            print(f"   Сотрудник: (не назначен)")


def update_service_admin(storage: ResortStorage) -> None:
    """Обновление услуги (админская обёртка вокруг storage.update_service)."""
    while True:
        try:
            service_id = prompt_id("service", "ID услуги для обновления (SRVNNN)")
            try:
                service = storage.get_service_by_id(service_id)
            except EntityNotFoundError as e:
                print(f"✗ {e}")
                continue
            print(f"Текущая услуга: {service}")
            name = prompt_name("Новое название услуги")
            duration = prompt_int("Новая длительность (мин): ")
            if duration <= 0:
                print("✗ Длительность должна быть положительной.")
                continue
            
            # Показываем доступные места
            locations = storage.list_locations()
            if locations:
                print("\nДоступные места:")
                for loc in locations:
                    print(f"  - {loc.location_id}: {loc.name}")
            else:
                print("\n⚠ Мест пока нет. Сначала создайте место.")
            print()
            
            location_id = prompt("Новый ID места для услуги (LNNN): ")
            if not location_id:
                print("✗ ID места обязателен.")
                continue
            
            # Показываем доступных сотрудников
            staff_members = storage.list_staff_members()
            if staff_members:
                print("\nДоступные сотрудники:")
                for staff in staff_members:
                    services_info = f", услуги: {', '.join(staff.service_ids)}" if staff.service_ids else " (нет привязанных услуг)"
                    print(f"  - {staff.staff_id}: {staff.name} ({staff.role}){services_info}")
            else:
                print("\n⚠ Сотрудников пока нет. Сначала создайте сотрудника.")
            print()
            
            staff_id = prompt("Новый ID сотрудника для услуги (SNNN): ")
            if not staff_id:
                print("✗ ID сотрудника обязателен.")
                continue
            # проверка существования
            try:
                storage.get_location_by_id(location_id)
                storage.get_staff_member_by_id(staff_id)
            except EntityNotFoundError as e:
                print(f"✗ {e}")
                continue

            updated_srv = Service(
                service_id=service_id,
                name=name,
                duration_minutes=duration,
            )
            updated_srv.assign_location(location_id)
            updated_srv.assign_staff(staff_id)
            storage.update_service(service_id, updated_srv)

            # Обновим привязку услуги к сотрудникам:
            # уберём услугу из всех сотрудников и добавим только выбранному
            for staff in storage.list_staff_members():
                if service_id in staff.service_ids and staff.staff_id != staff_id:
                    staff.service_ids.remove(service_id)
                    storage.update_staff_member(staff.staff_id, staff)
            staff = storage.get_staff_member_by_id(staff_id)
            if service_id not in staff.service_ids:
                staff.assign_service(service_id)
                storage.update_staff_member(staff_id, staff)

            print("✓ Услуга обновлена")
            mark_dirty()
            break
        except MenuExit:
            print("Отмена обновления услуги.")
            break
        except ValidationError as e:
            print(f"✗ Ошибка: {e}")


def delete_service_admin(storage: ResortStorage) -> None:
    while True:
        try:
            service_id = prompt_id("service", "ID услуги для удаления (SRVNNN)")
            try:
                service = storage.get_service_by_id(service_id)
            except EntityNotFoundError as e:
                print(f"✗ {e}")
                continue
            print(f"Вы действительно хотите удалить услугу: {service}?")
            confirm = prompt("Введите 'y' для удаления, Enter для отмены: ", allow_exit=False)
            if confirm.lower() == "y":
                # также уберём ссылку на услугу у сотрудников
                for staff in storage.list_staff_members():
                    if service_id in staff.service_ids:
                        staff.service_ids.remove(service_id)
                        storage.update_staff_member(staff.staff_id, staff)
                storage.delete_service(service_id)
                print("✓ Услуга удалена")
                mark_dirty()
            else:
                print("Удаление отменено.")
            break
        except MenuExit:
            print("Отмена удаления услуги.")
            break
        except EntityNotFoundError as e:
            print(f"✗ Ошибка: {e}")


def create_booking(storage: ResortStorage) -> None:
    while True:
        try:
            booking_id = storage.generate_booking_id()
            print(f"Автоматически сгенерирован ID: {booking_id}")
            
            # Показываем доступных гостей
            guests = storage.list_guests()
            if guests:
                print("\nДоступные гости:")
                for guest in guests:
                    print(f"  - {guest.guest_id}: {guest.name}")
            else:
                print("\n⚠ Гостей пока нет. Сначала создайте гостя.")
            print()
            
            guest_id = prompt("ID гостя (GNNN): ")
            if not guest_id:
                print("✗ ID гостя обязателен.")
                continue
            
            # Показываем доступные услуги с их местами и сотрудниками
            services = storage.list_services()
            if services:
                print("\nДоступные услуги:")
                for srv in services:
                    location_info = ""
                    staff_info = ""
                    if srv.location_id:
                        try:
                            loc = storage.get_location_by_id(srv.location_id)
                            location_info = f", место: {srv.location_id} ({loc.name})"
                        except EntityNotFoundError:
                            location_info = f", место: {srv.location_id} (не найдено)"
                    else:
                        location_info = ", место: (не назначено)"
                    
                    if srv.staff_id:
                        try:
                            staff = storage.get_staff_member_by_id(srv.staff_id)
                            staff_info = f", сотрудник: {srv.staff_id} ({staff.name})"
                        except EntityNotFoundError:
                            staff_info = f", сотрудник: {srv.staff_id} (не найден)"
                    else:
                        staff_info = ", сотрудник: (не назначен)"
                    
                    status = "✓" if srv.location_id and srv.staff_id else "⚠"
                    print(f"  {status} {srv.service_id}: {srv.name} ({srv.duration_minutes} мин){location_info}{staff_info}")
            else:
                print("\n⚠ Услуг пока нет. Сначала создайте услугу.")
            print()
            
            service_id = prompt("ID услуги (SRVNNN): ")
            if not service_id:
                print("✗ ID услуги обязателен.")
                continue
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
        except MenuExit:
            print("Отмена создания бронирования.")
            break
        except (EntityNotFoundError, ValidationError) as e:
            print(f"✗ Ошибка: {e}")


def list_bookings(storage: ResortStorage) -> None:
    bookings = storage.list_bookings()
    if not bookings:
        print("Бронирований нет.")
        return
    for i, booking in enumerate(bookings, 1):
        print(f"\n{i}. Бронирование ID={booking.booking_id}")
        print(f"   Гость: {booking.guest.guest_id} ({booking.guest.name})")
        print(f"   Услуга: {booking.service.service_id} ({booking.service.name}, {booking.service.duration_minutes} мин)")
        print(f"   Место: {booking.location.location_id} ({booking.location.name})")
        if booking.staff_member:
            print(f"   Сотрудник: {booking.staff_member.staff_id} ({booking.staff_member.name}, {booking.staff_member.role})")
        else:
            print(f"   Сотрудник: (не назначен)")
        print(f"   Время: {booking.time_slot.start_time.strftime('%Y-%m-%d %H:%M')} - {booking.time_slot.end_time.strftime('%H:%M')}")


def update_booking(storage: ResortStorage) -> None:
    """Обновить бронирование: реализовано как пересоздание с тем же ID через create_booking."""
    while True:
        try:
            booking_id = prompt_id("booking", "ID бронирования для обновления (BNNN)")
            try:
                existing = storage.get_booking_by_id(booking_id)
            except EntityNotFoundError as e:
                print(f"✗ {e}")
                continue
            print(f"Текущее бронирование: {existing}")
            
            # Показываем доступных гостей
            guests = storage.list_guests()
            if guests:
                print("\nДоступные гости:")
                for guest in guests:
                    print(f"  - {guest.guest_id}: {guest.name}")
            else:
                print("\n⚠ Гостей пока нет. Сначала создайте гостя.")
            print()

            guest_id = prompt("Новый ID гостя (GNNN): ")
            if not guest_id:
                print("✗ ID гостя обязателен.")
                continue
            
            # Показываем доступные услуги с их местами и сотрудниками
            services = storage.list_services()
            if services:
                print("\nДоступные услуги:")
                for srv in services:
                    location_info = ""
                    staff_info = ""
                    if srv.location_id:
                        try:
                            loc = storage.get_location_by_id(srv.location_id)
                            location_info = f", место: {srv.location_id} ({loc.name})"
                        except EntityNotFoundError:
                            location_info = f", место: {srv.location_id} (не найдено)"
                    else:
                        location_info = ", место: (не назначено)"
                    
                    if srv.staff_id:
                        try:
                            staff = storage.get_staff_member_by_id(srv.staff_id)
                            staff_info = f", сотрудник: {srv.staff_id} ({staff.name})"
                        except EntityNotFoundError:
                            staff_info = f", сотрудник: {srv.staff_id} (не найден)"
                    else:
                        staff_info = ", сотрудник: (не назначен)"
                    
                    status = "✓" if srv.location_id and srv.staff_id else "⚠"
                    print(f"  {status} {srv.service_id}: {srv.name} ({srv.duration_minutes} мин){location_info}{staff_info}")
            else:
                print("\n⚠ Услуг пока нет. Сначала создайте услугу.")
            print()
            
            service_id = prompt("Новый ID услуги (SRVNNN): ")
            if not service_id:
                print("✗ ID услуги обязателен.")
                continue
            start = prompt_datetime("Новое начало")

            guest = storage.get_guest_by_id(guest_id)
            service = storage.get_service_by_id(service_id)
            if not service.location_id or not service.staff_id:
                print("✗ Услуга должна иметь назначенные место и сотрудника.")
                continue
            location = storage.get_location_by_id(service.location_id)
            staff = storage.get_staff_member_by_id(service.staff_id)
            end = datetime.fromtimestamp(start.timestamp() + service.duration_minutes * 60)
            slot = TimeSlot(start_time=start, end_time=end)

            new_booking = Booking(
                booking_id=booking_id,
                guest=guest,
                service=service,
                time_slot=slot,
                location=location,
            )
            new_booking.assign_staff(staff)

            # удаляем старое бронирование и создаём новое с тем же ID, чтобы пройти все проверки
            storage.delete_booking(booking_id)
            storage.create_booking(new_booking)

            print("✓ Бронирование обновлено")
            mark_dirty()
            break
        except MenuExit:
            print("Отмена обновления бронирования.")
            break
        except (EntityNotFoundError, ValidationError) as e:
            print(f"✗ Ошибка: {e}")


def delete_booking(storage: ResortStorage) -> None:
    while True:
        try:
            booking_id = prompt_id("booking", "ID бронирования для удаления (BNNN)")
            try:
                booking = storage.get_booking_by_id(booking_id)
            except EntityNotFoundError as e:
                print(f"✗ {e}")
                continue
            print(f"Вы действительно хотите удалить бронирование: {booking}?")
            confirm = prompt("Введите 'y' для удаления, Enter для отмены: ", allow_exit=False)
            if confirm.lower() == "y":
                storage.delete_booking(booking_id)
                print("✓ Бронирование удалено")
                mark_dirty()
            else:
                print("Удаление отменено.")
            break
        except MenuExit:
            print("Отмена удаления бронирования.")
            break
        except EntityNotFoundError as e:
            print(f"✗ Ошибка: {e}")


 


def save_data(storage: ResortStorage) -> None:
    """Сохранить данные в оба формата (JSON и XML) синхронно."""
    json_path = prompt("Путь к JSON для сохранения (например, lab1/storage_data.json) [Enter — по умолчанию]: ")
    if not json_path:
        json_path = "lab1/storage_data.json"
    
    # Генерируем путь к XML на основе пути к JSON
    if json_path.endswith(".json"):
        xml_path = json_path[:-5] + ".xml"
    else:
        xml_path = json_path + ".xml"
    
    try:
        storage.save_to_json(json_path)
        storage.save_to_xml(xml_path)
        set_saved(json_path, "json")
        print(f"✓ Данные сохранены в оба формата:")
        print(f"  - JSON: {json_path}")
        print(f"  - XML: {xml_path}")
    except StorageError as e:
        print(f"✗ Ошибка сохранения: {e}")


def load_data_json(storage: ResortStorage) -> None:
    """Загрузить данные из JSON."""
    path = prompt("Путь к JSON для загрузки (например, lab1/storage_data.json) [Enter — по умолчанию]: ")
    if not path:
        path = "lab1/storage_data.json"
    try:
        storage.load_from_json(path)
        set_loaded(path, "json")
        print("✓ Данные загружены из JSON")
    except StorageError as e:
        print(f"✗ Ошибка: {e}")


def load_data_xml(storage: ResortStorage) -> None:
    """Загрузить данные из XML."""
    path = prompt("Путь к XML для загрузки (например, lab1/storage_data.xml) [Enter — по умолчанию]: ")
    if not path:
        path = "lab1/storage_data.xml"
    try:
        storage.load_from_xml(path)
        set_loaded(path, "xml")
        print("✓ Данные загружены из XML")
    except StorageError as e:
        print(f"✗ Ошибка: {e}")


def print_menu() -> None:
    print("\n=== Консольная админка курорта ===")
    print(current_state_text())
    print("\n--- ПРОСМОТР ---")
    print("1) Список гостей")
    print("2) Список сотрудников")
    print("3) Список мест")
    print("4) Список услуг")
    print("5) Список бронирований")
    print("\n--- ДОБАВЛЕНИЕ ---")
    print("6) Добавить гостя")
    print("7) Добавить сотрудника")
    print("8) Добавить место")
    print("9) Добавить услугу")
    print("10) Добавить бронирование")
    print("\n--- ИЗМЕНЕНИЕ ---")
    print("11) Обновить гостя")
    print("12) Обновить сотрудника")
    print("13) Обновить место")
    print("14) Обновить услугу")
    print("15) Обновить бронирование")
    print("\n--- УДАЛЕНИЕ ---")
    print("16) Удалить гостя")
    print("17) Удалить сотрудника")
    print("18) Удалить место")
    print("19) Удалить услугу")
    print("20) Удалить бронирование")
    print("\n--- ФАЙЛЫ ---")
    print("s) Сохранить (JSON + XML)")
    print("lj) Загрузить из JSON")
    print("lx) Загрузить из XML")
    print("q) Выход")
    print("\n(В любой момент ввода можно ввести 'q' или 'exit' для возврата в меню)")


def run_admin() -> None:
    storage = ResortStorage()
    actions = {
        # Просмотр
        "1": list_guests,
        "2": list_staff,
        "3": list_locations,
        "4": list_services,
        "5": list_bookings,
        # Добавление
        "6": create_guest,
        "7": create_staff,
        "8": create_location,
        "9": create_service,
        "10": create_booking,
        # Изменение
        "11": update_guest,
        "12": update_staff,
        "13": update_location,
        "14": update_service_admin,
        "15": update_booking,
        # Удаление
        "16": delete_guest,
        "17": delete_staff,
        "18": delete_location,
        "19": delete_service_admin,
        "20": delete_booking,
        # Файлы
        "s": save_data,
        "lj": load_data_json,
        "lx": load_data_xml,
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
        except MenuExit:
            # Пользователь вышел в меню - это нормально, не показываем ошибку
            pass
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


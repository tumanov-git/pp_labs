"""
Слой хранения данных курорта.
Предоставляет CRUD-операции и сериализацию доменной модели в JSON и XML.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

from exceptions import EntityNotFoundError, StorageError, ValidationError
from models import (
    Booking,
    ContactInfo,
    Guest,
    Location,
    Service,
    StaffMember,
    TimeSlot,
)


def _datetime_to_str(value: Optional[datetime]) -> Optional[str]:
    """Преобразовать дату/время в строку ISO."""
    return value.isoformat() if value else None


def _datetime_from_str(value: Optional[str]) -> Optional[datetime]:
    """Преобразовать строку ISO обратно в datetime."""
    if value:
        return datetime.fromisoformat(value)
    return None


def _contact_to_dict(contact: ContactInfo) -> Dict[str, Optional[str]]:
    """Преобразовать ContactInfo в словарь."""
    return {
        "email": contact.email,
        "phone": contact.phone,
        "address": contact.address,
    }


def _contact_from_dict(data: Dict[str, Any]) -> ContactInfo:
    """Создать ContactInfo из словаря."""
    return ContactInfo(
        email=data.get("email", ""),
        phone=data.get("phone", ""),
        address=data.get("address"),
    )


 


def _timeslot_to_dict(slot: TimeSlot) -> Dict[str, str]:
    """Преобразовать TimeSlot в словарь."""
    return {
        "start_time": slot.start_time.isoformat(),
        "end_time": slot.end_time.isoformat(),
    }


def _timeslot_from_dict(data: Dict[str, Any]) -> TimeSlot:
    """Создать TimeSlot из словаря."""
    return TimeSlot(
        start_time=datetime.fromisoformat(data["start_time"]),
        end_time=datetime.fromisoformat(data["end_time"]),
    )


def _guest_to_dict(guest: Guest) -> Dict[str, Any]:
    """Преобразовать Guest в словарь."""
    return {
        "guest_id": guest.guest_id,
        "name": guest.name,
        "contact": _contact_to_dict(guest.contact),
    }


def _guest_from_dict(data: Dict[str, Any]) -> Guest:
    """Создать Guest из словаря."""
    guest = Guest(
        guest_id=data.get("guest_id", ""),
        name=data.get("name", ""),
        contact=_contact_from_dict(data.get("contact", {})),
    )
    return guest


def _staff_to_dict(staff: StaffMember) -> Dict[str, Any]:
    """Преобразовать StaffMember в словарь."""
    return {
        "staff_id": staff.staff_id,
        "name": staff.name,
        "role": staff.role,
        "contact": _contact_to_dict(staff.contact),
        "service_ids": staff.service_ids,
    }


def _staff_from_dict(data: Dict[str, Any]) -> StaffMember:
    """Создать StaffMember из словаря."""
    staff = StaffMember(
        staff_id=data.get("staff_id", ""),
        name=data.get("name", ""),
        role=data.get("role", ""),
        contact=_contact_from_dict(data.get("contact", {})),
    )
    for sid in data.get("service_ids", []):
        staff.assign_service(sid)
    return staff


def _location_to_dict(location: Location) -> Dict[str, Any]:
    """Преобразовать Location в словарь."""
    return {
        "location_id": location.location_id,
        "name": location.name,
    }


def _location_from_dict(data: Dict[str, Any]) -> Location:
    """Создать Location из словаря."""
    location = Location(
        location_id=data.get("location_id", ""),
        name=data.get("name", ""),
    )
    return location


def _service_to_dict(service: Service) -> Dict[str, Any]:
    """Преобразовать Service в словарь."""
    return {
        "service_id": service.service_id,
        "name": service.name,
        "duration_minutes": service.duration_minutes,
        "location_id": service.location_id,
        "staff_id": service.staff_id,
    }


def _service_from_dict(data: Dict[str, Any]) -> Service:
    """Создать Service из словаря."""
    service = Service(
        service_id=data.get("service_id", ""),
        name=data.get("name", ""),
        duration_minutes=int(data.get("duration_minutes", 0)),
    )
    if data.get("location_id"):
        service.assign_location(data.get("location_id", ""))
    if data.get("staff_id"):
        service.assign_staff(data.get("staff_id", ""))
    return service


def _booking_to_dict(booking: Booking) -> Dict[str, Any]:
    """Преобразовать Booking в словарь."""
    return {
        "booking_id": booking.booking_id,
        "guest_id": booking.guest.guest_id,
        "service_id": booking.service.service_id,
        "location_id": booking.location.location_id,
        "staff_id": booking.staff_member.staff_id if booking.staff_member else None,
        "time_slot": _timeslot_to_dict(booking.time_slot),
    }


 


def _booking_from_dict(
    data: Dict[str, Any],
    guests: Dict[str, Guest],
    services: Dict[str, Service],
    locations: Dict[str, Location],
    staff_members: Dict[str, StaffMember],
) -> Booking:
    """Создать Booking из словаря."""
    guest_id = data.get("guest_id")
    service_id = data.get("service_id")
    location_id = data.get("location_id")

    if not guest_id or guest_id not in guests:
        raise KeyError("guest_id")
    if not service_id or service_id not in services:
        raise KeyError("service_id")
    if not location_id or location_id not in locations:
        raise KeyError("location_id")

    guest = guests[guest_id]
    service = services[service_id]
    location = locations[location_id]
    booking = Booking(
        booking_id=data.get("booking_id", ""),
        guest=guest,
        service=service,
        time_slot=_timeslot_from_dict(data.get("time_slot", {})),
        location=location,
    )
    staff_id = data.get("staff_id")
    if staff_id and staff_id in staff_members:
        booking.assign_staff(staff_members[staff_id])
    return booking


 


 


def _dict_to_xml(parent: ET.Element, data: Any) -> None:
    """Рекурсивно заполнить XML-элемент данными из словаря/списка."""
    if isinstance(data, dict):
        for key, value in data.items():
            child = ET.SubElement(parent, key)
            _dict_to_xml(child, value)
    elif isinstance(data, list):
        for item in data:
            child = ET.SubElement(parent, "item")
            _dict_to_xml(child, item)
    elif data is None:
        parent.text = ""
    else:
        parent.text = str(data)


def _xml_to_data(element: ET.Element) -> Any:
    """Рекурсивно преобразовать XML-элемент в структуру Python.

    Используется для простого восстановления словарей и списков из XML.
    """
    children = list(element)
    if not children:
        text = element.text if element.text is not None else ""
        return text if text != "" else None
    if all(child.tag == "item" for child in children):
        return [_xml_to_data(child) for child in children]
    result: Dict[str, Any] = {}
    for child in children:
        result[child.tag] = _xml_to_data(child)
    return result


class ResortStorage:
    """Хранилище сущностей курорта в памяти.
    
    Использует строковые доменные ID (например, G001) как ключи.
    """
    
    def __init__(self):
        """Инициализировать пустые коллекции для всех типов сущностей."""
        self._guests: Dict[str, Guest] = {}
        self._staff_members: Dict[str, StaffMember] = {}
        self._services: Dict[str, Service] = {}
        self._locations: Dict[str, Location] = {}
        self._bookings: Dict[str, Booking] = {}
        # Счетчики для автоматической генерации ID
        self._next_guest_id: int = 1
        self._next_staff_id: int = 1
        self._next_location_id: int = 1
        self._next_service_id: int = 1
        self._next_booking_id: int = 1
 
    
    def clear_all(self) -> None:
        """Полностью очистить хранилище."""
        self._guests.clear()
        self._staff_members.clear()
        self._services.clear()
        self._locations.clear()
        self._bookings.clear()
        # Сброс счетчиков ID
        self._next_guest_id = 1
        self._next_staff_id = 1
        self._next_location_id = 1
        self._next_service_id = 1
        self._next_booking_id = 1
 
    
    # ========== Генерация ID ==========
    
    def generate_guest_id(self) -> str:
        """Сгенерировать следующий ID для гостя."""
        while True:
            guest_id = f"G{self._next_guest_id:03d}"
            if guest_id not in self._guests:
                self._next_guest_id += 1
                return guest_id
            self._next_guest_id += 1
    
    def generate_staff_id(self) -> str:
        """Сгенерировать следующий ID для сотрудника."""
        while True:
            staff_id = f"S{self._next_staff_id:03d}"
            if staff_id not in self._staff_members:
                self._next_staff_id += 1
                return staff_id
            self._next_staff_id += 1
    
    def generate_location_id(self) -> str:
        """Сгенерировать следующий ID для места."""
        while True:
            location_id = f"L{self._next_location_id:03d}"
            if location_id not in self._locations:
                self._next_location_id += 1
                return location_id
            self._next_location_id += 1
    
    def generate_service_id(self) -> str:
        """Сгенерировать следующий ID для услуги."""
        while True:
            service_id = f"SRV{self._next_service_id:03d}"
            if service_id not in self._services:
                self._next_service_id += 1
                return service_id
            self._next_service_id += 1
    
    def generate_booking_id(self) -> str:
        """Сгенерировать следующий ID для бронирования."""
        while True:
            booking_id = f"B{self._next_booking_id:03d}"
            if booking_id not in self._bookings:
                self._next_booking_id += 1
                return booking_id
            self._next_booking_id += 1
    
    # ========== CRUD для Guest ==========
    
    def create_guest(self, guest: Guest) -> str:
        """Создать нового гостя в хранилище.
        
        Args:
            guest: Объект гостя для создания
            
        Returns:
            Строковый ID созданного гостя
        """
        if not guest.guest_id:
            raise ValidationError("guest_id не может быть пустым")
        if guest.guest_id in self._guests:
            raise ValidationError(f"Гость с ID='{guest.guest_id}' уже существует")
        self._guests[guest.guest_id] = guest
        return guest.guest_id
    
    def get_guest_by_id(self, guest_id: str) -> Guest:
        """Получить гостя по ID.
        
        Args:
            guest_id: ID гостя
            
        Returns:
            Объект гостя
            
        Raises:
            EntityNotFoundError: Если гость с указанным ID не найден
        """
        if guest_id not in self._guests:
            raise EntityNotFoundError(f"Гость с ID='{guest_id}' не найден")
        return self._guests[guest_id]
    
    def list_guests(self) -> List[Guest]:
        """Получить список всех гостей.
        
        Returns:
            Список всех гостей
        """
        return list(self._guests.values())
    
    def update_guest(self, guest_id: str, guest: Guest) -> None:
        """Обновить данные гостя.
        
        Args:
            guest_id: ID гостя для обновления
            guest: Обновлённый объект гостя
            
        Raises:
            EntityNotFoundError: Если гость с указанным ID не найден
        """
        if guest_id not in self._guests:
            raise EntityNotFoundError(f"Гость с ID='{guest_id}' не найден")
        self._guests[guest_id] = guest
    
    def delete_guest(self, guest_id: str) -> None:
        """Удалить гостя из хранилища.
        
        Args:
            guest_id: ID гостя для удаления
            
        Raises:
            EntityNotFoundError: Если гость с указанным ID не найден
        """
        if guest_id not in self._guests:
            raise EntityNotFoundError(f"Гость с ID='{guest_id}' не найден")
        del self._guests[guest_id]
    
    # ========== CRUD для StaffMember ==========
    
    def create_staff_member(self, staff: StaffMember) -> str:
        """Создать нового сотрудника в хранилище.
        
        Args:
            staff: Объект сотрудника для создания
            
        Returns:
            Строковый ID созданного сотрудника
        """
        if not staff.staff_id:
            raise ValidationError("staff_id не может быть пустым")
        # валидируем привязанные услуги
        for sid in staff.service_ids:
            if sid not in self._services:
                raise ValidationError(f"Услуга с ID='{sid}' не существует (для привязки к сотруднику)")
        if staff.staff_id in self._staff_members:
            raise ValidationError(f"Сотрудник с ID='{staff.staff_id}' уже существует")
        self._staff_members[staff.staff_id] = staff
        return staff.staff_id
    
    def get_staff_member_by_id(self, staff_id: str) -> StaffMember:
        """Получить сотрудника по ID.
        
        Args:
            staff_id: ID сотрудника
            
        Returns:
            Объект сотрудника
            
        Raises:
            EntityNotFoundError: Если сотрудник с указанным ID не найден
        """
        if staff_id not in self._staff_members:
            raise EntityNotFoundError(f"Сотрудник с ID='{staff_id}' не найден")
        return self._staff_members[staff_id]
    
    def list_staff_members(self) -> List[StaffMember]:
        """Получить список всех сотрудников.
        
        Returns:
            Список всех сотрудников
        """
        return list(self._staff_members.values())
    
    def update_staff_member(self, staff_id: str, staff: StaffMember) -> None:
        """Обновить данные сотрудника.
        
        Args:
            staff_id: ID сотрудника для обновления
            staff: Обновлённый объект сотрудника
            
        Raises:
            EntityNotFoundError: Если сотрудник с указанным ID не найден
        """
        if staff_id not in self._staff_members:
            raise EntityNotFoundError(f"Сотрудник с ID='{staff_id}' не найден")
        for sid in staff.service_ids:
            if sid not in self._services:
                raise ValidationError(f"Услуга с ID='{sid}' не существует (для привязки к сотруднику)")
        self._staff_members[staff_id] = staff
    
    def delete_staff_member(self, staff_id: str) -> None:
        """Удалить сотрудника из хранилища.
        
        Args:
            staff_id: ID сотрудника для удаления
            
        Raises:
            EntityNotFoundError: Если сотрудник с указанным ID не найден
        """
        if staff_id not in self._staff_members:
            raise EntityNotFoundError(f"Сотрудник с ID='{staff_id}' не найден")
        del self._staff_members[staff_id]
    
    # ========== CRUD для Service ==========
    
    def create_service(self, service: Service) -> str:
        """Создать новую услугу в хранилище.
        
        Args:
            service: Объект услуги для создания
            
        Returns:
            Строковый ID созданной услуги
            
        Raises:
            ValidationError: Если длительность <= 0
        """
        if service.duration_minutes <= 0:
            raise ValidationError(f"Длительность услуги должна быть положительной, получено: {service.duration_minutes}")
        if not service.service_id:
            raise ValidationError("service_id не может быть пустым")
        # валидируем привязанные место/сотрудника, если указаны
        if service.location_id is not None and service.location_id not in self._locations:
            raise ValidationError(f"Место с ID='{service.location_id}' не существует (для услуги)")
        if service.staff_id is not None and service.staff_id not in self._staff_members:
            raise ValidationError(f"Сотрудник с ID='{service.staff_id}' не существует (для услуги)")
        if service.service_id in self._services:
            raise ValidationError(f"Услуга с ID='{service.service_id}' уже существует")
        self._services[service.service_id] = service
        return service.service_id
    
    def get_service_by_id(self, service_id: str) -> Service:
        """Получить услугу по ID.
        
        Args:
            service_id: ID услуги
            
        Returns:
            Объект услуги
            
        Raises:
            EntityNotFoundError: Если услуга с указанным ID не найдена
        """
        if service_id not in self._services:
            raise EntityNotFoundError(f"Услуга с ID='{service_id}' не найдена")
        return self._services[service_id]
    
    def list_services(self) -> List[Service]:
        """Получить список всех услуг.
        
        Returns:
            Список всех услуг
        """
        return list(self._services.values())
    
    def update_service(self, service_id: str, service: Service) -> None:
        """Обновить данные услуги.
        
        Args:
            service_id: ID услуги для обновления
            service: Обновлённый объект услуги
            
        Raises:
            EntityNotFoundError: Если услуга с указанным ID не найдена
            ValidationError: Если длительность <= 0
        """
        if service_id not in self._services:
            raise EntityNotFoundError(f"Услуга с ID='{service_id}' не найдена")
        if service.duration_minutes <= 0:
            raise ValidationError(f"Длительность услуги должна быть положительной, получено: {service.duration_minutes}")
        if service.location_id is not None and service.location_id not in self._locations:
            raise ValidationError(f"Место с ID='{service.location_id}' не существует (для услуги)")
        if service.staff_id is not None and service.staff_id not in self._staff_members:
            raise ValidationError(f"Сотрудник с ID='{service.staff_id}' не существует (для услуги)")
        self._services[service_id] = service
    
    def delete_service(self, service_id: str) -> None:
        """Удалить услугу из хранилища.
        
        Args:
            service_id: ID услуги для удаления
            
        Raises:
            EntityNotFoundError: Если услуга с указанным ID не найдена
        """
        if service_id not in self._services:
            raise EntityNotFoundError(f"Услуга с ID='{service_id}' не найдена")
        del self._services[service_id]
    
    # ========== CRUD для Location ==========
    
    def create_location(self, location: Location) -> str:
        """Создать новое место в хранилище.
        
        Args:
            location: Объект места для создания
            
        Returns:
            Строковый ID созданного места
            
        Raises:
            ValidationError: Если некорректные данные
        """
        if not location.location_id:
            raise ValidationError("location_id не может быть пустым")
        if location.location_id in self._locations:
            raise ValidationError(f"Место с ID='{location.location_id}' уже существует")
        self._locations[location.location_id] = location
        return location.location_id
    
    def get_location_by_id(self, location_id: str) -> Location:
        """Получить место по ID.
        
        Args:
            location_id: ID места
            
        Returns:
            Объект места
            
        Raises:
            EntityNotFoundError: Если место с указанным ID не найдено
        """
        if location_id not in self._locations:
            raise EntityNotFoundError(f"Место с ID='{location_id}' не найдено")
        return self._locations[location_id]
    
    def list_locations(self) -> List[Location]:
        """Получить список всех мест.
        
        Returns:
            Список всех мест
        """
        return list(self._locations.values())
    
    def update_location(self, location_id: str, location: Location) -> None:
        """Обновить данные места.
        
        Args:
            location_id: ID места для обновления
            location: Обновлённый объект места
            
        Raises:
            EntityNotFoundError: Если место с указанным ID не найдено
            ValidationError: Если некорректные данные
        """
        if location_id not in self._locations:
            raise EntityNotFoundError(f"Место с ID='{location_id}' не найдено")
        self._locations[location_id] = location
    
    def delete_location(self, location_id: str) -> None:
        """Удалить место из хранилища.
        
        Args:
            location_id: ID места для удаления
            
        Raises:
            EntityNotFoundError: Если место с указанным ID не найдено
        """
        if location_id not in self._locations:
            raise EntityNotFoundError(f"Место с ID='{location_id}' не найдено")
        del self._locations[location_id]
    
    # ========== CRUD для Booking ==========
    
    def create_booking(self, booking: Booking) -> str:
        """Создать новое бронирование в хранилище.
        
        Args:
            booking: Объект бронирования для создания
            
        Returns:
            Строковый ID созданного бронирования
        """
        if not booking.booking_id:
            raise ValidationError("booking_id не может быть пустым")
        if booking.booking_id in self._bookings:
            raise ValidationError(f"Бронирование с ID='{booking.booking_id}' уже существует")
        # Требования: у услуги должны быть назначены место и сотрудник
        if not booking.service.location_id:
            raise ValidationError("Для услуги не назначено место")
        if not booking.service.staff_id:
            raise ValidationError("Для услуги не назначен сотрудник")
        # Проверка согласованности бронирования с услугой
        if booking.location.location_id != booking.service.location_id:
            raise ValidationError("Место бронирования не совпадает с местом услуги")
        if booking.staff_member is None or booking.staff_member.staff_id != booking.service.staff_id:
            raise ValidationError("Сотрудник бронирования не совпадает с сотрудником услуги")
        # Проверка занятости гостя, сотрудника и места
        for existing in self._bookings.values():
            if existing.time_slot.overlaps(booking.time_slot):
                if existing.guest.guest_id == booking.guest.guest_id:
                    raise ValidationError("Гость занят в это время")
                if existing.staff_member and booking.staff_member and existing.staff_member.staff_id == booking.staff_member.staff_id:
                    raise ValidationError("Сотрудник занят в это время")
                if existing.location.location_id == booking.location.location_id:
                    raise ValidationError("Место занято в это время")
        self._bookings[booking.booking_id] = booking
        return booking.booking_id
    
    def get_booking_by_id(self, booking_id: str) -> Booking:
        """Получить бронирование по ID.
        
        Args:
            booking_id: ID бронирования
            
        Returns:
            Объект бронирования
            
        Raises:
            EntityNotFoundError: Если бронирование с указанным ID не найдено
        """
        if booking_id not in self._bookings:
            raise EntityNotFoundError(f"Бронирование с ID='{booking_id}' не найдено")
        return self._bookings[booking_id]
    
    def list_bookings(self) -> List[Booking]:
        """Получить список всех бронирований.
        
        Returns:
            Список всех бронирований
        """
        return list(self._bookings.values())
    
    def update_booking(self, booking_id: str, booking: Booking) -> None:
        """Обновить данные бронирования.
        
        Args:
            booking_id: ID бронирования для обновления
            booking: Обновлённый объект бронирования
            
        Raises:
            EntityNotFoundError: Если бронирование с указанным ID не найдено
        """
        if booking_id not in self._bookings:
            raise EntityNotFoundError(f"Бронирование с ID='{booking_id}' не найдено")
        self._bookings[booking_id] = booking
    
    def delete_booking(self, booking_id: str) -> None:
        """Удалить бронирование из хранилища.
        
        Args:
            booking_id: ID бронирования для удаления
            
        Raises:
            EntityNotFoundError: Если бронирование с указанным ID не найдено
        """
        if booking_id not in self._bookings:
            raise EntityNotFoundError(f"Бронирование с ID='{booking_id}' не найдено")
        del self._bookings[booking_id]
    
    # (Секция Invoice удалена)
    
    # (Секция Event удалена)

    # ========== СЕРИАЛИЗАЦИЯ ==========

    def save_to_json(self, path: str) -> None:
        """Сохранить все сущности в JSON-файл.

        Args:
            path: Путь к файлу для сохранения
            
        Raises:
            StorageError: При ошибках записи файла
        """
        try:
            data = self._collect_serializable_data()
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except (IOError, OSError, json.JSONEncodeError) as e:
            raise StorageError(f"Ошибка сохранения в JSON-файл '{path}': {e}") from e

    def load_from_json(self, path: str) -> None:
        """Загрузить все сущности из JSON-файла.

        Args:
            path: Путь к файлу JSON
            
        Raises:
            StorageError: При ошибках чтения или парсинга файла
        """
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
            self._load_serializable_data(data)
        except FileNotFoundError:
            raise StorageError(f"Файл '{path}' не найден")
        except (IOError, OSError) as e:
            raise StorageError(f"Ошибка чтения JSON-файла '{path}': {e}") from e
        except json.JSONDecodeError as e:
            raise StorageError(f"Ошибка парсинга JSON-файла '{path}': {e}") from e
        except (KeyError, ValueError, TypeError) as e:
            raise StorageError(f"Ошибка формата данных в JSON-файле '{path}': {e}") from e

    def save_to_xml(self, path: str) -> None:
        """Сохранить все сущности в XML-файл.

        Args:
            path: Путь к файлу для сохранения
            
        Raises:
            StorageError: При ошибках записи файла
        """
        try:
            data = self._collect_serializable_data()
            root = ET.Element("resort_storage")
            for section_name, items in data.items():
                if section_name == "id_counters":
                    # Специальная обработка для счетчиков ID
                    counters_section = ET.SubElement(root, section_name)
                    _dict_to_xml(counters_section, items)
                else:
                    section = ET.SubElement(root, section_name)
                    for item in items:
                        item_element = ET.SubElement(section, "item")
                        _dict_to_xml(item_element, item)
            tree = ET.ElementTree(root)
            tree.write(path, encoding="utf-8", xml_declaration=True)
        except (IOError, OSError) as e:
            raise StorageError(f"Ошибка сохранения в XML-файл '{path}': {e}") from e

    def load_from_xml(self, path: str) -> None:
        """Загрузить все сущности из XML-файла.

        Args:
            path: Путь к XML-файлу
            
        Raises:
            StorageError: При ошибках чтения или парсинга файла
        """
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            data: Dict[str, Any] = {}
            for section in root:
                if section.tag == "id_counters":
                    # Специальная обработка для счетчиков ID
                    data[section.tag] = _xml_to_data(section)
                else:
                    items: List[Any] = []
                    for item in section.findall("item"):
                        items.append(_xml_to_data(item))
                    data[section.tag] = items
            self._load_serializable_data(data)
        except FileNotFoundError:
            raise StorageError(f"Файл '{path}' не найден")
        except (IOError, OSError) as e:
            raise StorageError(f"Ошибка чтения XML-файла '{path}': {e}") from e
        except ET.ParseError as e:
            raise StorageError(f"Ошибка парсинга XML-файла '{path}': {e}") from e
        except (KeyError, ValueError, TypeError) as e:
            raise StorageError(f"Ошибка формата данных в XML-файле '{path}': {e}") from e

    def _collect_serializable_data(self) -> Dict[str, Any]:
        """Собрать все сущности в сериализуемую структуру."""
        return {
            "guests": [
                _guest_to_dict(guest)
                for guest in self._guests.values()
            ],
            "staff_members": [
                _staff_to_dict(staff)
                for staff in self._staff_members.values()
            ],
            "services": [
                _service_to_dict(service)
                for service in self._services.values()
            ],
            "locations": [
                _location_to_dict(location)
                for location in self._locations.values()
            ],
            "bookings": [
                _booking_to_dict(booking)
                for booking in self._bookings.values()
            ],
            "id_counters": {
                "next_guest_id": self._next_guest_id,
                "next_staff_id": self._next_staff_id,
                "next_location_id": self._next_location_id,
                "next_service_id": self._next_service_id,
                "next_booking_id": self._next_booking_id,
            }
        }

    def _load_serializable_data(self, data: Dict[str, Any]) -> None:
        """Загрузить сущности из сериализованной структуры."""
        self.clear_all()

        guest_map: Dict[str, Guest] = {}
        for guest_data in data.get("guests", []):
            guest = _guest_from_dict(guest_data)
            if guest.guest_id:
                self._guests[guest.guest_id] = guest
                guest_map[guest.guest_id] = guest

        staff_map: Dict[str, StaffMember] = {}
        for staff_data in data.get("staff_members", []):
            staff = _staff_from_dict(staff_data)
            if staff.staff_id:
                self._staff_members[staff.staff_id] = staff
                staff_map[staff.staff_id] = staff

        location_map: Dict[str, Location] = {}
        for location_data in data.get("locations", []):
            location = _location_from_dict(location_data)
            if location.location_id:
                self._locations[location.location_id] = location
                location_map[location.location_id] = location

        service_map: Dict[str, Service] = {}
        for service_data in data.get("services", []):
            service = _service_from_dict(service_data)
            if service.service_id:
                self._services[service.service_id] = service
                service_map[service.service_id] = service

        for booking_data in data.get("bookings", []):
            try:
                booking = _booking_from_dict(
                    booking_data,
                    guests=guest_map,
                    services=service_map,
                    locations=location_map,
                    staff_members=staff_map,
                )
            except KeyError:
                continue
            if booking.booking_id:
                self._bookings[booking.booking_id] = booking

        # Секция invoices исключена

        # Секция events исключена
        
        # Восстановление счетчиков ID
        id_counters = data.get("id_counters", {})
        if id_counters:
            # Убеждаемся, что счетчики являются целыми числами
            self._next_guest_id = int(id_counters.get("next_guest_id", 1))
            self._next_staff_id = int(id_counters.get("next_staff_id", 1))
            self._next_location_id = int(id_counters.get("next_location_id", 1))
            self._next_service_id = int(id_counters.get("next_service_id", 1))
            self._next_booking_id = int(id_counters.get("next_booking_id", 1))
        else:
            # Если счетчиков нет, вычисляем максимальные значения из существующих ID
            self._update_id_counters_from_existing()
    
    def _update_id_counters_from_existing(self) -> None:
        """Обновить счетчики ID на основе максимальных значений существующих ID."""
        import re
        
        # Для гостей (G001, G002, ...)
        max_guest = 0
        for guest_id in self._guests.keys():
            match = re.match(r"^G(\d+)$", guest_id)
            if match:
                max_guest = max(max_guest, int(match.group(1)))
        self._next_guest_id = max_guest + 1
        
        # Для сотрудников (S001, S002, ...)
        max_staff = 0
        for staff_id in self._staff_members.keys():
            match = re.match(r"^S(\d+)$", staff_id)
            if match:
                max_staff = max(max_staff, int(match.group(1)))
        self._next_staff_id = max_staff + 1
        
        # Для мест (L001, L002, ...)
        max_location = 0
        for location_id in self._locations.keys():
            match = re.match(r"^L(\d+)$", location_id)
            if match:
                max_location = max(max_location, int(match.group(1)))
        self._next_location_id = max_location + 1
        
        # Для услуг (SRV001, SRV002, ...)
        max_service = 0
        for service_id in self._services.keys():
            match = re.match(r"^SRV(\d+)$", service_id)
            if match:
                max_service = max(max_service, int(match.group(1)))
        self._next_service_id = max_service + 1
        
        # Для бронирований (B001, B002, ...)
        max_booking = 0
        for booking_id in self._bookings.keys():
            match = re.match(r"^B(\d+)$", booking_id)
            if match:
                max_booking = max(max_booking, int(match.group(1)))
        self._next_booking_id = max_booking + 1


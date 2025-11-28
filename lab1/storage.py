"""
Слой хранения для курорта.
Предоставляет CRUD-операции и простую сериализацию доменной модели.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

from models import (
    Booking,
    ContactInfo,
    Event,
    Guest,
    Invoice,
    Location,
    Money,
    Resource,
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


def _money_to_dict(money: Money) -> Dict[str, Any]:
    """Преобразовать Money в словарь."""
    return {
        "amount": money.amount,
        "currency": money.currency,
    }


def _money_from_dict(data: Dict[str, Any]) -> Money:
    """Создать Money из словаря."""
    return Money(
        amount=float(data.get("amount", 0.0)),
        currency=data.get("currency", "RUB"),
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
        "arrival_date": _datetime_to_str(guest.arrival_date),
        "departure_date": _datetime_to_str(guest.departure_date),
    }


def _guest_from_dict(data: Dict[str, Any]) -> Guest:
    """Создать Guest из словаря."""
    guest = Guest(
        guest_id=data.get("guest_id", ""),
        name=data.get("name", ""),
        contact=_contact_from_dict(data.get("contact", {})),
    )
    arrival = _datetime_from_str(data.get("arrival_date"))
    departure = _datetime_from_str(data.get("departure_date"))
    if arrival and departure:
        guest.set_stay_dates(arrival, departure)
    return guest


def _staff_to_dict(staff: StaffMember) -> Dict[str, Any]:
    """Преобразовать StaffMember в словарь."""
    return {
        "staff_id": staff.staff_id,
        "name": staff.name,
        "position": staff.position,
        "contact": _contact_to_dict(staff.contact),
        "specializations": staff.specializations,
    }


def _staff_from_dict(data: Dict[str, Any]) -> StaffMember:
    """Создать StaffMember из словаря."""
    staff = StaffMember(
        staff_id=data.get("staff_id", ""),
        name=data.get("name", ""),
        position=data.get("position", ""),
        contact=_contact_from_dict(data.get("contact", {})),
    )
    for specialization in data.get("specializations", []):
        staff.add_specialization(specialization)
    return staff


def _location_to_dict(location: Location) -> Dict[str, Any]:
    """Преобразовать Location в словарь."""
    return {
        "location_id": location.location_id,
        "name": location.name,
        "capacity": location.capacity,
        "location_type": location.location_type,
        "description": location.description,
    }


def _location_from_dict(data: Dict[str, Any]) -> Location:
    """Создать Location из словаря."""
    location = Location(
        location_id=data.get("location_id", ""),
        name=data.get("name", ""),
        capacity=int(data.get("capacity", 0)),
        location_type=data.get("location_type", ""),
    )
    location.description = data.get("description")
    return location


def _resource_to_dict(resource: Resource) -> Dict[str, Any]:
    """Преобразовать Resource в словарь."""
    return {
        "resource_id": resource.resource_id,
        "name": resource.name,
        "resource_type": resource.resource_type,
        "quantity": resource.quantity,
        "unit": resource.unit,
    }


def _resource_from_dict(data: Dict[str, Any]) -> Resource:
    """Создать Resource из словаря."""
    return Resource(
        resource_id=data.get("resource_id", ""),
        name=data.get("name", ""),
        resource_type=data.get("resource_type", ""),
        quantity=float(data.get("quantity", 0.0)),
        unit=data.get("unit", ""),
    )


def _service_to_dict(service: Service) -> Dict[str, Any]:
    """Преобразовать Service в словарь."""
    return {
        "service_id": service.service_id,
        "name": service.name,
        "service_type": service.service_type,
        "base_price": _money_to_dict(service.base_price),
        "duration_minutes": service.duration_minutes,
        "description": service.description,
        "required_resources": [
            {"resource_id": resource_id, "amount": amount}
            for resource_id, amount in service.required_resources
        ],
    }


def _service_from_dict(data: Dict[str, Any]) -> Service:
    """Создать Service из словаря."""
    service = Service(
        service_id=data.get("service_id", ""),
        name=data.get("name", ""),
        service_type=data.get("service_type", ""),
        base_price=_money_from_dict(data.get("base_price", {})),
        duration_minutes=int(data.get("duration_minutes", 0)),
    )
    service.description = data.get("description")
    for resource in data.get("required_resources", []):
        service.add_required_resource(
            resource_id=resource.get("resource_id", ""),
            amount=float(resource.get("amount", 0.0)),
        )
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
        "status": booking.status,
    }


def _event_to_dict(event: Event) -> Dict[str, Any]:
    """Преобразовать Event в словарь."""
    return {
        "event_id": event.event_id,
        "name": event.name,
        "event_type": event.event_type,
        "time_slot": _timeslot_to_dict(event.time_slot),
        "location_id": event.location.location_id,
        "participants": [guest.guest_id for guest in event.participants],
        "description": event.description,
    }


def _invoice_to_dict(invoice: Invoice) -> Dict[str, Any]:
    """Преобразовать Invoice в словарь."""
    return {
        "invoice_id": invoice.invoice_id,
        "guest_id": invoice.guest.guest_id,
        "issue_date": _datetime_to_str(invoice.issue_date),
        "items": [
            {"service_id": service.service_id, "price": _money_to_dict(price)}
            for service, price in invoice.items
        ],
        "status": invoice.status,
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
        booking.status = data.get("status", booking.status)
    else:
        booking.status = data.get("status", booking.status)
    return booking


def _event_from_dict(
    data: Dict[str, Any],
    guests: Dict[str, Guest],
    locations: Dict[str, Location],
) -> Event:
    """Создать Event из словаря."""
    location_id = data.get("location_id")
    if not location_id or location_id not in locations:
        raise KeyError("location_id")
    location = locations[location_id]
    event = Event(
        event_id=data.get("event_id", ""),
        name=data.get("name", ""),
        event_type=data.get("event_type", ""),
        time_slot=_timeslot_from_dict(data.get("time_slot", {})),
        location=location,
    )
    event.description = data.get("description")
    for guest_id in data.get("participants", []):
        if guest_id in guests:
            event.add_participant(guests[guest_id])
    return event


def _invoice_from_dict(
    data: Dict[str, Any],
    guests: Dict[str, Guest],
    services: Dict[str, Service],
) -> Invoice:
    """Создать Invoice из словаря."""
    guest_id = data.get("guest_id")
    if not guest_id or guest_id not in guests:
        raise KeyError("guest_id")
    guest = guests[guest_id]
    invoice = Invoice(
        invoice_id=data.get("invoice_id", ""),
        guest=guest,
        issue_date=_datetime_from_str(data.get("issue_date")) or datetime.now(),
    )
    for item in data.get("items", []):
        service_id = item.get("service_id")
        if service_id in services:
            invoice.add_item(services[service_id], _money_from_dict(item.get("price", {})))
    invoice.status = data.get("status", invoice.status)
    return invoice


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
    """Рекурсивно преобразовать XML-элемент в структуру Python."""
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


def _safe_int(value: Any, default: int = 0) -> int:
    """Безопасно преобразовать значение к int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class ResortStorage:
    """Хранилище сущностей курорта в памяти."""
    
    def __init__(self):
        """Инициализировать хранилище с пустыми словарями для каждой сущности."""
        self._guests: Dict[int, Guest] = {}
        self._staff_members: Dict[int, StaffMember] = {}
        self._services: Dict[int, Service] = {}
        self._locations: Dict[int, Location] = {}
        self._resources: Dict[int, Resource] = {}
        self._bookings: Dict[int, Booking] = {}
        self._invoices: Dict[int, Invoice] = {}
        self._events: Dict[int, Event] = {}
        
        # Счётчики для генерации ID
        self._next_guest_id: int = 1
        self._next_staff_id: int = 1
        self._next_service_id: int = 1
        self._next_location_id: int = 1
        self._next_resource_id: int = 1
        self._next_booking_id: int = 1
        self._next_invoice_id: int = 1
        self._next_event_id: int = 1
    
    def clear_all(self) -> None:
        """Полностью очистить хранилище и сбросить счётчики."""
        self._guests.clear()
        self._staff_members.clear()
        self._services.clear()
        self._locations.clear()
        self._resources.clear()
        self._bookings.clear()
        self._invoices.clear()
        self._events.clear()
        
        self._next_guest_id = 1
        self._next_staff_id = 1
        self._next_service_id = 1
        self._next_location_id = 1
        self._next_resource_id = 1
        self._next_booking_id = 1
        self._next_invoice_id = 1
        self._next_event_id = 1
    
    # ========== CRUD для Guest ==========
    
    def create_guest(self, guest: Guest) -> int:
        """Создать нового гостя в хранилище.
        
        Args:
            guest: Объект гостя для создания
            
        Returns:
            Целочисленный ID созданного гостя
        """
        guest_id = self._next_guest_id
        self._next_guest_id += 1
        self._guests[guest_id] = guest
        return guest_id
    
    def get_guest_by_id(self, guest_id: int) -> Optional[Guest]:
        """Получить гостя по ID.
        
        Args:
            guest_id: ID гостя
            
        Returns:
            Объект гостя или None, если не найден
        """
        return self._guests.get(guest_id)
    
    def list_guests(self) -> List[Guest]:
        """Получить список всех гостей.
        
        Returns:
            Список всех гостей
        """
        return list(self._guests.values())
    
    def update_guest(self, guest_id: int, guest: Guest) -> bool:
        """Обновить данные гостя.
        
        Args:
            guest_id: ID гостя для обновления
            guest: Обновлённый объект гостя
            
        Returns:
            True, если обновление успешно, False если гость не найден
        """
        if guest_id not in self._guests:
            return False
        self._guests[guest_id] = guest
        return True
    
    def delete_guest(self, guest_id: int) -> bool:
        """Удалить гостя из хранилища.
        
        Args:
            guest_id: ID гостя для удаления
            
        Returns:
            True, если удаление успешно, False если гость не найден
        """
        if guest_id not in self._guests:
            return False
        del self._guests[guest_id]
        return True
    
    # ========== CRUD для StaffMember ==========
    
    def create_staff_member(self, staff: StaffMember) -> int:
        """Создать нового сотрудника в хранилище.
        
        Args:
            staff: Объект сотрудника для создания
            
        Returns:
            Целочисленный ID созданного сотрудника
        """
        staff_id = self._next_staff_id
        self._next_staff_id += 1
        self._staff_members[staff_id] = staff
        return staff_id
    
    def get_staff_member_by_id(self, staff_id: int) -> Optional[StaffMember]:
        """Получить сотрудника по ID.
        
        Args:
            staff_id: ID сотрудника
            
        Returns:
            Объект сотрудника или None, если не найден
        """
        return self._staff_members.get(staff_id)
    
    def list_staff_members(self) -> List[StaffMember]:
        """Получить список всех сотрудников.
        
        Returns:
            Список всех сотрудников
        """
        return list(self._staff_members.values())
    
    def update_staff_member(self, staff_id: int, staff: StaffMember) -> bool:
        """Обновить данные сотрудника.
        
        Args:
            staff_id: ID сотрудника для обновления
            staff: Обновлённый объект сотрудника
            
        Returns:
            True, если обновление успешно, False если сотрудник не найден
        """
        if staff_id not in self._staff_members:
            return False
        self._staff_members[staff_id] = staff
        return True
    
    def delete_staff_member(self, staff_id: int) -> bool:
        """Удалить сотрудника из хранилища.
        
        Args:
            staff_id: ID сотрудника для удаления
            
        Returns:
            True, если удаление успешно, False если сотрудник не найден
        """
        if staff_id not in self._staff_members:
            return False
        del self._staff_members[staff_id]
        return True
    
    # ========== CRUD для Service ==========
    
    def create_service(self, service: Service) -> int:
        """Создать новую услугу в хранилище.
        
        Args:
            service: Объект услуги для создания
            
        Returns:
            Целочисленный ID созданной услуги
        """
        service_id = self._next_service_id
        self._next_service_id += 1
        self._services[service_id] = service
        return service_id
    
    def get_service_by_id(self, service_id: int) -> Optional[Service]:
        """Получить услугу по ID.
        
        Args:
            service_id: ID услуги
            
        Returns:
            Объект услуги или None, если не найдена
        """
        return self._services.get(service_id)
    
    def list_services(self) -> List[Service]:
        """Получить список всех услуг.
        
        Returns:
            Список всех услуг
        """
        return list(self._services.values())
    
    def update_service(self, service_id: int, service: Service) -> bool:
        """Обновить данные услуги.
        
        Args:
            service_id: ID услуги для обновления
            service: Обновлённый объект услуги
            
        Returns:
            True, если обновление успешно, False если услуга не найдена
        """
        if service_id not in self._services:
            return False
        self._services[service_id] = service
        return True
    
    def delete_service(self, service_id: int) -> bool:
        """Удалить услугу из хранилища.
        
        Args:
            service_id: ID услуги для удаления
            
        Returns:
            True, если удаление успешно, False если услуга не найдена
        """
        if service_id not in self._services:
            return False
        del self._services[service_id]
        return True
    
    # ========== CRUD для Location ==========
    
    def create_location(self, location: Location) -> int:
        """Создать новое место в хранилище.
        
        Args:
            location: Объект места для создания
            
        Returns:
            Целочисленный ID созданного места
        """
        location_id = self._next_location_id
        self._next_location_id += 1
        self._locations[location_id] = location
        return location_id
    
    def get_location_by_id(self, location_id: int) -> Optional[Location]:
        """Получить место по ID.
        
        Args:
            location_id: ID места
            
        Returns:
            Объект места или None, если не найдено
        """
        return self._locations.get(location_id)
    
    def list_locations(self) -> List[Location]:
        """Получить список всех мест.
        
        Returns:
            Список всех мест
        """
        return list(self._locations.values())
    
    def update_location(self, location_id: int, location: Location) -> bool:
        """Обновить данные места.
        
        Args:
            location_id: ID места для обновления
            location: Обновлённый объект места
            
        Returns:
            True, если обновление успешно, False если место не найдено
        """
        if location_id not in self._locations:
            return False
        self._locations[location_id] = location
        return True
    
    def delete_location(self, location_id: int) -> bool:
        """Удалить место из хранилища.
        
        Args:
            location_id: ID места для удаления
            
        Returns:
            True, если удаление успешно, False если место не найдено
        """
        if location_id not in self._locations:
            return False
        del self._locations[location_id]
        return True
    
    # ========== CRUD для Resource ==========
    
    def create_resource(self, resource: Resource) -> int:
        """Создать новый ресурс в хранилище.
        
        Args:
            resource: Объект ресурса для создания
            
        Returns:
            Целочисленный ID созданного ресурса
        """
        resource_id = self._next_resource_id
        self._next_resource_id += 1
        self._resources[resource_id] = resource
        return resource_id
    
    def get_resource_by_id(self, resource_id: int) -> Optional[Resource]:
        """Получить ресурс по ID.
        
        Args:
            resource_id: ID ресурса
            
        Returns:
            Объект ресурса или None, если не найден
        """
        return self._resources.get(resource_id)
    
    def list_resources(self) -> List[Resource]:
        """Получить список всех ресурсов.
        
        Returns:
            Список всех ресурсов
        """
        return list(self._resources.values())
    
    def update_resource(self, resource_id: int, resource: Resource) -> bool:
        """Обновить данные ресурса.
        
        Args:
            resource_id: ID ресурса для обновления
            resource: Обновлённый объект ресурса
            
        Returns:
            True, если обновление успешно, False если ресурс не найден
        """
        if resource_id not in self._resources:
            return False
        self._resources[resource_id] = resource
        return True
    
    def delete_resource(self, resource_id: int) -> bool:
        """Удалить ресурс из хранилища.
        
        Args:
            resource_id: ID ресурса для удаления
            
        Returns:
            True, если удаление успешно, False если ресурс не найден
        """
        if resource_id not in self._resources:
            return False
        del self._resources[resource_id]
        return True
    
    # ========== CRUD для Booking ==========
    
    def create_booking(self, booking: Booking) -> int:
        """Создать новое бронирование в хранилище.
        
        Args:
            booking: Объект бронирования для создания
            
        Returns:
            Целочисленный ID созданного бронирования
        """
        booking_id = self._next_booking_id
        self._next_booking_id += 1
        self._bookings[booking_id] = booking
        return booking_id
    
    def get_booking_by_id(self, booking_id: int) -> Optional[Booking]:
        """Получить бронирование по ID.
        
        Args:
            booking_id: ID бронирования
            
        Returns:
            Объект бронирования или None, если не найдено
        """
        return self._bookings.get(booking_id)
    
    def list_bookings(self) -> List[Booking]:
        """Получить список всех бронирований.
        
        Returns:
            Список всех бронирований
        """
        return list(self._bookings.values())
    
    def update_booking(self, booking_id: int, booking: Booking) -> bool:
        """Обновить данные бронирования.
        
        Args:
            booking_id: ID бронирования для обновления
            booking: Обновлённый объект бронирования
            
        Returns:
            True, если обновление успешно, False если бронирование не найдено
        """
        if booking_id not in self._bookings:
            return False
        self._bookings[booking_id] = booking
        return True
    
    def delete_booking(self, booking_id: int) -> bool:
        """Удалить бронирование из хранилища.
        
        Args:
            booking_id: ID бронирования для удаления
            
        Returns:
            True, если удаление успешно, False если бронирование не найдено
        """
        if booking_id not in self._bookings:
            return False
        del self._bookings[booking_id]
        return True
    
    # ========== CRUD для Invoice ==========
    
    def create_invoice(self, invoice: Invoice) -> int:
        """Создать новый счёт в хранилище.
        
        Args:
            invoice: Объект счёта для создания
            
        Returns:
            Целочисленный ID созданного счёта
        """
        invoice_id = self._next_invoice_id
        self._next_invoice_id += 1
        self._invoices[invoice_id] = invoice
        return invoice_id
    
    def get_invoice_by_id(self, invoice_id: int) -> Optional[Invoice]:
        """Получить счёт по ID.
        
        Args:
            invoice_id: ID счёта
            
        Returns:
            Объект счёта или None, если не найден
        """
        return self._invoices.get(invoice_id)
    
    def list_invoices(self) -> List[Invoice]:
        """Получить список всех счетов.
        
        Returns:
            Список всех счетов
        """
        return list(self._invoices.values())
    
    def update_invoice(self, invoice_id: int, invoice: Invoice) -> bool:
        """Обновить данные счёта.
        
        Args:
            invoice_id: ID счёта для обновления
            invoice: Обновлённый объект счёта
            
        Returns:
            True, если обновление успешно, False если счёт не найден
        """
        if invoice_id not in self._invoices:
            return False
        self._invoices[invoice_id] = invoice
        return True
    
    def delete_invoice(self, invoice_id: int) -> bool:
        """Удалить счёт из хранилища.
        
        Args:
            invoice_id: ID счёта для удаления
            
        Returns:
            True, если удаление успешно, False если счёт не найден
        """
        if invoice_id not in self._invoices:
            return False
        del self._invoices[invoice_id]
        return True
    
    # ========== CRUD для Event ==========
    
    def create_event(self, event: Event) -> int:
        """Создать новое событие в хранилище.
        
        Args:
            event: Объект события для создания
            
        Returns:
            Целочисленный ID созданного события
        """
        event_id = self._next_event_id
        self._next_event_id += 1
        self._events[event_id] = event
        return event_id
    
    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """Получить событие по ID.
        
        Args:
            event_id: ID события
            
        Returns:
            Объект события или None, если не найдено
        """
        return self._events.get(event_id)
    
    def list_events(self) -> List[Event]:
        """Получить список всех событий.
        
        Returns:
            Список всех событий
        """
        return list(self._events.values())
    
    def update_event(self, event_id: int, event: Event) -> bool:
        """Обновить данные события.
        
        Args:
            event_id: ID события для обновления
            event: Обновлённый объект события
            
        Returns:
            True, если обновление успешно, False если событие не найдено
        """
        if event_id not in self._events:
            return False
        self._events[event_id] = event
        return True
    
    def delete_event(self, event_id: int) -> bool:
        """Удалить событие из хранилища.
        
        Args:
            event_id: ID события для удаления
            
        Returns:
            True, если удаление успешно, False если событие не найдено
        """
        if event_id not in self._events:
            return False
        del self._events[event_id]
        return True

    # ========== СЕРИАЛИЗАЦИЯ ==========

    def save_to_json(self, path: str) -> None:
        """Сохранить все сущности в JSON-файл.

        Args:
            path: Путь к файлу для сохранения
        """
        data = self._collect_serializable_data()
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def load_from_json(self, path: str) -> None:
        """Загрузить все сущности из JSON-файла.

        Args:
            path: Путь к файлу JSON
        """
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self._load_serializable_data(data)

    def save_to_xml(self, path: str) -> None:
        """Сохранить все сущности в XML-файл.

        Args:
            path: Путь к файлу для сохранения
        """
        data = self._collect_serializable_data()
        root = ET.Element("resort_storage")
        for section_name, items in data.items():
            section = ET.SubElement(root, section_name)
            for item in items:
                item_element = ET.SubElement(section, "item")
                _dict_to_xml(item_element, item)
        tree = ET.ElementTree(root)
        tree.write(path, encoding="utf-8", xml_declaration=True)

    def load_from_xml(self, path: str) -> None:
        """Загрузить все сущности из XML-файла.

        Args:
            path: Путь к XML-файлу
        """
        tree = ET.parse(path)
        root = tree.getroot()
        data: Dict[str, List[Any]] = {}
        for section in root:
            items: List[Any] = []
            for item in section.findall("item"):
                items.append(_xml_to_data(item))
            data[section.tag] = items
        self._load_serializable_data(data)

    def _collect_serializable_data(self) -> Dict[str, Any]:
        """Собрать все сущности в сериализуемую структуру."""
        return {
            "guests": [
                {"storage_id": guest_id, "data": _guest_to_dict(guest)}
                for guest_id, guest in self._guests.items()
            ],
            "staff_members": [
                {"storage_id": staff_id, "data": _staff_to_dict(staff)}
                for staff_id, staff in self._staff_members.items()
            ],
            "services": [
                {"storage_id": service_id, "data": _service_to_dict(service)}
                for service_id, service in self._services.items()
            ],
            "locations": [
                {"storage_id": location_id, "data": _location_to_dict(location)}
                for location_id, location in self._locations.items()
            ],
            "resources": [
                {"storage_id": resource_id, "data": _resource_to_dict(resource)}
                for resource_id, resource in self._resources.items()
            ],
            "bookings": [
                {"storage_id": booking_id, "data": _booking_to_dict(booking)}
                for booking_id, booking in self._bookings.items()
            ],
            "invoices": [
                {"storage_id": invoice_id, "data": _invoice_to_dict(invoice)}
                for invoice_id, invoice in self._invoices.items()
            ],
            "events": [
                {"storage_id": event_id, "data": _event_to_dict(event)}
                for event_id, event in self._events.items()
            ],
        }

    def _load_serializable_data(self, data: Dict[str, Any]) -> None:
        """Загрузить сущности из сериализованной структуры."""
        self.clear_all()

        guest_map: Dict[str, Guest] = {}
        for item in data.get("guests", []):
            storage_id = _safe_int(item.get("storage_id"), 0)
            guest = _guest_from_dict(item.get("data", {}))
            if storage_id <= 0:
                storage_id = self._next_guest_id
                self._next_guest_id += 1
            self._guests[storage_id] = guest
            guest_map[guest.guest_id] = guest
        self._next_guest_id = max(self._guests.keys(), default=0) + 1

        staff_map: Dict[str, StaffMember] = {}
        for item in data.get("staff_members", []):
            storage_id = _safe_int(item.get("storage_id"), 0)
            staff = _staff_from_dict(item.get("data", {}))
            if storage_id <= 0:
                storage_id = self._next_staff_id
                self._next_staff_id += 1
            self._staff_members[storage_id] = staff
            staff_map[staff.staff_id] = staff
        self._next_staff_id = max(self._staff_members.keys(), default=0) + 1

        location_map: Dict[str, Location] = {}
        for item in data.get("locations", []):
            storage_id = _safe_int(item.get("storage_id"), 0)
            location = _location_from_dict(item.get("data", {}))
            if storage_id <= 0:
                storage_id = self._next_location_id
                self._next_location_id += 1
            self._locations[storage_id] = location
            location_map[location.location_id] = location
        self._next_location_id = max(self._locations.keys(), default=0) + 1

        resource_map: Dict[str, Resource] = {}
        for item in data.get("resources", []):
            storage_id = _safe_int(item.get("storage_id"), 0)
            resource = _resource_from_dict(item.get("data", {}))
            if storage_id <= 0:
                storage_id = self._next_resource_id
                self._next_resource_id += 1
            self._resources[storage_id] = resource
            resource_map[resource.resource_id] = resource
        self._next_resource_id = max(self._resources.keys(), default=0) + 1

        service_map: Dict[str, Service] = {}
        for item in data.get("services", []):
            storage_id = _safe_int(item.get("storage_id"), 0)
            service = _service_from_dict(item.get("data", {}))
            if storage_id <= 0:
                storage_id = self._next_service_id
                self._next_service_id += 1
            self._services[storage_id] = service
            service_map[service.service_id] = service
        self._next_service_id = max(self._services.keys(), default=0) + 1

        for item in data.get("bookings", []):
            storage_id = _safe_int(item.get("storage_id"), 0)
            booking_data = item.get("data", {})
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
            if storage_id <= 0:
                storage_id = self._next_booking_id
                self._next_booking_id += 1
            self._bookings[storage_id] = booking
        self._next_booking_id = max(self._bookings.keys(), default=0) + 1

        for item in data.get("invoices", []):
            storage_id = _safe_int(item.get("storage_id"), 0)
            invoice_data = item.get("data", {})
            if not invoice_data.get("guest_id"):
                continue
            invoice = _invoice_from_dict(
                invoice_data,
                guests=guest_map,
                services=service_map,
            )
            if storage_id <= 0:
                storage_id = self._next_invoice_id
                self._next_invoice_id += 1
            self._invoices[storage_id] = invoice
        self._next_invoice_id = max(self._invoices.keys(), default=0) + 1

        for item in data.get("events", []):
            storage_id = _safe_int(item.get("storage_id"), 0)
            event_data = item.get("data", {})
            location_id = event_data.get("location_id")
            if not location_id or location_id not in location_map:
                continue
            event = _event_from_dict(
                event_data,
                guests=guest_map,
                locations=location_map,
            )
            if storage_id <= 0:
                storage_id = self._next_event_id
                self._next_event_id += 1
            self._events[storage_id] = event
        self._next_event_id = max(self._events.keys(), default=0) + 1


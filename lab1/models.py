"""
Доменная модель курорта.
Содержит основные классы: гости, персонал, услуги, бронирования и места.
"""

from datetime import datetime, time
from typing import Optional, List


class ContactInfo:
    """Контактная информация для гостей и сотрудников."""
    
    def __init__(self, email: str, phone: str, address: Optional[str] = None):
        self.email: str = email
        self.phone: str = phone
        self.address: Optional[str] = address
    
    def __str__(self) -> str:
        return f"КонтактнаяИнформация(email={self.email}, телефон={self.phone})"


class Guest:
    """Представляет гостя, проживающего на курорте."""
    
    def __init__(self, guest_id: str, name: str, contact: ContactInfo):
        self.guest_id: str = guest_id
        self.name: str = name
        self.contact: ContactInfo = contact
    
    def __str__(self) -> str:
        return f"Гость(id={self.guest_id}, имя={self.name})"


class StaffMember:
    """Представляет сотрудника, работающего на курорте."""
    
    def __init__(self, staff_id: str, name: str, role: str, contact: ContactInfo):
        self.staff_id: str = staff_id
        self.name: str = name
        self.role: str = role
        self.contact: ContactInfo = contact
        self.service_ids: List[str] = []
    
    def assign_service(self, service_id: str) -> None:
        """Привязать сотрудника к услуге по её ID."""
        if service_id and service_id not in self.service_ids:
            self.service_ids.append(service_id)
    
    def supports_service(self, service_id: str) -> bool:
        """Проверить, может ли сотрудник оказывать услугу с указанным ID."""
        return service_id in self.service_ids
    
    def __str__(self) -> str:
        return f"Сотрудник(id={self.staff_id}, имя={self.name}, роль={self.role})"


class Location:
    """Физическое место (кабинет, ванна, тропа и т.д.)."""
    
    def __init__(self, location_id: str, name: str, location_type: str):
        self.location_id: str = location_id
        self.name: str = name
        self.location_type: str = location_type  # например: "грязевая_ванна", "баня", "массажный_кабинет"
        self.description: Optional[str] = None
    
    def __str__(self) -> str:
        return f"Место(id={self.location_id}, название={self.name}, тип={self.location_type})"


class TimeSlot:
    """Временной интервал для планирования услуг."""
    
    def __init__(self, start_time: datetime, end_time: datetime):
        self.start_time: datetime = start_time
        self.end_time: datetime = end_time
    
    def overlaps(self, other: 'TimeSlot') -> bool:
        """Проверить пересечение с другим интервалом."""
        return (self.start_time < other.end_time and self.end_time > other.start_time)
    
    def duration_minutes(self) -> int:
        """Вычислить длительность временного слота в минутах."""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
    
    def __str__(self) -> str:
        return f"ВременнойСлот({self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')})"


class Service:
    """Услуга, предлагаемая на курорте."""
    
    def __init__(self, service_id: str, name: str, service_type: str, duration_minutes: int):
        self.service_id: str = service_id
        self.name: str = name
        self.service_type: str = service_type  # например: "грязевая_ванна", "массаж", "прогулка", "баня"
        self.duration_minutes: int = duration_minutes
        self.description: Optional[str] = None
        self.location_id: Optional[str] = None
        self.staff_id: Optional[str] = None
    
    def assign_location(self, location_id: str) -> None:
        self.location_id = location_id
    
    def assign_staff(self, staff_id: str) -> None:
        self.staff_id = staff_id
    
    def __str__(self) -> str:
        return f"Услуга(id={self.service_id}, название={self.name}, длительность={self.duration_minutes} мин)"


class Booking:
    """Бронирование услуги гостем."""
    
    def __init__(self, booking_id: str, guest: Guest, service: Service, time_slot: TimeSlot, location: Location):
        self.booking_id: str = booking_id
        self.guest: Guest = guest
        self.service: Service = service
        self.time_slot: TimeSlot = time_slot
        self.location: Location = location
        self.staff_member: Optional[StaffMember] = None
        self.status: str = "ожидает"  # варианты: "ожидает", "подтверждено", "завершено", "отменено"
    
    def assign_staff(self, staff: StaffMember) -> None:
        """Назначить сотрудника на бронирование."""
        self.staff_member = staff
        self.status = "подтверждено"
    
    def is_confirmed(self) -> bool:
        """Проверить, подтверждено ли бронирование."""
        return self.status == "подтверждено"
    
    def __str__(self) -> str:
        return f"Бронирование(id={self.booking_id}, гость={self.guest.name}, услуга={self.service.name}, статус={self.status})"


 


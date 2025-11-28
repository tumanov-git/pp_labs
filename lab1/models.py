"""
Доменная модель природного оздоровительного курорта в болотной зоне.
Содержит все основные классы для управления гостями, персоналом, услугами и бронированиями.
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


class Money:
    """Представляет денежные суммы в системе."""
    
    def __init__(self, amount: float, currency: str = "RUB"):
        self.amount: float = amount
        self.currency: str = currency
    
    def add(self, other: 'Money') -> 'Money':
        """Добавить другой объект Money к этому."""
        if self.currency != other.currency:
            raise ValueError("Нельзя складывать разные валюты")
        return Money(self.amount + other.amount, self.currency)
    
    def __str__(self) -> str:
        return f"{self.amount:.2f} {self.currency}"


class Guest:
    """Представляет гостя, проживающего на курорте."""
    
    def __init__(self, guest_id: str, name: str, contact: ContactInfo):
        self.guest_id: str = guest_id
        self.name: str = name
        self.contact: ContactInfo = contact
        self.arrival_date: Optional[datetime] = None
        self.departure_date: Optional[datetime] = None
    
    def set_stay_dates(self, arrival: datetime, departure: datetime) -> None:
        """Установить даты прибытия и отъезда для гостя."""
        self.arrival_date = arrival
        self.departure_date = departure
    
    def __str__(self) -> str:
        return f"Гость(id={self.guest_id}, имя={self.name})"


class StaffMember:
    """Представляет сотрудника, работающего на курорте."""
    
    def __init__(self, staff_id: str, name: str, position: str, contact: ContactInfo):
        self.staff_id: str = staff_id
        self.name: str = name
        self.position: str = position
        self.contact: ContactInfo = contact
        self.specializations: List[str] = []
    
    def add_specialization(self, specialization: str) -> None:
        """Добавить специализацию сотруднику."""
        if specialization not in self.specializations:
            self.specializations.append(specialization)
    
    def __str__(self) -> str:
        return f"Сотрудник(id={self.staff_id}, имя={self.name}, должность={self.position})"


class Location:
    """Представляет физическое место на курорте."""
    
    def __init__(self, location_id: str, name: str, capacity: int, location_type: str):
        self.location_id: str = location_id
        self.name: str = name
        self.capacity: int = capacity
        self.location_type: str = location_type  # например: "грязевая_ванна", "баня", "массажный_кабинет"
        self.description: Optional[str] = None
    
    def can_accommodate(self, number_of_people: int) -> bool:
        """Проверить, может ли место вместить указанное количество людей."""
        return number_of_people <= self.capacity
    
    def __str__(self) -> str:
        return f"Место(id={self.location_id}, название={self.name}, вместимость={self.capacity})"


class Resource:
    """Представляет ресурс, используемый на курорте (грязь, растительные материалы, расходники)."""
    
    def __init__(self, resource_id: str, name: str, resource_type: str, quantity: float, unit: str):
        self.resource_id: str = resource_id
        self.name: str = name
        self.resource_type: str = resource_type  # например: "грязь", "травы", "расходники"
        self.quantity: float = quantity
        self.unit: str = unit  # например: "кг", "литры", "штуки"
    
    def consume(self, amount: float) -> bool:
        """Потребить указанное количество ресурса. Возвращает True при успехе."""
        if amount <= self.quantity:
            self.quantity -= amount
            return True
        return False
    
    def is_available(self, required_amount: float) -> bool:
        """Проверить, достаточно ли ресурса доступно."""
        return self.quantity >= required_amount
    
    def __str__(self) -> str:
        return f"Ресурс(id={self.resource_id}, название={self.name}, количество={self.quantity} {self.unit})"


class TimeSlot:
    """Представляет временной слот для планирования услуг."""
    
    def __init__(self, start_time: datetime, end_time: datetime):
        self.start_time: datetime = start_time
        self.end_time: datetime = end_time
    
    def overlaps(self, other: 'TimeSlot') -> bool:
        """Проверить, пересекается ли этот временной слот с другим."""
        return (self.start_time < other.end_time and self.end_time > other.start_time)
    
    def duration_minutes(self) -> int:
        """Вычислить длительность временного слота в минутах."""
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)
    
    def __str__(self) -> str:
        return f"ВременнойСлот({self.start_time.strftime('%Y-%m-%d %H:%M')} - {self.end_time.strftime('%H:%M')})"


class Service:
    """Представляет услугу, предлагаемую на курорте."""
    
    def __init__(self, service_id: str, name: str, service_type: str, base_price: Money, duration_minutes: int):
        self.service_id: str = service_id
        self.name: str = name
        self.service_type: str = service_type  # например: "грязевая_ванна", "массаж", "прогулка", "баня"
        self.base_price: Money = base_price
        self.duration_minutes: int = duration_minutes
        self.description: Optional[str] = None
        self.required_resources: List[tuple] = []  # Список кортежей (resource_id, amount)
    
    def add_required_resource(self, resource_id: str, amount: float) -> None:
        """Добавить требуемый ресурс для этой услуги."""
        self.required_resources.append((resource_id, amount))
    
    def calculate_price(self, discount_percent: float = 0.0) -> Money:
        """Вычислить итоговую цену с опциональной скидкой."""
        discount_amount = self.base_price.amount * (discount_percent / 100)
        final_amount = self.base_price.amount - discount_amount
        return Money(final_amount, self.base_price.currency)
    
    def __str__(self) -> str:
        return f"Услуга(id={self.service_id}, название={self.name}, цена={self.base_price})"


class Booking:
    """Представляет бронирование услуги гостем."""
    
    def __init__(self, booking_id: str, guest: Guest, service: Service, time_slot: TimeSlot, location: Location):
        self.booking_id: str = booking_id
        self.guest: Guest = guest
        self.service: Service = service
        self.time_slot: TimeSlot = time_slot
        self.location: Location = location
        self.staff_member: Optional[StaffMember] = None
        self.status: str = "ожидает"  # "ожидает", "подтверждено", "завершено", "отменено"
    
    def assign_staff(self, staff: StaffMember) -> None:
        """Назначить сотрудника на это бронирование."""
        self.staff_member = staff
        self.status = "подтверждено"
    
    def is_confirmed(self) -> bool:
        """Проверить, подтверждено ли бронирование."""
        return self.status == "подтверждено"
    
    def __str__(self) -> str:
        return f"Бронирование(id={self.booking_id}, гость={self.guest.name}, услуга={self.service.name}, статус={self.status})"


class Event:
    """Представляет событие, происходящее на курорте."""
    
    def __init__(self, event_id: str, name: str, event_type: str, time_slot: TimeSlot, location: Location):
        self.event_id: str = event_id
        self.name: str = name
        self.event_type: str = event_type  # например: "оздоровительная_программа", "групповая_прогулка", "мастер_класс"
        self.time_slot: TimeSlot = time_slot
        self.location: Location = location
        self.participants: List[Guest] = []
        self.description: Optional[str] = None
    
    def add_participant(self, guest: Guest) -> bool:
        """Добавить участника к событию. Возвращает True при успехе."""
        if len(self.participants) < self.location.capacity:
            self.participants.append(guest)
            return True
        return False
    
    def participant_count(self) -> int:
        """Получить количество участников."""
        return len(self.participants)
    
    def __str__(self) -> str:
        return f"Событие(id={self.event_id}, название={self.name}, участников={self.participant_count()})"


class Invoice:
    """Представляет счёт за услуги, предоставленные гостю."""
    
    def __init__(self, invoice_id: str, guest: Guest, issue_date: datetime):
        self.invoice_id: str = invoice_id
        self.guest: Guest = guest
        self.issue_date: datetime = issue_date
        self.items: List[tuple] = []  # Список кортежей (service, price)
        self.status: str = "не_оплачен"  # "не_оплачен", "оплачен", "отменён"
    
    def add_item(self, service: Service, price: Money) -> None:
        """Добавить позицию услуги в счёт."""
        self.items.append((service, price))
    
    def calculate_total(self) -> Money:
        """Вычислить общую сумму счёта."""
        if not self.items:
            return Money(0.0)
        
        total = Money(0.0, self.items[0][1].currency)
        for _, price in self.items:
            total = total.add(price)
        return total
    
    def mark_paid(self) -> None:
        """Отметить счёт как оплаченный."""
        self.status = "оплачен"
    
    def __str__(self) -> str:
        return f"Счёт(id={self.invoice_id}, гость={self.guest.name}, итого={self.calculate_total()}, статус={self.status})"


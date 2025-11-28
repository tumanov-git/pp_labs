"""
Слой хранения для курорта.
Предоставляет CRUD-операции для всех сущностей доменной модели.
"""

from typing import Dict, List, Optional
from models import (
    Guest,
    StaffMember,
    Service,
    Location,
    Resource,
    Booking,
    Invoice,
    Event
)


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


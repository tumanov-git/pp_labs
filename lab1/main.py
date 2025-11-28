"""
Минимальный демонстрационный скрипт для доменной модели природного оздоровительного курорта.
Создаёт примеры объектов и выводит их для демонстрации модели.
"""

from datetime import datetime, timedelta
from models import (
    ContactInfo,
    Money,
    Guest,
    StaffMember,
    Location,
    Resource,
    TimeSlot,
    Service,
    Booking,
    Event,
    Invoice
)


def main():
    """Создать примеры объектов и продемонстрировать доменную модель."""
    
    # Создать контактную информацию
    guest_contact = ContactInfo(
        email="ivanpetrov@shrek.com",
        phone="+7-900-123-45-67",
        address="Москва, Россия"
    )
    
    staff_contact = ContactInfo(
        email="annamassage@shrek.com",
        phone="+7-900-987-65-43"
    )
    
    # Создать гостя
    guest = Guest(
        guest_id="G001",
        name="Иван Петров",
        contact=guest_contact
    )
    guest.set_stay_dates(
        arrival=datetime(2024, 6, 1, 14, 0),
        departure=datetime(2024, 6, 5, 12, 0)
    )
    
    # Создать сотрудника
    staff = StaffMember(
        staff_id="S001",
        name="Анна Волкова",
        position="Массажист",
        contact=staff_contact
    )
    staff.add_specialization("Шведский массаж")
    staff.add_specialization("Лечебный массаж")
    
    # Создать места
    mud_bath_location = Location(
        location_id="L001",
        name="Грязевая ванна №1",
        capacity=2,
        location_type="грязевая_ванна"
    )
    
    massage_room = Location(
        location_id="L002",
        name="Массажный кабинет №3",
        capacity=1,
        location_type="массажный_кабинет"
    )
    
    # Создать ресурсы
    therapeutic_mud = Resource(
        resource_id="R001",
        name="Лечебная болотная грязь",
        resource_type="грязь",
        quantity=500.0,
        unit="кг"
    )
    
    herbs = Resource(
        resource_id="R002",
        name="Коллекция болотных трав",
        resource_type="травы",
        quantity=100.0,
        unit="кг"
    )
    
    # Создать услуги
    mud_bath_service = Service(
        service_id="SRV001",
        name="Лечебная грязевая ванна",
        service_type="грязевая_ванна",
        base_price=Money(2500.0, "RUB"),
        duration_minutes=60
    )
    mud_bath_service.add_required_resource("R001", 10.0)
    
    massage_service = Service(
        service_id="SRV002",
        name="Расслабляющий массаж",
        service_type="массаж",
        base_price=Money(3000.0, "RUB"),
        duration_minutes=45
    )
    
    # Создать временные слоты
    morning_slot = TimeSlot(
        start_time=datetime(2024, 6, 2, 10, 0),
        end_time=datetime(2024, 6, 2, 11, 0)
    )
    
    afternoon_slot = TimeSlot(
        start_time=datetime(2024, 6, 2, 14, 0),
        end_time=datetime(2024, 6, 2, 14, 45)
    )
    
    # Создать бронирования
    mud_bath_booking = Booking(
        booking_id="B001",
        guest=guest,
        service=mud_bath_service,
        time_slot=morning_slot,
        location=mud_bath_location
    )
    mud_bath_booking.assign_staff(staff)
    
    massage_booking = Booking(
        booking_id="B002",
        guest=guest,
        service=massage_service,
        time_slot=afternoon_slot,
        location=massage_room
    )
    massage_booking.assign_staff(staff)
    
    # Создать событие
    wellness_walk = Event(
        event_id="E001",
        name="Утренняя оздоровительная прогулка",
        event_type="групповая_прогулка",
        time_slot=TimeSlot(
            start_time=datetime(2024, 6, 3, 8, 0),
            end_time=datetime(2024, 6, 3, 9, 0)
        ),
        location=Location(
            location_id="L003",
            name="Болотная тропа",
            capacity=15,
            location_type="тропа"
        )
    )
    wellness_walk.add_participant(guest)
    
    # Создать счёт
    invoice = Invoice(
        invoice_id="INV001",
        guest=guest,
        issue_date=datetime(2024, 6, 5, 10, 0)
    )
    invoice.add_item(mud_bath_service, mud_bath_service.calculate_price())
    invoice.add_item(massage_service, massage_service.calculate_price(discount_percent=10.0))
    
    # Вывести все объекты для демонстрации модели
    print("=" * 60)
    print("ПРИРОДНЫЙ ОЗДОРОВИТЕЛЬНЫЙ КУРОРТ - ДЕМОНСТРАЦИЯ ДОМЕННОЙ МОДЕЛИ")
    print("=" * 60)
    print()
    
    print("ГОСТЬ:")
    print(guest)
    print(f"  Контакты: {guest.contact}")
    print(f"  Проживание: {guest.arrival_date.strftime('%Y-%m-%d')} до {guest.departure_date.strftime('%Y-%m-%d')}")
    print()
    
    print("СОТРУДНИК:")
    print(staff)
    print(f"  Специализации: {', '.join(staff.specializations)}")
    print()
    
    print("МЕСТА:")
    print(mud_bath_location)
    print(massage_room)
    print(f"  Может ли грязевая ванна вместить 3 человек? {mud_bath_location.can_accommodate(3)}")
    print()
    
    print("РЕСУРСЫ:")
    print(therapeutic_mud)
    print(herbs)
    print(f"  Доступно ли 15 кг грязи? {therapeutic_mud.is_available(15.0)}")
    print()
    
    print("УСЛУГИ:")
    print(mud_bath_service)
    print(massage_service)
    print(f"  Массаж со скидкой 10%: {massage_service.calculate_price(10.0)}")
    print()
    
    print("ВРЕМЕННЫЕ СЛОТЫ:")
    print(morning_slot)
    print(afternoon_slot)
    print(f"  Длительность утреннего слота: {morning_slot.duration_minutes()} минут")
    print(f"  Пересекаются ли слоты? {morning_slot.overlaps(afternoon_slot)}")
    print()
    
    print("БРОНИРОВАНИЯ:")
    print(mud_bath_booking)
    print(massage_booking)
    print(f"  Бронирование грязевой ванны подтверждено? {mud_bath_booking.is_confirmed()}")
    print()
    
    print("СОБЫТИЕ:")
    print(wellness_walk)
    print(f"  Участников: {wellness_walk.participant_count()}")
    print()
    
    print("СЧЁТ:")
    print(invoice)
    print(f"  Общая сумма: {invoice.calculate_total()}")
    print()
    
    print("=" * 60)
    print("Демонстрация успешно завершена!")
    print("=" * 60)


if __name__ == "__main__":
    main()


"""
Демонстрационный скрипт для доменной модели природного оздоровительного курорта.
Создаёт примеры объектов через ResortStorage и демонстрирует CRUD-операции.
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
from storage import ResortStorage


def main():
    """Создать примеры объектов через ResortStorage и продемонстрировать CRUD-операции."""
    
    # Создать хранилище
    storage = ResortStorage()
    
    print("=" * 70)
    print("ПРИРОДНЫЙ ОЗДОРОВИТЕЛЬНЫЙ КУРОРТ - ДЕМОНСТРАЦИЯ CRUD ОПЕРАЦИЙ")
    print("=" * 70)
    print()
    
    # ========== CREATE - Создание сущностей ==========
    print("=" * 70)
    print("1. СОЗДАНИЕ СУЩНОСТЕЙ (CREATE)")
    print("=" * 70)
    print()
    
    # Создать гостей
    guest1_contact = ContactInfo(
        email="ivanpetrov@shrek.com",
        phone="+7-900-123-45-67",
        address="Москва, Россия"
    )
    guest1 = Guest(
        guest_id="G001",
        name="Иван Петров",
        contact=guest1_contact
    )
    guest1.set_stay_dates(
        arrival=datetime(2024, 6, 1, 14, 0),
        departure=datetime(2024, 6, 5, 12, 0)
    )
    guest1_id = storage.create_guest(guest1)
    print(f"✓ Создан гость ID={guest1_id}: {guest1}")
    
    guest2 = Guest(
        guest_id="G002",
        name="Мария Сидорова",
        contact=ContactInfo(
            email="mariasidorova@shrek.com",
            phone="+7-900-555-77-88",
            address="Санкт-Петербург, Россия"
        )
    )
    guest2.set_stay_dates(
        arrival=datetime(2024, 6, 3, 12, 0),
        departure=datetime(2024, 6, 7, 11, 0)
    )
    guest2_id = storage.create_guest(guest2)
    print(f"✓ Создан гость ID={guest2_id}: {guest2}")
    print()
    
    # Создать сотрудников
    staff1 = StaffMember(
        staff_id="S001",
        name="Анна Волкова",
        position="Массажист",
        contact=ContactInfo(
            email="annamassage@shrek.com",
            phone="+7-900-987-65-43"
        )
    )
    staff1.add_specialization("Шведский массаж")
    staff1.add_specialization("Лечебный массаж")
    staff1_id = storage.create_staff_member(staff1)
    print(f"✓ Создан сотрудник ID={staff1_id}: {staff1}")
    
    staff2 = StaffMember(
        staff_id="S002",
        name="Пётр Грязев",
        position="Специалист по грязевым ваннам",
        contact=ContactInfo(
            email="petrgryazev@shrek.com",
            phone="+7-900-111-22-33"
        )
    )
    staff2.add_specialization("Грязелечение")
    staff2_id = storage.create_staff_member(staff2)
    print(f"✓ Создан сотрудник ID={staff2_id}: {staff2}")
    print()
    
    # Создать места
    location1 = Location(
        location_id="L001",
        name="Грязевая ванна №1",
        capacity=2,
        location_type="грязевая_ванна"
    )
    location1_id = storage.create_location(location1)
    print(f"✓ Создано место ID={location1_id}: {location1}")
    
    location2 = Location(
        location_id="L002",
        name="Массажный кабинет №3",
        capacity=1,
        location_type="массажный_кабинет"
    )
    location2_id = storage.create_location(location2)
    print(f"✓ Создано место ID={location2_id}: {location2}")
    
    location3 = Location(
        location_id="L003",
        name="Болотная тропа",
        capacity=15,
        location_type="тропа"
    )
    location3_id = storage.create_location(location3)
    print(f"✓ Создано место ID={location3_id}: {location3}")
    print()
    
    # Создать ресурсы
    resource1 = Resource(
        resource_id="R001",
        name="Лечебная болотная грязь",
        resource_type="грязь",
        quantity=500.0,
        unit="кг"
    )
    resource1_id = storage.create_resource(resource1)
    print(f"✓ Создан ресурс ID={resource1_id}: {resource1}")
    
    resource2 = Resource(
        resource_id="R002",
        name="Коллекция болотных трав",
        resource_type="травы",
        quantity=100.0,
        unit="кг"
    )
    resource2_id = storage.create_resource(resource2)
    print(f"✓ Создан ресурс ID={resource2_id}: {resource2}")
    print()
    
    # Создать услуги
    service1 = Service(
        service_id="SRV001",
        name="Лечебная грязевая ванна",
        service_type="грязевая_ванна",
        base_price=Money(2500.0, "RUB"),
        duration_minutes=60
    )
    service1.add_required_resource("R001", 10.0)
    service1_id = storage.create_service(service1)
    print(f"✓ Создана услуга ID={service1_id}: {service1}")
    
    service2 = Service(
        service_id="SRV002",
        name="Расслабляющий массаж",
        service_type="массаж",
        base_price=Money(3000.0, "RUB"),
        duration_minutes=45
    )
    service2_id = storage.create_service(service2)
    print(f"✓ Создана услуга ID={service2_id}: {service2}")
    print()
    
    # Создать бронирования
    booking1 = Booking(
        booking_id="B001",
        guest=guest1,
        service=service1,
        time_slot=TimeSlot(
            start_time=datetime(2024, 6, 2, 10, 0),
            end_time=datetime(2024, 6, 2, 11, 0)
        ),
        location=location1
    )
    booking1.assign_staff(staff2)
    booking1_id = storage.create_booking(booking1)
    print(f"✓ Создано бронирование ID={booking1_id}: {booking1}")
    
    booking2 = Booking(
        booking_id="B002",
        guest=guest1,
        service=service2,
        time_slot=TimeSlot(
            start_time=datetime(2024, 6, 2, 14, 0),
            end_time=datetime(2024, 6, 2, 14, 45)
        ),
        location=location2
    )
    booking2.assign_staff(staff1)
    booking2_id = storage.create_booking(booking2)
    print(f"✓ Создано бронирование ID={booking2_id}: {booking2}")
    print()
    
    # Создать счёт
    invoice1 = Invoice(
        invoice_id="INV001",
        guest=guest1,
        issue_date=datetime(2024, 6, 5, 10, 0)
    )
    invoice1.add_item(service1, service1.calculate_price())
    invoice1.add_item(service2, service2.calculate_price(discount_percent=10.0))
    invoice1_id = storage.create_invoice(invoice1)
    print(f"✓ Создан счёт ID={invoice1_id}: {invoice1}")
    print()
    
    # Создать событие
    event1 = Event(
        event_id="E001",
        name="Утренняя оздоровительная прогулка",
        event_type="групповая_прогулка",
        time_slot=TimeSlot(
            start_time=datetime(2024, 6, 3, 8, 0),
            end_time=datetime(2024, 6, 3, 9, 0)
        ),
        location=location3
    )
    event1.add_participant(guest1)
    event1_id = storage.create_event(event1)
    print(f"✓ Создано событие ID={event1_id}: {event1}")
    print()
    
    # ========== READ - Чтение сущностей ==========
    print("=" * 70)
    print("2. ЧТЕНИЕ СУЩНОСТЕЙ (READ)")
    print("=" * 70)
    print()
    
    # Получить гостя по ID
    retrieved_guest = storage.get_guest_by_id(guest1_id)
    print(f"✓ Получен гость по ID={guest1_id}: {retrieved_guest}")
    print()
    
    # Получить список всех гостей
    all_guests = storage.list_guests()
    print(f"✓ Список всех гостей ({len(all_guests)} шт.):")
    for guest in all_guests:
        print(f"  - {guest}")
    print()
    
    # Получить список всех сотрудников
    all_staff = storage.list_staff_members()
    print(f"✓ Список всех сотрудников ({len(all_staff)} шт.):")
    for staff in all_staff:
        print(f"  - {staff}")
    print()
    
    # Получить список всех бронирований
    all_bookings = storage.list_bookings()
    print(f"✓ Список всех бронирований ({len(all_bookings)} шт.):")
    for booking in all_bookings:
        print(f"  - {booking}")
    print()
    
    # Получить список всех счетов
    all_invoices = storage.list_invoices()
    print(f"✓ Список всех счетов ({len(all_invoices)} шт.):")
    for invoice in all_invoices:
        print(f"  - {invoice}")
    print()
    
    # ========== UPDATE - Обновление сущностей ==========
    print("=" * 70)
    print("3. ОБНОВЛЕНИЕ СУЩНОСТЕЙ (UPDATE)")
    print("=" * 70)
    print()
    
    # Обновить данные гостя
    guest1.name = "Иван Петров (обновлено)"
    updated = storage.update_guest(guest1_id, guest1)
    if updated:
        updated_guest = storage.get_guest_by_id(guest1_id)
        print(f"✓ Обновлён гость ID={guest1_id}: {updated_guest}")
    print()
    
    # Обновить статус счёта
    invoice1.mark_paid()
    storage.update_invoice(invoice1_id, invoice1)
    updated_invoice = storage.get_invoice_by_id(invoice1_id)
    print(f"✓ Обновлён счёт ID={invoice1_id}: {updated_invoice}")
    print()
    
    # Обновить количество ресурса
    resource1.quantity = 450.0  # Потратили 50 кг
    storage.update_resource(resource1_id, resource1)
    updated_resource = storage.get_resource_by_id(resource1_id)
    print(f"✓ Обновлён ресурс ID={resource1_id}: {updated_resource}")
    print()
    
    # ========== DELETE - Удаление сущностей ==========
    print("=" * 70)
    print("4. УДАЛЕНИЕ СУЩНОСТЕЙ (DELETE)")
    print("=" * 70)
    print()
    
    # Удалить бронирование
    deleted = storage.delete_booking(booking2_id)
    if deleted:
        print(f"✓ Удалено бронирование ID={booking2_id}")
        remaining_bookings = storage.list_bookings()
        print(f"  Осталось бронирований: {len(remaining_bookings)}")
    print()
    
    # Удалить ресурс
    deleted = storage.delete_resource(resource2_id)
    if deleted:
        print(f"✓ Удалён ресурс ID={resource2_id}")
        remaining_resources = storage.list_resources()
        print(f"  Осталось ресурсов: {len(remaining_resources)}")
    print()
    
    # Попытка удалить несуществующую сущность
    deleted = storage.delete_guest(999)
    if not deleted:
        print(f"✓ Попытка удалить несуществующего гостя ID=999: не найдено")
    print()
    
    # ========== Итоговая статистика ==========
    print("=" * 70)
    print("5. ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 70)
    print()
    print(f"Гостей в хранилище: {len(storage.list_guests())}")
    print(f"Сотрудников в хранилище: {len(storage.list_staff_members())}")
    print(f"Мест в хранилище: {len(storage.list_locations())}")
    print(f"Ресурсов в хранилище: {len(storage.list_resources())}")
    print(f"Услуг в хранилище: {len(storage.list_services())}")
    print(f"Бронирований в хранилище: {len(storage.list_bookings())}")
    print(f"Счетов в хранилище: {len(storage.list_invoices())}")
    print(f"Событий в хранилище: {len(storage.list_events())}")
    print()

    print("=" * 70)
    print("6. СОХРАНЕНИЕ И ЗАГРУЗКА ДАННЫХ")
    print("=" * 70)
    print()

    json_path = "storage_data.json"
    xml_path = "storage_data.xml"
    storage.save_to_json(json_path)
    print(f"✓ Данные сохранены в JSON-файл: {json_path}")
    storage.save_to_xml(xml_path)
    print(f"✓ Данные сохранены в XML-файл: {xml_path}")
    print()

    storage.clear_all()
    print("Хранилище очищено.")
    print(f"  Гостей осталось: {len(storage.list_guests())}")
    print(f"  Бронирований осталось: {len(storage.list_bookings())}")
    print()

    storage.load_from_json(json_path)
    print(f"✓ Данные восстановлены из JSON-файла: {json_path}")
    print(f"  Гостей после загрузки: {len(storage.list_guests())}")
    print(f"  Бронирований после загрузки: {len(storage.list_bookings())}")
    loaded_guests = storage.list_guests()
    if loaded_guests:
        print(f"  Первый гость: {loaded_guests[0]}")
    loaded_bookings = storage.list_bookings()
    if loaded_bookings:
        print(f"  Первое бронирование: {loaded_bookings[0]}")
    print()
    
    print("=" * 70)
    print("Демонстрация CRUD и сериализации успешно завершена!")
    print("=" * 70)


if __name__ == "__main__":
    main()


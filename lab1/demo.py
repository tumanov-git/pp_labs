"""
Демонстрационный скрипт для доменной модели природного оздоровительного курорта.
Создаёт примеры объектов через ResortStorage и демонстрирует CRUD-операции.
"""

from datetime import datetime
import os
from classes import (
    ContactInfo,
    Guest,
    StaffMember,
    Location,
    TimeSlot,
    Service,
    Booking
)
from storage import ResortStorage
from exceptions import EntityNotFoundError, ValidationError, StorageError


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
    guest1 = Guest(
        guest_id="G001",
        name="Иван Петров",
        contact=ContactInfo(
            email="ivanpetrov@shrek.com",
            phone="+7-900-123-45-67",
            address="Москва, Россия",
        ),
    )
    guest1_id = storage.create_guest(guest1)
    print(f"✓ Создан гость ID={guest1_id}: {guest1}")

    guest2 = Guest(
        guest_id="G002",
        name="Мария Сидорова",
        contact=ContactInfo(
            email="mariasidorova@shrek.com",
            phone="+7-900-555-77-88",
            address="Санкт-Петербург, Россия",
        ),
    )
    guest2_id = storage.create_guest(guest2)
    print(f"✓ Создан гость ID={guest2_id}: {guest2}")

    guest3 = Guest(
        guest_id="G003",
        name="Олег Морозов",
        contact=ContactInfo(
            email="oleg.morozov@shrek.com",
            phone="+7-900-222-33-44",
            address="Новосибирск, Россия",
        ),
    )
    guest3_id = storage.create_guest(guest3)
    print(f"✓ Создан гость ID={guest3_id}: {guest3}")

    guest4 = Guest(
        guest_id="G004",
        name="Елена Лесная",
        contact=ContactInfo(
            email="elena.lesnaya@shrek.com",
            phone="+7-900-333-44-55",
            address="Екатеринбург, Россия",
        ),
    )
    guest4_id = storage.create_guest(guest4)
    print(f"✓ Создан гость ID={guest4_id}: {guest4}")

    guest5 = Guest(
        guest_id="G005",
        name="Сергей Моржов",
        contact=ContactInfo(
            email="sergey.morzhov@shrek.com",
            phone="+7-900-444-55-66",
            address="Казань, Россия",
        ),
    )
    guest5_id = storage.create_guest(guest5)
    print(f"✓ Создан гость ID={guest5_id}: {guest5}")
    print()
    
    # (Ресурсы удалены из предметной области)
    
    # Создать места
    location1 = Location(
        location_id="L001",
        name="Грязевая ванна №1"
    )
    location1_id = storage.create_location(location1)
    print(f"✓ Создано место ID={location1_id}: {location1}")
    
    location2 = Location(
        location_id="L002",
        name="Массажный кабинет №3"
    )
    location2_id = storage.create_location(location2)
    print(f"✓ Создано место ID={location2_id}: {location2}")
    
    location3 = Location(
        location_id="L003",
        name="Болотная тропа"
    )
    location3_id = storage.create_location(location3)
    print(f"✓ Создано место ID={location3_id}: {location3}")
    print()
    
    # Создать услуги
    service1 = Service(
        service_id="SRV001",
        name="Лечебная грязевая ванна",
        duration_minutes=60
    )
    # Привязать места к услугам (обязательное условие выполнения)
    service1.assign_location("L001")
    service2 = Service(
        service_id="SRV002",
        name="Расслабляющий массаж",
        duration_minutes=45
    )
    service2.assign_location("L002")
    service3 = Service(
        service_id="SRV003",
        name="Прогулка по болотной тропе",
        duration_minutes=90,
    )
    service3.assign_location("L003")
    service4 = Service(
        service_id="SRV004",
        name="Ароматический массаж",
        duration_minutes=30,
    )
    service4.assign_location("L002")
    service1_id = storage.create_service(service1)
    print(f"✓ Создана услуга ID={service1_id}: {service1}")
    service2_id = storage.create_service(service2)
    print(f"✓ Создана услуга ID={service2_id}: {service2}")
    service3_id = storage.create_service(service3)
    print(f"✓ Создана услуга ID={service3_id}: {service3}")
    service4_id = storage.create_service(service4)
    print(f"✓ Создана услуга ID={service4_id}: {service4}")
    print()
    
    # Создать сотрудников (после создания услуг) и привязать к услугам
    staff1 = StaffMember(
        staff_id="S001",
        name="Анна Волкова",
        role="Массажист",
        contact=ContactInfo(
            email="annamassage@shrek.com",
            phone="+7-900-987-65-43"
        )
    )
    staff1.assign_service("SRV002")
    staff1.assign_service("SRV004")
    staff1_id = storage.create_staff_member(staff1)
    print(f"✓ Создан сотрудник ID={staff1_id}: {staff1}")
    
    staff2 = StaffMember(
        staff_id="S002",
        name="Пётр Грязев",
        role="Специалист по грязевым ваннам",
        contact=ContactInfo(
            email="petrgryazev@shrek.com",
            phone="+7-900-111-22-33"
        )
    )
    staff2.assign_service("SRV001")
    staff2_id = storage.create_staff_member(staff2)
    print(f"✓ Создан сотрудник ID={staff2_id}: {staff2}")
    
    staff3 = StaffMember(
        staff_id="S003",
        name="Игорь Тропин",
        role="Гид по болотной тропе",
        contact=ContactInfo(
            email="igor.tropin@shrek.com",
            phone="+7-900-777-88-99"
        )
    )
    staff3.assign_service("SRV003")
    staff3_id = storage.create_staff_member(staff3)
    print(f"✓ Создан сотрудник ID={staff3_id}: {staff3}")
    print()
    
    # Назначить сотрудника для услуги и обновить услуги
    service1.assign_staff("S002")
    service2.assign_staff("S001")
    service3.assign_staff("S003")
    service4.assign_staff("S001")
    storage.update_service("SRV001", service1)
    storage.update_service("SRV002", service2)
    storage.update_service("SRV003", service3)
    storage.update_service("SRV004", service4)
    
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
    
    booking3 = Booking(
        booking_id="B003",
        guest=guest2,
        service=service1,
        time_slot=TimeSlot(
            start_time=datetime(2024, 6, 2, 11, 30),
            end_time=datetime(2024, 6, 2, 12, 30),
        ),
        location=location1,
    )
    booking3.assign_staff(staff2)
    booking3_id = storage.create_booking(booking3)
    print(f"✓ Создано бронирование ID={booking3_id}: {booking3}")

    booking4 = Booking(
        booking_id="B004",
        guest=guest3,
        service=service3,
        time_slot=TimeSlot(
            start_time=datetime(2024, 6, 2, 9, 0),
            end_time=datetime(2024, 6, 2, 10, 30),
        ),
        location=location3,
    )
    booking4.assign_staff(staff3)
    booking4_id = storage.create_booking(booking4)
    print(f"✓ Создано бронирование ID={booking4_id}: {booking4}")

    booking5 = Booking(
        booking_id="B005",
        guest=guest4,
        service=service4,
        time_slot=TimeSlot(
            start_time=datetime(2024, 6, 2, 16, 0),
            end_time=datetime(2024, 6, 2, 16, 30),
        ),
        location=location2,
    )
    booking5.assign_staff(staff1)
    booking5_id = storage.create_booking(booking5)
    print(f"✓ Создано бронирование ID={booking5_id}: {booking5}")
    print()
    
    # (Счета и деньги исключены из предметной области)
    
    # (События удалены из предметной области)
    
    # ========== READ - Чтение сущностей ==========
    print("=" * 70)
    print("2. ЧТЕНИЕ СУЩНОСТЕЙ (READ)")
    print("=" * 70)
    print()
    
    # Получить гостя по ID
    try:
        retrieved_guest = storage.get_guest_by_id(guest1_id)
        print(f"✓ Получен гость по ID={guest1_id}: {retrieved_guest}")
    except EntityNotFoundError as e:
        print(f"✗ Ошибка получения гостя: {e}")
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
    
    # (Счета исключены)
    
    # ========== UPDATE - Обновление сущностей ==========
    print("=" * 70)
    print("3. ОБНОВЛЕНИЕ СУЩНОСТЕЙ (UPDATE)")
    print("=" * 70)
    print()
    
    # Обновить данные гостя
    try:
        guest1.name = "Иван Петрович"
        storage.update_guest(guest1_id, guest1)
        updated_guest = storage.get_guest_by_id(guest1_id)
        print(f"✓ Обновлён гость ID={guest1_id}: {updated_guest}")
    except EntityNotFoundError as e:
        print(f"✗ Ошибка обновления гостя: {e}")
    print()
    
    # (Счета исключены)
    
    # (Операции с ресурсами удалены)
    
    # ========== DELETE - Удаление сущностей ==========
    print("=" * 70)
    print("4. УДАЛЕНИЕ СУЩНОСТЕЙ (DELETE)")
    print("=" * 70)
    print()
    
    # Удалить бронирование
    try:
        storage.delete_booking(booking2_id)
        print(f"✓ Удалено бронирование ID={booking2_id}")
        remaining_bookings = storage.list_bookings()
        print(f"  Осталось бронирований: {len(remaining_bookings)}")
    except EntityNotFoundError as e:
        print(f"✗ Ошибка удаления бронирования: {e}")
    print()
    
    # (Удаление ресурсов исключено)
    
    # ========== Итоговая статистика ==========
    print("=" * 70)
    print("5. ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 70)
    print()
    print(f"Гостей в хранилище: {len(storage.list_guests())}")
    print(f"Сотрудников в хранилище: {len(storage.list_staff_members())}")
    print(f"Мест в хранилище: {len(storage.list_locations())}")
    print(f"Услуг в хранилище: {len(storage.list_services())}")
    print(f"Бронирований в хранилище: {len(storage.list_bookings())}")
    print()

    print("=" * 70)
    print("6. СОХРАНЕНИЕ И ЗАГРУЗКА ДАННЫХ")
    print("=" * 70)
    print()

    base_dir = os.path.dirname(__file__)
    json_path = os.path.join(base_dir, "storage_data.json")
    xml_path = os.path.join(base_dir, "storage_data.xml")
    
    try:
        storage.save_to_json(json_path)
        print(f"✓ Данные сохранены в JSON-файл: {json_path}")
    except StorageError as e:
        print(f"✗ Ошибка сохранения в JSON: {e}")
    
    try:
        storage.save_to_xml(xml_path)
        print(f"✓ Данные сохранены в XML-файл: {xml_path}")
    except StorageError as e:
        print(f"✗ Ошибка сохранения в XML: {e}")
    print()

    storage.clear_all()
    print("Хранилище очищено.")
    print(f"  Гостей осталось: {len(storage.list_guests())}")
    print(f"  Бронирований осталось: {len(storage.list_bookings())}")
    print()

    try:
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
    except StorageError as e:
        print(f"✗ Ошибка загрузки из JSON: {e}")
    print()
    
    # ========== ДЕМОНСТРАЦИЯ ОБРАБОТКИ ОШИБОК ==========
    print("=" * 70)
    print("7. ДЕМОНСТРАЦИЯ ОБРАБОТКИ ОШИБОК")
    print("=" * 70)
    print()
    
    # --- EntityNotFoundError ---
    print("--- EntityNotFoundError (сущность не найдена) ---")
    print()
    
    # Попытка получить несуществующую сущность
    print("1. Попытка получить несуществующего гостя:")
    try:
        non_existent_guest = storage.get_guest_by_id("G999")
        print(f"  Гость найден: {non_existent_guest}")
    except EntityNotFoundError as e:
        print(f"  ✗ {e}")
    print()
    
    # Попытка обновить несуществующую сущность
    print("2. Попытка обновить несуществующего сотрудника:")
    try:
        fake_staff = StaffMember(
            staff_id="S999",
            name="Несуществующий",
            role="Тест",
            contact=ContactInfo(email="test@test.com", phone="+1234567890")
        )
        storage.update_staff_member("S999", fake_staff)
        print("  Сотрудник обновлён")
    except EntityNotFoundError as e:
        print(f"  ✗ {e}")
    print()
    
    # Попытка удалить несуществующую сущность
    print("3. Попытка удалить несуществующее место:")
    try:
        storage.delete_location("L999")
        print("  Место удалено")
    except EntityNotFoundError as e:
        print(f"  ✗ {e}")
    print()
    
    # --- ValidationError ---
    print("--- ValidationError (невалидные данные) ---")
    print()
    
    # Дублирование ID при создании
    print("4. Попытка создать гостя с уже существующим ID:")
    try:
        duplicate_guest = Guest(
            guest_id=guest1_id,  # Используем существующий ID
            name="Дубликат",
            contact=ContactInfo(email="duplicate@test.com", phone="+1111111111")
        )
        storage.create_guest(duplicate_guest)
        print("  Гость создан")
    except ValidationError as e:
        print(f"  ✗ {e}")
    print()
    
    # Создание услуги с некорректной длительностью
    print("5. Попытка создать услугу с некорректной длительностью (0 минут):")
    try:
        invalid_service = Service(
            service_id="SRV999",
            name="Невалидная услуга",
            duration_minutes=0
        )
        storage.create_service(invalid_service)
        print(f"  Услуга создана: {invalid_service}")
    except ValidationError as e:
        print(f"  ✗ {e}")
    print()
    
    # Создание услуги с отрицательной длительностью
    print("6. Попытка создать услугу с отрицательной длительностью:")
    try:
        negative_service = Service(
            service_id="SRV998",
            name="Отрицательная услуга",
            duration_minutes=-10
        )
        storage.create_service(negative_service)
        print("  Услуга создана")
    except ValidationError as e:
        print(f"  ✗ {e}")
    print()
    
    # Создание сотрудника с несуществующими услугами
    print("7. Попытка создать сотрудника с несуществующими услугами:")
    try:
        staff_with_bad_services = StaffMember(
            staff_id="S999",
            name="Тестовый сотрудник",
            role="Тестер",
            contact=ContactInfo(email="test@test.com", phone="+1234567890")
        )
        staff_with_bad_services.assign_service("SRV999")  # Несуществующая услуга
        storage.create_staff_member(staff_with_bad_services)
        print("  Сотрудник создан")
    except ValidationError as e:
        print(f"  ✗ {e}")
    print()
    
    # Создание услуги с несуществующим местом
    print("8. Попытка создать услугу с несуществующим местом:")
    try:
        service_bad_location = Service(
            service_id="SRV997",
            name="Услуга с плохим местом",
            duration_minutes=30
        )
        service_bad_location.assign_location("L999")  # Несуществующее место
        storage.create_service(service_bad_location)
        print("  Услуга создана")
    except ValidationError as e:
        print(f"  ✗ {e}")
    print()
    
    # Создание бронирования без места/сотрудника у услуги
    print("9. Попытка создать бронирование для услуги без назначенного места:")
    try:
        service_no_location = Service(
            service_id="SRV996",
            name="Услуга без места",
            duration_minutes=30
        )
        # Не назначаем место
        service_no_location.assign_staff(staff1_id)
        storage.create_service(service_no_location)
        
        booking_no_location = Booking(
            booking_id="B999",
            guest=guest1,
            service=service_no_location,
            time_slot=TimeSlot(
                start_time=datetime(2024, 6, 3, 10, 0),
                end_time=datetime(2024, 6, 3, 10, 30)
            ),
            location=location1
        )
        booking_no_location.assign_staff(staff1)
        storage.create_booking(booking_no_location)
        print("  Бронирование создано")
    except ValidationError as e:
        print(f"  ✗ {e}")
    print()
    
    # Создание бронирования с пересекающимся временем (гость занят)
    print("10. Попытка создать бронирование с пересекающимся временем (гость занят):")
    try:
        # Используем время, которое пересекается с существующим бронированием
        overlapping_booking = Booking(
            booking_id="B998",
            guest=guest1,  # Тот же гость
            service=service1,
            time_slot=TimeSlot(
                start_time=datetime(2024, 6, 2, 10, 30),  # Пересекается с booking1
                end_time=datetime(2024, 6, 2, 11, 30)
            ),
            location=location1
        )
        overlapping_booking.assign_staff(staff2)
        storage.create_booking(overlapping_booking)
        print("  Бронирование создано")
    except ValidationError as e:
        print(f"  ✗ {e}")
    print()
    
    # Создание бронирования с несовпадающим местом
    print("11. Попытка создать бронирование с местом, не совпадающим с местом услуги:")
    try:
        booking_wrong_location = Booking(
            booking_id="B997",
            guest=guest2,
            service=service1,  # service1 привязан к location1
            time_slot=TimeSlot(
                start_time=datetime(2024, 6, 3, 10, 0),
                end_time=datetime(2024, 6, 3, 11, 0)
            ),
            location=location2  # Но указываем location2
        )
        booking_wrong_location.assign_staff(staff2)
        storage.create_booking(booking_wrong_location)
        print("  Бронирование создано")
    except ValidationError as e:
        print(f"  ✗ {e}")
    print()
    
    # --- StorageError ---
    print("--- StorageError (ошибки работы с хранилищем) ---")
    print()
    
    # Попытка загрузить несуществующий файл
    print("12. Попытка загрузить несуществующий JSON-файл:")
    try:
        storage.load_from_json("несуществующий_файл.json")
        print("  Файл успешно загружен")
    except StorageError as e:
        print(f"  ✗ {e}")
    print()
    
    # Попытка загрузить несуществующий XML-файл
    print("13. Попытка загрузить несуществующий XML-файл:")
    try:
        storage.load_from_xml("несуществующий_файл.xml")
        print("  Файл успешно загружен")
    except StorageError as e:
        print(f"  ✗ {e}")
    print()
    
    print("=" * 70)
    print("Демонстрация CRUD, сериализации и обработки ошибок завершена!")
    print("=" * 70)


if __name__ == "__main__":
    main()


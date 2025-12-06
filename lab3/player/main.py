"""Точка входа в приложение"""
import sys
from PyQt6.QtWidgets import QApplication
from .window import MainWindow


def main():
    """Главная функция"""
    app = QApplication(sys.argv)
    
    # Загружаем кастомный шрифт и ставим его по умолчанию (с кириллицей)
    try:
        from PyQt6.QtGui import QFontDatabase, QFont
        from .config import config
        font_id = QFontDatabase.addApplicationFont(str(config.pixel_font))
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                app.setFont(QFont(families[0], config.ui_font_size))
    except Exception as e:
        print(f"Не удалось загрузить шрифт: {e}")
    
    # Создаем и показываем главное окно
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


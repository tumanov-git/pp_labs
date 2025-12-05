"""Точка входа в приложение"""
import sys
from PyQt6.QtWidgets import QApplication
from .window import MainWindow


def main():
    """Главная функция"""
    app = QApplication(sys.argv)
    
    # Создаем и показываем главное окно
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


"""Единая точка входа для приложения Ре-Файл+.

Этот модуль обеспечивает единую точку входа для GUI версии приложения.
"""

import logging
import os
import sys
from typing import List, Optional

# Локальные импорты
from app.cli_utils import process_cli_args

logger = logging.getLogger(__name__)


def run_gui(files_from_args: Optional[List[str]] = None) -> None:
    """Запуск GUI версии приложения.
    
    Args:
        files_from_args: Список файлов из аргументов командной строки
    """
    try:
        from PyQt6.QtWidgets import QApplication
        from app.app_core import ReFilePlusApp
    except ImportError as e:
        logger.error(f"PyQt6 не установлен: {e}")
        print("Ошибка: PyQt6 не установлен. Установите: pip install PyQt6")
        sys.exit(1)
    
    # Создание QApplication
    logger.info("Создание QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("Ре-Файл+")
    app.setOrganizationName("ReFilePlus")
    
    # Примечание: В PyQt6 высокое DPI масштабирование включено по умолчанию,
    # поэтому атрибуты AA_EnableHighDpiScaling и AA_UseHighDpiPixmaps больше не нужны
    
    # Создание и запуск приложения
    logger.info("Создание экземпляра приложения...")
    main_app = ReFilePlusApp(files_from_args=files_from_args)
    logger.info("Приложение создано успешно")
    
    # Запуск главного цикла
    logger.info("Запуск главного цикла приложения...")
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        logger.info("Получен сигнал KeyboardInterrupt, завершение приложения...")
    except Exception as e:
        logger.error(f"Критическая ошибка в главном цикле: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Приложение завершено")


def main() -> None:
    """Главная функция запуска приложения."""
    logger.info("Функция main() начала выполнение")
    
    # Обработка аргументов командной строки
    logger.info("Обработка аргументов командной строки...")
    files_from_args = process_cli_args()
    logger.info(f"Обработано файлов из аргументов: {len(files_from_args)}")
    
    # Запуск GUI версии
    run_gui(files_from_args)


if __name__ == '__main__':
    main()


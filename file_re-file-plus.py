"""Модуль для переименования файлов с графическим интерфейсом.

Точка входа приложения. Использует модульную архитектуру.
Основная логика находится в пакете app/.
"""

import logging
import os
import sys
import tkinter as tk

# Импорт для проверки прав администратора (Windows)
if sys.platform == 'win32':
    try:
        import ctypes
        HAS_CTYPES = True
    except ImportError:
        HAS_CTYPES = False
else:
    HAS_CTYPES = False

# Опциональные сторонние библиотеки
HAS_TKINTERDND2 = False
try:
    from tkinterdnd2 import TkinterDnD
    HAS_TKINTERDND2 = True
except ImportError:
    pass

# Локальные импорты
from app.app_core import FileRenamerApp, process_cli_args

# Настройка логирования
logger = logging.getLogger(__name__)


def is_admin():
    """Проверка, запущена ли программа от имени администратора."""
    if not HAS_CTYPES:
        return False
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except (OSError, AttributeError, ValueError) as e:
        logger.debug(f"Ошибка проверки прав администратора: {e}")
        return False

def run_as_admin():
    """Запуск программы от имени администратора."""
    if not HAS_CTYPES:
        return False
    if is_admin():
        return True
    else:
        # Перезапускаем программу с правами администратора
        # Используем Запуск.pyw если он существует, иначе file_re-file-plus.py
        script = os.path.abspath(__file__)
        script_dir = os.path.dirname(script)
        launch_script = os.path.join(script_dir, "Запуск.pyw")
        
        # Если есть Запуск.pyw, используем его, иначе текущий файл
        if os.path.exists(launch_script):
            script_to_run = launch_script
        else:
            script_to_run = script
        
        # Передаем аргументы командной строки
        args = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        if args:
            command = f'"{script_to_run}" {args}'
        else:
            command = f'"{script_to_run}"'
        
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, command, None, 1
        )
        return False

def main():
    """Главная функция запуска приложения."""
    logger.info("Функция main() начала выполнение")
    
    # Проверка и запрос прав администратора
    if sys.platform == 'win32' and HAS_CTYPES:
        logger.info("Проверка прав администратора...")
        if not is_admin():
            logger.info("Программа не запущена от имени администратора, перезапускаем с правами администратора...")
            run_as_admin()
            logger.info("Завершение текущего процесса после запроса прав администратора")
            sys.exit(0)
        else:
            logger.info("Программа запущена от имени администратора")
    else:
        logger.info("Проверка прав администратора пропущена (не Windows или ctypes недоступен)")
    
    # Обработка аргументов командной строки
    logger.info("Обработка аргументов командной строки...")
    files_from_args = process_cli_args()
    logger.info(f"Обработано файлов из аргументов: {len(files_from_args)}")
    
    # Создание корневого окна
    # Используем TkinterDnD если доступно
    logger.info("Создание корневого окна...")
    if HAS_TKINTERDND2:
        try:
            root = TkinterDnD.Tk()
            logger.info("Root окно создано как TkinterDnD.Tk()")
        except Exception as e:
            logger.error(f"Не удалось создать TkinterDnD.Tk(): {e}", exc_info=True)
            root = tk.Tk()
            logger.warning("Root окно создано как обычный tk.Tk() - drag and drop недоступен")
    else:
        root = tk.Tk()
        logger.warning("tkinterdnd2 недоступен - root окно создано как обычный tk.Tk()")
        logger.warning("Для включения drag and drop установите: pip install tkinterdnd2")
    
    # Создание и запуск приложения
    logger.info("Создание экземпляра FileRenamerApp...")
    app = FileRenamerApp(root, files_from_args=files_from_args)
    logger.info("FileRenamerApp создан успешно")
    
    # Обновляем окно, чтобы оно было видимо перед регистрацией drag and drop
    logger.info("Обновление окна перед регистрацией drag and drop...")
    root.update()
    
    logger.info("Запуск главного цикла приложения (root.mainloop())...")
    root.mainloop()
    logger.info("Главный цикл приложения завершен")


if __name__ == "__main__":
    main()

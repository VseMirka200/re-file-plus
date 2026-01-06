"""Файл запуска приложения "Ре-Файл+".

Этот файл предназначен для запуска приложения по двойному клику.
Использует расширение .pyw для запуска без отображения консольного окна.
"""

import logging
import os
import sys

# Проверка версии Python
if sys.version_info < (3, 7):
    print("Ошибка: Требуется Python 3.7 или выше")
    print(f"Текущая версия: {sys.version}")
    sys.exit(1)

# Настройка логирования
log_level = logging.INFO

# Определяем абсолютный путь к директории скрипта
script_file = os.path.abspath(__file__)
script_dir = os.path.dirname(script_file)

try:
    from config.constants import get_log_file_path, get_logs_dir
    logs_dir = get_logs_dir()
    log_file_path = get_log_file_path()
    if not logs_dir or not log_file_path:
        raise ValueError("Путь к директории логов не определен")
except (ImportError, ValueError, Exception) as e:
    app_data_dir = script_dir
    logs_dir = os.path.join(app_data_dir, "logs")
    log_file_path = os.path.join(logs_dir, "re-file-plus.log")
    if isinstance(e, ImportError):
        print(f"Информация: Не удалось импортировать config.constants, используется директория скрипта: {app_data_dir}")

# Создаем директорию для логов, если её нет
try:
    os.makedirs(logs_dir, exist_ok=True)
except (OSError, PermissionError):
    pass

# Настройка файлового обработчика логирования
try:
    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10 МБ
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
except Exception as e:
    print(f"Ошибка настройки логирования: {e}")

logger = logging.getLogger(__name__)

# Настройка кодировки для Windows
if sys.platform == 'win32':
    try:
        import locale
        if sys.stdout.encoding != 'utf-8':
            import codecs
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        pass

# Импорт и запуск приложения
try:
    logger.info("=" * 60)
    logger.info("Запуск приложения Ре-Файл+ (PyQt6)")
    logger.info("=" * 60)
    
    from app.entry_point import main
    
    logger.info("Запуск главной функции...")
    main()
    
except KeyboardInterrupt:
    logger.info("Получен сигнал прерывания (Ctrl+C)")
except Exception as e:
    logger.error(f"Критическая ошибка при запуске приложения: {e}", exc_info=True)
    
    # Показываем диалог с ошибкой (если возможно)
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        import sys as sys_module
        
        app = QApplication(sys_module.argv)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Критическая ошибка")
        msg.setText(f"Произошла критическая ошибка при запуске приложения:\n\n{str(e)}")
        msg.setDetailedText(str(e))
        msg.exec()
    except Exception:
        # Если не удалось показать диалог, выводим в консоль
        print(f"Критическая ошибка: {e}")
        input("Нажмите Enter для выхода...")
    
    sys.exit(1)
finally:
    logger.info("Приложение завершено")


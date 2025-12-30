"""Модуль для управления списком файлов.

Обеспечивает управление списком файлов для переименования, включая:
- Добавление/удаление файлов
- Отображение в Treeview
- Операции с файлами (открытие папки, копирование пути)
- Импорт/экспорт списка файлов (JSON, CSV)
- Сортировку и фильтрацию

ВНИМАНИЕ: Этот модуль является частью пакета приложения и не предназначен 
для прямого запуска. Запускайте приложение через файл Запуск.pyw или file_re-file-plus.py
"""

# Стандартная библиотека
import logging
from tkinter import messagebox

# Локальные импорты
from ui.file_list.manager import FileListManager as _FileListManager

logger = logging.getLogger(__name__)

# Импорт структурированного логирования
try:
    from utils.structured_logging import log_action, log_file_action, log_batch_action
except ImportError:
    # Fallback если модуль недоступен
    def log_action(logger, level, action, message, **kwargs):
        logger.log(level, f"[{action}] {message}")
    def log_file_action(logger, action, message, **kwargs):
        logger.info(f"[{action}] {message}")
    def log_batch_action(logger, action, message, file_count, **kwargs):
        logger.info(f"[{action}] {message} (файлов: {file_count})")


# Экспортируем класс для обратной совместимости
FileListManager = _FileListManager

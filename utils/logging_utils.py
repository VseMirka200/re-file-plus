"""Модуль для логирования приложения.

Объединяет структурированное логирование и обработчик ротации логов.
"""

import logging
import os
from typing import Dict, Optional, Any
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Упрощенный форматтер для логирования."""
    
    def format(self, record):
        """Форматирование записи лога с действием."""
        # Простой формат: время, уровень, действие (если есть), сообщение
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        level = record.levelname[:4]  # Сокращенный уровень (INFO -> INFO, DEBUG -> DEBU)
        message = record.getMessage()
        
        # Добавляем действие, если оно есть
        action = getattr(record, 'action', None)
        if action and action != 'UNKNOWN':
            return f"[{timestamp}] {level} [{action}] {message}"
        
        return f"[{timestamp}] {level} {message}"


class RotatingLogHandler(logging.FileHandler):
    """Обработчик логов с ограничением количества записей.
    
    Хранит только последние max_lines записей в файле лога.
    При превышении лимита удаляет старые записи.
    """
    
    def __init__(self, filename: str, max_lines: int = 100, mode: str = 'a', 
                 encoding: Optional[str] = None, delay: bool = False):
        """Инициализация обработчика.
        
        Args:
            filename: Путь к файлу лога
            max_lines: Максимальное количество записей в файле (по умолчанию 100)
            mode: Режим открытия файла (по умолчанию 'a')
            encoding: Кодировка файла (по умолчанию None)
            delay: Отложенное открытие файла (по умолчанию False)
        """
        # Создаем директорию, если её нет
        log_dir = os.path.dirname(filename)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        super().__init__(filename, mode, encoding, delay)
        self.max_lines = max_lines
    
    def emit(self, record: logging.LogRecord) -> None:
        """Запись записи в лог с проверкой лимита.
        
        Args:
            record: Запись лога для записи
        """
        # Сначала записываем запись
        super().emit(record)
        
        # Проверяем и ограничиваем количество строк
        try:
            self._limit_file_size()
        except Exception:
            # Игнорируем ошибки при ограничении размера файла
            # чтобы не прерывать логирование
            pass
    
    def _limit_file_size(self) -> None:
        """Ограничение размера файла до max_lines записей."""
        filename = self.baseFilename  # Используем baseFilename из FileHandler
        if not os.path.exists(filename):
            return
        
        try:
            # Читаем все строки из файла
            encoding = self.encoding or 'utf-8'
            with open(filename, 'r', encoding=encoding) as f:
                lines = f.readlines()
            
            # Если строк больше, чем лимит, оставляем только последние
            if len(lines) > self.max_lines:
                # Оставляем последние max_lines строк
                lines_to_keep = lines[-self.max_lines:]
                
                # Записываем обратно только последние строки
                with open(filename, 'w', encoding=encoding) as f:
                    f.writelines(lines_to_keep)
        except (OSError, IOError, UnicodeDecodeError):
            # Игнорируем ошибки при работе с файлом
            pass


def log_action(logger: logging.Logger, 
               level: int,
               action: str,
               message: str,
               details: Optional[Dict[str, Any]] = None,
               file_path: Optional[str] = None,
               file_count: Optional[int] = None,
               method_name: Optional[str] = None,
               duration_ms: Optional[float] = None,
               exc_info: bool = False):
    """Логирование действия.
    
    Логирует все действия с указанным уровнем логирования.
    
    Args:
        logger: Логгер для записи
        level: Уровень логирования (logging.INFO, logging.ERROR и т.д.)
        action: Название действия
        message: Текстовое сообщение
        details: Игнорируется (для упрощения)
        file_path: Игнорируется (для упрощения)
        file_count: Игнорируется (для упрощения)
        method_name: Игнорируется (для упрощения)
        duration_ms: Игнорируется (для упрощения)
        exc_info: Логировать ли информацию об исключении
    """
    extra = {'action': action}
    logger.log(level, message, extra=extra, exc_info=exc_info)


def log_file_action(logger: logging.Logger,
                    action: str,
                    message: str,
                    file_path: Optional[str] = None,
                    old_name: Optional[str] = None,
                    new_name: Optional[str] = None,
                    **kwargs):
    """Упрощенное логирование действия с файлом.
    
    Args:
        logger: Логгер
        action: Название действия
        message: Сообщение
        file_path: Игнорируется (для упрощения)
        old_name: Игнорируется (для упрощения)
        new_name: Игнорируется (для упрощения)
        **kwargs: Игнорируется (для упрощения)
    """
    extra = {'action': action}
    logger.info(message, extra=extra)


def log_batch_action(logger: logging.Logger,
                    action: str,
                    message: str,
                    file_count: int,
                    success_count: Optional[int] = None,
                    error_count: Optional[int] = None,
                    **kwargs):
    """Упрощенное логирование пакетного действия.
    
    Args:
        logger: Логгер
        action: Название действия
        message: Сообщение
        file_count: Количество файлов (добавляется в сообщение)
        success_count: Игнорируется (для упрощения)
        error_count: Игнорируется (для упрощения)
        **kwargs: Игнорируется (для упрощения)
    """
    extra = {'action': action}
    # Упрощенное сообщение с количеством файлов
    if file_count > 0:
        logger.info(f"{message} (файлов: {file_count})", extra=extra)
    else:
        logger.info(message, extra=extra)


"""Модуль для структурированного логирования действий приложения.

Обеспечивает единообразное логирование всех действий с метаданными:
- Действие (action)
- Детали (details)
- Контекст (file_path, file_count, user_id и т.д.)
"""

import logging
import os
from typing import Dict, Optional, Any
from datetime import datetime


class StructuredFormatter(logging.Formatter):
    """Упрощенный форматтер для логирования."""
    
    def format(self, record):
        """Упрощенное форматирование записи лога."""
        # Простой формат: время, уровень, сообщение
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        level = record.levelname[:4]  # Сокращенный уровень (INFO -> INFO, DEBUG -> DEBU)
        message = record.getMessage()
        
        # Добавляем действие только для важных событий
        action = getattr(record, 'action', None)
        if action and action != 'UNKNOWN' and record.levelno >= logging.WARNING:
            return f"[{timestamp}] {level} [{action}] {message}"
        
        return f"[{timestamp}] {level} {message}"


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
    """Упрощенное логирование действия.
    
    Логирует только WARNING и выше с действиями, остальное - просто сообщения.
    
    Args:
        logger: Логгер для записи
        level: Уровень логирования (logging.INFO, logging.ERROR и т.д.)
        action: Название действия (используется только для WARNING+)
        message: Текстовое сообщение
        details: Игнорируется (для упрощения)
        file_path: Игнорируется (для упрощения)
        file_count: Игнорируется (для упрощения)
        method_name: Игнорируется (для упрощения)
        duration_ms: Игнорируется (для упрощения)
        exc_info: Логировать ли информацию об исключении
    """
    # Логируем только важные события (WARNING и выше) с действиями
    if level >= logging.WARNING:
        extra = {'action': action}
        logger.log(level, message, extra=extra, exc_info=exc_info)
    elif level >= logging.INFO:
        # Для INFO просто логируем сообщение без лишних данных
        logger.log(level, message, exc_info=exc_info)
    # DEBUG логи игнорируются для упрощения


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
        action: Название действия (используется только для WARNING+)
        message: Сообщение
        file_path: Игнорируется (для упрощения)
        old_name: Игнорируется (для упрощения)
        new_name: Игнорируется (для упрощения)
        **kwargs: Игнорируется (для упрощения)
    """
    # Логируем только важные события
    logger.info(message)


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
        action: Игнорируется (для упрощения)
        message: Сообщение
        file_count: Количество файлов (добавляется в сообщение)
        success_count: Игнорируется (для упрощения)
        error_count: Игнорируется (для упрощения)
        **kwargs: Игнорируется (для упрощения)
    """
    # Упрощенное сообщение с количеством файлов
    if file_count > 0:
        logger.info(f"{message} (файлов: {file_count})")
    else:
        logger.info(message)

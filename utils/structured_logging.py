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
    """Форматтер для структурированного логирования действий."""
    
    def format(self, record):
        """Форматирование записи лога в структурированном виде."""
        # Извлекаем структурированные данные из extra
        action = getattr(record, 'action', 'UNKNOWN')
        details = getattr(record, 'details', {})
        file_path = getattr(record, 'file_path', None)
        file_count = getattr(record, 'file_count', None)
        method_name = getattr(record, 'method_name', None)
        duration_ms = getattr(record, 'duration_ms', None)
        
        # Формируем структурированное сообщение
        # Используем datetime для получения миллисекунд, так как time.strftime не поддерживает %f
        timestamp = datetime.fromtimestamp(record.created)
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Миллисекунды
        
        parts = [
            timestamp_str,
            record.levelname,
            record.name.split('.')[-1] if '.' in record.name else record.name,  # Только имя модуля
        ]
        
        # Добавляем действие только если оно не UNKNOWN
        if action != 'UNKNOWN':
            parts.append(f"ACTION:{action}")
        
        # Добавляем дополнительные поля только если они есть
        if method_name:
            parts.append(f"METHOD:{method_name}")
        if file_path:
            file_name = os.path.basename(file_path) if file_path else 'N/A'
            parts.append(f"FILE:{file_name}")
        if file_count is not None:
            parts.append(f"FILES:{file_count}")
        if duration_ms is not None:
            parts.append(f"DURATION:{duration_ms:.2f}ms")
        
        # Основное сообщение
        parts.append(record.getMessage())
        
        # Детали в формате key=value (только если есть детали и действие не UNKNOWN)
        if details and action != 'UNKNOWN':
            detail_items = []
            for k, v in details.items():
                if isinstance(v, (list, tuple)):
                    v = ','.join(map(str, v))
                elif isinstance(v, dict):
                    v = ','.join(f'{k2}={v2}' for k2, v2 in v.items())
                detail_items.append(f"{k}={v}")
            if detail_items:
                parts.append(f"DETAILS:{','.join(detail_items)}")
        
        return " ".join(parts)


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
    """Логирование действия со структурированными данными.
    
    Args:
        logger: Логгер для записи
        level: Уровень логирования (logging.INFO, logging.ERROR и т.д.)
        action: Название действия (например, 'FILE_ADDED', 'RENAME_STARTED')
        message: Текстовое сообщение
        details: Дополнительные детали в виде словаря
        file_path: Путь к файлу (если применимо)
        file_count: Количество файлов (если применимо)
        method_name: Название метода/функции
        duration_ms: Длительность операции в миллисекундах
        exc_info: Логировать ли информацию об исключении
    """
    extra = {
        'action': action,
        'details': details or {},
        'file_path': file_path,
        'file_count': file_count,
        'method_name': method_name,
        'duration_ms': duration_ms
    }
    logger.log(level, message, extra=extra, exc_info=exc_info)


def log_file_action(logger: logging.Logger,
                    action: str,
                    message: str,
                    file_path: Optional[str] = None,
                    old_name: Optional[str] = None,
                    new_name: Optional[str] = None,
                    **kwargs):
    """Логирование действия с файлом.
    
    Args:
        logger: Логгер
        action: Название действия
        message: Сообщение
        file_path: Путь к файлу
        old_name: Старое имя файла
        new_name: Новое имя файла
        **kwargs: Дополнительные детали
    """
    details = kwargs.copy()
    if old_name:
        details['old_name'] = old_name
    if new_name:
        details['new_name'] = new_name
    
    log_action(
        logger=logger,
        level=logging.INFO,
        action=action,
        message=message,
        details=details,
        file_path=file_path,
        **{k: v for k, v in kwargs.items() if k not in details}
    )


def log_batch_action(logger: logging.Logger,
                    action: str,
                    message: str,
                    file_count: int,
                    success_count: Optional[int] = None,
                    error_count: Optional[int] = None,
                    **kwargs):
    """Логирование пакетного действия.
    
    Args:
        logger: Логгер
        action: Название действия
        message: Сообщение
        file_count: Общее количество файлов
        success_count: Количество успешных операций
        error_count: Количество ошибок
        **kwargs: Дополнительные детали
    """
    details = kwargs.copy()
    if success_count is not None:
        details['success_count'] = success_count
    if error_count is not None:
        details['error_count'] = error_count
    
    log_action(
        logger=logger,
        level=logging.INFO,
        action=action,
        message=message,
        details=details,
        file_count=file_count
    )

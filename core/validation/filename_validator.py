"""Валидатор имен файлов."""

import os
import sys
import logging
from typing import Optional

try:
    from config.constants import (
        WINDOWS_RESERVED_NAMES,
        INVALID_FILENAME_CHARS,
        WINDOWS_MAX_FILENAME_LENGTH,
        WINDOWS_MAX_PATH_LENGTH
    )
except ImportError:
    # Fallback значения
    WINDOWS_RESERVED_NAMES = frozenset(
        ['CON', 'PRN', 'AUX', 'NUL'] +
        [f'COM{i}' for i in range(1, 10)] +
        [f'LPT{i}' for i in range(1, 10)]
    )
    INVALID_FILENAME_CHARS = frozenset(['<', '>', ':', '"', '/', '\\', '|', '?', '*'])
    WINDOWS_MAX_FILENAME_LENGTH = 255
    WINDOWS_MAX_PATH_LENGTH = 260

logger = logging.getLogger(__name__)


class FilenameValidator:
    """Класс для валидации имен файлов."""
    
    @staticmethod
    def is_valid_filename(name: str, extension: str = '') -> tuple[bool, Optional[str]]:
        """Проверка валидности имени файла.
        
        Args:
            name: Имя файла (без расширения)
            extension: Расширение файла (с точкой или без)
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Имя файла не может быть пустым"
        
        # Нормализуем расширение
        if extension and not extension.startswith('.'):
            extension = '.' + extension
        
        full_name = name + extension
        
        # Проверка длины
        if sys.platform == 'win32':
            if len(full_name) > WINDOWS_MAX_FILENAME_LENGTH:
                return False, f"Имя файла слишком длинное (максимум {WINDOWS_MAX_FILENAME_LENGTH} символов)"
        
        # Проверка зарезервированных имен Windows
        if sys.platform == 'win32':
            name_upper = name.upper()
            if name_upper in WINDOWS_RESERVED_NAMES:
                return False, f"Имя '{name}' зарезервировано в Windows"
        
        # Проверка запрещенных символов
        for char in INVALID_FILENAME_CHARS:
            if char in name:
                return False, f"Имя файла содержит запрещенный символ: '{char}'"
        
        # Проверка на точки в конце (Windows)
        if sys.platform == 'win32':
            if name.endswith('.') or name.endswith(' '):
                return False, "Имя файла не может заканчиваться точкой или пробелом в Windows"
        
        return True, None
    
    @staticmethod
    def is_valid_path_length(full_path: str) -> tuple[bool, Optional[str]]:
        """Проверка длины пути.
        
        Args:
            full_path: Полный путь к файлу
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if sys.platform == 'win32':
            if len(full_path) > WINDOWS_MAX_PATH_LENGTH and not full_path.startswith('\\\\?\\'):
                return False, f"Путь слишком длинный (максимум {WINDOWS_MAX_PATH_LENGTH} символов)"
        return True, None
    
    @staticmethod
    def sanitize_filename(name: str, replacement: str = '_') -> str:
        """Очистка имени файла от недопустимых символов.
        
        Args:
            name: Имя файла для очистки
            replacement: Символ для замены недопустимых символов
            
        Returns:
            Очищенное имя файла
        """
        sanitized = name
        for char in INVALID_FILENAME_CHARS:
            sanitized = sanitized.replace(char, replacement)
        
        # Убираем точки и пробелы в конце (Windows)
        if sys.platform == 'win32':
            sanitized = sanitized.rstrip('. ')
        
        return sanitized


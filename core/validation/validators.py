"""Валидаторы имен файлов и путей."""

import os
import sys
import logging
from pathlib import Path
from typing import List, Optional

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


class PathValidator:
    """Класс для валидации путей к файлам и директориям."""
    
    @staticmethod
    def is_safe_path(
        path: str,
        allowed_dirs: Optional[List[str]] = None,
        must_exist: bool = True,
        must_be_file: bool = True
    ) -> bool:
        """Проверка безопасности пути.
        
        Args:
            path: Путь к файлу для проверки
            allowed_dirs: Список разрешенных директорий (опционально)
            must_exist: Должен ли путь существовать
            must_be_file: Должен ли путь указывать на файл (True) или директорию (False)
            
        Returns:
            True если путь безопасен, False в противном случае
        """
        try:
            # Нормализуем путь
            normalized_path = os.path.normpath(os.path.abspath(path))
            
            # Проверяем существование
            if must_exist and not os.path.exists(normalized_path):
                return False
            
            # Проверяем тип (файл или директория)
            if must_exist:
                if must_be_file and not os.path.isfile(normalized_path):
                    return False
                if not must_be_file and not os.path.isdir(normalized_path):
                    return False
            
            # Проверяем разрешенные директории (если указаны)
            if allowed_dirs:
                path_dir = os.path.dirname(normalized_path) if must_be_file else normalized_path
                # Проверяем, находится ли путь в одной из разрешенных директорий
                for allowed_dir in allowed_dirs:
                    normalized_allowed = os.path.normpath(os.path.abspath(allowed_dir))
                    try:
                        # Используем pathlib для более надежной проверки
                        path_obj = Path(path_dir)
                        allowed_obj = Path(normalized_allowed)
                        if path_obj.is_relative_to(allowed_obj):
                            return True
                    except (ValueError, AttributeError):
                        # Для старых версий Python или если путь не относительный
                        if path_dir.startswith(normalized_allowed):
                            return True
                return False
            
            return True
        except Exception as e:
            logger.debug(f"Ошибка при проверке пути: {e}")
            return False
    
    @staticmethod
    def validate_path(
        path: str,
        allowed_dirs: Optional[List[str]] = None,
        must_exist: bool = True,
        must_be_file: bool = True
    ) -> tuple[bool, Optional[str]]:
        """Валидация пути с возвратом результата и ошибки.
        
        Args:
            path: Путь к файлу для проверки
            allowed_dirs: Список разрешенных директорий (опционально)
            must_exist: Должен ли путь существовать
            must_be_file: Должен ли путь указывать на файл (True) или директорию (False)
            
        Returns:
            Tuple[валидность, сообщение об ошибке или None]
        """
        try:
            normalized_path = os.path.normpath(os.path.abspath(path))
            
            if must_exist and not os.path.exists(normalized_path):
                return False, f"Путь не существует: {normalized_path}"
            
            if must_exist:
                if must_be_file and not os.path.isfile(normalized_path):
                    return False, f"Путь не является файлом: {normalized_path}"
                if not must_be_file and not os.path.isdir(normalized_path):
                    return False, f"Путь не является директорией: {normalized_path}"
            
            if allowed_dirs:
                path_dir = os.path.dirname(normalized_path) if must_be_file else normalized_path
                for allowed_dir in allowed_dirs:
                    normalized_allowed = os.path.normpath(os.path.abspath(allowed_dir))
                    try:
                        path_obj = Path(path_dir)
                        allowed_obj = Path(normalized_allowed)
                        if path_obj.is_relative_to(allowed_obj):
                            return True, None
                    except (ValueError, AttributeError):
                        if path_dir.startswith(normalized_allowed):
                            return True, None
                return False, f"Путь не находится в разрешенных директориях: {normalized_path}"
            
            return True, None
        except Exception as e:
            return False, f"Ошибка при проверке пути: {str(e)}"


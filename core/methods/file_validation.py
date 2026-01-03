"""Модуль валидации и проверки конфликтов имен файлов.

Объединяет функции для:
- Валидации имен файлов с кэшированием результатов
- Проверки конфликтов имен файлов при переименовании
"""

import logging
import os
import sys
from collections import OrderedDict, defaultdict
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ============================================================================
# Кэширование
# ============================================================================

# Кэш для результатов валидации имен файлов
_validation_cache: OrderedDict[Tuple[str, str, str], str] = OrderedDict()
_VALIDATION_CACHE_SIZE = 5000

# Кэш для нормализованных путей (для оптимизации проверки дубликатов)
try:
    from config.constants import MAX_PATH_CACHE_SIZE
    _MAX_CACHE_SIZE = MAX_PATH_CACHE_SIZE
except ImportError:
    _MAX_CACHE_SIZE = 10000

_path_cache: OrderedDict[str, None] = OrderedDict()

# Импортируем константы из config
try:
    from config.constants import INVALID_FILENAME_CHARS, WINDOWS_RESERVED_NAMES
    _RESERVED_NAMES = WINDOWS_RESERVED_NAMES
    _INVALID_CHARS = INVALID_FILENAME_CHARS
except ImportError:
    _RESERVED_NAMES = frozenset(
        ['CON', 'PRN', 'AUX', 'NUL'] +
        [f'COM{i}' for i in range(1, 10)] +
        [f'LPT{i}' for i in range(1, 10)]
    )
    _INVALID_CHARS = frozenset(['<', '>', ':', '"', '/', '\\', '|', '?', '*'])


# ============================================================================
# Вспомогательные функции для валидации
# ============================================================================

def _get_validation_cache_key(name: str, extension: str, path: str) -> Tuple[str, str, str]:
    """Создает ключ для кеша валидации."""
    # Нормализуем путь для консистентности
    try:
        normalized_path = os.path.dirname(os.path.normpath(path)) if path else ""
    except (OSError, ValueError):
        normalized_path = path if path else ""
    return (name, extension, normalized_path)


def _get_cached_validation(name: str, extension: str, path: str) -> Optional[str]:
    """Получает результат валидации из кеша."""
    cache_key = _get_validation_cache_key(name, extension, path)
    return _validation_cache.get(cache_key)


def _set_cached_validation(name: str, extension: str, path: str, result: str) -> None:
    """Сохраняет результат валидации в кеш."""
    cache_key = _get_validation_cache_key(name, extension, path)
    if len(_validation_cache) >= _VALIDATION_CACHE_SIZE:
        _validation_cache.popitem(last=False)
    _validation_cache[cache_key] = result


def _clear_validation_cache() -> None:
    """Очистка кеша валидации."""
    _validation_cache.clear()


def _add_to_path_cache(path: str) -> None:
    """Добавление пути в кеш с ограничением размера."""
    if len(_path_cache) >= _MAX_CACHE_SIZE:
        _path_cache.popitem(last=False)
    _path_cache[path] = None


def _clear_path_cache() -> None:
    """Очистка кеша путей."""
    _path_cache.clear()


def clear_all_caches() -> None:
    """Очистка всех кешей валидации и путей."""
    _validation_cache.clear()
    _path_cache.clear()
    logger.info("Все кеши валидации и путей очищены")


# ============================================================================
# Валидация имен файлов
# ============================================================================

def validate_filename(name: str, extension: str, path: str, index: int) -> str:
    """Валидация имени файла.
    
    Использует новый FilenameValidator для валидации, сохраняя обратную совместимость.
    
    Args:
        name: Имя файла без расширения
        extension: Расширение файла
        path: Путь к файлу
        index: Индекс файла в списке
        
    Returns:
        Статус валидации ("Готов" или сообщение об ошибке)
    """
    # Проверяем кеш перед выполнением валидации
    cached_result = _get_cached_validation(name, extension, path)
    if cached_result is not None:
        return cached_result
    
    # Используем новый FilenameValidator
    try:
        from core.validation import FilenameValidator
        
        is_valid, error_msg = FilenameValidator.is_valid_filename(name, extension)
        if not is_valid:
            result = f"Ошибка: {error_msg}" if error_msg else "Ошибка: недопустимое имя файла"
            _set_cached_validation(name, extension, path, result)
            return result
        
        # Проверка длины пути
        try:
            full_path = os.path.join(os.path.dirname(path) if path else "", name + extension)
            is_path_valid, path_error = FilenameValidator.is_valid_path_length(full_path)
            if not is_path_valid:
                result = f"Ошибка: {path_error}" if path_error else "Ошибка: путь слишком длинный"
                _set_cached_validation(name, extension, path, result)
                return result
        except (OSError, ValueError, AttributeError):
            pass  # Если не удалось проверить путь, продолжаем
        
        # Если все проверки пройдены, возвращаем успех
        result = "Готов"
        _set_cached_validation(name, extension, path, result)
        return result
        
    except ImportError:
        # Fallback на старую логику если новый модуль недоступен
        if not name or not name.strip():
            result = "Ошибка: пустое имя"
            _set_cached_validation(name, extension, path, result)
            return result
        
        # Запрещенные символы в именах файлов Windows
        if any(char in name for char in _INVALID_CHARS):
            for char in _INVALID_CHARS:
                if char in name:
                    result = f"Ошибка: недопустимый символ '{char}'"
                    _set_cached_validation(name, extension, path, result)
                    return result
        
        # Проверка на зарезервированные имена Windows
        if name.upper() in _RESERVED_NAMES:
            result = f"Ошибка: зарезервированное имя '{name}'"
            _set_cached_validation(name, extension, path, result)
            return result
        
        # Проверка длины имени
        try:
            from config.constants import (
                WINDOWS_MAX_FILENAME_LENGTH,
                WINDOWS_MAX_PATH_LENGTH,
                check_windows_path_length
            )
            MAX_FILENAME_LEN = WINDOWS_MAX_FILENAME_LENGTH
            MAX_PATH_LEN = WINDOWS_MAX_PATH_LENGTH
            has_path_check = True
        except ImportError:
            MAX_FILENAME_LEN = 255
            MAX_PATH_LEN = 260
            has_path_check = False
        
        full_name = name + extension
        if len(full_name) > MAX_FILENAME_LEN:
            result = f"Ошибка: имя слишком длинное ({len(full_name)} > {MAX_FILENAME_LEN})"
            _set_cached_validation(name, extension, path, result)
            return result
        
        # Проверка на точки в конце имени (Windows не позволяет)
        if name.endswith('.') or name.endswith(' '):
            result = "Ошибка: имя не может заканчиваться точкой или пробелом"
            _set_cached_validation(name, extension, path, result)
            return result
        
        # Проверка длины полного пути для Windows
        if sys.platform == 'win32' and path:
            try:
                directory = os.path.dirname(path)
                full_path = os.path.join(directory, full_name)
                if has_path_check:
                    if not check_windows_path_length(full_path):
                        result = f"Ошибка: полный путь слишком длинный (>{MAX_PATH_LEN} символов)"
                        _set_cached_validation(name, extension, path, result)
                        return result
                elif len(full_path) > MAX_PATH_LEN and not full_path.startswith('\\\\?\\'):
                    result = f"Ошибка: полный путь слишком длинный (>{MAX_PATH_LEN} символов)"
                    _set_cached_validation(name, extension, path, result)
                    return result
            except (OSError, ValueError):
                pass  # Игнорируем ошибки проверки пути
        
        result = "Готов"
        _set_cached_validation(name, extension, path, result)
        return result


# ============================================================================
# Проверка конфликтов
# ============================================================================

def check_conflicts(files_list: List[Dict[str, Any]]) -> None:
    """Проверка конфликтов имен файлов.
    
    Оптимизированная версия с использованием defaultdict для O(1) добавления.
    
    Args:
        files_list: Список файлов с информацией о переименовании
    """
    # Используем defaultdict для группировки файлов по новому имени
    # Это позволяет избежать множественных проверок и улучшить производительность
    new_names_map: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    # Собираем все новые имена и группируем файлы по новым именам
    for file_data in files_list:
        new_name = file_data.get('new_name', '')
        new_ext = file_data.get('extension', '')
        new_full_name = f"{new_name}{new_ext}"
        
        # Нормализуем путь для проверки дубликатов
        file_path = file_data.get('path', '') or file_data.get('full_path', '')
        if file_path:
            normalized_path = os.path.normpath(os.path.abspath(file_path))
            _add_to_path_cache(normalized_path)
        
        # Добавляем файл в группу с таким же новым именем
        new_names_map[new_full_name].append(file_data)
    
    # Проверяем конфликты: если несколько файлов имеют одно и то же новое имя
    for new_full_name, files_with_same_name in new_names_map.items():
        if len(files_with_same_name) > 1:
            # Конфликт: несколько файлов будут иметь одно и то же имя
            for file_data in files_with_same_name:
                file_data['status'] = 'conflict'
                file_data['error'] = f"Конфликт: несколько файлов будут иметь имя '{new_full_name}'"
                logger.warning(f"Конфликт имен: файл {file_data.get('path', 'unknown')} будет иметь имя '{new_full_name}' вместе с другими файлами")
        
        # Также проверяем, не существует ли уже файл с таким именем
        if len(files_with_same_name) == 1:
            file_data = files_with_same_name[0]
            file_path = file_data.get('path', '') or file_data.get('full_path', '')
            if file_path:
                # Проверяем, не будет ли конфликт с существующим файлом
                directory = os.path.dirname(file_path)
                new_full_path = os.path.join(directory, new_full_name)
                
                # Нормализуем пути для сравнения
                try:
                    normalized_old = os.path.normpath(os.path.abspath(file_path))
                    normalized_new = os.path.normpath(os.path.abspath(new_full_path))
                    
                    # Если новый путь отличается от старого и файл уже существует
                    if normalized_new != normalized_old and os.path.exists(normalized_new):
                        file_data['status'] = 'conflict'
                        file_data['error'] = f"Конфликт: файл '{new_full_name}' уже существует"
                        logger.warning(f"Конфликт: файл '{new_full_name}' уже существует в {directory}")
                except (OSError, ValueError) as e:
                    # Игнорируем ошибки нормализации путей
                    logger.debug(f"Ошибка при нормализации путей для проверки конфликтов: {e}")


"""Кеш для проверок существования файлов.

Оптимизирует производительность за счет кеширования результатов проверок существования файлов.
"""

import os
import logging
import time
from collections import OrderedDict
from typing import Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

# Глобальный кеш для проверок существования файлов
_file_exists_cache: OrderedDict[str, Tuple[bool, float]] = OrderedDict()
_cache_max_size = 10000
_cache_ttl = 5.0  # Время жизни кеша в секундах (5 секунд)


def clear_file_cache() -> None:
    """Очистка кеша проверок существования файлов."""
    _file_exists_cache.clear()
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Кеш проверок существования файлов очищен")


def get_file_exists_cached(file_path: str) -> Optional[bool]:
    """Получение результата проверки существования файла из кеша.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        True если файл существует, False если не существует, None если нет в кеше
    """
    normalized_path = str(Path(file_path).resolve())
    current_time = time.time()
    
    if normalized_path in _file_exists_cache:
        exists, cached_time = _file_exists_cache[normalized_path]
        # Проверяем, не устарел ли кеш
        if current_time - cached_time < _cache_ttl:
            # Обновляем порядок (LRU)
            _file_exists_cache.move_to_end(normalized_path)
            return exists
        else:
            # Удаляем устаревшую запись
            del _file_exists_cache[normalized_path]
    
    return None


def set_file_exists_cached(file_path: str, exists: bool) -> None:
    """Сохранение результата проверки существования файла в кеш.
    
    Args:
        file_path: Путь к файлу
        exists: Результат проверки
    """
    normalized_path = str(Path(file_path).resolve())
    current_time = time.time()
    
    # Ограничиваем размер кеша
    if len(_file_exists_cache) >= _cache_max_size:
        # Удаляем самую старую запись
        _file_exists_cache.popitem(last=False)
    
    _file_exists_cache[normalized_path] = (exists, current_time)


def is_file_cached(file_path: str) -> bool:
    """Проверка существования файла с использованием кеша.
    
    Args:
        file_path: Путь к файлу
        
    Returns:
        True если файл существует, False иначе
    """
    # Пробуем получить из кеша
    cached_result = get_file_exists_cached(file_path)
    if cached_result is not None:
        return cached_result
    
    # Если нет в кеше, проверяем и сохраняем результат
    try:
        exists = os.path.isfile(file_path)
        set_file_exists_cached(file_path, exists)
        return exists
    except (OSError, ValueError) as e:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Ошибка при проверке существования файла {file_path}: {e}")
        return False


def is_dir_cached(dir_path: str) -> bool:
    """Проверка существования директории с использованием кеша.
    
    Args:
        dir_path: Путь к директории
        
    Returns:
        True если директория существует, False иначе
    """
    normalized_path = str(Path(dir_path).resolve())
    current_time = time.time()
    
    # Для директорий используем тот же кеш, но с другим ключом
    cache_key = f"dir:{normalized_path}"
    
    if cache_key in _file_exists_cache:
        exists, cached_time = _file_exists_cache[cache_key]
        if current_time - cached_time < _cache_ttl:
            _file_exists_cache.move_to_end(cache_key)
            return exists
        else:
            del _file_exists_cache[cache_key]
    
    try:
        exists = os.path.isdir(dir_path)
        if len(_file_exists_cache) >= _cache_max_size:
            _file_exists_cache.popitem(last=False)
        _file_exists_cache[cache_key] = (exists, current_time)
        return exists
    except (OSError, ValueError) as e:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Ошибка при проверке существования директории {dir_path}: {e}")
        return False


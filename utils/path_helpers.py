"""Централизованные функции для работы с путями.

Этот модуль предоставляет единую точку доступа к функциям работы с путями,
устраняя необходимость в множественных fallback импортах.
"""

import logging
import os
from typing import Optional, List, Dict, Callable, Any

logger = logging.getLogger(__name__)

# Кеш для результатов импорта
_path_functions_cache: Dict[str, Optional[Dict[str, Callable[..., Any]]]] = {}


def _get_path_functions() -> Optional[Dict[str, Callable[..., Any]]]:
    """Получение функций работы с путями с кешированием.
    
    Returns:
        Словарь с функциями работы с путями или None
    """
    if 'module' in _path_functions_cache:
        return _path_functions_cache['module']
    
    # Пробуем импортировать из infrastructure/system/paths.py
    try:
        from infrastructure.system.paths import (
            get_app_data_dir,
            get_logs_dir,
            get_data_dir,
            get_log_file_path,
            get_settings_file_path,
            get_templates_file_path,
            ensure_directory_exists,
            is_safe_path,
            check_windows_path_length
        )
        _path_functions_cache['module'] = {
            'get_app_data_dir': get_app_data_dir,
            'get_logs_dir': get_logs_dir,
            'get_data_dir': get_data_dir,
            'get_log_file_path': get_log_file_path,
            'get_settings_file_path': get_settings_file_path,
            'get_templates_file_path': get_templates_file_path,
            'ensure_directory_exists': ensure_directory_exists,
            'is_safe_path': is_safe_path,
            'check_windows_path_length': check_windows_path_length,
        }
        return _path_functions_cache['module']
    except ImportError:
        # Если импорт не удался, возвращаем None
        # Вызывающий код должен использовать fallback
        if logger.isEnabledFor(logging.WARNING):
            logger.warning("Не удалось импортировать функции из infrastructure.system.paths")
        return None


def get_path_function(func_name: str) -> Optional[Callable[..., Any]]:
    """Получение функции работы с путями по имени.
    
    Args:
        func_name: Имя функции
        
    Returns:
        Функция или None
    """
    path_funcs = _get_path_functions()
    if path_funcs:
        return path_funcs.get(func_name)
    return None


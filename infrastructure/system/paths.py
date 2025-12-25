"""Утилиты для работы с путями."""

import os
import logging
import tempfile
from pathlib import Path
from typing import Optional, List

# Импорт констант
try:
    from config.constants import (
        LOG_FILE,
        CONTEXT_MENU_WRAPPER_LOG,
        SETTINGS_FILE,
        TEMPLATES_FILE,
        WINDOWS_MAX_PATH_LENGTH
    )
except ImportError:
    # Fallback если константы недоступны
    LOG_FILE = "re-file-plus.log"
    CONTEXT_MENU_WRAPPER_LOG = "context_menu_wrapper.log"
    SETTINGS_FILE = "re-file-plus_settings.json"
    TEMPLATES_FILE = "re-file-plus_templates.json"
    WINDOWS_MAX_PATH_LENGTH = 260

logger = logging.getLogger(__name__)


def get_app_data_dir() -> str:
    """Получение директории программы для хранения конфигурационных файлов.
    
    Использует абсолютный путь к файлу, чтобы работать корректно
    при запуске через ярлык (когда рабочая директория может быть другой).
    
    Returns:
        Путь к директории программы
    """
    # Определяем директорию, где находится этот файл (infrastructure/system/paths.py)
    # Используем os.path.abspath(__file__) для получения абсолютного пути
    # независимо от текущей рабочей директории
    current_file = os.path.abspath(__file__)
    # Переходим от infrastructure/system/paths.py к корню проекта
    system_dir = os.path.dirname(current_file)
    infrastructure_dir = os.path.dirname(system_dir)
    app_dir = os.path.dirname(infrastructure_dir)  # Корень проекта
    # Нормализуем путь (убираем двойные слеши и т.д.)
    app_dir = os.path.normpath(app_dir)
    return app_dir


def get_logs_dir() -> str:
    """Получение директории для хранения логов.
    
    Создает директорию, если её нет. Использует абсолютные пути
    для корректной работы при запуске через ярлык.
    
    Returns:
        Путь к директории логов
    """
    app_dir = get_app_data_dir()
    logs_dir = os.path.join(app_dir, "logs")
    # Нормализуем путь
    logs_dir = os.path.normpath(logs_dir)
    
    # Создаём директорию, если её нет
    if not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir, exist_ok=True)
            # Проверяем, что директория действительно создана
            if not os.path.exists(logs_dir):
                # Логируем предупреждение, если логгер уже настроен
                try:
                    logger.warning(f"Не удалось создать директорию логов: {logs_dir}")
                except:
                    # Если логгер еще не настроен, выводим в консоль
                    print(f"Предупреждение: Не удалось создать директорию логов: {logs_dir}")
        except (OSError, PermissionError) as e:
            # Логируем ошибку, если логгер уже настроен
            try:
                logger.error(f"Ошибка при создании директории логов {logs_dir}: {e}")
            except:
                print(f"Ошибка при создании директории логов {logs_dir}: {e}")
            
            # Пробуем использовать временную директорию как fallback
            try:
                temp_logs_dir = os.path.join(tempfile.gettempdir(), "re-file-plus-logs")
                temp_logs_dir = os.path.normpath(temp_logs_dir)
                os.makedirs(temp_logs_dir, exist_ok=True)
                try:
                    logger.info(f"Используется временная директория для логов: {temp_logs_dir}")
                except:
                    print(f"Информация: Используется временная директория для логов: {temp_logs_dir}")
                return temp_logs_dir
            except Exception as temp_e:
                try:
                    logger.error(f"Не удалось создать временную директорию для логов: {temp_e}")
                except:
                    print(f"Ошибка: Не удалось создать временную директорию для логов: {temp_e}")
    return logs_dir


def get_data_dir() -> str:
    """Получение директории для хранения конфигурационных файлов и кеша.
    
    Returns:
        Путь к директории данных
    """
    data_dir = os.path.join(get_app_data_dir(), "data")
    # Создаём директорию, если её нет
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
        except Exception:
            pass
    return data_dir


def get_log_file_path() -> str:
    """Получение полного пути к файлу основного лога."""
    return os.path.join(get_logs_dir(), LOG_FILE)


def get_context_menu_wrapper_log_path() -> str:
    """Получение полного пути к файлу лога обёртки контекстного меню."""
    return os.path.join(get_logs_dir(), CONTEXT_MENU_WRAPPER_LOG)


def get_settings_file_path() -> str:
    """Получение полного пути к файлу настроек."""
    return os.path.join(get_data_dir(), SETTINGS_FILE)


def get_templates_file_path() -> str:
    """Получение полного пути к файлу шаблонов."""
    return os.path.join(get_data_dir(), TEMPLATES_FILE)


def ensure_directory_exists(path: str) -> bool:
    """Создание директории если не существует.
    
    Args:
        path: Путь к директории
        
    Returns:
        True если директория существует или была создана, False в противном случае
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except (OSError, PermissionError) as e:
        logger.error(f"Не удалось создать директорию {path}: {e}")
        return False


def is_safe_path(path: str, allowed_dirs: Optional[List[str]] = None) -> bool:
    """Проверка безопасности пути.
    
    Args:
        path: Путь к файлу для проверки
        allowed_dirs: Список разрешенных директорий (опционально)
        
    Returns:
        True если путь безопасен, False в противном случае
    """
    try:
        # Проверка типа
        if not isinstance(path, str):
            return False
        if not path or not path.strip():
            return False
        
        # Проверяем на path traversal
        if '..' in path or path.startswith('~'):
            return False
        
        # Нормализуем путь
        abs_path = os.path.abspath(path)
        
        # Проверяем, что это файл
        if not os.path.isfile(abs_path):
            return False
        
        # Если указаны разрешенные директории, проверяем
        if allowed_dirs:
            for allowed_dir in allowed_dirs:
                allowed_abs = os.path.abspath(allowed_dir)
                if abs_path.startswith(allowed_abs):
                    return True
            return False
        
        return True
    except (OSError, ValueError, TypeError):
        return False


def check_windows_path_length(full_path: str) -> bool:
    """Проверка длины пути для Windows.
    
    Args:
        full_path: Полный путь к файлу
        
    Returns:
        True если длина пути допустима, False в противном случае
    """
    import sys
    if sys.platform == 'win32':
        # Windows MAX_PATH = 260, но можно использовать длинные пути с \\?\ 
        return len(full_path) <= WINDOWS_MAX_PATH_LENGTH or full_path.startswith('\\\\?\\')
    return True


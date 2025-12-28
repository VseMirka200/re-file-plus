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
        SETTINGS_FILE,
        TEMPLATES_FILE,
        WINDOWS_MAX_PATH_LENGTH
    )
except ImportError:
    # Fallback если константы недоступны
    LOG_FILE = "re-file-plus.log"
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
    # Используем pathlib для более современного подхода
    current_file = Path(__file__).resolve()
    # Переходим от infrastructure/system/paths.py к корню проекта
    app_dir = current_file.parent.parent.parent  # infrastructure -> system -> infrastructure -> корень
    return str(app_dir)


def get_logs_dir() -> str:
    """Получение директории для хранения логов.
    
    Создает директорию, если её нет. Использует абсолютные пути
    для корректной работы при запуске через ярлык.
    
    Returns:
        Путь к директории логов
    """
    app_dir = Path(get_app_data_dir())
    logs_dir = app_dir / "logs"
    
    # Создаём директорию, если её нет
    if not logs_dir.exists():
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
            # Проверяем, что директория действительно создана
            if not logs_dir.exists():
                # Логируем предупреждение, если логгер уже настроен
                try:
                    logger.warning(f"Не удалось создать директорию логов: {logs_dir}")
                except (AttributeError, NameError):
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
                temp_logs_dir = Path(tempfile.gettempdir()) / "re-file-plus-logs"
                temp_logs_dir.mkdir(parents=True, exist_ok=True)
                try:
                    logger.info(f"Используется временная директория для логов: {temp_logs_dir}")
                except:
                    print(f"Информация: Используется временная директория для логов: {temp_logs_dir}")
                return str(temp_logs_dir)
            except Exception as temp_e:
                try:
                    logger.error(f"Не удалось создать временную директорию для логов: {temp_e}")
                except:
                    print(f"Ошибка: Не удалось создать временную директорию для логов: {temp_e}")
    return str(logs_dir)


def get_data_dir() -> str:
    """Получение директории для хранения конфигурационных файлов и кеша.
    
    Returns:
        Путь к директории данных (используется app_data_dir вместо отдельной папки data)
    """
    # Используем app_data_dir напрямую, без создания отдельной папки data
    return get_app_data_dir()


def get_log_file_path() -> str:
    """Получение полного пути к файлу основного лога."""
    return str(Path(get_logs_dir()) / LOG_FILE)


def get_settings_file_path() -> str:
    """Получение полного пути к файлу настроек."""
    return str(Path(get_data_dir()) / SETTINGS_FILE)


def get_templates_file_path() -> str:
    """Получение полного пути к файлу шаблонов."""
    return str(Path(get_data_dir()) / TEMPLATES_FILE)


def ensure_directory_exists(path: str) -> bool:
    """Создание директории если не существует.
    
    Args:
        path: Путь к директории
        
    Returns:
        True если директория существует или была создана, False в противном случае
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError) as e:
        logger.error(f"Не удалось создать директорию {path}: {e}")
        return False


def is_safe_path(path: str, allowed_dirs: Optional[List[str]] = None) -> bool:
    """Проверка безопасности пути.
    
    Использует новый PathValidator для валидации, сохраняя обратную совместимость.
    
    Args:
        path: Путь к файлу для проверки
        allowed_dirs: Список разрешенных директорий (опционально)
        
    Returns:
        True если путь безопасен, False в противном случае
    """
    try:
        # Используем новый PathValidator если доступен
        from core.validation import PathValidator
        return PathValidator.is_safe_path(
            path,
            allowed_dirs=allowed_dirs,
            must_exist=True,
            must_be_file=True
        )
    except ImportError:
        # Fallback на старую логику если новый модуль недоступен
        try:
            # Проверка типа
            if not isinstance(path, str):
                return False
            if not path or not path.strip():
                return False
            
            # Проверка на NULL байты (могут использоваться для обхода проверок)
            if '\0' in path:
                return False
            
            # Улучшенная проверка на path traversal
            # Проверяем, что '..' не является частью пути (не в имени файла)
            path_parts = path.split(os.sep)
            if '..' in path_parts or path.startswith('~'):
                return False
            
            # Проверка на абсолютные пути с символами подстановки
            if os.path.isabs(path):
                # Проверяем на использование символов подстановки в пути
                if '*' in path or '?' in path:
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


"""Утилиты для обеспечения безопасности приложения."""

import os
import shlex
import logging
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


def validate_path_for_subprocess(path: str, must_exist: bool = True, must_be_file: bool = False) -> Tuple[bool, Optional[str]]:
    """Валидация пути перед передачей в subprocess.
    
    Args:
        path: Путь для валидации
        must_exist: Должен ли путь существовать
        must_be_file: Должен ли путь быть файлом (если True, проверяет isfile)
        
    Returns:
        Tuple[валиден, сообщение_об_ошибке]
    """
    if not isinstance(path, str):
        return False, "Путь должен быть строкой"
    
    if not path or not path.strip():
        return False, "Путь не может быть пустым"
    
    # Проверка на NULL байты
    if '\0' in path:
        return False, "Путь содержит NULL байты"
    
    # Проверка на wildcard символы (могут быть использованы для атак)
    if '*' in path or '?' in path:
        return False, "Путь содержит wildcard символы (* или ?)"
    
    # Проверка на пути, начинающиеся с ~ (home directory expansion)
    if path.startswith('~'):
        return False, "Путь содержит расширение домашней директории (~)"
    
    # Проверка на path traversal
    try:
        path_obj = Path(path)
        # Проверяем, что нормализованный путь не содержит '..'
        normalized = path_obj.resolve()
        if '..' in normalized.parts:
            return False, "Путь содержит path traversal (..)"
        
        # Проверка на символические ссылки (может быть обходом)
        if normalized.is_symlink():
            # Разрешаем символические ссылки только если они ведут в безопасную директорию
            real_path = normalized.resolve()
            if not real_path.exists():
                return False, "Символическая ссылка ведет к несуществующему пути"
    except (OSError, ValueError) as e:
        return False, f"Ошибка валидации пути: {e}"
    
    # Проверка существования
    if must_exist:
        if not os.path.exists(path):
            return False, "Путь не существует"
        
        if must_be_file and not os.path.isfile(path):
            return False, "Путь не является файлом"
    
    return True, None


def sanitize_path_for_subprocess(path: str) -> Optional[str]:
    """Очистка и валидация пути для использования в subprocess.
    
    Args:
        path: Путь для очистки
        
    Returns:
        Валидированный абсолютный путь или None
    """
    try:
        # Нормализуем путь
        abs_path = os.path.abspath(os.path.normpath(path))
        
        # Валидируем
        is_valid, error_msg = validate_path_for_subprocess(abs_path, must_exist=True)
        if not is_valid:
            logger.warning(f"Небезопасный путь отклонен: {abs_path} - {error_msg}")
            return None
        
        return abs_path
    except (OSError, ValueError) as e:
        logger.warning(f"Ошибка при очистке пути {path}: {e}")
        return None


def sanitize_command_args(args: List[str], validate_paths: bool = True) -> List[str]:
    """Очистка аргументов команды для subprocess.
    
    Args:
        args: Список аргументов команды
        validate_paths: Валидировать ли пути в аргументах
        
    Returns:
        Очищенный список аргументов
    """
    sanitized = []
    
    for arg in args:
        if not isinstance(arg, str):
            logger.warning(f"Пропущен нестроковый аргумент: {type(arg)}")
            continue
        
        # Если это путь и нужно валидировать
        if validate_paths and (os.path.sep in arg or os.path.altsep in arg):
            sanitized_path = sanitize_path_for_subprocess(arg)
            if sanitized_path:
                sanitized.append(sanitized_path)
            else:
                logger.warning(f"Пропущен небезопасный путь: {arg}")
        else:
            # Для не-путей используем shlex.quote для безопасности
            # Но только если это не опция команды (начинается с -)
            if arg.startswith('-'):
                sanitized.append(arg)
            else:
                # Экранируем специальные символы
                sanitized.append(shlex.quote(arg))
    
    return sanitized


def validate_json_size(file_path: str, max_size_mb: int = 10) -> Tuple[bool, Optional[str]]:
    """Валидация размера JSON файла перед загрузкой.
    
    Args:
        file_path: Путь к JSON файлу
        max_size_mb: Максимальный размер в мегабайтах
        
    Returns:
        Tuple[валиден, сообщение_об_ошибке]
    """
    try:
        if not os.path.exists(file_path):
            return True, None  # Файл не существует - это нормально
        
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            return False, f"Файл слишком большой: {file_size / 1024 / 1024:.2f} MB (максимум {max_size_mb} MB)"
        
        return True, None
    except (OSError, ValueError) as e:
        return False, f"Ошибка проверки размера файла: {e}"


"""Утилиты для обработки путей из аргументов командной строки."""

import logging
import os
import sys
from typing import List, Optional

logger = logging.getLogger(__name__)

# Импорт функции валидации путей
try:
    from infrastructure.system.paths import is_safe_path
    HAS_PATH_VALIDATION = True
except ImportError:
    try:
        from config.constants import is_safe_path
        HAS_PATH_VALIDATION = True
    except ImportError:
        HAS_PATH_VALIDATION = False
        logger.warning("Функция is_safe_path недоступна, валидация путей отключена")


def process_file_argument(arg: str) -> Optional[str]:
    """Обработка одного аргумента командной строки как пути к файлу.
    
    Args:
        arg: Аргумент командной строки
        
    Returns:
        Нормализованный путь к файлу или None, если аргумент не является файлом
    """
    if not arg or not arg.strip():
        return None
    
    # Обработка URL-формата (file://) - используется LibreOffice и другими приложениями
    if arg.startswith('file://'):
        try:
            # Удаляем префикс file:// и декодируем URL
            import urllib.parse
            file_path = urllib.parse.unquote(arg[7:])  # Убираем file://
            # Убираем начальный слеш для Windows путей (file:///C:/...)
            if sys.platform == 'win32' and file_path.startswith('/') and len(file_path) > 2:
                if file_path[1].isalpha() and file_path[2] == ':':
                    file_path = file_path[1:]  # Убираем лишний слеш
            normalized_path = os.path.normpath(file_path)
            
            # Валидация безопасности пути
            if HAS_PATH_VALIDATION and not is_safe_path(normalized_path):
                logger.warning(f"Небезопасный URL-путь отклонен: {normalized_path}")
                return None
            
            if os.path.exists(normalized_path) and os.path.isfile(normalized_path):
                logger.info(f"Обработан URL-путь: {arg} -> {normalized_path}")
                return normalized_path
        except Exception as e:
            logger.debug(f"Ошибка обработки URL-пути {arg}: {e}")
        return None
    
    # Обработка путей в кавычках (для путей с пробелами)
    cleaned_arg = arg.strip('"').strip("'")
    
    # Пропускаем аргументы, которые выглядят как опции (начинаются с -)
    # но проверяем, не является ли это путем к файлу
    if arg.startswith('-'):
        # Проверяем, существует ли это как файл
        normalized_arg = os.path.normpath(arg)
        
        # Проверяем как абсолютный путь
        file_exists = False
        if os.path.exists(normalized_arg) and os.path.isfile(normalized_arg):
            file_exists = True
        else:
            # Проверяем как относительный путь от текущей директории
            try:
                abs_path = os.path.abspath(normalized_arg)
                if os.path.exists(abs_path) and os.path.isfile(abs_path):
                    file_exists = True
            except (OSError, ValueError):
                pass
        
        # Если это файл, возвращаем его
        if file_exists:
            return normalized_arg
        # Иначе пропускаем (это опция)
        return None
    
    # Обработка обычных путей
    normalized_arg = os.path.normpath(cleaned_arg)
    
    # Валидация безопасности пути
    if HAS_PATH_VALIDATION and not is_safe_path(normalized_arg):
        logger.warning(f"Небезопасный путь отклонен: {normalized_arg}")
        return None
    
    # Проверяем существование файла
    if os.path.exists(normalized_arg) and os.path.isfile(normalized_arg):
        return normalized_arg
    else:
        # Попытка обработать как абсолютный путь
        try:
            abs_path = os.path.abspath(normalized_arg)
            # Валидация абсолютного пути
            if HAS_PATH_VALIDATION and not is_safe_path(abs_path):
                logger.warning(f"Небезопасный абсолютный путь отклонен: {abs_path}")
                return None
            if os.path.exists(abs_path) and os.path.isfile(abs_path):
                logger.info(f"Обработан относительный путь: {arg} -> {abs_path}")
                return abs_path
        except (OSError, ValueError) as e:
            logger.debug(f"Не удалось обработать путь {arg}: {e}")
    
    return None


def filter_cli_args(args: List[str]) -> List[str]:
    """Фильтрация аргументов командной строки, оставляя только существующие файлы.
    
    Args:
        args: Список аргументов командной строки (без имени скрипта)
        
    Returns:
        Список путей к файлам
    """
    filtered_args = []
    
    for arg in args:
        file_path = process_file_argument(arg)
        if file_path:
            filtered_args.append(file_path)
    
    return filtered_args


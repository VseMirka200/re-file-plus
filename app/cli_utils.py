"""Утилиты для обработки аргументов командной строки.

Этот модуль содержит функции для обработки и валидации аргументов командной строки,
используемые как в GUI, так и в CLI версиях приложения.
"""

import logging
import os
import sys
from typing import List

logger = logging.getLogger(__name__)

# Импорт функции валидации путей
try:
    try:
        from infrastructure.system.paths import is_safe_path
    except ImportError:
        from config.constants import is_safe_path
    HAS_PATH_VALIDATION = True
except ImportError:
    HAS_PATH_VALIDATION = False
    logger.warning("Функция is_safe_path недоступна, валидация путей отключена")


def process_cli_args() -> List[str]:
    """Обработка аргументов командной строки.
    
    Фильтрует аргументы командной строки, оставляя только существующие файлы.
    Игнорирует опции (аргументы, начинающиеся с -), если они не являются путями к файлам.
    Поддерживает различные форматы путей, включая URL-формат (file://) и пути в кавычках.
    
    Returns:
        List[str]: Список путей к файлам из аргументов командной строки
    """
    try:
        from utils.path_processing import filter_cli_args
        if len(sys.argv) > 1:
            logger.info(f"Аргументы командной строки: {sys.argv[1:]}")
            files_from_args = filter_cli_args(sys.argv[1:])
            logger.info(f"Обработано файлов из аргументов: {len(files_from_args)}")
            return files_from_args
    except ImportError:
        # Fallback на старую логику, если модуль недоступен
        logger.warning("Модуль utils.path_processing недоступен, используется fallback логика")
        files_from_args = []
        
        if len(sys.argv) > 1:
            logger.info(f"Аргументы командной строки: {sys.argv[1:]}")
            
            for arg in sys.argv[1:]:
                if not arg or not arg.strip():
                    continue
                
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
                            continue
                        if os.path.exists(normalized_path) and os.path.isfile(normalized_path):
                            files_from_args.append(normalized_path)
                            logger.info(f"Обработан URL-путь: {arg} -> {normalized_path}")
                            continue
                    except (ValueError, urllib.parse.UnquoteError, OSError) as e:
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"Ошибка обработки URL-пути {arg}: {e}")
                    except (AttributeError, TypeError) as e:
                        if logger.isEnabledFor(logging.DEBUG):
                            logger.debug(f"Ошибка типа/атрибутов при обработке URL-пути {arg}: {e}")
                    except (MemoryError, RecursionError) as e:
                        # Ошибки памяти/рекурсии
                        pass
                    # Финальный catch для неожиданных исключений (критично для стабильности)
                    except BaseException as e:
                        if isinstance(e, (KeyboardInterrupt, SystemExit)):
                            raise
                        logger.warning(f"Неожиданная ошибка обработки URL-пути {arg}: {e}", exc_info=True)
                
                # Обработка коротких опций (начинаются с одного дефиса)
                if arg.startswith('-') and not arg.startswith('--'):
                    normalized_arg = os.path.normpath(arg)
                    # Проверяем, не является ли это путем к файлу, начинающимся с дефиса
                    if os.path.exists(normalized_arg) and os.path.isfile(normalized_arg):
                        files_from_args.append(normalized_arg)
                        continue
                    # Если это не файл, пропускаем (это опция)
                    continue
                
                # Обработка длинных опций (начинаются с двух дефисов)
                if arg.startswith('--'):
                    normalized_arg = os.path.normpath(arg)
                    if os.path.exists(normalized_arg) and os.path.isfile(normalized_arg):
                        files_from_args.append(normalized_arg)
                    # Пропускаем опции, которые не являются файлами
                    continue
                
                # Обработка путей в кавычках (для путей с пробелами)
                cleaned_arg = arg.strip('"').strip("'")
                
                # Обработка обычных путей
                normalized_arg = os.path.normpath(cleaned_arg)
                
                # Валидация безопасности пути
                if HAS_PATH_VALIDATION and not is_safe_path(normalized_arg):
                    logger.warning(f"Небезопасный путь отклонен: {normalized_arg}")
                    continue
                
                # Проверяем существование файла
                if os.path.exists(normalized_arg) and os.path.isfile(normalized_arg):
                    files_from_args.append(normalized_arg)
                else:
                    # Попытка обработать как абсолютный путь
                    try:
                        abs_path = os.path.abspath(normalized_arg)
                        # Валидация абсолютного пути
                        if HAS_PATH_VALIDATION and not is_safe_path(abs_path):
                            logger.warning(f"Небезопасный абсолютный путь отклонен: {abs_path}")
                            continue
                        if os.path.exists(abs_path) and os.path.isfile(abs_path):
                            files_from_args.append(abs_path)
                            logger.info(f"Обработан относительный путь: {arg} -> {abs_path}")
                    except (OSError, ValueError) as e:
                        logger.debug(f"Не удалось обработать путь {arg}: {e}")
        
        logger.info(f"Обработано файлов из аргументов: {len(files_from_args)}")
        return files_from_args
    
    return []


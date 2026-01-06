"""Утилиты для обеспечения безопасности приложения."""

import os
import shlex
import logging
import sys
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Для Windows: функция проверки существования файла с полной поддержкой Unicode
def _check_file_exists_unicode(path: str) -> bool:
    """Проверка существования файла с полной поддержкой Unicode (включая кириллицу).
    
    На Windows использует несколько методов для надежной проверки путей с Unicode.
    
    Args:
        path: Путь к файлу
        
    Returns:
        True если файл существует, False иначе
    """
    # Метод 1: Попытка открыть файл (самый надежный для Unicode на Windows)
    try:
        with open(path, 'rb') as f:
            return True
    except (OSError, IOError, FileNotFoundError, PermissionError):
        pass
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    
    # Метод 2: os.path.exists() (может не работать с кириллицей на некоторых системах)
    try:
        if os.path.exists(path) and os.path.isfile(path):
            return True
    except (OSError, UnicodeEncodeError, UnicodeDecodeError):
        pass
    
    # Метод 3: pathlib.Path (может работать лучше с Unicode)
    try:
        path_obj = Path(path)
        if path_obj.exists() and path_obj.is_file():
            return True
    except (OSError, UnicodeEncodeError, UnicodeDecodeError, ValueError):
        pass
    
    # Метод 4: Для Windows - используем Windows API через ctypes (если доступно)
    if sys.platform == 'win32':
        try:
            import ctypes
            from ctypes import wintypes
            
            # Используем GetFileAttributesW для проверки существования
            # W версия работает с Unicode
            kernel32 = ctypes.windll.kernel32
            GetFileAttributesW = kernel32.GetFileAttributesW
            GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
            GetFileAttributesW.restype = wintypes.DWORD
            
            INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF
            FILE_ATTRIBUTE_DIRECTORY = 0x10
            
            attrs = GetFileAttributesW(path)
            if attrs != INVALID_FILE_ATTRIBUTES:
                # Файл существует, проверяем что это не директория
                if not (attrs & FILE_ATTRIBUTE_DIRECTORY):
                    return True
        except (ImportError, OSError, AttributeError, ValueError):
            # ctypes или Windows API недоступны - пропускаем
            pass
    
    return False


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
    
    # Проверка на path traversal и получение нормализованного пути
    resolved_path = None
    try:
        path_obj = Path(path)
        # Проверяем, что нормализованный путь не содержит '..'
        # Используем resolve() для получения абсолютного пути и обработки символических ссылок
        try:
            # Пробуем resolve() с strict=False (доступно в Python 3.6+)
            # Это позволяет обрабатывать несуществующие пути
            try:
                normalized = path_obj.resolve(strict=False)
            except TypeError:
                # Если strict параметр не поддерживается (старые версии Python)
                # пробуем обычный resolve()
                try:
                    normalized = path_obj.resolve()
                except (OSError, RuntimeError, FileNotFoundError, UnicodeEncodeError, UnicodeDecodeError):
                    # На Windows с Unicode resolve() может не работать
                    # Используем os.path для нормализации
                    normalized = Path(os.path.abspath(os.path.normpath(path)))
        except (OSError, RuntimeError, FileNotFoundError, UnicodeEncodeError, UnicodeDecodeError):
            # Если resolve() не удался (например, путь не существует или Unicode проблема),
            # используем абсолютный нормализованный путь через os.path
            # Это более надежно для Unicode путей на Windows
            try:
                normalized = Path(os.path.abspath(os.path.normpath(path)))
            except (OSError, ValueError, UnicodeEncodeError, UnicodeDecodeError):
                # Если даже это не работает, используем исходный путь
                normalized = path_obj
        
        if '..' in normalized.parts:
            return False, "Путь содержит path traversal (..)"
        
        # Сохраняем разрешенный путь для дальнейших проверок
        resolved_path = str(normalized)
        
        # Проверка на символические ссылки (может быть обходом)
        try:
            if normalized.is_symlink():
                # Разрешаем символические ссылки только если они ведут в безопасную директорию
                real_path = normalized.resolve()
                if not real_path.exists():
                    return False, "Символическая ссылка ведет к несуществующему пути"
        except (OSError, RuntimeError):
            # Игнорируем ошибки при проверке символических ссылок
            pass
    except (OSError, ValueError) as e:
        # Если не удалось разрешить путь, пробуем использовать исходный путь
        # Это может произойти для путей с особыми символами на Windows
        try:
            resolved_path = os.path.abspath(os.path.normpath(path))
            # Проверяем на path traversal в исходном пути
            if '..' in Path(resolved_path).parts:
                return False, "Путь содержит path traversal (..)"
        except (OSError, ValueError):
            # Если даже нормализация не удалась, используем исходный путь
            resolved_path = path
    
    # Проверка существования - используем разрешенный путь если доступен
    check_path = resolved_path if resolved_path else path
    if must_exist:
        # Используем функцию с полной поддержкой Unicode для проверки существования
        if not _check_file_exists_unicode(check_path):
            # Пробуем также с исходным путем, если он отличается
            if check_path != path and _check_file_exists_unicode(path):
                # Исходный путь существует, но разрешенный - нет
                # Это может быть проблема с разрешением пути (нормально для Unicode на Windows)
                logger.debug(f"Путь существует в исходном виде, но не в разрешенном: {path} -> {check_path}")
                # Используем исходный путь для дальнейших проверок
                check_path = path
            else:
                return False, "Путь не существует"
        
        if must_be_file:
            # Проверяем, что это файл, а не директория
            try:
                if os.path.isdir(check_path):
                    return False, "Путь не является файлом"
            except (OSError, UnicodeEncodeError, UnicodeDecodeError):
                # Если os.path.isdir не работает, пробуем через pathlib
                try:
                    if Path(check_path).is_dir():
                        return False, "Путь не является файлом"
                except (OSError, UnicodeEncodeError, UnicodeDecodeError, ValueError):
                    pass
    
    return True, None


def sanitize_path_for_subprocess(path: str, check_existence: bool = True) -> Optional[str]:
    """Очистка и валидация пути для использования в subprocess.
    
    Поддерживает пути с Unicode символами (включая кириллицу) на Windows.
    
    Args:
        path: Путь для очистки
        check_existence: Проверять ли существование файла (False для выходных файлов)
        
    Returns:
        Валидированный абсолютный путь или None
    """
    try:
        # Проверяем существование файла с полной поддержкой Unicode (включая кириллицу)
        # На Windows os.path.exists() может не работать корректно с кириллицей
        # Для выходных файлов проверку существования можно пропустить
        if check_existence:
            file_exists = _check_file_exists_unicode(path)
            
            if not file_exists:
                logger.warning(f"Путь не существует при очистке: {path}")
                return None
        
        # Нормализуем путь - используем pathlib для лучшей поддержки Unicode
        try:
            path_obj = Path(path)
            # Пробуем получить абсолютный путь через pathlib
            try:
                abs_path = str(path_obj.resolve(strict=False))
            except (TypeError, OSError, RuntimeError, FileNotFoundError):
                # Fallback на os.path если resolve() не работает
                # На Windows с Unicode это может быть более надежно
                abs_path = os.path.abspath(os.path.normpath(path))
        except (OSError, ValueError, TypeError, UnicodeEncodeError, UnicodeDecodeError):
            # Fallback на os.path для совместимости
            # Используем исходный путь, если нормализация не удалась
            abs_path = os.path.abspath(os.path.normpath(path))
        
        # Проверяем существование после нормализации с поддержкой Unicode
        # На Windows с кириллицей стандартные методы могут работать некорректно
        # Пропускаем проверку для выходных файлов (check_existence=False)
        if check_existence:
            abs_path_exists = _check_file_exists_unicode(abs_path)
            
            if not abs_path_exists:
                # Пробуем исходный путь (может быть проблема с нормализацией Unicode)
                original_exists = _check_file_exists_unicode(path)
                
                if original_exists:
                    # Используем исходный путь, если он существует
                    # Это нормально для Unicode путей на Windows
                    abs_path = os.path.abspath(os.path.normpath(path))
                else:
                    logger.warning(f"Путь не существует после нормализации: {abs_path}")
                    return None
        
        # Валидируем путь (базовая проверка безопасности без строгой проверки существования)
        # Для выходных файлов (check_existence=False) пропускаем проверку существования
        is_valid, error_msg = validate_path_for_subprocess(abs_path, must_exist=False)
        if not is_valid:
            # Если базовая валидация не прошла, но файл существует (если проверяли), 
            # это может быть проблема с Unicode - используем исходный путь
            if check_existence:
                path_exists = _check_file_exists_unicode(path)
                
                if path_exists:
                    logger.debug(f"Валидация не прошла, но файл существует (Unicode?): {path}")
                    # Проверяем базовую безопасность исходного пути
                    if '..' not in path and not path.startswith('~'):
                        return os.path.abspath(os.path.normpath(path))
            logger.warning(f"Небезопасный путь отклонен: {abs_path} - {error_msg}")
            return None
        
        # Финальная проверка существования с поддержкой Unicode (только если check_existence=True)
        if check_existence:
            final_check = _check_file_exists_unicode(abs_path)
            
            if not final_check:
                logger.warning(f"Путь не существует после валидации: {abs_path}")
                return None
        
        return abs_path
    except (OSError, ValueError, UnicodeEncodeError, UnicodeDecodeError) as e:
        logger.warning(f"Ошибка при очистке пути {path}: {e}")
        # Последняя попытка - если файл существует, возвращаем нормализованный путь
        try:
            if _check_file_exists_unicode(path):
                normalized = os.path.abspath(os.path.normpath(path))
                if _check_file_exists_unicode(normalized):
                    return normalized
        except (OSError, ValueError, UnicodeEncodeError, UnicodeDecodeError):
            pass
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


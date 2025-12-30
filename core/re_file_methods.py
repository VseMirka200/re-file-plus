"""Модуль методов re-file операций.

Реализует различные стратегии re-file операций через паттерн Strategy.
Каждый метод re-file наследуется от базового класса ReFileMethod
и реализует метод apply() для преобразования имени файла.

Также содержит функции для работы с файлами: валидация имен,
проверка конфликтов и re-file операции.

ПРИМЕЧАНИЕ: Этот модуль теперь использует разбитые на подмодули компоненты
из core/methods/ для лучшей организации кода. Все классы и функции
экспортируются для обратной совместимости.
"""

# Стандартная библиотека
import logging
import os
import re
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Локальные импорты
logger = logging.getLogger(__name__)


# Импортируем классы и функции из разбитых модулей
try:
    from .methods.base import ReFileMethod
    from .methods.implementations import (
        AddRemoveMethod,
        ReplaceMethod,
        CaseMethod,
        NumberingMethod,
        MetadataMethod,
        RegexMethod,
        NewNameMethod,
    )
    from .methods.file_validation import validate_filename, check_conflicts, _get_cached_validation, _set_cached_validation
    from .methods.file_renamer import re_file_files_thread
except ImportError:
    # Fallback для обратной совместимости (если модули еще не созданы)
    logger.error("КРИТИЧЕСКАЯ ОШИБКА: Не удалось импортировать методы из core.methods. Модули должны существовать!")
    raise ImportError("Модули core.methods не найдены. Проверьте структуру проекта.")


# Все классы методов теперь импортируются из core/methods/implementations.py
# Дублирующиеся определения удалены для избежания конфликтов


# ============================================================================
# ДВИЖОК СКРИПТОВ (объединен из core/script_engine.py)
# ============================================================================

class ScriptEngine:
    """Класс для выполнения пользовательских скриптов."""
    
    def __init__(self):
        """Инициализация движка скриптов."""
        import os
        self.scripts_dir = os.path.join(
            os.path.expanduser("~"),
            ".re_file_plus_scripts"
        )
        self._ensure_scripts_dir()
    
    def _ensure_scripts_dir(self):
        """Создание директории для скриптов."""
        import os
        try:
            os.makedirs(self.scripts_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"Не удалось создать директорию для скриптов: {e}")
    
    def execute_script(self, script_path: str, context: dict, timeout: float = 5.0) -> Optional[Any]:
        """Выполнение скрипта с валидацией и таймаутом.
        
        Args:
            script_path: Путь к скрипту
            context: Контекст выполнения (file_data, methods и т.д.)
            timeout: Максимальное время выполнения в секундах (по умолчанию 5.0)
            
        Returns:
            Результат выполнения скрипта или None
        """
        import os
        import signal
        import threading
        from typing import Any, Optional
        
        if not os.path.exists(script_path):
            logger.error(f"Скрипт не найден: {script_path}")
            return None
        
        # Логируем выполнение скрипта
        logger.info(f"Выполнение скрипта: {script_path}")
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_code = f.read()
            
            # Валидация скрипта перед выполнением
            validation_result, validation_error = self.validate_script_content(script_code)
            if not validation_result:
                logger.error(f"Скрипт не прошел валидацию: {validation_error}")
                return None
            
            # Безопасное выполнение скрипта
            # Ограничиваем доступные функции
            # ВАЖНО: os ограничен только безопасными функциями для работы с путями
            safe_os = {
                'path': {
                    'join': os.path.join,
                    'exists': os.path.exists,
                    'isfile': os.path.isfile,
                    'isdir': os.path.isdir,
                    'basename': os.path.basename,
                    'dirname': os.path.dirname,
                    'splitext': os.path.splitext,
                    'normpath': os.path.normpath,
                    'abspath': os.path.abspath,
                },
                'name': os.name,
                'sep': os.sep,
            }
            
            safe_globals = {
                '__builtins__': {
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'list': list,
                    'dict': dict,
                    'tuple': tuple,
                    'range': range,
                    'enumerate': enumerate,
                    'zip': zip,
                    'min': min,
                    'max': max,
                    'sum': sum,
                    'abs': abs,
                    'round': round,
                },
                'os': safe_os,  # Ограниченный доступ к os
                're': __import__('re'),
            }
            
            # Добавляем контекст
            safe_globals.update(context)
            
            # Выполняем скрипт с таймаутом
            result = None
            execution_error = None
            
            def execute():
                nonlocal result, execution_error
                try:
                    # Выполняем скрипт
                    exec(script_code, safe_globals)
                    
                    # Возвращаем результат, если есть функция main
                    if 'main' in safe_globals and callable(safe_globals['main']):
                        result = safe_globals['main']()
                except Exception as e:
                    execution_error = e
            
            # Запускаем выполнение в отдельном потоке с таймаутом
            execution_thread = threading.Thread(target=execute, daemon=True)
            execution_thread.start()
            execution_thread.join(timeout=timeout)
            
            if execution_thread.is_alive():
                logger.error(f"Таймаут выполнения скрипта {script_path} (>{timeout} сек)")
                return None
            
            if execution_error:
                raise execution_error
            
            logger.debug(f"Скрипт {script_path} выполнен успешно")
            return result
            
        except (SyntaxError, ValueError, TypeError) as e:
            logger.error(f"Ошибка синтаксиса/типа в скрипте {script_path}: {e}", exc_info=True)
            return None
        except (OSError, PermissionError) as e:
            logger.error(f"Ошибка доступа при выполнении скрипта {script_path}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Ошибка выполнения скрипта {script_path}: {e}", exc_info=True)
            return None
    
    def validate_script_content(self, script_code: str) -> Tuple[bool, Optional[str]]:
        """Валидация содержимого скрипта через AST.
        
        Проверяет на наличие опасных конструкций:
        - import/__import__
        - eval/exec/compile
        - open/file operations
        - subprocess/system calls
        
        Args:
            script_code: Код скрипта для валидации
            
        Returns:
            Tuple[валиден, сообщение_об_ошибке]
        """
        import ast
        
        try:
            # Парсим AST
            tree = ast.parse(script_code)
            
            # Запрещенные имена и атрибуты
            forbidden_names = {
                'eval', 'exec', 'compile', '__import__', 'open', 'file',
                'input', 'raw_input', 'execfile', 'reload', '__builtins__',
                'subprocess', 'os', 'sys', 'shutil', 'pickle', 'marshal'
            }
            
            forbidden_attributes = {
                'system', 'popen', 'call', 'run', 'spawn', 'fork', 'exec',
                'remove', 'unlink', 'rmdir', 'rmtree', 'chmod', 'chown'
            }
            
            # Проверяем все узлы AST
            for node in ast.walk(tree):
                # Проверяем импорты
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(name=node.module or '')]):
                        module_name = alias.name if isinstance(alias, ast.alias) else alias
                        if any(forbidden in module_name for forbidden in forbidden_names):
                            return False, f"Запрещенный импорт: {module_name}"
                
                # Проверяем вызовы функций
                if isinstance(node, ast.Call):
                    # Проверяем имя функции
                    if isinstance(node.func, ast.Name):
                        if node.func.id in forbidden_names:
                            return False, f"Запрещенная функция: {node.func.id}"
                    # Проверяем атрибуты
                    elif isinstance(node.func, ast.Attribute):
                        if node.func.attr in forbidden_attributes:
                            return False, f"Запрещенный метод: {node.func.attr}"
            
            return True, None
            
        except SyntaxError as e:
            return False, f"Синтаксическая ошибка: {e}"
        except Exception as e:
            return False, f"Ошибка валидации: {e}"
    
    def validate_script(self, script_path: str) -> Tuple[bool, Optional[str]]:
        """Валидация скрипта.
        
        Args:
            script_path: Путь к скрипту
            
        Returns:
            Tuple[валиден, сообщение_об_ошибке]
        """
        import os
        if not os.path.exists(script_path):
            return False, "Скрипт не найден"
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_code = f.read()
            
            # Валидация содержимого через AST
            validation_result, validation_error = self.validate_script_content(script_code)
            if not validation_result:
                return False, validation_error
            
            # Компилируем для проверки синтаксиса
            compile(script_code, script_path, 'exec')
            return True, None
        except SyntaxError as e:
            return False, f"Синтаксическая ошибка: {e}"
        except (OSError, PermissionError) as e:
            return False, f"Ошибка доступа к файлу: {e}"
        except Exception as e:
            return False, f"Ошибка: {e}"


# ============================================================================
# ФУНКЦИИ РАБОТЫ С ФАЙЛАМИ (объединены из core/file_operations.py)
# ============================================================================

def add_file_to_list(
    file_path: str,
    files_list: List[Dict[str, Any]],
    path_cache: Optional[Set[str]] = None
) -> Optional[Dict[str, Any]]:
    """Добавление файла в список для переименования.
    
    Args:
        file_path: Путь к файлу
        files_list: Список файлов для добавления
        path_cache: Множество нормализованных путей для быстрой проверки дубликатов (опционально)
        
    Returns:
        Словарь с данными файла или None если файл уже существует
    """
    # Используем одну проверку os.path.exists вместо двух
    try:
        if not os.path.isfile(file_path):
            return None
    except (OSError, ValueError):
        return None
    
    # Проверка на дубликаты - используем OrderedDict для O(1) проверки
    normalized_path = os.path.normpath(os.path.abspath(file_path))
    
    # Используем переданный кэш или создаем из списка файлов
    if path_cache is None:
        path_cache = set()
        for f in files_list:
            if hasattr(f, 'full_path'):
                # FileInfo объект
                existing_path = f.full_path or str(f.path) if hasattr(f, 'path') else ''
            elif isinstance(f, dict):
                # Словарь
                existing_path = f.get('full_path') or f.get('path', '')
            else:
                continue
            if existing_path:
                path_cache.add(os.path.normpath(os.path.abspath(existing_path)))
    
    # Проверяем дубликаты только в переданном кэше (локальном для текущего списка)
    # Глобальный кэш не используем для проверки, так как он может содержать старые данные
    if normalized_path in path_cache:
        return None
    
    # Добавляем путь в кэш с ограничением размера
    _add_to_path_cache(normalized_path)
    if isinstance(path_cache, set):
        path_cache.add(normalized_path)
    
    # Получаем имя файла и расширение
    path_obj = Path(file_path)
    name = path_obj.stem
    extension = path_obj.suffix
    
    file_data = {
        'path': file_path,
        'full_path': file_path,
        'old_name': name,
        'new_name': name,
        'extension': extension,
        'status': 'Готов'
    }
    
    files_list.append(file_data)
    return file_data


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
        except Exception:
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
        
        # Запрещенные символы в именах файлов Windows (используем кэш)
        if any(char in name for char in _INVALID_CHARS):
            # Находим первый недопустимый символ для сообщения об ошибке
            for char in _INVALID_CHARS:
                if char in name:
                    result = f"Ошибка: недопустимый символ '{char}'"
                    _set_cached_validation(name, extension, path, result)
                    return result
        
        # Проверка на зарезервированные имена Windows (используем кэш)
        if name.upper() in _RESERVED_NAMES:
            result = f"Ошибка: зарезервированное имя '{name}'"
            _set_cached_validation(name, extension, path, result)
            return result
        
        # Проверка длины имени (Windows ограничение: 255 символов для полного пути)
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


def check_conflicts(files_list: List[Dict[str, Any]]) -> None:
    """Проверка конфликтов имен файлов.
    
    Оптимизированная версия с использованием defaultdict для O(1) добавления.
    
    Args:
        files_list: Список файлов для проверки
    """
    from collections import defaultdict
    
    # Создаем словарь для подсчета одинаковых имен (оптимизация: defaultdict)
    name_counts: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for file_data in files_list:
        full_name = file_data['new_name'] + file_data['extension']
        name_counts[full_name].append(file_data)
    
    # Помечаем конфликты (только для групп с более чем одним файлом)
    for full_name, file_list in name_counts.items():
        if len(file_list) > 1:
            # Есть конфликт
            conflict_msg = f"Конфликт: {len(file_list)} файла с именем '{full_name}'"
            for file_data in file_list:
                if hasattr(file_data, 'set_error'):
                    file_data.set_error(conflict_msg)
                elif isinstance(file_data, dict):
                    file_data['status'] = conflict_msg

# Функция re_file_files_thread импортируется из core.methods.file_renamer (строка 42)
# Удалено неполное определение для использования правильной реализации

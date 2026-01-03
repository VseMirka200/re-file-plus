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


class ScriptEngine:
    """Класс для выполнения пользовательских скриптов.
    
    Обеспечивает безопасное выполнение пользовательских скриптов с использованием:
    - AST валидации для проверки безопасности кода перед выполнением
    - Изолированного контекста выполнения с ограниченными builtins
    - Ограниченного доступа к модулям (только безопасные операции)
    - Таймаута выполнения для предотвращения зависаний
    
    Безопасность:
    - Запрещены опасные функции: eval, exec, compile, __import__, open, file, input
    - Запрещены опасные модули: subprocess, os (кроме безопасных операций), sys
    - Все скрипты проходят AST валидацию перед выполнением
    - Используется изолированный словарь globals с ограниченными builtins
    
    Пример использования:
        engine = ScriptEngine()
        context = {'name': 'test', 'extension': '.txt'}
        result = engine.execute_script('/path/to/script.py', context)
    """
    
    def __init__(self):
        """Инициализация движка скриптов.
        
        Создает директорию для пользовательских скриптов в домашней директории пользователя.
        """
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
        except (OSError, PermissionError) as e:
            logger.error(f"Не удалось создать директорию для скриптов: {e}")
        except (ValueError, TypeError) as e:
            logger.error(f"Ошибка типа/значения при создании директории для скриптов: {e}", exc_info=True)
        except (KeyError, IndexError) as e:
            logger.error(f"Ошибка доступа к данным при создании директории для скриптов: {e}", exc_info=True)
        except (MemoryError, RecursionError) as e:
            logger.error(f"Ошибка памяти/рекурсии при создании директории для скриптов: {e}", exc_info=True)
        # Финальный catch для неожиданных исключений (критично для стабильности)
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            logger.error(f"Критическая ошибка при создании директории для скриптов: {e}", exc_info=True)
    
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
        if logger.isEnabledFor(logging.INFO):
            logger.info(f"Выполнение скрипта: {script_path}")
        
        try:
            # Проверка размера файла перед чтением
            try:
                from config.constants import MAX_SCRIPT_SIZE_KB
                file_size = os.path.getsize(script_path)
                max_size_bytes = MAX_SCRIPT_SIZE_KB * 1024
                if file_size > max_size_bytes:
                    logger.error(f"Скрипт слишком большой: {file_size / 1024:.2f} KB (максимум {MAX_SCRIPT_SIZE_KB} KB)")
                    return None
            except (OSError, ValueError) as size_error:
                if logger.isEnabledFor(logging.WARNING):
                    logger.warning(f"Не удалось проверить размер скрипта: {size_error}")
                # Продолжаем без проверки размера
            except ImportError:
                # Если константа недоступна, используем fallback значение
                try:
                    file_size = os.path.getsize(script_path)
                    if file_size > 100 * 1024:
                        logger.error(f"Скрипт слишком большой: {file_size / 1024:.2f} KB (максимум 100 KB)")
                        return None
                except (OSError, ValueError):
                    pass  # Продолжаем без проверки
            
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
            
            # Создаем ограниченный словарь builtins (только безопасные функции)
            restricted_builtins = {
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
                'sorted': sorted,
                'reversed': reversed,
                'any': any,
                'all': all,
                'isinstance': isinstance,
                'type': type,
                'hasattr': hasattr,
                'getattr': getattr,
                'setattr': setattr,
                'print': print,  # Разрешаем print для отладки
                # Явно запрещаем опасные функции (они не должны быть доступны)
            }
            # Убеждаемся, что опасные функции не доступны
            for dangerous in ['eval', 'exec', 'compile', '__import__', 'open', 'file', 
                            'input', 'raw_input', 'execfile', 'reload', 'exit', 'quit']:
                restricted_builtins.pop(dangerous, None)
            
            safe_globals = {
                '__builtins__': restricted_builtins,
                'os': safe_os,  # Ограниченный доступ к os
                're': __import__('re'),
            }
            
            # Добавляем контекст (только безопасные типы)
            # Контекст передается из вызывающего кода и содержит данные о файле,
            # методах и т.д. Мы фильтруем его, чтобы разрешить только безопасные типы
            for key, value in context.items():
                # Разрешаем только простые типы (immutable и базовые коллекции)
                # Эти типы не могут выполнить опасные операции напрямую
                if isinstance(value, (str, int, float, bool, list, dict, tuple, type(None))):
                    safe_globals[key] = value
                elif hasattr(value, '__dict__'):
                    # Для объектов разрешаем доступ, но они должны быть проверены
                    # на безопасность в вызывающем коде (например, FileInfo, ReFileMethod)
                    # ВАЖНО: объекты могут иметь методы, но мы полагаемся на валидацию AST,
                    # которая запрещает вызов опасных методов
                    safe_globals[key] = value
                else:
                    # Неизвестный тип - пропускаем для безопасности
                    logger.warning(f"Пропущен небезопасный контекстный ключ: {key}")
            
            # Выполняем скрипт с таймаутом
            result = None
            execution_error = None
            
            def execute():
                nonlocal result, execution_error
                try:
                    # Дополнительная проверка: убеждаемся, что скрипт прошел валидацию
                    is_valid, validation_error = self.validate_script_content(script_code)
                    if not is_valid:
                        execution_error = ValueError(f"Скрипт не прошел валидацию: {validation_error}")
                        return
                    
                    # Компилируем скрипт для дополнительной проверки
                    compiled_code = compile(script_code, script_path, 'exec')
                    
                    # Дополнительная защита: создаем полностью изолированный контекст
                    # Копируем безопасный словарь globals, чтобы не изменять оригинал
                    isolated_globals = safe_globals.copy()
                    # Убеждаемся, что __builtins__ не содержит опасных функций
                    # Это критично для безопасности: даже если в safe_globals случайно
                    # попала опасная функция, мы удаляем её здесь
                    if '__builtins__' in isolated_globals:
                        # Создаем копию словаря builtins для изоляции
                        isolated_builtins = isolated_globals['__builtins__'].copy() if isinstance(isolated_globals['__builtins__'], dict) else {}
                        # Удаляем все функции, которые не были явно разрешены
                        # Этот список включает все потенциально опасные функции Python:
                        # - eval, exec, compile - выполнение кода
                        # - __import__ - импорт модулей
                        # - open, file - работа с файлами
                        # - input, raw_input - ввод данных
                        # - exit, quit - завершение программы
                        dangerous_builtins = {'eval', 'exec', 'compile', '__import__', 'open', 'file', 
                                            'input', 'raw_input', 'execfile', 'reload', '__builtins__',
                                            'exit', 'quit', 'help', 'license', 'credits'}
                        for dangerous in dangerous_builtins:
                            isolated_builtins.pop(dangerous, None)
                        isolated_globals['__builtins__'] = isolated_builtins
                    
                    # Выполняем скрипт в изолированном контексте.
                    exec(compiled_code, isolated_globals)
                    
                    # Возвращаем результат, если есть функция main
                    if 'main' in isolated_globals and callable(isolated_globals['main']):
                        # Дополнительная проверка: функция main должна быть безопасной
                        result = isolated_globals['main']()
                except (SyntaxError, NameError, TypeError, ValueError, AttributeError) as e:
                    execution_error = e
                except (OSError, PermissionError) as e:
                    # Файловые операции не должны выполняться
                    execution_error = PermissionError(f"Запрещенная операция: {e}")
                except (RuntimeError, AttributeError) as e:
                    # Ошибки выполнения или доступа к атрибутам
                    logger.error(f"Ошибка выполнения скрипта: {e}", exc_info=True)
                    execution_error = e
                except (KeyError, IndexError) as e:
                    # Ошибки доступа к данным
                    logger.error(f"Ошибка доступа к данным при выполнении скрипта: {e}", exc_info=True)
                    execution_error = e
                except (MemoryError, RecursionError) as e:
                    # Ошибки памяти/рекурсии
                    logger.error(f"Ошибка памяти/рекурсии при выполнении скрипта: {e}", exc_info=True)
                    execution_error = e
                # Финальный catch для неожиданных исключений (критично для стабильности)
                except BaseException as e:
                    if isinstance(e, (KeyboardInterrupt, SystemExit)):
                        raise
                    # Логируем критические исключения
                    logger.error(f"Критическая ошибка выполнения скрипта: {e}", exc_info=True)
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
            
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Скрипт {script_path} выполнен успешно")
            return result
            
        except (SyntaxError, ValueError, TypeError, NameError, AttributeError) as e:
            logger.error(f"Ошибка синтаксиса/типа в скрипте {script_path}: {e}", exc_info=True)
            return None
        except (OSError, PermissionError) as e:
            logger.error(f"Ошибка доступа при выполнении скрипта {script_path}: {e}", exc_info=True)
            return None
        except (KeyboardInterrupt, SystemExit):
            # Не перехватываем системные исключения
            raise
        except (MemoryError, RecursionError) as e:
            logger.error(f"Ошибка памяти/рекурсии при выполнении скрипта {script_path}: {e}", exc_info=True)
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Ошибка доступа к данным при выполнении скрипта {script_path}: {e}", exc_info=True)
            return None
        # Финальный catch для неожиданных исключений (критично для стабильности)
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            logger.error(f"Критическая ошибка выполнения скрипта {script_path}: {e}", exc_info=True)
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
            # Проверяем размер скрипта
            try:
                from config.constants import MAX_SCRIPT_SIZE_KB
                script_size_bytes = len(script_code.encode('utf-8'))
                script_size_kb = script_size_bytes / 1024
                max_size_bytes = MAX_SCRIPT_SIZE_KB * 1024
                if script_size_bytes > max_size_bytes:
                    return False, f"Скрипт слишком большой ({script_size_kb:.2f} KB, максимум {MAX_SCRIPT_SIZE_KB} KB)"
            except ImportError:
                # Fallback если константа недоступна
                script_size_bytes = len(script_code.encode('utf-8'))
                if script_size_bytes > 100 * 1024:
                    return False, "Скрипт слишком большой (максимум 100KB)"
            
            # Парсим AST
            tree = ast.parse(script_code)
            
            # Запрещенные имена и атрибуты
            forbidden_names = {
                'eval', 'exec', 'compile', '__import__', 'open', 'file',
                'input', 'raw_input', 'execfile', 'reload', '__builtins__',
                'subprocess', 'sys', 'shutil', 'pickle', 'marshal', 'ctypes',
                'socket', 'urllib', 'requests', 'http', 'ftplib', 'smtplib',
                '__file__', '__name__', '__package__', '__loader__', '__spec__'
            }
            
            forbidden_attributes = {
                'system', 'popen', 'call', 'run', 'spawn', 'fork', 'exec',
                'remove', 'unlink', 'rmdir', 'rmtree', 'chmod', 'chown',
                'remove', 'unlink', 'rmdir', 'rmtree', 'chmod', 'chown',
                'connect', 'send', 'recv', 'sendall', 'bind', 'listen'
            }
            
            # Запрещенные модули для импорта
            forbidden_modules = {
                'os', 'sys', 'subprocess', 'shutil', 'pickle', 'marshal',
                'ctypes', 'socket', 'urllib', 'requests', 'http', 'ftplib',
                'smtplib', 'multiprocessing', 'threading', 'asyncio'
            }
            
            # Проверяем все узлы AST
            for node in ast.walk(tree):
                # Проверяем импорты
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split('.')[0]  # Берем только корневой модуль
                        if module_name in forbidden_modules:
                            return False, f"Запрещенный импорт: {module_name}"
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module.split('.')[0]
                        if module_name in forbidden_modules:
                            return False, f"Запрещенный импорт из: {module_name}"
                
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
                        # Проверяем, что не обращаемся к опасным модулям
                        if isinstance(node.func.value, ast.Name):
                            if node.func.value.id in forbidden_modules:
                                return False, f"Запрещенный доступ к модулю: {node.func.value.id}"
                
                # Проверяем на использование __import__
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    if node.func.id == '__import__':
                        return False, "Использование __import__ запрещено"
            
            return True, None
            
        except SyntaxError as e:
            return False, f"Синтаксическая ошибка: {e}"
        except (ValueError, TypeError) as e:
            return False, f"Ошибка валидации AST: {e}"
        except (AttributeError, RuntimeError) as e:
            logger.error(f"Ошибка валидации скрипта: {e}", exc_info=True)
            return False, f"Ошибка валидации: {e}"
        except (MemoryError, RecursionError) as e:
            logger.error(f"Ошибка памяти/рекурсии при валидации скрипта: {e}", exc_info=True)
            return False, f"Ошибка памяти/рекурсии: {e}"
        except (KeyError, IndexError) as e:
            logger.error(f"Ошибка доступа к данным при валидации скрипта: {e}", exc_info=True)
            return False, f"Ошибка доступа к данным: {e}"
        except (MemoryError, RecursionError) as e:
            logger.error(f"Ошибка памяти/рекурсии при валидации скрипта: {e}", exc_info=True)
            return False, f"Ошибка памяти/рекурсии: {e}"
        # Финальный catch для неожиданных исключений (критично для стабильности)
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            logger.error(f"Критическая ошибка валидации скрипта: {e}", exc_info=True)
            return False, f"Критическая ошибка валидации: {e}"
    
    def validate_script(self, script_path: str) -> Tuple[bool, Optional[str]]:
        """Валидация скрипта.
        
        Args:
            script_path: Путь к скрипту
            
        Returns:
            Tuple[валиден, сообщение_об_ошибке]
        """
        import os
        # Используем кеш для проверки существования
        try:
            from utils.file_cache import is_file_cached
            if not is_file_cached(script_path):
                return False, "Скрипт не найден"
        except ImportError:
            # Fallback если кеш недоступен
            if not os.path.exists(script_path) or not os.path.isfile(script_path):
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
        except (ValueError, TypeError, AttributeError) as e:
            return False, f"Ошибка валидации: {e}"
        except (UnicodeDecodeError, IOError) as e:
            return False, f"Ошибка чтения файла: {e}"
        except (MemoryError, RecursionError) as e:
            logger.warning(f"Ошибка памяти/рекурсии при валидации скрипта: {e}", exc_info=True)
            return False, f"Ошибка памяти/рекурсии: {e}"
        except (KeyError, IndexError) as e:
            logger.warning(f"Ошибка доступа к данным при валидации скрипта: {e}", exc_info=True)
            return False, f"Ошибка доступа к данным: {e}"
        except (MemoryError, RecursionError) as e:
            logger.warning(f"Ошибка памяти/рекурсии при валидации скрипта: {e}", exc_info=True)
            return False, f"Ошибка памяти/рекурсии: {e}"
        # Финальный catch для неожиданных исключений (критично для стабильности)
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            logger.warning(f"Критическая ошибка при валидации скрипта: {e}", exc_info=True)
            return False, f"Критическая ошибка: {e}"


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
    # Используем кеш для оптимизации проверок существования
    try:
        from utils.file_cache import is_file_cached
        if not is_file_cached(file_path):
            return None
    except ImportError:
        # Fallback если кеш недоступен
        try:
            if not os.path.isfile(file_path):
                return None
        except (OSError, ValueError):
            return None
    except (OSError, ValueError, TypeError):
        return None
    
    # Проверка на дубликаты - используем set для O(1) проверки существования
    # Нормализуем путь (убираем двойные слеши, преобразуем в абсолютный)
    # чтобы разные представления одного пути считались одинаковыми
    normalized_path = os.path.normpath(os.path.abspath(file_path))
    
    # Используем переданный кэш или создаем из списка файлов
    # path_cache - это set нормализованных путей для быстрой проверки дубликатов
    if path_cache is None:
        path_cache = set()
        # Строим кэш из существующих файлов в списке
        for f in files_list:
            # Поддерживаем два формата: FileInfo объекты и словари (для обратной совместимости)
            if hasattr(f, 'full_path'):
                # FileInfo объект: используем full_path или path
                existing_path = f.full_path or str(f.path) if hasattr(f, 'path') else ''
            elif isinstance(f, dict):
                # Словарь: используем full_path или path
                existing_path = f.get('full_path') or f.get('path', '')
            else:
                continue
            if existing_path:
                # Нормализуем и добавляем в кэш
                path_cache.add(os.path.normpath(os.path.abspath(existing_path)))
    
    # Проверяем дубликаты только в переданном кэше (локальном для текущего списка)
    # Глобальный кэш не используем для проверки, так как он может содержать старые данные
    # из предыдущих операций и не отражать текущее состояние списка файлов
    if normalized_path in path_cache:
        # Файл уже есть в списке - возвращаем None, чтобы не добавлять дубликат
        return None
    
    # Добавляем путь в кэш с ограничением размера
    try:
        from core.methods.file_validation import _add_to_path_cache
        _add_to_path_cache(normalized_path)
    except ImportError:
        # Fallback если кеш недоступен
        pass
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
    # Кеширование позволяет избежать повторных проверок для одинаковых имен,
    # что значительно ускоряет работу при обработке большого количества файлов
    cached_result = _get_cached_validation(name, extension, path)
    if cached_result is not None:
        return cached_result
    
    # Используем новый FilenameValidator для основной валидации
    # Это централизованная валидация, которая проверяет базовые правила
    try:
        from core.validation import FilenameValidator
        
        is_valid, error_msg = FilenameValidator.is_valid_filename(name, extension)
        if not is_valid:
            # Имя не прошло базовую валидацию - возвращаем ошибку
            result = f"Ошибка: {error_msg}" if error_msg else "Ошибка: недопустимое имя файла"
            _set_cached_validation(name, extension, path, result)
            return result
        
        # Проверка длины пути (дополнительная проверка для Windows)
        # Формируем полный путь для проверки общей длины
        try:
            full_path = os.path.join(os.path.dirname(path) if path else "", name + extension)
            is_path_valid, path_error = FilenameValidator.is_valid_path_length(full_path)
            if not is_path_valid:
                result = f"Ошибка: {path_error}" if path_error else "Ошибка: путь слишком длинный"
                _set_cached_validation(name, extension, path, result)
                return result
        except (OSError, ValueError, AttributeError, TypeError):
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
        
        # Импортируем константы для валидации
        try:
            from config.constants import INVALID_FILENAME_CHARS, WINDOWS_RESERVED_NAMES
            invalid_chars = INVALID_FILENAME_CHARS
            reserved_names = WINDOWS_RESERVED_NAMES
        except ImportError:
            # Fallback значения
            invalid_chars = frozenset(['<', '>', ':', '"', '/', '\\', '|', '?', '*'])
            reserved_names = frozenset(
                ['CON', 'PRN', 'AUX', 'NUL'] +
                [f'COM{i}' for i in range(1, 10)] +
                [f'LPT{i}' for i in range(1, 10)]
            )
        
        # Запрещенные символы в именах файлов Windows
        if any(char in name for char in invalid_chars):
            # Находим первый недопустимый символ для сообщения об ошибке
            for char in invalid_chars:
                if char in name:
                    result = f"Ошибка: недопустимый символ '{char}'"
                    _set_cached_validation(name, extension, path, result)
                    return result
        
        # Проверка на зарезервированные имена Windows
        if name.upper() in reserved_names:
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
    
    # Создаем словарь для группировки файлов по новым именам
    # defaultdict(list) автоматически создает пустой список для нового ключа,
    # что упрощает код и делает его эффективнее (O(1) добавление вместо O(n) проверки)
    name_counts: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for file_data in files_list:
        # Формируем полное имя (имя + расширение) для группировки
        full_name = file_data['new_name'] + file_data['extension']
        # Добавляем файл в группу с таким же именем
        name_counts[full_name].append(file_data)
    
    # Помечаем конфликты (только для групп с более чем одним файлом)
    # Если в группе только один файл, конфликта нет
    for full_name, file_list in name_counts.items():
        if len(file_list) > 1:
            # Есть конфликт: несколько файлов получают одно имя
            # Помечаем все конфликтующие файлы сообщением об ошибке
            conflict_msg = f"Конфликт: {len(file_list)} файла с именем '{full_name}'"
            for file_data in file_list:
                # Поддерживаем два формата: FileInfo объекты и словари
                if hasattr(file_data, 'set_error'):
                    # FileInfo объект: используем метод set_error
                    file_data.set_error(conflict_msg)
                elif isinstance(file_data, dict):
                    # Словарь: устанавливаем статус напрямую
                    file_data['status'] = conflict_msg

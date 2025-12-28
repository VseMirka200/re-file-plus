"""Модуль методов re-file операций.

Реализует различные стратегии re-file операций через паттерн Strategy.
Каждый метод re-file наследуется от базового класса ReFileMethod
и реализует метод apply() для преобразования имени файла.

Также содержит функции для работы с файлами: валидация имен,
проверка конфликтов и re-file операции.
"""

# Стандартная библиотека
import logging
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Локальные импорты
logger = logging.getLogger(__name__)

# Импорт менеджера резервных копий (опционально)
try:
    from .backup_manager import BackupManager
    HAS_BACKUP = True
except ImportError:
    HAS_BACKUP = False
    BackupManager = None

# Кэш для нормализованных путей (для оптимизации проверки дубликатов)
try:
    from config.constants import MAX_PATH_CACHE_SIZE
    _MAX_CACHE_SIZE = MAX_PATH_CACHE_SIZE
except ImportError:
    _MAX_CACHE_SIZE = 10000

_path_cache: OrderedDict[str, None] = OrderedDict()

def _add_to_path_cache(path: str) -> None:
    """Добавление пути в кеш с ограничением размера."""
    if len(_path_cache) >= _MAX_CACHE_SIZE:
        _path_cache.popitem(last=False)
    _path_cache[path] = None

def _clear_path_cache() -> None:
    """Очистка кеша путей."""
    _path_cache.clear()

# Кэш для результатов валидации имен файлов (для оптимизации производительности)
_validation_cache: OrderedDict[Tuple[str, str, str], str] = OrderedDict()
_VALIDATION_CACHE_SIZE = 5000

def _get_validation_cache_key(name: str, extension: str, path: str) -> Tuple[str, str, str]:
    """Создает ключ для кеша валидации."""
    # Нормализуем путь для консистентности
    try:
        normalized_path = os.path.dirname(os.path.normpath(path)) if path else ""
    except (OSError, ValueError):
        normalized_path = path if path else ""
    return (name, extension, normalized_path)

def _get_cached_validation(name: str, extension: str, path: str) -> Optional[str]:
    """Получает результат валидации из кеша."""
    cache_key = _get_validation_cache_key(name, extension, path)
    return _validation_cache.get(cache_key)

def _set_cached_validation(name: str, extension: str, path: str, result: str) -> None:
    """Сохраняет результат валидации в кеш."""
    cache_key = _get_validation_cache_key(name, extension, path)
    if len(_validation_cache) >= _VALIDATION_CACHE_SIZE:
        _validation_cache.popitem(last=False)
    _validation_cache[cache_key] = result

def _clear_validation_cache() -> None:
    """Очистка кеша валидации."""
    _validation_cache.clear()

# Импортируем константы из config
try:
    from config.constants import INVALID_FILENAME_CHARS, WINDOWS_RESERVED_NAMES
    _RESERVED_NAMES = WINDOWS_RESERVED_NAMES
    _INVALID_CHARS = INVALID_FILENAME_CHARS
except ImportError:
    _RESERVED_NAMES = frozenset(
        ['CON', 'PRN', 'AUX', 'NUL'] +
        [f'COM{i}' for i in range(1, 10)] +
        [f'LPT{i}' for i in range(1, 10)]
    )
    _INVALID_CHARS = frozenset(['<', '>', ':', '"', '/', '\\', '|', '?', '*'])


class ReFileMethod(ABC):
    """Базовый абстрактный класс для методов re-file операций.
    
    Все методы re-file должны наследоваться от этого класса
    и реализовывать метод apply() для преобразования имени файла.
    
    Методы re-file применяются последовательно к каждому файлу
    в порядке их добавления в MethodsManager.
    """
    
    @abstractmethod
    def apply(self, name: str, extension: str, file_path: str) -> Tuple[str, str]:
        """
        Применяет метод переименования к имени файла
        
        Args:
            name: Имя файла без расширения
            extension: Расширение файла (с точкой)
            file_path: Полный путь к файлу
            
        Returns:
            Tuple[str, str]: Новое имя и расширение
        """
        pass


class AddRemoveMethod(ReFileMethod):
    """Метод добавления/удаления текста"""
    
    def __init__(
        self,
        operation: str,
        text: str = "",
        position: str = "before",
        remove_type: Optional[str] = None,
        remove_start: Optional[str] = None,
        remove_end: Optional[str] = None
    ):
        """
        Args:
            operation: "add" или "remove"
            text: Текст для добавления
            position: "before", "after", "start", "end"
            remove_type: "chars" или "range" (для удаления)
            remove_start: Начальная позиция/количество для удаления
            remove_end: Конечная позиция для удаления (для диапазона)
        """
        self.operation = operation
        self.text = text
        self.position = position
        self.remove_type = remove_type
        self.remove_start = remove_start
        self.remove_end = remove_end
    
    def apply(self, name: str, extension: str, file_path: str) -> Tuple[str, str]:
        if self.operation == "add":
            return self._add_text(name, extension)
        else:
            return self._remove_text(name, extension)
    
    def _add_text(self, name: str, extension: str) -> Tuple[str, str]:
        """Добавление текста"""
        if not self.text:
            return name, extension
        
        if self.position == "before":
            # Перед именем (но после расширения не добавляем)
            new_name = self.text + name
            return new_name, extension
        elif self.position == "after":
            # После имени (перед расширением)
            new_name = name + self.text
            return new_name, extension
        elif self.position == "start":
            # В начале всего имени
            new_name = self.text + name
            return new_name, extension
        elif self.position == "end":
            # В конце всего имени (перед расширением)
            new_name = name + self.text
            return new_name, extension
        
        return name, extension
    
    def _remove_text(self, name: str, extension: str) -> Tuple[str, str]:
        """Удаление текста"""
        if self.remove_type == "chars":
            # Удаление N символов
            try:
                count = int(self.remove_start or "0")
                if self.position == "start":
                    new_name = name[count:] if count < len(name) else ""
                elif self.position == "end":
                    new_name = name[:-count] if count < len(name) else ""
                else:
                    new_name = name
                return new_name, extension
            except ValueError:
                return name, extension
        
        elif self.remove_type == "range":
            # Удаление по диапазону
            try:
                start = int(self.remove_start or "0")
                end = int(self.remove_end or str(len(name)))
                if 0 <= start < len(name) and start < end:
                    new_name = name[:start] + name[end:]
                else:
                    new_name = name
                return new_name, extension
            except ValueError:
                return name, extension
        
        # Удаление конкретного текста
        if self.text:
            new_name = name.replace(self.text, "")
            return new_name, extension
        
        return name, extension


class ReplaceMethod(ReFileMethod):
    """Метод замены текста"""
    
    def __init__(self, find: str, replace: str, case_sensitive: bool = False,
                 full_match: bool = False):
        """
        Args:
            find: Текст для поиска
            replace: Текст для замены
            case_sensitive: Учитывать регистр
            full_match: Только полное совпадение
        """
        self.find = find
        self.replace = replace
        self.case_sensitive = case_sensitive
        self.full_match = full_match
        # Кэшируем скомпилированный regex для регистронезависимой замены
        self._compiled_pattern = None
        if find and not case_sensitive and not full_match:
            try:
                self._compiled_pattern = re.compile(re.escape(find), re.IGNORECASE)
            except re.error:
                self._compiled_pattern = None
    
    def apply(self, name: str, extension: str, file_path: str) -> Tuple[str, str]:
        if not self.find:
            return name, extension
        
        if self.full_match:
            # Полное совпадение
            if self.case_sensitive:
                if name == self.find:
                    new_name = self.replace
                else:
                    new_name = name
            else:
                if name.lower() == self.find.lower():
                    new_name = self.replace
                else:
                    new_name = name
        else:
            # Частичное совпадение
            if self.case_sensitive:
                new_name = name.replace(self.find, self.replace)
            else:
                # Регистронезависимая замена - используем кэшированный паттерн
                if self._compiled_pattern:
                    new_name = self._compiled_pattern.sub(self.replace, name)
                else:
                    # Fallback, если компиляция не удалась
                    pattern = re.compile(re.escape(self.find), re.IGNORECASE)
                    new_name = pattern.sub(self.replace, name)
        
        return new_name, extension


class CaseMethod(ReFileMethod):
    """Метод изменения регистра"""
    
    def __init__(self, case_type: str, apply_to: str = "name"):
        """
        Args:
            case_type: "upper", "lower", "capitalize", "title"
            apply_to: "name", "ext", "all"
        """
        self.case_type = case_type
        self.apply_to = apply_to
    
    def apply(self, name: str, extension: str, file_path: str) -> Tuple[str, str]:
        new_name = name
        new_ext = extension
        
        if self.apply_to == "name" or self.apply_to == "all":
            if self.case_type == "upper":
                new_name = name.upper()
            elif self.case_type == "lower":
                new_name = name.lower()
            elif self.case_type == "capitalize":
                new_name = name.capitalize()
            elif self.case_type == "title":
                new_name = name.title()
        
        if self.apply_to == "ext" or self.apply_to == "all":
            if extension:
                if self.case_type == "upper":
                    new_ext = extension.upper()
                elif self.case_type == "lower":
                    new_ext = extension.lower()
                elif self.case_type == "capitalize":
                    new_ext = extension.capitalize()
                elif self.case_type == "title":
                    new_ext = extension.title()
        
        return new_name, new_ext


class NumberingMethod(ReFileMethod):
    """Метод нумерации файлов"""
    
    def __init__(
        self,
        start: int = 1,
        step: int = 1,
        digits: int = 3,
        format_str: str = "({n})",
        position: str = "end"
    ):
        """
        Args:
            start: Начальный индекс
            step: Шаг приращения
            digits: Количество цифр (с ведущими нулями)
            format_str: Формат номера (используйте {n} для номера)
            position: "start" или "end"
        """
        self.start = start
        self.step = step
        self.digits = digits
        self.format_str = format_str
        self.position = position
        self.current_number = start
    
    def apply(self, name: str, extension: str, file_path: str) -> Tuple[str, str]:
        # Форматирование номера с ведущими нулями
        number_str = str(self.current_number).zfill(self.digits)
        formatted_number = self.format_str.replace("{n}", number_str)
        
        # Добавление номера
        if self.position == "start":
            new_name = formatted_number + name
        else:  # end
            new_name = name + formatted_number
        
        # Увеличение номера для следующего файла
        self.current_number += self.step
        
        return new_name, extension
    
    def reset(self) -> None:
        """Сброс счетчика (вызывается перед применением к новому списку)."""
        self.current_number = self.start


class MetadataMethod(ReFileMethod):
    """Метод вставки метаданных"""
    
    def __init__(self, tag: str, position: str = "end", extractor=None):
        """
        Args:
            tag: Тег метаданных (например, "{width}x{height}")
            position: "start" или "end"
            extractor: Экземпляр MetadataExtractor
        """
        self.tag = tag
        self.position = position
        self.extractor = extractor
    
    def apply(self, name: str, extension: str, file_path: str) -> Tuple[str, str]:
        if not self.extractor:
            return name, extension
        
        # Извлечение метаданных
        metadata_value = self.extractor.extract(self.tag, file_path)
        
        if metadata_value:
            if self.position == "start":
                new_name = metadata_value + name
            else:  # end
                new_name = name + metadata_value
        else:
            new_name = name
        
        return new_name, extension


class RegexMethod(ReFileMethod):
    """Метод переименования с использованием регулярных выражений"""
    
    def __init__(self, pattern: str, replace: str):
        """
        Args:
            pattern: Регулярное выражение
            replace: Строка замены (может содержать группы \1, \2 и т.д.)
        """
        self.pattern = pattern
        self.replace = replace
        self.compiled_pattern = None
        
        if pattern:
            try:
                self.compiled_pattern = re.compile(pattern)
            except re.error:
                self.compiled_pattern = None
    
    def apply(self, name: str, extension: str, file_path: str) -> Tuple[str, str]:
        if not self.compiled_pattern:
            return name, extension
        
        try:
            new_name = self.compiled_pattern.sub(self.replace, name)
            return new_name, extension
        except Exception as e:
            logger.warning(f"Ошибка применения regex паттерна '{self.pattern}': {e}")
            return name, extension


class NewNameMethod(ReFileMethod):
    """Метод полной замены имени по шаблону"""
    
    def __init__(self, template: str, metadata_extractor=None, file_number: int = 1, zeros_count: int = 0):
        """
        Args:
            template: Шаблон нового имени (может содержать {name}, {ext}, {n}, 
                     {width}x{height}, {date_created} и т.д.)
            metadata_extractor: Экстрактор метаданных
            file_number: Начальный номер файла (для {n})
            zeros_count: Количество ведущих нулей для {n} (например, 3 для 001, 002)
        """
        self.template = template
        self.metadata_extractor = metadata_extractor
        self.start_number = file_number
        self.file_number = file_number
        self.zeros_count = zeros_count
        # Предварительно определяем, какие метаданные теги используются в шаблоне
        self.required_metadata_tags = self._detect_metadata_tags(template)
    
    def _detect_metadata_tags(self, template: str) -> set:
        """Определение используемых тегов метаданных в шаблоне"""
        metadata_tags = {
            "{width}x{height}", "{width}", "{height}", 
            "{date}", "{date_created}", "{date_modified}", "{date_created_time}", "{date_modified_time}",
            "{year}", "{month}", "{day}", "{hour}", "{minute}", "{second}",
            "{file_size}", "{filename}", "{dirname}", "{parent_dir}", "{format}",
            "{artist}", "{title}", "{album}", "{audio_year}", "{track}", "{genre}",
            "{duration}", "{bitrate}",
            "{camera}", "{iso}", "{focal_length}", "{aperture}", "{exposure_time}"
        }
        found_tags = set()
        for tag in metadata_tags:
            if tag in template:
                found_tags.add(tag)
        return found_tags
    
    def apply(self, name: str, extension: str, file_path: str) -> Tuple[str, str]:
        """Применение шаблона для создания нового имени"""
        if not self.template:
            return name, extension
        
        # Начинаем с шаблона - он полностью заменяет имя, если нет {name}
        new_name = self.template
        
        # Заменяем переменные в фигурных скобках
        # {ext} - расширение (без точки)
        ext_without_dot = extension.lstrip('.') if extension else ""
        new_name = new_name.replace("{ext}", ext_without_dot)
        
        # {n} - номер файла (с поддержкой ведущих нулей)
        if self.zeros_count > 0:
            # Форматирование с ведущими нулями
            formatted_number = f"{self.file_number:0{self.zeros_count}d}"
            new_name = new_name.replace("{n}", formatted_number)
        else:
            # Простая замена {n} без ведущих нулей
            new_name = new_name.replace("{n}", str(self.file_number))
        
        # Метаданные (если доступны) - используем предварительно определенные теги
        if self.metadata_extractor and self.required_metadata_tags:
            # Извлекаем все необходимые метаданные за один проход
            metadata_values = {}
            for tag in self.required_metadata_tags:
                value = self.metadata_extractor.extract(tag, file_path)
                metadata_values[tag] = value or ""
            
            # Заменяем все теги одним проходом
            for tag, value in metadata_values.items():
                new_name = new_name.replace(tag, value)
        
        # Условная логика в шаблонах: {if:condition:then:else}
        # Пример: {if:{ext}==jpg:IMG_{n}:FILE_{n}}
        import re as regex_module
        conditional_pattern = r'\{if:([^:]+):([^:]+):([^}]+)\}'
        matches = regex_module.finditer(conditional_pattern, new_name)
        for match in reversed(list(matches)):  # Обратный порядок для корректной замены
            condition = match.group(1)
            then_part = match.group(2)
            else_part = match.group(3)
            
            # Вычисляем условие (простая проверка равенства)
            result = False
            if '==' in condition:
                parts = condition.split('==', 1)
                left = parts[0].strip().strip('"\'')
                right = parts[1].strip().strip('"\'')
                # Подставляем переменные
                left = self._substitute_variables(left, name, extension, file_path)
                result = left == right
            elif '!=' in condition:
                parts = condition.split('!=', 1)
                left = parts[0].strip().strip('"\'')
                right = parts[1].strip().strip('"\'')
                left = self._substitute_variables(left, name, extension, file_path)
                result = left != right
            elif 'in' in condition:
                parts = condition.split(' in ', 1)
                left = parts[0].strip().strip('"\'')
                right = parts[1].strip().strip('"\'')
                left = self._substitute_variables(left, name, extension, file_path)
                right = self._substitute_variables(right, name, extension, file_path)
                result = left in right
            else:
                # Простая проверка на существование/непустоту
                var = self._substitute_variables(condition, name, extension, file_path)
                result = bool(var and str(var).strip())
            
            # Подставляем результат
            if result:
                replacement = then_part
            else:
                replacement = else_part
            
            # Подставляем переменные в результат
            replacement = self._substitute_variables(replacement, name, extension, file_path)
            new_name = new_name[:match.start()] + replacement + new_name[match.end():]
        
        # Замена {name} в самом конце (если есть в шаблоне)
        # Если {name} нет в шаблоне, то шаблон полностью заменяет имя
        if "{name}" in new_name:
            new_name = new_name.replace("{name}", name)
        
        # Увеличение номера для следующего файла
        self.file_number += 1
        
        return new_name, extension
    
    def _substitute_variables(self, text: str, name: str, extension: str, file_path: str) -> str:
        """Подстановка переменных в текст.
        
        Args:
            text: Текст с переменными
            name: Имя файла
            extension: Расширение
            file_path: Путь к файлу
            
        Returns:
            Текст с подставленными переменными
        """
        result = text
        ext_without_dot = extension.lstrip('.') if extension else ""
        result = result.replace("{ext}", ext_without_dot)
        result = result.replace("{name}", name)
        
        if self.metadata_extractor:
            # Подставляем метаданные
            for tag in ["{width}", "{height}", "{date}", "{date_created}", "{date_modified}", 
                       "{date_created_time}", "{date_modified_time}",
                       "{year}", "{month}", "{day}", "{hour}", "{minute}", "{second}",
                       "{file_size}", "{filename}", "{dirname}", "{parent_dir}", "{format}",
                       "{artist}", "{title}", "{album}", "{audio_year}", "{track}", "{genre}",
                       "{duration}", "{bitrate}",
                       "{camera}", "{iso}", "{focal_length}", "{aperture}", "{exposure_time}"]:
                if tag in result:
                    value = self.metadata_extractor.extract(tag, file_path)
                    result = result.replace(tag, value or "")
        
        return result
    
    def reset(self) -> None:
        """Сброс счетчика (вызывается перед применением к новому списку)."""
        self.file_number = self.start_number


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
    
    def execute_script(self, script_path: str, context: dict) -> Optional[Any]:
        """Выполнение скрипта.
        
        Args:
            script_path: Путь к скрипту
            context: Контекст выполнения (file_data, methods и т.д.)
            
        Returns:
            Результат выполнения скрипта или None
        """
        import os
        from typing import Any, Optional
        
        if not os.path.exists(script_path):
            logger.error(f"Скрипт не найден: {script_path}")
            return None
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_code = f.read()
            
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
            
            # Выполняем скрипт
            exec(script_code, safe_globals)
            
            # Возвращаем результат, если есть функция main
            if 'main' in safe_globals and callable(safe_globals['main']):
                return safe_globals['main']()
            
            return None
        except Exception as e:
            logger.error(f"Ошибка выполнения скрипта {script_path}: {e}", exc_info=True)
            return None
    
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
            
            # Компилируем для проверки синтаксиса
            compile(script_code, script_path, 'exec')
            return True, None
        except SyntaxError as e:
            return False, f"Синтаксическая ошибка: {e}"
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
        path_cache = {os.path.normpath(os.path.abspath(f.get('full_path') or f.get('path', '')))
                     for f in files_list if f.get('full_path') or f.get('path')}
    
    if normalized_path in path_cache or normalized_path in _path_cache:
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
    
    Args:
        files_list: Список файлов для проверки
    """
    # Создаем словарь для подсчета одинаковых имен
    name_counts = {}
    for file_data in files_list:
        full_name = file_data['new_name'] + file_data['extension']
        if full_name not in name_counts:
            name_counts[full_name] = []
        name_counts[full_name].append(file_data)
    
    # Помечаем конфликты
    for full_name, file_list in name_counts.items():
        if len(file_list) > 1:
            # Есть конфликт
            for file_data in file_list:
                file_data['status'] = f"Конфликт: {len(file_list)} файла с именем '{full_name}'"


def re_file_files_thread(
    files_to_rename: List[Dict],
    callback: Callable[[int, int, List[Dict]], None],
    log_callback: Optional[Callable[[str], None]] = None,
    backup_manager: Optional[BackupManager] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    cancel_var: Optional[threading.Event] = None
) -> None:
    """Re-file операции с файлами в отдельном потоке.
    
    Args:
        files_to_rename: Список файлов для переименования
        callback: Функция обратного вызова после завершения
        log_callback: Функция для логирования (опционально)
        backup_manager: Менеджер резервных копий (опционально)
        progress_callback: Функция для обновления прогресса (current, total, filename)
        cancel_var: Событие для отмены операции (опционально)
    """
    def re_file_worker():
        success_count = 0
        error_count = 0
        renamed_files = []
        total = len(files_to_rename)
        
        logger.info(f"re_file_worker начал работу: {total} файлов для обработки")
        
        try:
            # Создаем резервные копии, если включено
            backups = {}
            if backup_manager and HAS_BACKUP:
                try:
                    backups = backup_manager.create_backups(files_to_rename)
                    if backups and log_callback:
                        log_callback(f"Создано резервных копий: {len(backups)}")
                except Exception as e:
                    logger.error(f"Ошибка при создании резервных копий: {e}")
                    if log_callback:
                        log_callback(f"Предупреждение: не удалось создать резервные копии")
            
            for i, file_data in enumerate(files_to_rename):
                # Проверка отмены
                if cancel_var and cancel_var.is_set():
                    if log_callback:
                        log_callback("Операция переименования отменена пользователем")
                    break
                old_path = None
                new_path = None
                try:
                    # Поддержка как словарей, так и FileInfo объектов
                    if hasattr(file_data, 'full_path'):
                        # FileInfo объект
                        old_path = file_data.full_path or str(file_data.path)
                        is_folder = (file_data.metadata and file_data.metadata.get('is_folder', False)) if hasattr(file_data, 'metadata') else False
                    else:
                        # Словарь
                        old_path = file_data.get('full_path') or file_data.get('path')
                        is_folder = file_data.get('is_folder', False) or (
                            file_data.get('metadata', {}).get('is_folder', False) if isinstance(file_data.get('metadata'), dict) else False
                        )
                    
                    if not old_path:
                        error_msg = "Не указан путь к файлу/папке"
                        if log_callback:
                            log_callback(f"Ошибка: {error_msg}")
                        if hasattr(file_data, 'set_error'):
                            file_data.set_error(error_msg)
                        else:
                            file_data['status'] = f"Ошибка: {error_msg}"
                        error_count += 1
                        continue
                    
                    # Нормализуем путь
                    old_path = os.path.normpath(old_path)
                    
                    # Проверяем существование исходного файла/папки (объединяем проверки)
                    try:
                        if not os.path.exists(old_path):
                            item_type = "папка" if is_folder else "файл"
                            error_msg = f"Исходный {item_type} не найден: {os.path.basename(old_path)}"
                            if log_callback:
                                log_callback(f"Ошибка: {error_msg}")
                            file_data['status'] = f"Ошибка: {error_msg}"
                            error_count += 1
                            continue
                        # Проверяем, что это действительно файл или папка (но не что-то другое)
                        if not (os.path.isfile(old_path) or os.path.isdir(old_path)):
                            item_type = "папка" if is_folder else "файл"
                            error_msg = f"Путь не является {item_type}: {os.path.basename(old_path)}"
                            if log_callback:
                                log_callback(f"Ошибка: {error_msg}")
                            file_data['status'] = f"Ошибка: {error_msg}"
                            error_count += 1
                            continue
                        # Если это папка, но путь указывает на файл (или наоборот)
                        if is_folder and not os.path.isdir(old_path):
                            error_msg = f"Путь указывает на файл, а не на папку: {os.path.basename(old_path)}"
                            if log_callback:
                                log_callback(f"Ошибка: {error_msg}")
                            file_data['status'] = f"Ошибка: {error_msg}"
                            error_count += 1
                            continue
                        if not is_folder and not os.path.isfile(old_path):
                            error_msg = f"Путь указывает на папку, а не на файл: {os.path.basename(old_path)}"
                            if log_callback:
                                log_callback(f"Ошибка: {error_msg}")
                            file_data['status'] = f"Ошибка: {error_msg}"
                            error_count += 1
                            continue
                    except (OSError, ValueError):
                        item_type = "папка" if is_folder else "файл"
                        error_msg = f"Исходный {item_type} не найден: {os.path.basename(old_path)}"
                        if log_callback:
                            log_callback(f"Ошибка: {error_msg}")
                        file_data['status'] = f"Ошибка: {error_msg}"
                        error_count += 1
                        continue
                    
                    # Получаем new_name и extension
                    if hasattr(file_data, 'new_name'):
                        # FileInfo объект
                        new_name = file_data.new_name
                        extension = '' if is_folder else file_data.extension
                    else:
                        # Словарь
                        new_name = file_data.get('new_name', '')
                        extension = '' if is_folder else file_data.get('extension', '')
                    
                    # Валидация нового имени
                    if not new_name or not new_name.strip():
                        item_type = "папки" if is_folder else "файла"
                        error_msg = f"Пустое имя {item_type}"
                        if log_callback:
                            log_callback(f"Ошибка: {error_msg}")
                        if hasattr(file_data, 'set_error'):
                            file_data.set_error(error_msg)
                        else:
                            file_data['status'] = f"Ошибка: {error_msg}"
                        error_count += 1
                        continue
                    
                    # Получаем директорию и создаем новый путь
                    directory = os.path.dirname(old_path)
                    # Для папок extension пустой, для файлов используем extension
                    new_path = os.path.join(directory, new_name + extension)
                    new_path = os.path.normpath(new_path)
                    
                    # Проверяем, что новый путь отличается от старого
                    if old_path == new_path:
                        item_type = "папка" if is_folder else "файл"
                        if log_callback:
                            log_callback(f"Без изменений: '{os.path.basename(old_path)}' ({item_type})")
                        success_count += 1
                        continue
                    
                    # Переименовываем файл/папку (os.rename работает и для папок тоже)
                    # os.rename атомарен и сам проверит существование, поэтому объединяем проверку и переименование
                    try:
                        # Проверяем существование нового пути перед переименованием
                        # Это оптимизация - избегаем лишних вызовов os.path.exists
                        if os.path.exists(new_path):
                            item_type = "папка" if is_folder else "файл"
                            item_name = new_name if is_folder else new_name + extension
                            error_msg = f"{item_type.capitalize()} '{item_name}' уже существует"
                            if log_callback:
                                log_callback(f"Ошибка: {error_msg}")
                            file_data['status'] = f"Ошибка: {error_msg}"
                            error_count += 1
                            continue
                        
                        # Выполняем переименование (атомарная операция)
                        # Если файл уже существует, это вызовет FileExistsError
                        os.rename(old_path, new_path)
                    except FileExistsError:
                        # Race condition: файл был создан между проверкой и переименованием
                        item_type = "папка" if is_folder else "файл"
                        item_name = new_name if is_folder else new_name + extension
                        error_msg = f"{item_type.capitalize()} '{item_name}' уже существует (race condition)"
                        if log_callback:
                            log_callback(f"Ошибка: {error_msg}")
                        file_data['status'] = f"Ошибка: {error_msg}"
                        error_count += 1
                        logger.warning(f"Race condition при переименовании {old_path} -> {new_path}")
                        continue
                    except OSError as rename_error:
                        # Другие ошибки файловой системы
                        item_type = "папка" if is_folder else "файл"
                        # Проверяем, что исходный файл/папка все еще существует
                        try:
                            if not os.path.exists(old_path):
                                error_msg = f"Исходный {item_type} был удален при переименовании: {os.path.basename(old_path)}"
                            else:
                                error_msg = f"Ошибка переименования: {str(rename_error)}"
                        except (OSError, ValueError):
                            error_msg = f"Ошибка переименования: {str(rename_error)}"
                        if log_callback:
                            log_callback(f"Ошибка: {error_msg}")
                        file_data['status'] = f"Ошибка: {error_msg}"
                        error_count += 1
                        logger.error(f"Ошибка переименования {old_path} -> {new_path}: {rename_error}", exc_info=True)
                        continue
                    
                    # Обновляем путь в данных файла/папки
                    if hasattr(file_data, 'path'):
                        # FileInfo объект
                        from pathlib import Path
                        file_data.path = Path(new_path)
                        file_data.full_path = new_path
                        file_data.old_name = new_name
                    else:
                        # Словарь
                        file_data['path'] = new_path
                        file_data['full_path'] = new_path
                        file_data['old_name'] = new_name
                    
                    renamed_files.append(file_data)
                    success_count += 1
                    
                    item_name = new_name if is_folder else new_name + extension
                    if log_callback:
                        log_callback(f"Переименован {item_type}: '{os.path.basename(old_path)}' -> '{item_name}'")
                        
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Ошибка при переименовании '{file_data.get('old_name', 'unknown')}': {error_msg}", exc_info=True)
                    if log_callback:
                        log_callback(f"Ошибка при переименовании '{file_data.get('old_name', 'unknown')}': {error_msg}")
                    file_data['status'] = f"Ошибка: {error_msg}"
                    error_count += 1
                    # Проверяем, что исходный файл все еще существует (опционально, только для логирования)
                    if old_path:
                        try:
                            if os.path.exists(old_path) and log_callback:
                                log_callback(f"Исходный файл сохранен: {os.path.basename(old_path)}")
                        except (OSError, ValueError):
                            pass
                    
                    # Обновление прогресса даже при ошибке
                    if progress_callback:
                        try:
                            progress_callback(i + 1, total, file_data.get('old_name', 'unknown'))
                        except Exception:
                            pass
        except Exception as e:
            # Критическая ошибка - логируем и продолжаем
            logger.error(f"Критическая ошибка в re_file_worker: {e}", exc_info=True)
            if log_callback:
                log_callback(f"Критическая ошибка: {e}")
        finally:
            # Всегда вызываем callback, даже при ошибках
            logger.info(f"re_file_worker завершает работу: успешно {success_count}, ошибок {error_count}")
            if callback:
                try:
                    logger.debug(f"Вызов callback с результатами: success={success_count}, error={error_count}, files={len(renamed_files)}")
                    callback(success_count, error_count, renamed_files)
                    logger.debug("Callback успешно выполнен")
                except Exception as callback_error:
                    logger.error(f"Ошибка при вызове callback: {callback_error}", exc_info=True)
            else:
                logger.warning("Callback не предоставлен, результат не будет передан")
    
    # Запускаем worker в отдельном потоке
    try:
        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="re_file_files")
        future = executor.submit(re_file_worker)
        executor.shutdown(wait=False)  # Не ждем завершения, поток daemon
        
        # Добавляем таймаут для защиты от зависания
        def check_completion():
            """Проверка завершения операции через 10 секунд"""
            import time
            time.sleep(10)
            if not future.done():
                logger.warning("Операция re_file_worker не завершилась за 10 секунд, возможно зависание")
        
        # Запускаем проверку в отдельном потоке (не блокируем основной)
        import threading
        timeout_thread = threading.Thread(target=check_completion, daemon=True)
        timeout_thread.start()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске re_file_worker: {e}", exc_info=True)
        # Если не удалось запустить worker, вызываем callback с ошибкой
        if callback:
            try:
                callback(0, len(files_to_rename), [])
            except Exception as callback_error:
                logger.error(f"Ошибка при вызове callback после ошибки запуска: {callback_error}", exc_info=True)


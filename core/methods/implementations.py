"""Реализации методов re-file операций.

Содержит конкретные классы методов переименования:
- AddRemoveMethod: добавление/удаление текста
- ReplaceMethod: замена текста
- CaseMethod: изменение регистра
- NumberingMethod: нумерация файлов
- MetadataMethod: вставка метаданных
- RegexMethod: регулярные выражения
- NewNameMethod: полная замена имени по шаблону
"""

import logging
import re
from typing import Optional, Tuple

from .base import ReFileMethod

logger = logging.getLogger(__name__)


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
            new_name = self.text + name
            return new_name, extension
        elif self.position == "after":
            new_name = name + self.text
            return new_name, extension
        elif self.position == "start":
            new_name = self.text + name
            return new_name, extension
        elif self.position == "end":
            new_name = name + self.text
            return new_name, extension
        
        return name, extension
    
    def _remove_text(self, name: str, extension: str) -> Tuple[str, str]:
        """Удаление текста"""
        if self.remove_type == "chars":
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
        
        # {n} или {n:start:zeros} - номер файла (с поддержкой параметров в шаблоне)
        n_pattern = re.compile(r'\{n(?::(\d+)(?::(\d+))?)?\}')
        
        def replace_n(match):
            """Замена {n} или {n:start:zeros} на номер"""
            start_str = match.group(1)
            zeros_str = match.group(2)
            
            # Если указаны параметры в шаблоне, используем их
            if start_str is not None:
                try:
                    custom_start = int(start_str)
                    offset = self.file_number - self.start_number
                    current_num = custom_start + offset
                except ValueError:
                    current_num = self.file_number
            else:
                current_num = self.file_number
            
            # Если указано количество нулей в шаблоне, используем его
            if zeros_str is not None:
                try:
                    custom_zeros = int(zeros_str)
                    if custom_zeros > 0:
                        return f"{current_num:0{custom_zeros}d}"
                    else:
                        return str(current_num)
                except ValueError:
                    zeros = self.zeros_count
                    if zeros > 0:
                        return f"{current_num:0{zeros}d}"
                    else:
                        return str(current_num)
            else:
                zeros = self.zeros_count
                if zeros > 0:
                    return f"{current_num:0{zeros}d}"
                else:
                    return str(current_num)
        
        # Заменяем все вхождения {n} или {n:start:zeros} за один проход
        new_name = n_pattern.sub(replace_n, new_name)
        
        # Метаданные (если доступны)
        if self.metadata_extractor and self.required_metadata_tags:
            metadata_values = {}
            for tag in self.required_metadata_tags:
                value = self.metadata_extractor.extract(tag, file_path)
                metadata_values[tag] = value or ""
            
            for tag, value in metadata_values.items():
                new_name = new_name.replace(tag, value)
        
        # Условная логика в шаблонах: {if:condition:then:else}
        conditional_pattern = r'\{if:([^:]+):([^:]+):([^}]+)\}'
        matches = re.finditer(conditional_pattern, new_name)
        for match in reversed(list(matches)):
            condition = match.group(1)
            then_part = match.group(2)
            else_part = match.group(3)
            
            result = False
            if '==' in condition:
                parts = condition.split('==', 1)
                left = parts[0].strip().strip('"\'')
                right = parts[1].strip().strip('"\'')
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
                var = self._substitute_variables(condition, name, extension, file_path)
                result = bool(var and str(var).strip())
            
            replacement = then_part if result else else_part
            replacement = self._substitute_variables(replacement, name, extension, file_path)
            if '{n' in replacement:
                replacement = n_pattern.sub(replace_n, replacement)
            new_name = new_name[:match.start()] + replacement + new_name[match.end():]
        
        # Замена {name} в самом конце (если есть в шаблоне)
        if "{name}" in new_name:
            new_name = new_name.replace("{name}", name)
        
        # Увеличение номера для следующего файла
        self.file_number += 1
        
        return new_name, extension
    
    def _substitute_variables(self, text: str, name: str, extension: str, file_path: str) -> str:
        """Подстановка переменных в текст."""
        result = text
        ext_without_dot = extension.lstrip('.') if extension else ""
        result = result.replace("{ext}", ext_without_dot)
        result = result.replace("{name}", name)
        
        if self.metadata_extractor:
            for tag in ["{width}", "{height}", "{date}", "{date_created}", "{date_modified}", 
                       "{date_created_time}", "{date_modified_time}",
                       "{year}", "{month}", "{day}", "{hour}", "{minute}", "{second}",
                       "{file_size}", "{filename}", "{dirname}", "{parent_dir}", "{format}",
                       "{duration}", "{bitrate}",
                       "{camera}", "{iso}", "{focal_length}", "{aperture}", "{exposure_time}"]:
                if tag in result:
                    value = self.metadata_extractor.extract(tag, file_path)
                    result = result.replace(tag, value or "")
        
        return result
    
    def reset(self) -> None:
        """Сброс счетчика (вызывается перед применением к новому списку)."""
        self.file_number = self.start_number


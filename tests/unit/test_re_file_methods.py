"""Тесты для методов re-file."""

import os
import pytest
from core.re_file_methods import (
    AddRemoveMethod,
    ReplaceMethod,
    CaseMethod,
    NumberingMethod,
    RegexMethod,
    validate_filename
)


class TestAddRemoveMethod:
    """Тесты для метода добавления/удаления текста."""
    
    def test_add_text_before(self):
        """Тест: добавление текста перед именем."""
        method = AddRemoveMethod(operation="add", text="prefix_", position="before")
        name, ext = method.apply("file", ".txt", "/path/to/file.txt")
        assert name == "prefix_file"
        assert ext == ".txt"
    
    def test_add_text_after(self):
        """Тест: добавление текста после имени."""
        method = AddRemoveMethod(operation="add", text="_suffix", position="after")
        name, ext = method.apply("file", ".txt", "/path/to/file.txt")
        assert name == "file_suffix"
        assert ext == ".txt"
    
    def test_remove_text_chars(self):
        """Тест: удаление символов."""
        method = AddRemoveMethod(
            operation="remove",
            remove_type="chars",
            remove_start="3",
            position="start"
        )
        name, ext = method.apply("filename", ".txt", "/path/to/filename.txt")
        assert name == "ename"  # Удаляем 3 символа с начала: "fil" -> остается "ename"
        assert ext == ".txt"
    
    def test_remove_text_range(self):
        """Тест: удаление диапазона символов."""
        method = AddRemoveMethod(
            operation="remove",
            remove_type="range",
            remove_start="2",
            remove_end="5"
        )
        name, ext = method.apply("filename", ".txt", "/path/to/filename.txt")
        # Удаляем символы с индекса 2 до 5: "len" -> остается "fiamme" -> "fiamme"
        # filename[0:2] + filename[5:] = "fi" + "ame" = "fiame"
        assert name == "fiame"
        assert ext == ".txt"


class TestReplaceMethod:
    """Тесты для метода замены текста."""
    
    def test_replace_simple(self):
        """Тест: простая замена."""
        method = ReplaceMethod(find="old", replace="new")
        name, ext = method.apply("oldfile", ".txt", "/path/to/oldfile.txt")
        assert name == "newfile"
        assert ext == ".txt"
    
    def test_replace_case_sensitive(self):
        """Тест: замена с учетом регистра."""
        method = ReplaceMethod(find="OLD", replace="new", case_sensitive=True)
        name, ext = method.apply("oldfile", ".txt", "/path/to/oldfile.txt")
        assert name == "oldfile"  # Не заменится, т.к. регистр не совпадает
        assert ext == ".txt"
    
    def test_replace_case_insensitive(self):
        """Тест: замена без учета регистра."""
        method = ReplaceMethod(find="OLD", replace="new", case_sensitive=False)
        name, ext = method.apply("oldfile", ".txt", "/path/to/oldfile.txt")
        assert name == "newfile"
        assert ext == ".txt"
    
    def test_replace_regex(self):
        """Тест: замена с использованием регулярных выражений."""
        # ReplaceMethod не поддерживает regex напрямую, используем RegexMethod
        from core.re_file_methods import RegexMethod
        method = RegexMethod(pattern=r"\d+", replace="NUM")
        name, ext = method.apply("file123", ".txt", "/path/to/file123.txt")
        assert name == "fileNUM"
        assert ext == ".txt"


class TestCaseMethod:
    """Тесты для метода изменения регистра."""
    
    def test_case_upper(self):
        """Тест: преобразование в верхний регистр."""
        method = CaseMethod(case_type="upper")
        name, ext = method.apply("filename", ".txt", "/path/to/filename.txt")
        assert name == "FILENAME"
        assert ext == ".txt"
    
    def test_case_lower(self):
        """Тест: преобразование в нижний регистр."""
        method = CaseMethod(case_type="lower")
        name, ext = method.apply("FILENAME", ".txt", "/path/to/FILENAME.txt")
        assert name == "filename"
        assert ext == ".txt"
    
    def test_case_title(self):
        """Тест: преобразование в title case."""
        method = CaseMethod(case_type="title")
        name, ext = method.apply("file name", ".txt", "/path/to/file name.txt")
        assert name == "File Name"
        assert ext == ".txt"


class TestNumberingMethod:
    """Тесты для метода нумерации."""
    
    def test_numbering_simple(self):
        """Тест: простая нумерация."""
        method = NumberingMethod(start=1, step=1, digits=1, format_str="_{n}")
        name, ext = method.apply("file", ".txt", "/path/to/file.txt")
        assert name == "file_1"
        assert ext == ".txt"
    
    def test_numbering_with_zeros(self):
        """Тест: нумерация с ведущими нулями."""
        method = NumberingMethod(start=1, step=1, digits=3, format_str="_{n}")
        name, ext = method.apply("file", ".txt", "/path/to/file.txt")
        assert name == "file_001"
        assert ext == ".txt"
    
    def test_numbering_custom_start(self):
        """Тест: нумерация с кастомным началом."""
        method = NumberingMethod(start=10, step=5, digits=1, format_str="-{n}")
        name, ext = method.apply("file", ".txt", "/path/to/file.txt")
        assert name == "file-10"
        assert ext == ".txt"


class TestValidateFilename:
    """Тесты для валидации имен файлов."""
    
    def test_validate_filename_valid(self):
        """Тест: валидное имя файла."""
        result = validate_filename("valid_file_name", ".txt", "/path/to/file.txt", 0)
        assert result == "Готов"
        result = validate_filename("file123", ".txt", "/path/to/file.txt", 0)
        assert result == "Готов"
        result = validate_filename("file-name", ".txt", "/path/to/file.txt", 0)
        assert result == "Готов"
    
    def test_validate_filename_invalid_chars(self):
        """Тест: имя с недопустимыми символами."""
        result = validate_filename("file<name>", ".txt", "/path/to/file.txt", 0)
        assert "Ошибка" in result
        result = validate_filename("file:name", ".txt", "/path/to/file.txt", 0)
        assert "Ошибка" in result
        result = validate_filename("file|name", ".txt", "/path/to/file.txt", 0)
        assert "Ошибка" in result
    
    def test_validate_filename_reserved_names(self):
        """Тест: зарезервированные имена Windows."""
        if os.name == 'nt':  # Только на Windows
            result = validate_filename("CON", ".txt", "/path/to/file.txt", 0)
            assert "Ошибка" in result
            result = validate_filename("PRN", ".txt", "/path/to/file.txt", 0)
            assert "Ошибка" in result
            result = validate_filename("COM1", ".txt", "/path/to/file.txt", 0)
            assert "Ошибка" in result
    
    def test_validate_filename_empty(self):
        """Тест: пустое имя файла."""
        result = validate_filename("", ".txt", "/path/to/file.txt", 0)
        assert "Ошибка" in result
        result = validate_filename("", ".txt", "/path/to/file.txt", 0)
        assert "Ошибка" in result  # Только расширение
    
    def test_validate_filename_too_long(self):
        """Тест: слишком длинное имя файла."""
        long_name = "a" * 300
        result = validate_filename(long_name, ".txt", "/path/to/file.txt", 0)
        assert "Ошибка" in result


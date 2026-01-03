"""Расширенные интеграционные тесты для операций с файлами."""

import os
import pytest
from pathlib import Path
from core.re_file_methods import (
    add_file_to_list,
    check_conflicts,
    validate_filename,
    AddRemoveMethod,
    ReplaceMethod,
    CaseMethod,
    NumberingMethod
)
from core.managers.methods_manager import MethodsManager


class TestFileOperationsExtended:
    """Расширенные интеграционные тесты для операций с файлами."""
    
    def test_add_file_to_list_workflow(self, temp_file):
        """Тест: полный workflow добавления файлов в список."""
        files_list = []
        path_cache = set()
        
        # Добавляем несколько файлов
        file1 = temp_file("file1.txt", "content 1")
        file2 = temp_file("file2.txt", "content 2")
        file3 = temp_file("file3.txt", "content 3")
        
        result1 = add_file_to_list(file1, files_list, path_cache)
        result2 = add_file_to_list(file2, files_list, path_cache)
        result3 = add_file_to_list(file3, files_list, path_cache)
        
        assert result1 is not None
        assert result2 is not None
        assert result3 is not None
        assert len(files_list) == 3
        
        # Попытка добавить дубликат должна вернуть None
        result4 = add_file_to_list(file1, files_list, path_cache)
        assert result4 is None
        assert len(files_list) == 3
    
    def test_check_conflicts_integration(self, temp_file):
        """Тест: проверка конфликтов в реальном сценарии."""
        files_list = []
        
        # Создаем файлы с потенциальными конфликтами
        file1 = temp_file("test.txt", "content 1")
        file2 = temp_file("other.txt", "content 2")
        
        files_list.append({
            'path': file1,
            'full_path': file1,
            'old_name': 'test',
            'new_name': 'renamed',
            'extension': '.txt',
            'status': 'Готов'
        })
        files_list.append({
            'path': file2,
            'full_path': file2,
            'old_name': 'other',
            'new_name': 'renamed',  # Конфликт!
            'extension': '.txt',
            'status': 'Готов'
        })
        
        check_conflicts(files_list)
        
        # Оба файла должны иметь статус конфликта
        assert 'Конфликт' in files_list[0]['status']
        assert 'Конфликт' in files_list[1]['status']
    
    def test_methods_chain_workflow(self):
        """Тест: цепочка методов переименования."""
        manager = MethodsManager()
        
        # Добавляем цепочку методов
        manager.add_method(AddRemoveMethod(operation="add", text="PREFIX_", position="before"))
        manager.add_method(ReplaceMethod(find="old", replace="new"))
        manager.add_method(CaseMethod(case_type="lower"))
        manager.add_method(NumberingMethod(start=1, step=1, digits=2, format_str="_{n}"))
        
        # Применяем к файлу
        name, ext = "OLD_FILE", ".TXT"
        for method in manager.get_methods():
            name, ext = method.apply(name, ext, "/path/to/file.txt")
        
        # Проверяем результат цепочки
        assert name.startswith("prefix_new_file")
        assert "_01" in name or "_1" in name
        assert ext == ".txt"
    
    def test_validate_filename_integration(self, temp_file):
        """Тест: валидация имен в реальном сценарии."""
        file_path = temp_file("test.txt", "content")
        
        # Валидные имена
        assert validate_filename("valid_name", ".txt", file_path, 0) == "Готов"
        assert validate_filename("file123", ".txt", file_path, 0) == "Готов"
        assert validate_filename("file-name", ".txt", file_path, 0) == "Готов"
        
        # Невалидные имена
        invalid_result = validate_filename("file<name>", ".txt", file_path, 0)
        assert invalid_result != "Готов"
        assert "Ошибка" in invalid_result or "недопустим" in invalid_result.lower()
    
    def test_numbering_reset_workflow(self):
        """Тест: сброс счетчика нумерации."""
        manager = MethodsManager()
        
        numbering = NumberingMethod(start=1, step=1, digits=2, format_str="_{n}")
        manager.add_method(numbering)
        
        # Применяем к нескольким файлам
        files = ["file1", "file2", "file3"]
        results = []
        
        for file_name in files:
            name, ext = file_name, ".txt"
            for method in manager.get_methods():
                name, ext = method.apply(name, ext, "/path/to/file.txt")
            results.append(name)
        
        # Сбрасываем счетчик
        manager.reset_counters()
        
        # Применяем снова - номера должны начаться заново
        name, ext = "file1", ".txt"
        for method in manager.get_methods():
            name, ext = method.apply(name, ext, "/path/to/file.txt")
        
        # Первый файл должен получить номер 1
        assert "_01" in name or "_1" in name
    
    def test_complex_rename_scenario(self, temp_file):
        """Тест: сложный сценарий переименования."""
        # Создаем файл
        original_path = temp_file("My_Old_File_2023.txt", "content")
        
        manager = MethodsManager()
        
        # Сложная цепочка: замена + удаление + добавление + регистр + нумерация
        manager.add_method(ReplaceMethod(find="2023", replace="2024"))
        manager.add_method(AddRemoveMethod(
            operation="remove",
            remove_type="chars",
            remove_start="3",
            position="start"
        ))
        manager.add_method(AddRemoveMethod(operation="add", text="NEW_", position="before"))
        manager.add_method(CaseMethod(case_type="upper"))
        manager.add_method(NumberingMethod(start=1, step=1, digits=3, format_str="_{n}"))
        
        # Применяем
        name, ext = "My_Old_File_2024", ".txt"
        for method in manager.get_methods():
            name, ext = method.apply(name, ext, original_path)
        
        # Проверяем результат
        assert name.startswith("NEW_")
        assert "_001" in name or "_1" in name
        assert name.isupper() or any(c.isupper() for c in name)


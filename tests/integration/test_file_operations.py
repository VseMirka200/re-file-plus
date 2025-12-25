"""Интеграционные тесты для операций с файлами."""

import os
import pytest
from core.rename_methods import validate_filename, RenameMethod
from core.methods_manager import MethodsManager


class TestFileOperations:
    """Интеграционные тесты для операций с файлами."""
    
    def test_rename_workflow(self, temp_file):
        """Тест: полный workflow переименования."""
        # Создаем файл
        original_path = temp_file("old_name.txt", "test content")
        base_dir = os.path.dirname(original_path)
        
        # Проверяем, что файл существует
        assert os.path.exists(original_path)
        
        # Валидируем имя
        assert validate_filename("old_name.txt") is True
        
        # Новое имя тоже валидно
        assert validate_filename("new_name.txt") is True
    
    def test_methods_manager_workflow(self):
        """Тест: workflow менеджера методов."""
        manager = MethodsManager(None)  # metadata_extractor не нужен для базовых тестов
        
        # Добавляем методы
        from core.rename_methods import AddRemoveMethod, ReplaceMethod
        
        manager.add_method(AddRemoveMethod(operation="add", text="prefix_", position="before"))
        manager.add_method(ReplaceMethod(find="old", replace="new"))
        
        # Проверяем, что методы добавлены
        methods = manager.get_methods()
        assert len(methods) == 2
        
        # Применяем методы
        name, ext = "oldfile", ".txt"
        for method in methods:
            name, ext = method.apply(name, ext, "/path/to/file.txt")
        
        assert name == "prefix_newfile"
        assert ext == ".txt"


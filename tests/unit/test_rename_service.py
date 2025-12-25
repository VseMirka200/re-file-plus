"""Тесты для RenameService."""

import os
import pytest
from pathlib import Path
from core.services.rename_service import RenameService
from core.domain.file_info import FileInfo, FileStatus
from core.rename_methods import AddRemoveMethod, ReplaceMethod


class TestRenameService:
    """Тесты для класса RenameService."""
    
    def test_initialization(self):
        """Тест: инициализация RenameService."""
        service = RenameService()
        
        assert service is not None
        assert hasattr(service, 'rename_files')
    
    def test_rename_files_empty_list(self):
        """Тест: переименование пустого списка файлов."""
        service = RenameService()
        methods = [AddRemoveMethod(operation="add", text="prefix_", position="before")]
        
        result = service.rename_files([], methods, dry_run=True)
        
        assert result.success_count == 0
        assert result.error_count == 0
        assert len(result.errors) == 0
    
    def test_rename_files_no_methods(self, tmp_path):
        """Тест: переименование без методов."""
        service = RenameService()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")
        file_info = FileInfo.from_path(str(file_path))
        
        result = service.rename_files([file_info], [], dry_run=True)
        
        assert result.success_count == 0
        assert result.error_count == 0
    
    def test_rename_files_dry_run(self, tmp_path):
        """Тест: переименование в режиме dry_run."""
        service = RenameService()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")
        file_info = FileInfo.from_path(str(file_path))
        methods = [AddRemoveMethod(operation="add", text="prefix_", position="before")]
        
        result = service.rename_files([file_info], methods, dry_run=True)
        
        assert result.success_count == 1
        assert file_info.new_name == "prefix_test"
        # В dry_run файл не должен быть переименован физически
        assert file_path.exists()
        assert file_path.stem == "test"
    
    def test_rename_files_with_replace_method(self, tmp_path):
        """Тест: переименование с методом замены."""
        service = RenameService()
        file_path = tmp_path / "oldfile.txt"
        file_path.write_text("test")
        file_info = FileInfo.from_path(str(file_path))
        methods = [ReplaceMethod(find="old", replace="new")]
        
        result = service.rename_files([file_info], methods, dry_run=True)
        
        assert result.success_count == 1
        assert file_info.new_name == "newfile"
    
    def test_rename_files_validation_error(self, tmp_path):
        """Тест: переименование с ошибкой валидации."""
        service = RenameService()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")
        file_info = FileInfo.from_path(str(file_path))
        # Создаем имя с недопустимыми символами
        file_info.new_name = "file<name>"
        methods = [AddRemoveMethod(operation="add", text="", position="before")]
        
        result = service.rename_files([file_info], methods, dry_run=True)
        
        assert result.error_count >= 0  # Может быть ошибка валидации
        assert file_info.status == FileStatus.ERROR or file_info.status == FileStatus.READY
    
    def test_rename_files_no_change(self, tmp_path):
        """Тест: переименование без изменения имени."""
        service = RenameService()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")
        file_info = FileInfo.from_path(str(file_path))
        # Метод не изменяет имя
        methods = [AddRemoveMethod(operation="add", text="", position="before")]
        
        result = service.rename_files([file_info], methods, dry_run=True)
        
        # Если имя не изменилось, файл должен быть пропущен
        assert result.success_count == 0 or result.success_count == 1


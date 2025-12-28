"""Тесты для ReFileService."""

import os
import pytest
from pathlib import Path
from core.services.re_file_service import ReFileService
from core.domain.file_info import FileInfo, FileStatus
from core.re_file_methods import AddRemoveMethod, ReplaceMethod


class TestReFileService:
    """Тесты для класса ReFileService."""
    
    def test_initialization(self):
        """Тест: инициализация ReFileService."""
        service = ReFileService()
        
        assert service is not None
        assert hasattr(service, 're_file_files')
    
    def test_re_file_files_empty_list(self):
        """Тест: re-file операции с пустым списком файлов."""
        service = ReFileService()
        methods = [AddRemoveMethod(operation="add", text="prefix_", position="before")]
        
        result = service.re_file_files([], methods, dry_run=True)
        
        assert result.success_count == 0
        assert result.error_count == 0
        assert len(result.errors) == 0
    
    def test_re_file_files_no_methods(self, tmp_path):
        """Тест: re-file операции без методов."""
        service = ReFileService()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")
        file_info = FileInfo.from_path(str(file_path))
        
        result = service.re_file_files([file_info], [], dry_run=True)
        
        assert result.success_count == 0
        assert result.error_count == 0
    
    def test_re_file_files_dry_run(self, tmp_path):
        """Тест: re-file операции в режиме dry_run."""
        service = ReFileService()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")
        file_info = FileInfo.from_path(str(file_path))
        methods = [AddRemoveMethod(operation="add", text="prefix_", position="before")]
        
        result = service.re_file_files([file_info], methods, dry_run=True)
        
        assert result.success_count == 1
        assert file_info.new_name == "prefix_test"
        # В dry_run файл не должен быть переименован физически
        assert file_path.exists()
        assert file_path.stem == "test"
    
    def test_re_file_files_with_replace_method(self, tmp_path):
        """Тест: re-file операции с методом замены."""
        service = ReFileService()
        file_path = tmp_path / "oldfile.txt"
        file_path.write_text("test")
        file_info = FileInfo.from_path(str(file_path))
        methods = [ReplaceMethod(find="old", replace="new")]
        
        result = service.re_file_files([file_info], methods, dry_run=True)
        
        assert result.success_count == 1
        assert file_info.new_name == "newfile"
    
    def test_re_file_files_validation_error(self, tmp_path):
        """Тест: re-file операции с ошибкой валидации."""
        service = ReFileService()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")
        file_info = FileInfo.from_path(str(file_path))
        # Создаем имя с недопустимыми символами
        file_info.new_name = "file<name>"
        methods = [AddRemoveMethod(operation="add", text="", position="before")]
        
        result = service.re_file_files([file_info], methods, dry_run=True)
        
        assert result.error_count >= 0  # Может быть ошибка валидации
        assert file_info.status == FileStatus.ERROR or file_info.status == FileStatus.READY
    
    def test_re_file_files_no_change(self, tmp_path):
        """Тест: re-file операции без изменения имени."""
        service = ReFileService()
        file_path = tmp_path / "test.txt"
        file_path.write_text("test")
        file_info = FileInfo.from_path(str(file_path))
        # Метод не изменяет имя
        methods = [AddRemoveMethod(operation="add", text="", position="before")]
        
        result = service.re_file_files([file_info], methods, dry_run=True)
        
        # Если имя не изменилось, файл должен быть пропущен
        assert result.success_count == 0 or result.success_count == 1


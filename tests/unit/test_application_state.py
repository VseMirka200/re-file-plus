"""Тесты для ApplicationState."""

import pytest
from core.domain.application_state import ApplicationState
from core.domain.file_info import FileInfo, FileStatus
from pathlib import Path


class TestApplicationState:
    """Тесты для класса ApplicationState."""
    
    def test_initialization(self):
        """Тест: инициализация ApplicationState."""
        state = ApplicationState()
        
        assert state.files == []
        assert state.undo_stack == []
        assert state.redo_stack == []
        assert state.cancel_flag is False
        assert state.converter_files == []
        assert state.sorter_filters == []
    
    def test_add_file(self, temp_file):
        """Тест: добавление файла."""
        state = ApplicationState()
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        
        result = state.add_file(file_info)
        
        assert result is True
        assert len(state.files) == 1
        assert state.files[0] == file_info
    
    def test_add_duplicate_file(self, temp_file):
        """Тест: добавление дубликата файла."""
        state = ApplicationState()
        file_path = temp_file("test.txt")
        file_info1 = FileInfo.from_path(file_path)
        file_info2 = FileInfo.from_path(file_path)
        
        state.add_file(file_info1)
        result = state.add_file(file_info2)
        
        assert result is False
        assert len(state.files) == 1
    
    def test_remove_file(self, temp_file):
        """Тест: удаление файла."""
        state = ApplicationState()
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        
        state.add_file(file_info)
        result = state.remove_file(file_info)
        
        assert result is True
        assert len(state.files) == 0
    
    def test_remove_nonexistent_file(self, temp_file):
        """Тест: удаление несуществующего файла."""
        state = ApplicationState()
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        
        result = state.remove_file(file_info)
        
        assert result is False
        assert len(state.files) == 0
    
    def test_clear_files(self, temp_file):
        """Тест: очистка списка файлов."""
        state = ApplicationState()
        file_path1 = temp_file("test1.txt")
        file_path2 = temp_file("test2.txt")
        
        state.add_file(FileInfo.from_path(file_path1))
        state.add_file(FileInfo.from_path(file_path2))
        
        assert len(state.files) == 2
        
        state.clear_files()
        
        assert len(state.files) == 0
    
    def test_get_file_by_path(self, temp_file):
        """Тест: получение файла по пути."""
        state = ApplicationState()
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        
        state.add_file(file_info)
        result = state.get_file_by_path(file_path)
        
        assert result == file_info
    
    def test_get_file_by_path_nonexistent(self, temp_file):
        """Тест: получение несуществующего файла по пути."""
        state = ApplicationState()
        file_path = temp_file("test.txt")
        
        result = state.get_file_by_path(file_path)
        
        assert result is None
    
    def test_get_file_by_path_different_format(self, temp_file):
        """Тест: получение файла по пути в другом формате."""
        state = ApplicationState()
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        
        state.add_file(file_info)
        # Пробуем найти по строке вместо Path
        result = state.get_file_by_path(str(file_path))
        
        assert result == file_info


"""Тесты для модели FileInfo."""

import pytest
from pathlib import Path
from core.domain.file_info import FileInfo, FileStatus


class TestFileInfo:
    """Тесты для класса FileInfo."""
    
    def test_from_path(self, temp_file):
        """Тест: создание FileInfo из пути."""
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        
        assert file_info.path == Path(file_path)
        assert file_info.old_name == "test"
        assert file_info.new_name == "test"
        assert file_info.extension == ".txt"
        assert file_info.status == FileStatus.READY
        assert file_info.full_path == file_path
    
    def test_from_dict(self):
        """Тест: создание FileInfo из словаря."""
        data = {
            'full_path': '/path/to/file.txt',
            'old_name': 'file',
            'new_name': 'newfile',
            'extension': '.txt',
            'status': 'Готов',
            'metadata': {'key': 'value'}
        }
        
        file_info = FileInfo.from_dict(data)
        
        assert file_info.old_name == 'file'
        assert file_info.new_name == 'newfile'
        assert file_info.extension == '.txt'
        assert file_info.status == FileStatus.READY
        assert file_info.metadata == {'key': 'value'}
    
    def test_from_dict_with_error(self):
        """Тест: создание FileInfo из словаря с ошибкой."""
        data = {
            'full_path': '/path/to/file.txt',
            'old_name': 'file',
            'new_name': 'newfile',
            'extension': '.txt',
            'status': 'Ошибка: Файл не найден'
        }
        
        file_info = FileInfo.from_dict(data)
        
        assert file_info.status == FileStatus.ERROR
        assert file_info.error_message == 'Файл не найден'
    
    def test_to_dict(self, temp_file):
        """Тест: преобразование FileInfo в словарь."""
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        file_info.new_name = "newtest"
        
        result = file_info.to_dict()
        
        assert isinstance(result, dict)
        assert result['old_name'] == 'test'
        assert result['new_name'] == 'newtest'
        assert result['extension'] == '.txt'
        assert result['status'] == 'Готов'
    
    def test_to_dict_with_error(self, temp_file):
        """Тест: преобразование FileInfo с ошибкой в словарь."""
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        file_info.set_error("Тестовая ошибка")
        
        result = file_info.to_dict()
        
        assert result['status'] == 'Ошибка: Тестовая ошибка'
    
    def test_is_renamed(self, temp_file):
        """Тест: проверка, изменилось ли имя."""
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        
        assert file_info.is_renamed() is False
        
        file_info.new_name = "newtest"
        assert file_info.is_renamed() is True
    
    def test_is_ready(self, temp_file):
        """Тест: проверка готовности файла."""
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        
        assert file_info.is_ready() is True
        
        file_info.set_error("Ошибка")
        assert file_info.is_ready() is False
    
    def test_set_error(self, temp_file):
        """Тест: установка ошибки."""
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        
        file_info.set_error("Тестовая ошибка")
        
        assert file_info.status == FileStatus.ERROR
        assert file_info.error_message == "Тестовая ошибка"
    
    def test_set_ready(self, temp_file):
        """Тест: установка статуса готов."""
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        file_info.set_error("Ошибка")
        
        file_info.set_ready()
        
        assert file_info.status == FileStatus.READY
        assert file_info.error_message is None
    
    def test_new_path(self, temp_file):
        """Тест: получение нового пути."""
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        file_info.new_name = "newtest"
        
        new_path = file_info.new_path
        
        assert new_path == Path(file_path).parent / "newtest.txt"
    
    def test_old_full_name(self, temp_file):
        """Тест: получение полного старого имени."""
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        
        assert file_info.old_full_name == "test.txt"
    
    def test_new_full_name(self, temp_file):
        """Тест: получение полного нового имени."""
        file_path = temp_file("test.txt")
        file_info = FileInfo.from_path(file_path)
        file_info.new_name = "newtest"
        
        assert file_info.new_full_name == "newtest.txt"


class TestFileStatus:
    """Тесты для класса FileStatus."""
    
    def test_from_string_ready(self):
        """Тест: создание статуса из строки 'Готов'."""
        status = FileStatus.from_string("Готов")
        assert status == FileStatus.READY
    
    def test_from_string_error(self):
        """Тест: создание статуса из строки с ошибкой."""
        status = FileStatus.from_string("Ошибка: Файл не найден")
        assert status == FileStatus.ERROR
    
    def test_from_string_unknown(self):
        """Тест: создание статуса из неизвестной строки."""
        status = FileStatus.from_string("Неизвестный статус")
        assert status == FileStatus.READY  # По умолчанию READY


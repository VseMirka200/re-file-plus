"""Интеграционные тесты для ReFileService с реальными файлами."""

import os
import pytest
from pathlib import Path
from core.services.re_file_service import ReFileService
from core.domain.file_info import FileInfo
from core.re_file_methods import AddRemoveMethod, ReplaceMethod, CaseMethod, NumberingMethod


class TestReFileServiceIntegration:
    """Интеграционные тесты для ReFileService."""
    
    def test_re_file_single_file(self, temp_file):
        """Тест: переименование одного файла."""
        # Создаем файл
        original_path = temp_file("old_name.txt", "test content")
        file_info = FileInfo.from_path(original_path)
        
        # Создаем сервис
        service = ReFileService()
        
        # Метод переименования
        methods = [ReplaceMethod(find="old", replace="new")]
        
        # Выполняем dry-run
        result = service.re_file_files([file_info], methods, dry_run=True)
        
        assert result.success_count == 1
        assert result.error_count == 0
        assert file_info.new_name == "new"
        assert file_info.extension == ".txt"
        
        # Проверяем, что файл не был переименован (dry-run)
        assert os.path.exists(original_path)
        assert os.path.basename(original_path) == "old_name.txt"
    
    def test_re_file_multiple_files(self, sample_files):
        """Тест: переименование нескольких файлов."""
        # Создаем FileInfo для всех файлов
        file_infos = [FileInfo.from_path(f) for f in sample_files]
        
        # Создаем сервис
        service = ReFileService()
        
        # Метод добавления префикса
        methods = [AddRemoveMethod(operation="add", text="renamed_", position="before")]
        
        # Выполняем dry-run
        result = service.re_file_files(file_infos, methods, dry_run=True)
        
        assert result.success_count == len(sample_files)
        assert result.error_count == 0
        
        # Проверяем, что все файлы получили префикс
        for file_info in file_infos:
            assert file_info.new_name.startswith("renamed_")
    
    def test_re_file_multiple_methods(self, temp_file):
        """Тест: применение нескольких методов последовательно."""
        original_path = temp_file("old_file_name.txt", "test content")
        file_info = FileInfo.from_path(original_path)
        
        service = ReFileService()
        
        # Комбинация методов: замена + добавление префикса + изменение регистра
        methods = [
            ReplaceMethod(find="old", replace="new"),
            AddRemoveMethod(operation="add", text="PREFIX_", position="before"),
            CaseMethod(case_type="upper")
        ]
        
        result = service.re_file_files([file_info], methods, dry_run=True)
        
        assert result.success_count == 1
        assert file_info.new_name == "PREFIX_NEW_FILE_NAME"
    
    def test_re_file_conflicts(self, temp_file):
        """Тест: обработка конфликтов имен."""
        # Создаем два файла в одной папке
        file1_path = temp_file("file.txt", "content 1")
        file2_path = temp_file("other.txt", "content 2")
        
        file1 = FileInfo.from_path(file1_path)
        file2 = FileInfo.from_path(file2_path)
        
        service = ReFileService()
        
        # Метод, который создаст одинаковые имена
        methods = [ReplaceMethod(find=".*", replace="same_name", full_match=True)]
        
        result = service.re_file_files([file1, file2], methods, dry_run=True)
        
        # Оба файла должны иметь одинаковое новое имя (конфликт)
        assert file1.new_name == file2.new_name
        # В реальном сценарии это должно быть обработано как конфликт
    
    def test_re_file_numbering(self, sample_files):
        """Тест: нумерация файлов."""
        file_infos = [FileInfo.from_path(f) for f in sample_files]
        
        service = ReFileService()
        
        # Метод нумерации
        methods = [NumberingMethod(start=1, step=1, digits=2, format_str="_{n}")]
        
        result = service.re_file_files(file_infos, methods, dry_run=True)
        
        assert result.success_count == len(sample_files)
        
        # Проверяем, что файлы получили номера
        names = [f.new_name for f in file_infos]
        assert any("_01" in name for name in names)
        assert any("_02" in name for name in names)
    
    def test_re_file_invalid_filename(self, temp_file):
        """Тест: обработка невалидных имен файлов."""
        original_path = temp_file("valid.txt", "test content")
        file_info = FileInfo.from_path(original_path)
        
        service = ReFileService()
        
        # Метод, который создаст невалидное имя (с недопустимыми символами)
        methods = [ReplaceMethod(find="valid", replace="file<name>")]
        
        result = service.re_file_files([file_info], methods, dry_run=True)
        
        # Должна быть ошибка валидации
        assert result.error_count == 1
        assert file_info.status.value == "error"
    
    def test_re_file_empty_methods(self, temp_file):
        """Тест: применение без методов (файлы не должны измениться)."""
        original_path = temp_file("test.txt", "test content")
        file_info = FileInfo.from_path(original_path)
        
        service = ReFileService()
        
        # Пустой список методов
        methods = []
        
        result = service.re_file_files([file_info], methods, dry_run=True)
        
        # Файлы не должны быть переименованы
        assert result.success_count == 0
        assert file_info.new_name == file_info.old_name


class TestReFileServicePerformance:
    """Тесты производительности ReFileService."""
    
    def test_re_file_large_batch(self, temp_dir):
        """Тест: производительность на большом количестве файлов."""
        # Создаем много файлов
        files = []
        for i in range(100):
            file_path = os.path.join(temp_dir, f"file_{i:03d}.txt")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"Content {i}")
            files.append(file_path)
        
        file_infos = [FileInfo.from_path(f) for f in files]
        service = ReFileService()
        methods = [AddRemoveMethod(operation="add", text="renamed_", position="before")]
        
        import time
        start_time = time.time()
        result = service.re_file_files(file_infos, methods, dry_run=True)
        elapsed_time = time.time() - start_time
        
        assert result.success_count == 100
        # Проверяем, что обработка 100 файлов занимает менее 1 секунды
        assert elapsed_time < 1.0, f"Обработка заняла слишком много времени: {elapsed_time:.3f}s"


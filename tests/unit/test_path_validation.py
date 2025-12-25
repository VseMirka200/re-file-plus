"""Тесты для валидации путей."""

import os
import pytest
# Импорт функций валидации путей
try:
    from infrastructure.system.paths import is_safe_path, check_windows_path_length
except ImportError:
    from config.constants import is_safe_path, check_windows_path_length


class TestPathValidation:
    """Тесты для функции is_safe_path."""
    
    def test_safe_path_valid_file(self, temp_file):
        """Тест: валидный путь к существующему файлу."""
        file_path = temp_file("test.txt")
        assert is_safe_path(file_path) is True
    
    def test_safe_path_nonexistent_file(self):
        """Тест: несуществующий файл должен быть отклонен."""
        assert is_safe_path("/nonexistent/file.txt") is False
    
    def test_safe_path_empty_string(self):
        """Тест: пустая строка должна быть отклонена."""
        assert is_safe_path("") is False
        assert is_safe_path("   ") is False
    
    def test_safe_path_path_traversal(self, temp_file):
        """Тест: path traversal атаки должны быть отклонены."""
        file_path = temp_file("test.txt")
        base_dir = os.path.dirname(file_path)
        
        # Попытка выйти за пределы директории
        malicious_path = os.path.join(base_dir, "..", "test.txt")
        assert is_safe_path(malicious_path) is False
        
        # Путь с ~
        assert is_safe_path("~/test.txt") is False
    
    def test_safe_path_directory_not_file(self, temp_dir):
        """Тест: директория не должна проходить валидацию (только файлы)."""
        assert is_safe_path(temp_dir) is False
    
    def test_safe_path_allowed_dirs(self, temp_file):
        """Тест: проверка разрешенных директорий."""
        file_path = temp_file("test.txt")
        base_dir = os.path.dirname(file_path)
        
        # Файл в разрешенной директории
        assert is_safe_path(file_path, allowed_dirs=[base_dir]) is True
        
        # Файл вне разрешенной директории - создаем другой файл в другой директории
        import tempfile
        other_temp_dir = tempfile.mkdtemp()
        try:
            other_file = os.path.join(other_temp_dir, "other.txt")
            with open(other_file, 'w') as f:
                f.write("test")
            assert is_safe_path(other_file, allowed_dirs=[base_dir]) is False
        finally:
            import shutil
            shutil.rmtree(other_temp_dir, ignore_errors=True)
    
    def test_safe_path_invalid_types(self):
        """Тест: невалидные типы должны быть отклонены."""
        # Функция должна обрабатывать невалидные типы без ошибок
        try:
            result = is_safe_path(None)  # type: ignore
            assert result is False
        except (AttributeError, TypeError):
            pass  # Ожидаемое поведение - функция должна обрабатывать ошибки
        
        try:
            result = is_safe_path(123)  # type: ignore
            assert result is False
        except (AttributeError, TypeError):
            pass  # Ожидаемое поведение
        
        try:
            result = is_safe_path([])  # type: ignore
            assert result is False
        except (AttributeError, TypeError):
            pass  # Ожидаемое поведение


class TestWindowsPathLength:
    """Тесты для проверки длины пути Windows."""
    
    def test_windows_path_length_valid(self):
        """Тест: валидная длина пути."""
        short_path = "C:\\test\\file.txt"
        assert check_windows_path_length(short_path) is True
    
    def test_windows_path_length_too_long(self):
        """Тест: путь превышающий MAX_PATH должен быть отклонен."""
        # Создаем путь длиннее 260 символов
        long_path = "C:\\" + "a" * 300 + "\\file.txt"
        if os.name == 'nt':  # Только на Windows
            assert check_windows_path_length(long_path) is False
    
    def test_windows_path_length_exact_limit(self):
        """Тест: путь на границе лимита."""
        if os.name == 'nt':  # Только на Windows
            # Путь длиной ровно 260 символов (C:\ + 253 символа + .txt = 260)
            # C:\ = 3 символа, .txt = 4 символа, значит нужно 253 символа 'a'
            exact_path = "C:\\" + "a" * 253 + ".txt"
            # Проверяем, что длина = 260
            assert len(exact_path) == 260
            # Функция должна вернуть True для пути длиной ровно 260
            result = check_windows_path_length(exact_path)
            assert result is True


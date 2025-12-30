"""Тесты для функции check_conflicts."""

import pytest
from core.re_file_methods import check_conflicts


class TestCheckConflicts:
    """Тесты для функции проверки конфликтов имен файлов."""
    
    def test_no_conflicts(self):
        """Тест: нет конфликтов при разных именах."""
        files_list = [
            {'new_name': 'file1', 'extension': '.txt', 'status': 'Готов'},
            {'new_name': 'file2', 'extension': '.txt', 'status': 'Готов'},
            {'new_name': 'file3', 'extension': '.pdf', 'status': 'Готов'}
        ]
        check_conflicts(files_list)
        
        # Статусы не должны измениться
        assert files_list[0]['status'] == 'Готов'
        assert files_list[1]['status'] == 'Готов'
        assert files_list[2]['status'] == 'Готов'
    
    def test_single_conflict(self):
        """Тест: один конфликт между двумя файлами."""
        files_list = [
            {'new_name': 'file1', 'extension': '.txt', 'status': 'Готов'},
            {'new_name': 'file1', 'extension': '.txt', 'status': 'Готов'},
            {'new_name': 'file2', 'extension': '.pdf', 'status': 'Готов'}
        ]
        check_conflicts(files_list)
        
        # Первые два файла должны иметь статус конфликта
        assert 'Конфликт' in files_list[0]['status']
        assert 'Конфликт' in files_list[1]['status']
        assert files_list[2]['status'] == 'Готов'
    
    def test_multiple_conflicts(self):
        """Тест: несколько конфликтов."""
        files_list = [
            {'new_name': 'file1', 'extension': '.txt', 'status': 'Готов'},
            {'new_name': 'file1', 'extension': '.txt', 'status': 'Готов'},
            {'new_name': 'file1', 'extension': '.txt', 'status': 'Готов'},
            {'new_name': 'file2', 'extension': '.pdf', 'status': 'Готов'},
            {'new_name': 'file2', 'extension': '.pdf', 'status': 'Готов'}
        ]
        check_conflicts(files_list)
        
        # Первые три файла должны иметь конфликт с 3 файлами
        assert 'Конфликт' in files_list[0]['status']
        assert '3 файла' in files_list[0]['status']
        assert 'Конфликт' in files_list[1]['status']
        assert 'Конфликт' in files_list[2]['status']
        
        # Последние два файла должны иметь конфликт с 2 файлами
        assert 'Конфликт' in files_list[3]['status']
        assert '2 файла' in files_list[3]['status']
        assert 'Конфликт' in files_list[4]['status']
    
    def test_empty_list(self):
        """Тест: пустой список файлов."""
        files_list = []
        check_conflicts(files_list)
        assert len(files_list) == 0
    
    def test_different_extensions_no_conflict(self):
        """Тест: разные расширения не создают конфликт."""
        files_list = [
            {'new_name': 'file1', 'extension': '.txt', 'status': 'Готов'},
            {'new_name': 'file1', 'extension': '.pdf', 'status': 'Готов'}
        ]
        check_conflicts(files_list)
        
        # Не должно быть конфликтов, так как расширения разные
        assert files_list[0]['status'] == 'Готов'
        assert files_list[1]['status'] == 'Готов'
    
    def test_performance_large_list(self):
        """Тест: производительность на большом списке."""
        # Создаем большой список файлов
        files_list = [
            {'new_name': f'file{i}', 'extension': '.txt', 'status': 'Готов'}
            for i in range(1000)
        ]
        
        # Добавляем несколько конфликтов
        files_list[100]['new_name'] = 'file1'
        files_list[200]['new_name'] = 'file1'
        files_list[300]['new_name'] = 'file2'
        files_list[400]['new_name'] = 'file2'
        
        import time
        start_time = time.time()
        check_conflicts(files_list)
        elapsed_time = time.time() - start_time
        
        # Проверяем, что функция выполняется быстро (< 1 секунды для 1000 файлов)
        assert elapsed_time < 1.0, f"Функция выполняется слишком медленно: {elapsed_time:.3f}s"
        
        # Проверяем, что конфликты найдены
        conflict_count = sum(1 for f in files_list if 'Конфликт' in f['status'])
        assert conflict_count == 4  # 2 конфликта по 2 файла каждый


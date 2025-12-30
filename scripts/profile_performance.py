"""Скрипт для профилирования производительности приложения.

Использование:
    python scripts/profile_performance.py
"""

import cProfile
import pstats
import io
import os
import sys
import tempfile
from pathlib import Path

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.re_file_methods import (
    check_conflicts,
    add_file_to_list,
    validate_filename,
    AddRemoveMethod,
    ReplaceMethod,
    CaseMethod,
    NumberingMethod
)
from core.methods_manager import MethodsManager
from core.services.re_file_service import ReFileService
from core.domain.file_info import FileInfo


def create_test_files(count: int, temp_dir: str) -> list:
    """Создает тестовые файлы."""
    files = []
    for i in range(count):
        file_path = os.path.join(temp_dir, f"test_file_{i:04d}.txt")
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Test content {i}")
        files.append(file_path)
    return files


def profile_check_conflicts():
    """Профилирование функции check_conflicts."""
    print("\n=== Профилирование check_conflicts ===")
    
    # Создаем большой список файлов
    files_list = []
    for i in range(1000):
        files_list.append({
            'new_name': f'file_{i % 100}',  # Создаем конфликты
            'extension': '.txt',
            'status': 'Готов'
        })
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    check_conflicts(files_list)
    
    profiler.disable()
    
    # Выводим статистику
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(20)  # Топ 20 функций
    print(s.getvalue())


def profile_add_file_to_list():
    """Профилирование функции add_file_to_list."""
    print("\n=== Профилирование add_file_to_list ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_files = create_test_files(500, temp_dir)
        
        files_list = []
        path_cache = set()
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        for file_path in test_files:
            add_file_to_list(file_path, files_list, path_cache)
        
        profiler.disable()
        
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats(20)
        print(s.getvalue())


def profile_validate_filename():
    """Профилирование функции validate_filename."""
    print("\n=== Профилирование validate_filename ===")
    
    test_path = "/tmp/test_file.txt"
    test_names = [
        "valid_name",
        "file<invalid>",
        "CON",
        "a" * 300,  # Слишком длинное
        "normal_file_123"
    ] * 200  # Повторяем для статистики
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    for i, name in enumerate(test_names):
        validate_filename(name, ".txt", test_path, i)
    
    profiler.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(20)
    print(s.getvalue())


def profile_methods_application():
    """Профилирование применения методов."""
    print("\n=== Профилирование применения методов ===")
    
    manager = MethodsManager()
    manager.add_method(AddRemoveMethod(operation="add", text="prefix_", position="before"))
    manager.add_method(ReplaceMethod(find="old", replace="new"))
    manager.add_method(CaseMethod(case_type="upper"))
    manager.add_method(NumberingMethod(start=1, step=1, digits=3, format_str="_{n}"))
    
    # Создаем много файлов для обработки
    test_cases = [("old_file_name", ".txt", "/path/to/file.txt")] * 1000
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    for name, ext, path in test_cases:
        current_name, current_ext = name, ext
        for method in manager.get_methods():
            current_name, current_ext = method.apply(current_name, current_ext, path)
    
    profiler.disable()
    
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(20)
    print(s.getvalue())


def profile_re_file_service():
    """Профилирование ReFileService."""
    print("\n=== Профилирование ReFileService ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        test_files = create_test_files(200, temp_dir)
        file_infos = [FileInfo.from_path(f) for f in test_files]
        
        service = ReFileService()
        methods = [
            AddRemoveMethod(operation="add", text="renamed_", position="before"),
            ReplaceMethod(find="test", replace="new"),
            CaseMethod(case_type="title")
        ]
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        result = service.re_file_files(file_infos, methods, dry_run=True)
        
        profiler.disable()
        
        print(f"Обработано файлов: {result.success_count}")
        print(f"Ошибок: {result.error_count}")
        
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)
        ps.sort_stats('cumulative')
        ps.print_stats(30)
        print(s.getvalue())


def main():
    """Главная функция для запуска профилирования."""
    print("=" * 60)
    print("Профилирование производительности Re-File-Plus")
    print("=" * 60)
    
    try:
        profile_check_conflicts()
        profile_add_file_to_list()
        profile_validate_filename()
        profile_methods_application()
        profile_re_file_service()
        
        print("\n" + "=" * 60)
        print("Профилирование завершено!")
        print("=" * 60)
        print("\nРекомендации:")
        print("1. Обратите внимание на функции с высоким 'cumulative' временем")
        print("2. Проверьте функции с большим количеством вызовов")
        print("3. Оптимизируйте узкие места для улучшения производительности")
        
    except Exception as e:
        print(f"\nОшибка при профилировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


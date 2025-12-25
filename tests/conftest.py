"""Конфигурация pytest для проекта Rename+."""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest


@pytest.fixture
def temp_dir():
    """Создает временную директорию для тестов."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def temp_file(temp_dir):
    """Создает временный файл для тестов."""
    def _create_file(filename: str, content: str = "test content") -> str:
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return file_path
    return _create_file


@pytest.fixture
def sample_files(temp_dir):
    """Создает набор тестовых файлов."""
    files = []
    for i in range(5):
        filename = f"test_file_{i}.txt"
        file_path = os.path.join(temp_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Content of file {i}")
        files.append(file_path)
    return files


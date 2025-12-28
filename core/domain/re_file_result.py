"""Результат операции re-file."""

from dataclasses import dataclass, field
from typing import List, Optional
from .file_info import FileInfo


@dataclass
class ReFiledFile:
    """Информация о файле после re-file операции."""
    old_path: str
    new_path: str
    preview: bool = False  # True для dry-run


@dataclass
class ReFileResult:
    """Результат операции re-file."""
    success_count: int = 0
    error_count: int = 0
    re_filed_files: List[ReFiledFile] = field(default_factory=list)
    errors_list: List[str] = field(default_factory=list)
    
    def add_success(self, file: FileInfo, new_path: Optional[str] = None, preview: bool = False):
        """Добавление успешного результата.
        
        Args:
            file: Файл, который был переименован
            new_path: Новый путь (если отличается от file.new_path)
            preview: True если это предпросмотр
        """
        self.success_count += 1
        if new_path is None:
            new_path = str(file.new_path)
        self.re_filed_files.append(ReFiledFile(
            old_path=str(file.path),
            new_path=new_path,
            preview=preview
        ))
    
    def add_error(self, file: FileInfo, error_message: str):
        """Добавление ошибки.
        
        Args:
            file: Файл, с которым произошла ошибка
            error_message: Сообщение об ошибке
        """
        self.error_count += 1
        self.errors_list.append(f"{file.path}: {error_message}")
    
    def is_successful(self) -> bool:
        """Проверка, была ли операция успешной."""
        return self.error_count == 0
    
    def has_errors(self) -> bool:
        """Проверка, есть ли ошибки."""
        return self.error_count > 0


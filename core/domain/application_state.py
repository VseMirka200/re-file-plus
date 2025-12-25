"""Состояние приложения."""

from dataclasses import dataclass, field
from typing import List, Optional
from .file_info import FileInfo


@dataclass
class ApplicationState:
    """Состояние приложения."""
    files: List[FileInfo] = field(default_factory=list)
    undo_stack: List[List[FileInfo]] = field(default_factory=list)
    redo_stack: List[List[FileInfo]] = field(default_factory=list)
    cancel_flag: bool = False
    
    # Данные для вкладок
    converter_files: List = field(default_factory=list)
    sorter_filters: List = field(default_factory=list)
    
    def add_file(self, file: FileInfo) -> bool:
        """Добавление файла.
        
        Args:
            file: Файл для добавления
            
        Returns:
            True если файл добавлен, False если уже существует
        """
        # Проверяем, нет ли уже такого файла
        for existing_file in self.files:
            if existing_file.path == file.path:
                return False
        
        self.files.append(file)
        return True
    
    def remove_file(self, file: FileInfo) -> bool:
        """Удаление файла.
        
        Args:
            file: Файл для удаления
            
        Returns:
            True если файл удален, False если не найден
        """
        if file in self.files:
            self.files.remove(file)
            return True
        return False
    
    def clear_files(self) -> None:
        """Очистка списка файлов."""
        self.files.clear()
    
    def get_file_by_path(self, path: str) -> Optional[FileInfo]:
        """Получение файла по пути.
        
        Args:
            path: Путь к файлу
            
        Returns:
            FileInfo или None
        """
        from pathlib import Path
        target_path = Path(path)
        for file in self.files:
            if file.path == target_path:
                return file
        return None
    
    def push_undo(self, files: List[FileInfo]) -> None:
        """Добавление состояния в стек отмены.
        
        Args:
            files: Список файлов для сохранения
        """
        # Создаем копию состояния
        files_copy = [FileInfo(
            path=f.path,
            old_name=f.old_name,
            new_name=f.new_name,
            extension=f.extension,
            status=f.status,
            metadata=f.metadata.copy() if f.metadata else {},
            error_message=f.error_message,
            full_path=f.full_path
        ) for f in files]
        
        self.undo_stack.append(files_copy)
        # Ограничиваем размер стека
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
        # Очищаем стек повтора при новом действии
        self.redo_stack.clear()
    
    def pop_undo(self) -> Optional[List[FileInfo]]:
        """Извлечение состояния из стека отмены.
        
        Returns:
            Список файлов или None
        """
        if not self.undo_stack:
            return None
        return self.undo_stack.pop()
    
    def push_redo(self, files: List[FileInfo]) -> None:
        """Добавление состояния в стек повтора.
        
        Args:
            files: Список файлов для сохранения
        """
        files_copy = [FileInfo(
            path=f.path,
            old_name=f.old_name,
            new_name=f.new_name,
            extension=f.extension,
            status=f.status,
            metadata=f.metadata.copy() if f.metadata else {},
            error_message=f.error_message,
            full_path=f.full_path
        ) for f in files]
        
        self.redo_stack.append(files_copy)
        if len(self.redo_stack) > 50:
            self.redo_stack.pop(0)
    
    def pop_redo(self) -> Optional[List[FileInfo]]:
        """Извлечение состояния из стека повтора.
        
        Returns:
            Список файлов или None
        """
        if not self.redo_stack:
            return None
        return self.redo_stack.pop()


"""Модель информации о файле."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict
from enum import Enum


class FileStatus(Enum):
    """Статус файла."""
    READY = "Готов"
    CONFLICT = "Конфликт"
    ERROR = "Ошибка"
    PROCESSING = "Обработка"
    
    @classmethod
    def from_string(cls, status_str: str) -> 'FileStatus':
        """Создание статуса из строки."""
        for status in cls:
            if status.value == status_str or status_str.startswith(status.value):
                return status
        # Если статус начинается с "Ошибка:", возвращаем ERROR
        if status_str.startswith("Ошибка"):
            return cls.ERROR
        return cls.READY


@dataclass
class FileInfo:
    """Модель информации о файле."""
    path: Path
    old_name: str
    new_name: str
    extension: str
    status: FileStatus = FileStatus.READY
    metadata: Optional[Dict] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    # Для обратной совместимости
    full_path: Optional[str] = None
    
    def __post_init__(self):
        """Инициализация после создания."""
        if self.full_path is None:
            self.full_path = str(self.path)
        # Убеждаемся, что path - это Path объект
        if isinstance(self.path, str):
            self.path = Path(self.path)
    
    @classmethod
    def from_path(cls, file_path: str, metadata: Optional[Dict] = None) -> 'FileInfo':
        """Создание FileInfo из пути к файлу.
        
        Args:
            file_path: Путь к файлу
            metadata: Опциональные метаданные
            
        Returns:
            FileInfo объект
        """
        path_obj = Path(file_path)
        old_name = path_obj.stem
        extension = path_obj.suffix
        
        return cls(
            path=path_obj,
            old_name=old_name,
            new_name=old_name,
            extension=extension,
            status=FileStatus.READY,
            metadata=metadata or {},
            full_path=file_path
        )
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FileInfo':
        """Создание FileInfo из словаря (для обратной совместимости).
        
        Args:
            data: Словарь с данными файла
            
        Returns:
            FileInfo объект
        """
        # Поддержка разных форматов словарей
        file_path = data.get('full_path') or data.get('path', '')
        if not file_path:
            # Если нет полного пути, собираем из path и old_name
            dir_path = data.get('path', '')
            old_name = data.get('old_name', '')
            extension = data.get('extension', '')
            file_path = str(Path(dir_path) / f"{old_name}{extension}")
        
        path_obj = Path(file_path)
        old_name = data.get('old_name', path_obj.stem)
        new_name = data.get('new_name', old_name)
        extension = data.get('extension', path_obj.suffix)
        status_str = data.get('status', 'Готов')
        
        # Извлекаем сообщение об ошибке из статуса
        error_message = None
        if status_str.startswith('Ошибка:'):
            error_message = status_str.replace('Ошибка:', '').strip()
        
        return cls(
            path=path_obj,
            old_name=old_name,
            new_name=new_name,
            extension=extension,
            status=FileStatus.from_string(status_str),
            metadata=data.get('metadata', {}),
            error_message=error_message,
            full_path=file_path
        )
    
    def to_dict(self) -> Dict:
        """Преобразование в словарь (для обратной совместимости).
        
        Returns:
            Словарь с данными файла
        """
        # Обрабатываем status - может быть FileStatus или строка
        if isinstance(self.status, FileStatus):
            status_str = self.status.value
        elif isinstance(self.status, str):
            status_str = self.status
        else:
            # Fallback
            status_str = str(self.status) if self.status else 'Готов'
        
        if self.error_message:
            status_str = f"Ошибка: {self.error_message}"
        
        return {
            'path': str(self.path.parent),
            'full_path': self.full_path or str(self.path),
            'old_name': self.old_name,
            'new_name': self.new_name,
            'extension': self.extension,
            'status': status_str,
            'metadata': self.metadata
        }
    
    @property
    def old_full_name(self) -> str:
        """Полное старое имя с расширением."""
        return f"{self.old_name}{self.extension}"
    
    @property
    def new_full_name(self) -> str:
        """Полное новое имя с расширением."""
        return f"{self.new_name}{self.extension}"
    
    @property
    def new_path(self) -> Path:
        """Новый путь к файлу."""
        return self.path.parent / self.new_full_name
    
    def is_renamed(self) -> bool:
        """Проверка, изменилось ли имя."""
        return self.old_name != self.new_name or self.extension != self.extension
    
    def is_ready(self) -> bool:
        """Проверка, готов ли файл к переименованию."""
        return self.status == FileStatus.READY
    
    def set_error(self, message: str):
        """Установка ошибки."""
        self.status = FileStatus.ERROR
        self.error_message = message
    
    def set_ready(self):
        """Установка статуса готов."""
        self.status = FileStatus.READY
        self.error_message = None


"""Базовый класс для методов re-file операций."""

from abc import ABC, abstractmethod
from typing import Tuple


class ReFileMethod(ABC):
    """Базовый абстрактный класс для методов re-file операций.
    
    Все методы re-file должны наследоваться от этого класса
    и реализовывать метод apply() для преобразования имени файла.
    
    Методы re-file применяются последовательно к каждому файлу
    в порядке их добавления в MethodsManager.
    """
    
    @abstractmethod
    def apply(self, name: str, extension: str, file_path: str) -> Tuple[str, str]:
        """
        Применяет метод переименования к имени файла
        
        Args:
            name: Имя файла без расширения
            extension: Расширение файла (с точкой)
            file_path: Полный путь к файлу
            
        Returns:
            Tuple[str, str]: Новое имя и расширение
        """
        pass


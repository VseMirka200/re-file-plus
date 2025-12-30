"""Модуль управления списком файлов.

Разбит на подмодули для лучшей организации кода:
- manager: Основной класс FileListManager
- file_adder: Добавление файлов и папок
- file_operations: Операции с файлами (открытие, копирование)
- import_export: Импорт и экспорт списка файлов
- treeview: Отображение в Treeview и обновление UI
"""

from .manager import FileListManager

__all__ = ['FileListManager']


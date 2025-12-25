"""Координатор вкладки конвертации файлов.

Использует модульную структуру для разделения UI, логики и обработчиков.
Для обратной совместимости импортирует методы из старого модуля.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk

logger = logging.getLogger(__name__)

# Импорт для обратной совместимости
# Постепенно методы будут перенесены в отдельные модули
try:
    from ui.converter_tab import ConverterTab as LegacyConverterTab
    HAS_LEGACY = True
except ImportError:
    HAS_LEGACY = False
    LegacyConverterTab = None


class ConverterTab:
    """Класс для управления вкладкой конвертации файлов.
    
    Координирует работу UI компонентов, бизнес-логики и обработчиков событий.
    """
    
    def __init__(self, app) -> None:
        """Инициализация вкладки конвертации.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
        # Для обратной совместимости используем старый класс
        if HAS_LEGACY:
            self._legacy = LegacyConverterTab(app)
        else:
            self._legacy = None
    
    def create_tab(self):
        """Создание вкладки конвертации файлов на главном экране."""
        if self._legacy:
            # Используем старую реализацию для обратной совместимости
            return self._legacy.create_tab()
        
        # Новая реализация (будет реализована позже)
        logger.warning("Новая реализация ConverterTab еще не завершена, используйте старую версию")
    
    # Делегируем все методы старому классу для обратной совместимости
    def process_files_from_args(self):
        """Обработка файлов из аргументов командной строки."""
        if self._legacy:
            return self._legacy.process_files_from_args()
    
    def add_files_for_conversion(self):
        """Добавление файлов для конвертации."""
        if self._legacy:
            return self._legacy.add_files_for_conversion()
    
    def update_available_formats(self):
        """Обновление списка доступных форматов."""
        if self._legacy:
            return self._legacy.update_available_formats()
    
    def filter_converter_files_by_type(self):
        """Фильтрация файлов по типу."""
        if self._legacy:
            return self._legacy.filter_converter_files_by_type()
    
    def convert_files(self):
        """Конвертация выбранных файлов."""
        if self._legacy:
            return self._legacy.convert_files()
    
    def update_converter_progress(self, current: int, total: int, filename: str):
        """Обновление прогресс-бара конвертации."""
        if self._legacy:
            return self._legacy.update_converter_progress(current, total, filename)
    
    def update_converter_status(self, index: int, success: bool, message: str, output_path=None):
        """Обновление статуса файла в списке конвертации."""
        if self._legacy:
            return self._legacy.update_converter_status(index, success, message, output_path)
    
    def clear_converter_files_list(self):
        """Очистка списка файлов для конвертации."""
        if self._legacy:
            return self._legacy.clear_converter_files_list()
    
    def setup_converter_drag_drop(self, list_frame, tree, tab_frame):
        """Настройка drag and drop для вкладки конвертации."""
        if self._legacy:
            return self._legacy.setup_converter_drag_drop(list_frame, tree, tab_frame)
    
    def show_converter_context_menu(self, event):
        """Показ контекстного меню для файла в конвертации."""
        if self._legacy:
            return self._legacy.show_converter_context_menu(event)
    
    def open_converter_file(self):
        """Открытие файла конвертации."""
        if self._legacy:
            return self._legacy.open_converter_file()
    
    def open_converter_file_folder(self):
        """Открытие папки с выбранным файлом."""
        if self._legacy:
            return self._legacy.open_converter_file_folder()
    
    def copy_converter_file_path(self):
        """Копирование пути файла в буфер обмена."""
        if self._legacy:
            return self._legacy.copy_converter_file_path()
    
    def remove_selected_converter_files(self):
        """Удаление выбранных файлов из списка."""
        if self._legacy:
            return self._legacy.remove_selected_converter_files()


"""Модуль для вкладки конвертации файлов.

Обеспечивает интерфейс для конвертации файлов между различными форматами
с поддержкой выбора формата, настроек качества и отслеживания прогресса.
"""

import logging
import os

logger = logging.getLogger(__name__)


class ConverterTab:
    """Класс для управления вкладкой конвертации файлов.
    
    Координирует работу различных модулей конвертации.
    """
    
    def __init__(self, app) -> None:
        """Инициализация вкладки конвертации.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
        
        # Инициализируем модули
        from ui.converter.file_handler import ConverterFileHandler
        from ui.converter.ui_components import ConverterUIComponents
        from ui.converter.drag_drop import ConverterDragDrop
        from ui.converter.context_menu import ConverterContextMenu
        from ui.converter.converter import ConverterProcessor
        from ui.converter.progress import ConverterProgress
        from ui.converter.tab_builder import ConverterTabBuilder
        from ui.converter.args_processor import ConverterArgsProcessor
        
        self.file_handler = ConverterFileHandler(app)
        self.ui_components = ConverterUIComponents(app)
        self.drag_drop = ConverterDragDrop(app)
        self.context_menu = ConverterContextMenu(app)
        self.converter = ConverterProcessor(app)
        self.progress = ConverterProgress(app)
        self.tab_builder = ConverterTabBuilder(app, self)
        self.args_processor = ConverterArgsProcessor(app, self)
    
    def create_tab(self):
        """Создание вкладки конвертации файлов на главном экране."""
        return self.tab_builder.create_tab()
    
    def create_tab_content(self, parent):
        """Создание содержимого вкладки конвертации (только правая панель с настройками).
        
        Args:
            parent: Родительский контейнер для размещения содержимого
        """
        return self.tab_builder.create_tab_content(parent)
    
    def process_files_from_args(self):
        """Обработка файлов из аргументов командной строки."""
        return self.args_processor.process_files_from_args()
    
    def add_files_for_conversion(self):
        """Добавление файлов для конвертации."""
        return self.file_handler.add_files_for_conversion()
    
    def update_available_formats(self):
        """Обновление списка доступных форматов в combobox на основе выбранных файлов."""
        return self.ui_components.update_available_formats()
    
    def filter_converter_files_by_type(self):
        """Фильтрация файлов в конвертере по типу (использует общий список файлов)."""
        return self.ui_components.filter_converter_files_by_type()
    
    def convert_files(self):
        """Конвертация выбранных файлов."""
        return self.converter.convert_files()
    
    def update_converter_progress(self, current: int, total: int, filename: str):
        """Обновление прогресса конвертации."""
        return self.progress.update_progress(current, total, filename)
    
    def _set_file_in_progress(self, file_path: str):
        """Установка желтого тега "в работе" для файла в treeview."""
        return self.progress.set_file_in_progress(file_path)
    
    def update_converter_status(self, index: int, success: bool, message: str, output_path=None, file_path=None):
        """Обновление статуса файла в списке конвертации."""
        return self.progress.update_status(index, success, message, output_path, file_path)
    
    def _update_file_status_in_treeview(self, file_path: str, success: bool, message: str):
        """Обновление статуса и цвета файла в treeview после конвертации."""
        return self.progress.update_file_status_in_treeview(file_path, success, message)
    
    def _check_if_file_already_converted(self, file_path: str, available_formats: list):
        """Проверка, был ли файл уже конвертирован."""
        return self.file_handler.check_if_file_already_converted(file_path, available_formats)
    
    def clear_converter_files_list(self):
        """Очистка списка файлов для конвертации."""
        return self.file_handler.clear_converter_files_list()
    
    def setup_converter_drag_drop(self, list_frame, tree, tab_frame):
        """Настройка drag and drop для вкладки конвертации."""
        return self.drag_drop.setup_drag_drop(list_frame, tree, tab_frame)
    
    def on_drop_converter_files(self, event):
        """Обработка перетаскивания файлов на вкладку конвертации."""
        return self.drag_drop.on_drop_files(event)
    
    def show_converter_context_menu(self, event):
        """Показ контекстного меню для файла в конвертации."""
        return self.context_menu.show_context_menu(event)
    
    def open_converter_file(self):
        """Открытие файла конвертации в программе по умолчанию."""
        return self.context_menu.open_file()
    
    def open_converter_file_folder(self):
        """Открытие папки с выбранным файлом конвертации."""
        return self.context_menu.open_file_folder()
    
    def copy_converter_file_path(self):
        """Копирование пути файла конвертации в буфер обмена."""
        return self.context_menu.copy_file_path()
    
    def remove_selected_converter_files(self):
        """Удаление выбранных файлов из списка конвертации."""
        if not hasattr(self.app, 'converter_tree'):
            return
        
        selected_items = self.app.converter_tree.selection()
        if not selected_items:
            return
        
        files_to_remove = []
        for item in selected_items:
            values = self.app.converter_tree.item(item, 'values')
            if values and len(values) > 0:
                files_to_remove.append(values[0])
        
        if hasattr(self.app, 'converter_files'):
            self.app.converter_files = [f for f in self.app.converter_files 
                                        if os.path.basename(f.get('path', '')) not in files_to_remove]
        
        self.filter_converter_files_by_type()
        self.app.log(f"Удалено файлов из списка конвертации: {len(files_to_remove)}")

"""Основной класс управления списком файлов."""

import logging
from tkinter import messagebox

logger = logging.getLogger(__name__)


class FileListManager:
    """Класс для управления списком файлов и их отображением."""
    
    def __init__(self, app) -> None:
        """Инициализация менеджера списка файлов.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
        
        # Инициализируем подмодули
        from .file_adder import FileAdder
        from .file_operations import FileOperations
        from .import_export import ImportExportManager
        from .treeview import TreeViewManager
        
        self.file_adder = FileAdder(app)
        self.file_operations = FileOperations(app)
        self.import_export = ImportExportManager(app)
        self.treeview = TreeViewManager(app)
    
    def refresh_treeview(self) -> None:
        """Обновление таблицы для синхронизации с списком файлов."""
        self.treeview.refresh_treeview()
    
    def add_files(self) -> None:
        """Добавление файлов через диалог выбора."""
        self.file_adder.add_files()
    
    def add_folder(self) -> None:
        """Добавление папки в список."""
        self.file_adder.add_folder()
    
    def add_file(self, file_path: str) -> bool:
        """Добавление одного файла в список."""
        return self.file_adder.add_file(file_path)
    
    def add_folder_item(self, folder_path: str) -> bool:
        """Добавление папки как отдельного элемента в список."""
        return self.file_adder.add_folder_item(folder_path)
    
    def clear_files(self) -> None:
        """Очистка списка файлов."""
        if self.app.files:
            if messagebox.askyesno("Подтверждение", "Очистить список файлов?"):
                files_count = len(self.app.files)
                if hasattr(self.app, 'state') and self.app.state:
                    self.app.state.files.clear()
                else:
                    if hasattr(self.app, '_files_compat'):
                        self.app._files_compat.clear()
                    elif hasattr(self.app, '_get_files_list'):
                        files_list = self.app._get_files_list()
                        files_list.clear()
                
                for item in self.app.tree.get_children():
                    self.app.tree.delete(item)
                
                self.update_status()
                self.app.log("Список файлов очищен")
    
    def delete_selected(self) -> None:
        """Удаление выбранных файлов из списка."""
        selected = self.app.tree.selection()
        if not selected:
            return
        
        indices = sorted(
            [self.app.tree.index(item) for item in selected],
            reverse=True
        )
        for index in indices:
            if index >= 0 and index < len(self.app.files):
                self.app.files.pop(index)
        
        self.refresh_treeview()
        self.update_status()
        self.app.log(f"Удалено файлов: {len(selected)}")
    
    def select_all(self) -> None:
        """Выделение всех файлов."""
        all_items = self.app.tree.get_children()
        self.app.tree.selection_set(all_items)
    
    def deselect_all(self) -> None:
        """Снятие выделения со всех файлов."""
        self.app.tree.selection_set(())
    
    def apply_to_selected(self) -> None:
        """Применение методов только к выбранным файлам."""
        self.file_operations.apply_to_selected()
    
    def show_file_context_menu(self, event) -> None:
        """Показ контекстного меню для файла."""
        self.file_operations.show_file_context_menu(event)
    
    def open_file(self) -> None:
        """Открытие выбранного файла в системе."""
        self.file_operations.open_file()
    
    def open_file_folder(self) -> None:
        """Открытие папки с выбранным файлом."""
        self.file_operations.open_file_folder()
    
    def rename_file_manually(self) -> None:
        """Ручное переименование выбранного файла."""
        self.file_operations.rename_file_manually()
    
    def copy_file_path(self) -> None:
        """Копирование пути файла в буфер обмена."""
        self.file_operations.copy_file_path()
    
    def update_status(self) -> None:
        """Обновление статусной строки."""
        self.treeview.update_status()
    
    def export_files_list(self) -> None:
        """Экспорт списка файлов в файл."""
        self.import_export.export_files_list()
    
    def import_files_list(self) -> None:
        """Импорт списка файлов из файла."""
        self.import_export.import_files_list()
    
    def sort_column(self, col: str) -> None:
        """Сортировка по колонке."""
        self.treeview.sort_column(col)
    
    def create_treeview(self, parent) -> None:
        """Создание Treeview виджета для отображения списка файлов.
        
        Args:
            parent: Родительский контейнер для списка файлов
        """
        self.treeview.create_treeview(parent)


"""Основной класс управления списком файлов."""

import logging
from PyQt6.QtWidgets import QMessageBox

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
        from .treeview import TreeViewManager
        
        self.file_adder = FileAdder(app)
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
        """Добавление одного файла в список.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            True если файл добавлен, False в противном случае
        """
        return self.file_adder.add_file(file_path)
    
    def add_folder_item(self, folder_path: str) -> bool:
        """Добавление папки как отдельного элемента в список.
        
        Args:
            folder_path: Путь к папке
            
        Returns:
            True если папка добавлена, False в противном случае
        """
        return self.file_adder.add_folder_item(folder_path)
    
    def clear_files(self) -> None:
        """Очистка списка файлов."""
        if not hasattr(self.app, 'tree') or not self.app.tree:
            if hasattr(self.app, 'files'):
                self.app.files.clear()
            return
        
        if self.app.files:
            reply = QMessageBox.question(
                None,
                "Подтверждение",
                "Очистить список файлов?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                files_count = len(self.app.files)
                if hasattr(self.app, 'state') and self.app.state:
                    self.app.state.files.clear()
                else:
                    self.app.files.clear()
                
                self.app.tree.clear()
                self.update_status()
                logger.info(f"Список файлов очищен: удалено {files_count} файлов")
    
    def update_status(self) -> None:
        """Обновление статуса списка файлов."""
        self.refresh_treeview()


"""Модуль отображения списка файлов в QTreeWidget."""

import logging
import os
from typing import Optional
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


class TreeViewManager:
    """Класс для управления отображением списка файлов в QTreeWidget."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def create_treeview(self) -> QTreeWidget:
        """Создание QTreeWidget для отображения списка файлов.
        
        Returns:
            QTreeWidget: Виджет дерева файлов
        """
        tree = QTreeWidget()
        tree.setHeaderLabels(["Имя файла", "Старое имя", "Новое имя", "Путь"])
        tree.setAlternatingRowColors(True)
        tree.setRootIsDecorated(False)
        tree.header().setStretchLastSection(True)
        tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        return tree
    
    def refresh_treeview(self) -> None:
        """Обновление таблицы для синхронизации с списком файлов."""
        if not hasattr(self.app, 'tree') or not self.app.tree:
            return
        
        tree = self.app.tree
        tree.clear()
        
        # Получаем список файлов
        files = []
        if hasattr(self.app, 'state') and self.app.state:
            files = self.app.state.files
        elif hasattr(self.app, 'files'):
            files = self.app.files
        else:
            return
        
        # Добавляем файлы в дерево
        for file_data in files:
            item = QTreeWidgetItem(tree)
            
            # Получаем данные файла
            if hasattr(file_data, 'old_name'):
                old_name = file_data.old_name or ''
                new_name = file_data.new_name if hasattr(file_data, 'new_name') and file_data.new_name else old_name
                extension = file_data.extension or ''
                full_path = file_data.full_path or (str(file_data.path) if hasattr(file_data, 'path') else '')
            else:
                old_name = file_data.get('old_name', '')
                new_name = file_data.get('new_name', old_name)
                extension = file_data.get('extension', '')
                full_path = file_data.get('full_path', '')
            
            # Устанавливаем значения колонок
            item.setText(0, os.path.basename(full_path) if full_path else old_name)
            item.setText(1, old_name)
            item.setText(2, new_name)
            if tree.columnCount() > 3:
                item.setText(3, "Готово" if new_name != old_name else "")
            
            # Сохраняем путь к файлу в данных элемента
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)
        
        # Обновляем заголовок
        if hasattr(self.app, 'files_label'):
            count = len(files)
            self.app.files_label.setText(f"Список файлов (Файлов: {count})")
    
    def update_status(self) -> None:
        """Обновление статуса (для совместимости)."""
        self.refresh_treeview()


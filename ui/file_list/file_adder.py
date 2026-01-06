"""Модуль добавления файлов и папок в список."""

import logging
import os
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from utils.path_processing import normalize_path

logger = logging.getLogger(__name__)


class FileAdder:
    """Класс для добавления файлов и папок в список."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def _get_files_list(self):
        """Получить список файлов из state или app.files.
        
        Returns:
            Список файлов
        """
        if hasattr(self.app, 'state') and self.app.state:
            return self.app.state.files
        elif hasattr(self.app, 'files'):
            return self.app.files
        else:
            # Инициализируем пустой список, если его нет
            if not hasattr(self.app, 'files'):
                self.app.files = []
            return self.app.files
    
    def _set_files_list(self, files):
        """Установить список файлов в state или app.files.
        
        Args:
            files: Список файлов
        """
        if hasattr(self.app, 'state') and self.app.state:
            self.app.state.files = files
        else:
            self.app.files = files
    
    def add_files(self) -> None:
        """Добавление файлов через диалог выбора."""
        files, _ = QFileDialog.getOpenFileNames(
            None,
            "Выберите файлы",
            "",
            "Все файлы (*.*);;"
            "Изображения (*.png *.jpg *.jpeg *.ico *.webp *.gif *.pdf);;"
            "Документы (*.pdf *.doc *.docx *.odt);;"
            "Презентации (*.pptx *.ppt *.odp)"
        )
        if files:
            # Проверка на максимальное количество файлов
            try:
                from config.constants import MAX_FILES_IN_LIST
                # Получаем список файлов из state или app.files
                files_list = self._get_files_list()
                current_count = len(files_list)
                if current_count >= MAX_FILES_IN_LIST:
                    QMessageBox.warning(
                        None,
                        "Превышен лимит",
                        f"Достигнут максимальный лимит файлов в списке ({MAX_FILES_IN_LIST}).\n"
                        f"Удалите некоторые файлы перед добавлением новых."
                    )
                    return
                remaining_slots = MAX_FILES_IN_LIST - current_count
                if len(files) > remaining_slots:
                    reply = QMessageBox.question(
                        None,
                        "Превышение лимита",
                        f"Вы пытаетесь добавить {len(files)} файлов, но доступно только {remaining_slots} слотов.\n"
                        f"Добавить только первые {remaining_slots} файлов?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        return
                    files = files[:remaining_slots]
            except ImportError:
                pass
            
            files_list = self._get_files_list()
            files_before = len(files_list)
            added_files = []
            skipped_files = []
            
            for file_path in files:
                result = self.add_file(file_path)
                if result:
                    added_files.append(file_path)
                else:
                    skipped_files.append(file_path)
            
            # Обновляем интерфейс
            if hasattr(self.app, 'file_list_manager'):
                self.app.file_list_manager.refresh_treeview()
                self.app.file_list_manager.update_status()
            
            files_list = self._get_files_list()
            actual_count = len(files_list) - files_before
            if actual_count > 0:
                logger.info(f"Добавлено файлов: {actual_count}")
    
    def add_folder(self) -> None:
        """Добавление папки в список."""
        folder = QFileDialog.getExistingDirectory(None, "Выберите папку")
        if folder:
            if self.add_folder_item(folder):
                if hasattr(self.app, 'file_list_manager'):
                    self.app.file_list_manager.refresh_treeview()
                    self.app.file_list_manager.update_status()
                logger.info(f"Добавлена папка: {folder}")
    
    def add_folder_item(self, folder_path: str) -> bool:
        """Добавление папки как отдельного элемента в список.
        
        Args:
            folder_path: Путь к папке
            
        Returns:
            True если папка добавлена, False в противном случае
        """
        try:
            normalized_path = normalize_path(folder_path)
            if not os.path.exists(normalized_path) or not os.path.isdir(normalized_path):
                return False
            
            # Проверка на дубликаты
            files_list = self._get_files_list()
            for file_data in files_list:
                    if hasattr(file_data, 'full_path'):
                        if file_data.full_path == normalized_path:
                            return False
                    elif isinstance(file_data, dict):
                        if file_data.get('full_path') == normalized_path:
                            return False
            
            # Добавляем папку
            from core.domain.file_info import FileInfo
            try:
                file_info = FileInfo.from_path(normalized_path)
                file_info.metadata = file_info.metadata or {}
                file_info.metadata['is_folder'] = True
                
                files_list = self._get_files_list()
                files_list.append(file_info)
                
                return True
            except Exception as e:
                logger.error(f"Ошибка при создании FileInfo для папки {normalized_path}: {e}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при добавлении папки {folder_path}: {e}")
            return False
    
    def add_file(self, file_path: str) -> bool:
        """Добавление одного файла в список.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            True если файл добавлен, False в противном случае
        """
        try:
            normalized_path = normalize_path(file_path)
            if not os.path.exists(normalized_path) or not os.path.isfile(normalized_path):
                return False
            
            # Проверка на дубликаты
            files_list = self._get_files_list()
            for file_data in files_list:
                    if hasattr(file_data, 'full_path'):
                        if file_data.full_path == normalized_path:
                            return False
                    elif isinstance(file_data, dict):
                        if file_data.get('full_path') == normalized_path:
                            return False
            
            # Добавляем файл
            from core.domain.file_info import FileInfo
            try:
                file_info = FileInfo.from_path(normalized_path)
                
                files_list = self._get_files_list()
                files_list.append(file_info)
                
                return True
            except Exception as e:
                logger.error(f"Ошибка при создании FileInfo для файла {normalized_path}: {e}")
                return False
        except Exception as e:
            logger.error(f"Ошибка при добавлении файла {file_path}: {e}")
            return False


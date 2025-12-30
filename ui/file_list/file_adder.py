"""Модуль добавления файлов и папок в список."""

import logging
import os
from pathlib import Path
from tkinter import filedialog, messagebox

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
    
    def add_files(self) -> None:
        """Добавление файлов через диалог выбора."""
        files = filedialog.askopenfilenames(
            title="Выберите файлы",
            filetypes=[
                ("Все файлы", "*.*"),
                (
                    "Изображения",
                    "*.png *.jpg *.jpeg *.ico *.webp *.gif *.pdf"
                ),
                (
                    "Документы",
                    "*.pdf *.doc *.docx *.odt"
                ),
                (
                    "Презентации",
                    "*.pptx *.ppt *.odp"
                ),
            ]
        )
        if files:
            files_before = len(self.app.files)
            added_files = []
            skipped_files = []
            for file_path in files:
                result = self.add_file(file_path)
                if result:
                    added_files.append(file_path)
                else:
                    skipped_files.append(file_path)
                    logger.debug(f"Файл не добавлен: {file_path}")
            # Применяем методы (включая шаблон), если они есть
            if self.app.methods_manager.get_methods():
                self.app.apply_methods()
            else:
                # Если есть шаблон в поле, но нет метода, применяем шаблон
                if hasattr(self.app, 'new_name_template'):
                    template = self.app.new_name_template.get().strip()
                    if template:
                        if hasattr(self.app, 'ui_templates_manager'):
                            self.app.ui_templates_manager.apply_template_quick(auto=True)
            # Обновляем интерфейс
            self.app.file_list_manager.refresh_treeview()
            self.app.file_list_manager.update_status()
            actual_count = len(self.app.files) - files_before
            if skipped_files:
                self.app.log(f"Добавлено файлов: {actual_count}, пропущено: {len(skipped_files)}")
            else:
                self.app.log(f"Добавлено файлов: {actual_count}")
    
    def add_folder(self) -> None:
        """Добавление папки как отдельного элемента в список."""
        folder = filedialog.askdirectory(title="Выберите папку")
        if folder:
            if self.add_folder_item(folder):
                # Применяем методы (включая шаблон), если они есть
                if self.app.methods_manager.get_methods():
                    self.app.apply_methods()
                else:
                    # Обновляем интерфейс
                    self.app.file_list_manager.refresh_treeview()
                self.app.file_list_manager.update_status()
                self.app.log(f"Добавлена папка: {folder}")
    
    def add_folder_item(self, folder_path: str) -> bool:
        """Добавление папки как элемента списка.
        
        Args:
            folder_path: Путь к папке
            
        Returns:
            True если папка добавлена, False иначе
        """
        if not os.path.isdir(folder_path):
            return False
        
        folder_path = normalize_path(folder_path)
        
        # Проверяем на дубликаты
        files_list = self.app._get_files_list()
        for existing_file in files_list:
            existing_path = None
            if hasattr(existing_file, 'full_path'):
                # Для FileInfo объектов
                if existing_file.full_path:
                    existing_path = existing_file.full_path
                else:
                    # Если full_path не установлен, собираем из path
                    try:
                        existing_path = str(existing_file.path)
                    except (AttributeError, TypeError):
                        continue
            elif isinstance(existing_file, dict):
                # Для словарей
                existing_path = existing_file.get('full_path')
                if not existing_path:
                    # Если full_path нет, используем path напрямую
                    existing_path = existing_file.get('path', '')
            
            if existing_path:
                try:
                    existing_path_normalized = normalize_path(existing_path)
                    if existing_path_normalized == folder_path:
                        return False
                except (OSError, ValueError):
                    continue
        
        logger.info(f"Добавление папки в список: {folder_path}")
        
        # Используем внутренний метод для добавления папки
        files_list = self.app._get_files_list()
        
        # Создаем запись для папки
        path_obj = Path(folder_path)
        old_name = path_obj.name
        
        # Для папок extension будет пустым, но добавим метку что это папка
        if self.app.state:
            from core.domain.file_info import FileInfo, FileStatus
            # Для FileInfo создаем объект с пустым расширением
            # Используем parent путь и имя папки
            file_info = FileInfo(
                path=path_obj,
                old_name=old_name,
                new_name=old_name,
                extension="",
                status=FileStatus.READY,
                metadata={"is_folder": True},
                full_path=folder_path
            )
            files_list.append(file_info)
        else:
            # Fallback для обратной совместимости
            file_data = {
                'path': str(path_obj.parent),
                'old_name': old_name,
                'new_name': old_name,
                'extension': "",
                'full_path': folder_path,
                'status': 'Готов',
                'is_folder': True  # Метка что это папка
            }
            files_list.append(file_data)
        
        return True
    
    def add_file(self, file_path: str) -> bool:
        """Добавление одного файла в список.
        
        Args:
            file_path: Путь к файлу для добавления
            
        Returns:
            True если файл добавлен, False иначе
        """
        if not os.path.isfile(file_path):
            return False
        
        file_path_normalized = normalize_path(file_path)
        
        # Проверяем на дубликаты
        files_list = self.app._get_files_list()
        for existing_file in files_list:
            existing_path = None
            if hasattr(existing_file, 'full_path'):
                # Для FileInfo объектов
                if existing_file.full_path:
                    existing_path = existing_file.full_path
                else:
                    # Если full_path не установлен, используем path напрямую (он уже содержит полный путь)
                    try:
                        existing_path = str(existing_file.path)
                    except (AttributeError, TypeError):
                        continue
            elif isinstance(existing_file, dict):
                # Для словарей
                existing_path = existing_file.get('full_path')
                if not existing_path:
                    # Если full_path нет, собираем из path + old_name + extension
                    dir_path = existing_file.get('path', '')
                    old_name = existing_file.get('old_name', '')
                    extension = existing_file.get('extension', '')
                    if dir_path and old_name:
                        existing_path = str(Path(dir_path) / f"{old_name}{extension}")
                    else:
                        continue
            
            if existing_path:
                try:
                    # Нормализуем оба пути для корректного сравнения
                    existing_path_str = str(existing_path)
                    existing_path_normalized = normalize_path(existing_path_str)
                    if existing_path_normalized == file_path_normalized:
                        logger.debug(f"Файл уже в списке (дубликат): {file_path_normalized}")
                        return False
                except (OSError, ValueError):
                    continue
        
        self.app.log(f"Добавление файла: {os.path.basename(file_path)}")
        
        try:
            files_list = self.app._get_files_list()
            
            if self.app.state:
                from core.domain.file_info import FileInfo
                file_info = FileInfo.from_path(file_path_normalized)
                files_list.append(file_info)
            else:
                path_obj = Path(file_path_normalized)
                old_name = path_obj.stem
                extension = path_obj.suffix
                path = str(path_obj.parent)
                
                file_data = {
                    'path': path,
                    'old_name': old_name,
                    'new_name': old_name,
                    'extension': extension,
                    'full_path': file_path_normalized,
                    'status': 'Готов'
                }
                files_list.append(file_data)
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении файла {file_path}: {e}", exc_info=True)
            self.app.log(f"Ошибка при добавлении файла {os.path.basename(file_path)}: {e}")
            return False


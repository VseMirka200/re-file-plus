"""Модуль для управления списком файлов.

Обеспечивает управление списком файлов для переименования, включая:
- Добавление/удаление файлов
- Отображение в Treeview
- Операции с файлами (открытие папки, копирование пути)
- Импорт/экспорт списка файлов (JSON, CSV)
- Сортировку и фильтрацию

ВНИМАНИЕ: Этот модуль является частью пакета приложения и не предназначен 
для прямого запуска. Запускайте приложение через файл Запуск.pyw или file_re-file-plus.py
"""

# Защита от прямого запуска модуля (должна быть ДО импортов локальных модулей)
import sys
if __name__ == "__main__":
    print("=" * 60)
    print("ОШИБКА: Этот модуль не предназначен для прямого запуска.")
    print("=" * 60)
    print("\nЭтот файл является частью пакета приложения.")
    print("Запускайте приложение через один из следующих файлов:")
    print("  - Запуск.pyw (рекомендуется)")
    print("  - file_re-file-plus.py")
    print("\nПример команды:")
    print("  python Запуск.pyw")
    print("=" * 60)
    sys.exit(1)

# Стандартная библиотека
import csv
import json
import logging
import os
import re
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

# Локальные импорты
from core.rename_methods import check_conflicts

logger = logging.getLogger(__name__)

# Импорт структурированного логирования
try:
    from utils.structured_logging import log_action, log_file_action, log_batch_action
except ImportError:
    # Fallback если модуль недоступен
    def log_action(logger, level, action, message, **kwargs):
        logger.log(level, f"[{action}] {message}")
    def log_file_action(logger, action, message, **kwargs):
        logger.info(f"[{action}] {message}")
    def log_batch_action(logger, action, message, file_count, **kwargs):
        logger.info(f"[{action}] {message} (файлов: {file_count})")


class FileListManager:
    """Класс для управления списком файлов и их отображением.
    
    Интегрируется с Treeview для отображения файлов и предоставляет
    методы для работы со списком файлов.
    """
    
    def __init__(self, app) -> None:
        """Инициализация менеджера списка файлов.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
    
    def refresh_treeview(self) -> None:
        """Обновление таблицы для синхронизации с списком файлов."""
        # Удаляем все элементы
        for item in self.app.tree.get_children():
            self.app.tree.delete(item)
        
        # Получаем текст поиска
        search_text = ""
        use_regex = False
        if hasattr(self.app, 'search_entry'):
            search_text = self.app.search_entry.get().strip()
            if hasattr(self.app, 'search_regex_var'):
                use_regex = self.app.search_regex_var.get()
        
        # Компилируем regex паттерн, если включен regex
        search_pattern = None
        if search_text and use_regex:
            try:
                search_pattern = re.compile(search_text, re.IGNORECASE)
            except re.error:
                # Если regex невалидный, используем обычный поиск
                use_regex = False
        
        # Группируем файлы по папкам
        files_by_path = {}
        for file_data in self.app.files:
            # Получаем путь к папке файла
            folder_path = None
            
            # Получаем данные файла/папки
            if hasattr(file_data, 'old_name'):
                # FileInfo объект
                full_path = file_data.full_path or str(file_data.path)
                if os.path.exists(full_path):
                    if os.path.isfile(full_path):
                        folder_path = os.path.dirname(full_path)
                    elif os.path.isdir(full_path):
                        folder_path = full_path
                else:
                    path = str(file_data.path.parent) if hasattr(file_data.path, 'parent') else str(file_data.path)
                    folder_path = os.path.dirname(path) if os.path.isfile(path) else path
            else:
                # Словарь
                full_path = file_data.get('full_path', '')
                if not full_path:
                    path = file_data.get('path', '')
                    old_name = file_data.get('old_name', '')
                    extension = file_data.get('extension', '')
                    is_folder = file_data.get('is_folder', False)
                    
                    if path:
                        if is_folder:
                            folder_path = path
                        elif old_name:
                            full_path = os.path.join(path, old_name + extension)
                            if os.path.exists(full_path) and os.path.isfile(full_path):
                                folder_path = os.path.dirname(full_path)
                            else:
                                folder_path = path
                        else:
                            folder_path = path if os.path.isdir(path) else os.path.dirname(path)
                else:
                    if os.path.exists(full_path):
                        folder_path = os.path.dirname(full_path) if os.path.isfile(full_path) else full_path
                    else:
                        folder_path = os.path.dirname(full_path)
            
            # Нормализуем путь
            if folder_path:
                folder_path = os.path.normpath(os.path.abspath(folder_path))
                if folder_path not in files_by_path:
                    files_by_path[folder_path] = []
                files_by_path[folder_path].append(file_data)
        
        # Сортируем пути для консистентного отображения
        sorted_paths = sorted(files_by_path.keys())
        
        # Добавляем файлы, группируя по папкам
        for folder_path in sorted_paths:
            files_in_folder = files_by_path[folder_path]
            
            # Вставляем строку с путем перед группой файлов
            path_text = folder_path
            self.app.tree.insert("", tk.END, values=(path_text, ""), tags=('path_row',))
            
            # Добавляем файлы из этой папки
            for file_data in files_in_folder:
                # Получаем данные файла/папки
                if hasattr(file_data, 'old_name'):
                    # FileInfo объект
                    old_name = file_data.old_name
                    new_name = file_data.new_name
                    extension = file_data.extension
                    full_path = file_data.full_path or str(file_data.path)
                    # Проверяем, является ли это папкой
                    is_folder = (file_data.metadata and file_data.metadata.get('is_folder', False)) or (
                        not extension and os.path.isdir(full_path) if os.path.exists(full_path) else False
                    )
                else:
                    # Словарь
                    old_name = file_data.get('old_name', '')
                    new_name = file_data.get('new_name', '')
                    extension = file_data.get('extension', '')
                    full_path = file_data.get('full_path', '')
                    # Проверяем, является ли это папкой
                    is_folder = file_data.get('is_folder', False) or (
                        not extension and full_path and os.path.isdir(full_path) if os.path.exists(full_path) else False
                    )
                
                # Фильтрация по поисковому запросу
                if search_text:
                    if use_regex and search_pattern:
                        # Поиск по regex
                        full_text = f"{old_name} {new_name} {folder_path} {extension}"
                        if not search_pattern.search(full_text):
                            continue
                    else:
                        # Обычный поиск
                        search_lower = search_text.lower()
                        old_name_lower = old_name.lower()
                        new_name_lower = new_name.lower()
                        path_lower = folder_path.lower()
                        extension_lower = extension.lower()
                        
                        if (search_lower not in old_name_lower and 
                            search_lower not in new_name_lower and 
                            search_lower not in path_lower and 
                            search_lower not in extension_lower):
                            continue
                
                # Убрана подцветка статуса - теги не используются
                tags = ()
                
                # Формируем полные имена с расширениями для отображения
                # Если new_name не установлен, используем old_name
                if not new_name:
                    new_name = old_name
                
                # Для папок добавляем метку [Папка]
                folder_label = " [Папка]" if is_folder else ""
                old_full_name = f"{old_name}{extension}" if extension else old_name
                new_full_name = f"{new_name}{extension}" if extension else new_name
                
                # Добавляем метку только для старого имени, чтобы показать что это папка
                old_display_name = f"{old_full_name}{folder_label}"
                new_display_name = new_full_name  # Новое имя без метки
                
                self.app.tree.insert("", tk.END, values=(
                    old_display_name,
                    new_display_name
                ), tags=tags)
        
        # Обновляем видимость скроллбаров после обновления содержимого
        if (hasattr(self.app, 'tree_scrollbar_y') and
                hasattr(self.app, 'tree_scrollbar_x')):
            self.app.root.after_idle(
                lambda: self.app.update_scrollbar_visibility(
                    self.app.tree,
                    self.app.tree_scrollbar_y,
                    'vertical'
                )
            )
            self.app.root.after_idle(
                lambda: self.app.update_scrollbar_visibility(
                    self.app.tree,
                    self.app.tree_scrollbar_x,
                    'horizontal'
                )
            )
        
        # Пути теперь вставляются прямо в refresh_treeview, дополнительное обновление не нужно
    
    def add_files(self) -> None:
        """Добавление файлов через диалог выбора."""
        logger.info("Открыт диалог выбора файлов")
        files = filedialog.askopenfilenames(
            title="Выберите файлы",
            filetypes=[
                ("Все файлы", "*.*"),
                (
                    "Изображения",
                    "*.jpg *.jpeg *.png *.gif *.bmp *.webp *.tiff *.tif "
                    "*.ico *.svg *.heic *.heif *.avif *.dng *.cr2 *.nef *.raw"
                ),
                (
                    "Документы",
                    "*.pdf *.docx *.doc *.xlsx *.xls *.pptx *.ppt *.txt "
                    "*.rtf *.csv *.html *.htm *.odt *.ods *.odp"
                ),
                (
                    "Аудио",
                    "*.mp3 *.wav *.flac *.aac *.ogg *.m4a *.wma *.opus"
                ),
                (
                    "Видео",
                    "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v "
                    "*.mpg *.mpeg *.3gp"
                ),
            ]
        )
        if files:
            log_batch_action(
                logger=logger,
                action='FILES_SELECTED',
                message=f"Выбрано файлов для добавления: {len(files)}",
                file_count=len(files),
                method_name='add_files'
            )
            files_before = len(self.app.files)
            added_files = []
            for file_path in files:
                if self.add_file(file_path):
                    added_files.append(file_path)
            # Применяем методы (включая шаблон), если они есть
            if self.app.methods_manager.get_methods():
                log_action(
                    logger=logger,
                    level=logging.INFO,
                    action='METHODS_APPLIED',
                    message="Применяются методы переименования к добавленным файлам",
                    method_name='add_files',
                    file_count=len(added_files)
                )
                self.app.apply_methods()
            else:
                # Обновляем интерфейс
                self.refresh_treeview()
            self.update_status()
            actual_count = len(self.app.files) - files_before
            log_batch_action(
                logger=logger,
                action='FILES_ADDED',
                message=f"Добавлено файлов в список: {actual_count}",
                file_count=actual_count,
                method_name='add_files',
                success_count=actual_count
            )
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
                    self.refresh_treeview()
                self.update_status()
                self.app.log(f"Добавлена папка: {folder}")
    
    def add_folder_item(self, folder_path: str) -> bool:
        """Добавление папки как отдельного элемента в список.
        
        Args:
            folder_path: Путь к папке для добавления
            
        Returns:
            True если папка добавлена, False иначе
        """
        if not os.path.isdir(folder_path):
            logger.debug(
                f"Попытка добавить несуществующую папку: {folder_path}"
            )
            return False
        
        # Нормализуем путь для проверки дубликатов
        folder_path = os.path.normpath(os.path.abspath(folder_path))
        
        # Проверяем, нет ли уже такой папки в списке
        files_list_check = self.app._get_files_list()
        for existing_file in files_list_check:
            # Поддержка как FileInfo, так и словарей
            if hasattr(existing_file, 'full_path'):
                # FileInfo объект
                existing_path = existing_file.full_path
            elif isinstance(existing_file, dict):
                # Словарь
                existing_path = (
                    existing_file.get('full_path') or
                    existing_file.get('path', '')
                )
            else:
                continue
            
            if existing_path:
                existing_path = os.path.normpath(
                    os.path.abspath(existing_path)
                )
            else:
                continue
            if existing_path == folder_path:
                # Папка уже есть в списке, пропускаем
                logger.debug(
                    f"Папка уже в списке, пропущена: {folder_path}"
                )
                return False
        
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
            logger.debug(
                f"Попытка добавить несуществующий файл: {file_path}"
            )
            return False
        
        # Нормализуем путь для проверки дубликатов
        file_path = os.path.normpath(os.path.abspath(file_path))
        
        # Проверяем, нет ли уже такого файла в списке
        files_list_check = self.app._get_files_list()
        for existing_file in files_list_check:
            # Поддержка как FileInfo, так и словарей
            if hasattr(existing_file, 'full_path'):
                # FileInfo объект
                existing_path = existing_file.full_path
            elif isinstance(existing_file, dict):
                # Словарь
                existing_path = (
                    existing_file.get('full_path') or
                    existing_file.get('path', '')
                )
            else:
                continue
            
            if existing_path:
                existing_path = os.path.normpath(
                    os.path.abspath(existing_path)
                )
            else:
                continue
            if existing_path == file_path:
                # Файл уже есть в списке, пропускаем
                logger.debug(
                    f"Файл уже в списке, пропущен: {file_path}"
                )
                return False
        
        logger.info(f"Добавление файла в список: {file_path}")
        self.app.log(f"Добавление файла: {os.path.basename(file_path)}")
        
        # Используем внутренний метод для добавления файла
        # чтобы обойти проблему с property
        files_list = self.app._get_files_list()
        files_count_before = len(files_list)
        
        # Если state доступен, создаем FileInfo объект, иначе словарь
        if self.app.state:
            from core.domain.file_info import FileInfo
            file_info = FileInfo.from_path(file_path)
            files_list.append(file_info)
        else:
            # Fallback для обратной совместимости
            path_obj = Path(file_path)
            old_name = path_obj.stem
            extension = path_obj.suffix
            path = str(path_obj.parent)
            
            file_data = {
                'path': path,
                'old_name': old_name,
                'new_name': old_name,
                'extension': extension,
                'full_path': file_path,
                'status': 'Готов'
            }
            files_list.append(file_data)
        
        files_count_after = len(files_list)
        logger.info(f"Файл добавлен. Было файлов: {files_count_before}, стало: {files_count_after}")
        
        # Пути теперь вставляются прямо в refresh_treeview, дополнительное обновление не нужно
        
        return True
    
    def clear_files(self) -> None:
        """Очистка списка файлов."""
        if self.app.files:
            if messagebox.askyesno("Подтверждение", "Очистить список файлов?"):
                files_count = len(self.app.files)
                log_batch_action(
                    logger=logger,
                    action='FILES_CLEARED',
                    message=f"Очистка списка файлов",
                    file_count=files_count,
                    method_name='clear_files'
                )
                # ВАЖНО: Очищаем state.files напрямую, а не через property
                # так как property возвращает копию списка, и clear() очищает только копию
                if hasattr(self.app, 'state') and self.app.state:
                    # Очищаем state.files напрямую
                    self.app.state.files.clear()
                else:
                    # Fallback для обратной совместимости
                    if hasattr(self.app, '_files_compat'):
                        self.app._files_compat.clear()
                    elif hasattr(self.app, '_get_files_list'):
                        # Используем внутренний метод для получения реального списка
                        files_list = self.app._get_files_list()
                        files_list.clear()
                
                # Очищаем дерево
                for item in self.app.tree.get_children():
                    self.app.tree.delete(item)
                
                # Обновляем статус
                self.update_status()
                self.app.log("Список файлов очищен")
    
    def delete_selected(self) -> None:
        """Удаление выбранных файлов из списка."""
        selected = self.app.tree.selection()
        if selected:
            # Фильтруем строку с путем (нельзя удалять)
            selected = [item for item in selected 
                       if 'path_row' not in self.app.tree.item(item, 'tags')]
            
            if not selected:
                return
            
            deleted_files = []
            # Сортируем индексы в обратном порядке для корректного удаления
            indices = sorted(
                [self.app.tree.index(item) for item in selected],
                reverse=True
            )
            for index in indices:
                # Учитываем, что строка с путем всегда на позиции 0
                # Корректируем индекс для списка файлов
                file_index = index - 1 if index > 0 else 0
                
                if file_index >= 0 and file_index < len(self.app.files):
                    file_data = self.app.files[file_index]
                    deleted_files.append(file_data.get('path', ''))
                    self.app.files.pop(file_index)
                
                # Удаляем из дерева
                item = selected[indices.index(index)]
                self.app.tree.delete(item)
            self.refresh_treeview()
            self.update_status()
            # Пути теперь вставляются прямо в refresh_treeview, дополнительное обновление не нужно
            log_batch_action(
                logger=logger,
                action='FILES_DELETED',
                message=f"Удалено файлов из списка: {len(selected)}",
                file_count=len(selected),
                method_name='delete_selected',
                details={'deleted_files': deleted_files[:5]}
            )
            self.app.log(f"Удалено файлов: {len(selected)}")
    
    def select_all(self) -> None:
        """Выделение всех файлов."""
        # Исключаем строку с путем из выделения
        all_items = self.app.tree.get_children()
        items_to_select = [item for item in all_items 
                          if 'path_row' not in self.app.tree.item(item, 'tags')]
        self.app.tree.selection_set(items_to_select)
    
    def deselect_all(self) -> None:
        """Снятие выделения со всех файлов."""
        self.app.tree.selection_set(())
    
    def apply_to_selected(self) -> None:
        """Применение методов только к выбранным файлам."""
        selected = self.app.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите файлы для применения методов")
            return
        
        # Получаем индексы выбранных файлов
        selected_indices = [
            self.app.tree.index(item) for item in selected
        ]
        selected_files = [
            self.app.files[i]
            for i in selected_indices
            if i < len(self.app.files)
        ]
        
        if not selected_files:
            return
        
        # Применяем методы только к выбранным файлам
        for file_data in selected_files:
            try:
                from core.rename_methods import validate_filename
                
                new_name, extension = self.app.methods_manager.apply_methods(
                    file_data.get('old_name', ''),
                    file_data.get('extension', ''),
                    file_data.get('full_path') or file_data.get('path', '')
                )
                file_data['new_name'] = new_name
                file_data['extension'] = extension
                
                # Валидация
                file_path = file_data.get('path') or file_data.get('full_path', '')
                status = validate_filename(new_name, extension, file_path, 0)
                file_data['status'] = status
            except Exception as e:
                file_data['status'] = f"Ошибка: {str(e)}"
                logger.error(f"Ошибка применения методов к файлу: {e}", exc_info=True)
        
        # Проверка конфликтов
        check_conflicts(selected_files)
        self.refresh_treeview()
        self.app.log(f"Методы применены к {len(selected_files)} выбранным файлам")
    
    def show_file_context_menu(self, event) -> None:
        """Показ контекстного меню для файла."""
        item = self.app.tree.identify_row(event.y)
        if not item:
            return
        
        # Игнорируем строку с путем (не показываем меню)
        tags = self.app.tree.item(item, 'tags')
        if tags and 'path_row' in tags:
            return
        
        # Выделяем элемент, если он не выделен
        if item not in self.app.tree.selection():
            self.app.tree.selection_set(item)
        
        # Создаем контекстное меню
        context_menu = tk.Menu(
            self.app.root,
            tearoff=0,
            bg=self.app.colors.get('bg_card', '#ffffff'),
            fg=self.app.colors.get('text_primary', '#000000'),
            activebackground=self.app.colors.get('primary', '#4a90e2'),
            activeforeground='white'
        )
        
        context_menu.add_command(label="Удалить из списка", command=self.delete_selected)
        context_menu.add_separator()
        context_menu.add_command(label="Открыть файл", command=self.open_file)
        context_menu.add_command(label="Открыть папку", command=self.open_file_folder)
        context_menu.add_command(label="Переименовать вручную", command=self.rename_file_manually)
        context_menu.add_separator()
        context_menu.add_command(label="Копировать путь", command=self.copy_file_path)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def open_file(self) -> None:
        """Открытие файла в программе по умолчанию."""
        selected_items = self.app.tree.selection()
        if not selected_items:
            return
        
        # Фильтруем строку с путем
        selected_items = [item for item in selected_items 
                        if 'path_row' not in self.app.tree.item(item, 'tags')]
        
        if not selected_items:
            return
        
        for item in selected_items:
            values = self.app.tree.item(item, 'values')
            if not values or len(values) < 1:
                continue
            
            old_name = values[0]
            # Находим файл в списке
            file_info = None
            for f in self.app.files:
                if f.get('old_name') == old_name:
                    file_info = f
                    break
            
            if file_info:
                # Используем full_path если есть, иначе собираем путь из компонентов
                file_path = file_info.get('full_path', '')
                if not file_path:
                    # Собираем путь из компонентов
                    path = file_info.get('path', '')
                    old_name = file_info.get('old_name', '')
                    extension = file_info.get('extension', '')
                    if path and old_name:
                        file_path = os.path.join(path, old_name + extension)
                
                if file_path and os.path.exists(file_path) and os.path.isfile(file_path):
                    try:
                        if sys.platform == 'win32':
                            os.startfile(file_path)
                        elif sys.platform == 'darwin':
                            subprocess.Popen(['open', file_path])
                        else:
                            subprocess.Popen(['xdg-open', file_path])
                    except Exception as e:
                        logger.error(f"Ошибка открытия файла {file_path}: {e}", exc_info=True)
                        self.app.log(f"Не удалось открыть файл: {file_path}")
    
    def open_file_folder(self) -> None:
        """Открытие папки с выбранным файлом."""
        selected = self.app.tree.selection()
        if not selected:
            return
        
        # Фильтруем строку с путем
        selected = [item for item in selected 
                   if 'path_row' not in self.app.tree.item(item, 'tags')]
        
        if not selected:
            return
        
        try:
            import platform
            
            item = selected[0]
            index = self.app.tree.index(item)
            # Учитываем, что строка с путем всегда на позиции 0
            file_index = index - 1 if index > 0 else 0
            if file_index >= 0 and file_index < len(self.app.files):
                file_data = self.app.files[file_index]
                file_path = file_data.get('full_path') or file_data.get('path', '')
                if file_path:
                    folder_path = os.path.dirname(file_path)
                    if platform.system() == 'Windows':
                        subprocess.Popen(f'explorer "{folder_path}"')
                    elif platform.system() == 'Darwin':
                        subprocess.Popen(['open', folder_path])
                    else:
                        subprocess.Popen(['xdg-open', folder_path])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть папку:\n{str(e)}")
            logger.error(f"Ошибка открытия папки: {e}", exc_info=True)
    
    def rename_file_manually(self) -> None:
        """Ручное переименование выбранного файла."""
        selected = self.app.tree.selection()
        if not selected:
            return
        
        item = selected[0]
        index = self.app.tree.index(item)
        # Учитываем, что строка с путем всегда на позиции 0
        file_index = index - 1 if index > 0 else 0
        if file_index < 0 or file_index >= len(self.app.files):
            return
        
        file_data = self.app.files[file_index]
        old_name = file_data.get('old_name', '')
        extension = file_data.get('extension', '')
        
        new_name = simpledialog.askstring(
            "Переименовать файл",
            f"Введите новое имя для файла:",
            initialvalue=old_name
        )
        
        if new_name and new_name.strip():
            new_name = new_name.strip()
            file_data['new_name'] = new_name
            file_data['extension'] = extension
            self.refresh_treeview()
            self.app.log(f"Имя файла изменено вручную: {old_name} -> {new_name}")
    
    def copy_file_path(self) -> None:
        """Копирование пути файла в буфер обмена."""
        selected = self.app.tree.selection()
        if not selected:
            return
        
        # Фильтруем строку с путем
        selected = [item for item in selected 
                   if 'path_row' not in self.app.tree.item(item, 'tags')]
        
        if not selected:
            return
        
        try:
            item = selected[0]
            index = self.app.tree.index(item)
            # Учитываем, что строка с путем всегда на позиции 0
            file_index = index - 1 if index > 0 else 0
            if file_index >= 0 and file_index < len(self.app.files):
                file_data = self.app.files[file_index]
                file_path = file_data.get('full_path') or file_data.get('path', '')
                if file_path:
                    self.app.root.clipboard_clear()
                    self.app.root.clipboard_append(file_path)
                    self.app.log(f"Путь скопирован в буфер обмена: {file_path}")
        except Exception as e:
            logger.error(f"Ошибка копирования пути: {e}", exc_info=True)
    
    def update_status(self) -> None:
        """Обновление статусной строки."""
        count = len(self.app.files)
        if hasattr(self.app, 'left_panel'):
            self.app.left_panel.config(text=f"Список файлов (Файлов: {count})")
    
    def export_files_list(self) -> None:
        """Экспорт списка файлов в файл."""
        if not self.app.files:
            messagebox.showwarning("Предупреждение", "Список файлов пуст")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON файлы", "*.json"),
                ("CSV файлы", "*.csv"),
                ("Все файлы", "*.*")
            ],
            title="Экспорт списка файлов"
        )
        
        if not filename:
            return
        
        try:
            if filename.endswith('.csv'):
                # Экспорт в CSV
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'Старое имя',
                        'Новое имя',
                        'Расширение',
                        'Путь',
                        'Статус'
                    ])
                    for file_data in self.app.files:
                        writer.writerow([
                            file_data.get('old_name', ''),
                            file_data.get('new_name', ''),
                            file_data.get('path', ''),
                            file_data.get('status', 'Готов')
                        ])
            else:
                # Экспорт в JSON
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(
                        self.app.files,
                        f,
                        ensure_ascii=False,
                        indent=2
                    )
            
            messagebox.showinfo(
                "Успех",
                f"Список файлов экспортирован в:\n{filename}"
            )
            self.app.log(f"Список файлов экспортирован: {filename}")
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось экспортировать список файлов:\n{str(e)}"
            )
            logger.error(
                f"Ошибка экспорта списка файлов: {e}",
                exc_info=True
            )
    
    def import_files_list(self) -> None:
        """Импорт списка файлов из файла."""
        filename = filedialog.askopenfilename(
            filetypes=[
                ("JSON файлы", "*.json"),
                ("CSV файлы", "*.csv"),
                ("Все файлы", "*.*")
            ],
            title="Импорт списка файлов"
        )
        
        if not filename:
            return
        
        try:
            imported_files = []
            
            if filename.endswith('.csv'):
                # Импорт из CSV
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        file_path = row.get('Путь', '')
                        if file_path and os.path.exists(file_path) and os.path.isfile(file_path):
                            file_data = {
                                'path': file_path,
                                'full_path': file_path,
                                'old_name': row.get('Старое имя', ''),
                                'new_name': row.get('Новое имя', ''),
                                'extension': row.get('Расширение', ''),
                                'status': row.get('Статус', 'Готов')
                            }
                            imported_files.append(file_data)
            else:
                # Импорт из JSON
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for file_data in data:
                            file_path = (
                                file_data.get('path') or
                                file_data.get('full_path', '')
                            )
                            if (file_path and
                                    os.path.exists(file_path) and
                                    os.path.isfile(file_path)):
                                imported_files.append(file_data)
            
            if imported_files:
                # Добавляем файлы в список
                for file_data in imported_files:
                    # Проверяем на дубликаты
                    is_duplicate = False
                    file_path = file_data.get('full_path') or file_data.get('path', '')
                    if file_path:
                        file_path = os.path.normpath(os.path.abspath(file_path))
                        files_list = self.app._get_files_list()
                        for existing_file in files_list:
                            # Поддержка как FileInfo, так и словарей
                            if hasattr(existing_file, 'full_path'):
                                # FileInfo объект
                                existing_path = existing_file.full_path
                            elif isinstance(existing_file, dict):
                                # Словарь
                                existing_path = existing_file.get('full_path') or existing_file.get('path', '')
                            else:
                                continue
                            
                            if existing_path:
                                existing_path = os.path.normpath(os.path.abspath(existing_path))
                                if existing_path == file_path:
                                    is_duplicate = True
                                    break
                    
                    if not is_duplicate:
                        # Используем внутренний метод для добавления файла
                        files_list = self.app._get_files_list()
                        
                        # Если state доступен, создаем FileInfo объект, иначе используем словарь
                        if self.app.state:
                            from core.domain.file_info import FileInfo
                            file_info = FileInfo.from_dict(file_data)
                            files_list.append(file_info)
                        else:
                            files_list.append(file_data)
                
                # Применяем методы (включая шаблон), если они есть
                if self.app.methods_manager.get_methods():
                    self.app.apply_methods()
                else:
                    # Обновляем интерфейс
                    self.refresh_treeview()
                self.update_status()
                messagebox.showinfo(
                    "Успех",
                    f"Импортировано файлов: {len(imported_files)}"
                )
                self.app.log(f"Импортировано файлов: {len(imported_files)}")
            else:
                messagebox.showwarning(
                    "Предупреждение",
                    "Не найдено валидных файлов для импорта"
                )
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось импортировать список файлов:\n{str(e)}"
            )
            logger.error(
                f"Ошибка импорта списка файлов: {e}",
                exc_info=True
            )
    
    def sort_column(self, col: str) -> None:
        """Сортировка по колонке.
        
        Args:
            col: Имя колонки для сортировки
        """
        if not hasattr(self.app, 'tree') or not self.app.tree:
            return
        
        # Находим и сохраняем строку с путем
        path_item = None
        for item in self.app.tree.get_children(""):
            tags = self.app.tree.item(item, 'tags')
            if tags and 'path_row' in tags:
                path_item = item
                break
        
        # Получаем все элементы кроме строки с путем
        items = [
            (self.app.tree.set(item, col), item)
            for item in self.app.tree.get_children("")
            if item != path_item
        ]
        items.sort()
        
        # Перемещаем элементы, начиная с индекса 1 (после строки с путем)
        start_index = 1 if path_item else 0
        for index, (val, item) in enumerate(items):
            self.app.tree.move(item, "", start_index + index)

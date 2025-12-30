"""Модуль операций с файлами (открытие, копирование, переименование)."""

import logging
import os
import subprocess
import sys
from tkinter import messagebox, simpledialog

logger = logging.getLogger(__name__)


class FileOperations:
    """Класс для операций с файлами."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def open_file(self) -> None:
        """Открытие файла в программе по умолчанию."""
        selected_items = self.app.tree.selection()
        if not selected_items:
            return
        
        for item in selected_items:
            item_index = self.app.tree.index(item)
            if item_index < 0 or item_index >= len(self.app.files):
                continue
            
            file_info = self.app.files[item_index]
            
            if file_info:
                # Используем full_path если есть, иначе собираем путь из компонентов
                file_path = None
                if hasattr(file_info, 'full_path'):
                    file_path = file_info.full_path
                elif isinstance(file_info, dict):
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
        
        try:
            import platform
            
            item = selected[0]
            file_index = self.app.tree.index(item)
            if file_index >= 0 and file_index < len(self.app.files):
                file_data = self.app.files[file_index]
                file_path = None
                if hasattr(file_data, 'full_path'):
                    file_path = file_data.full_path
                elif isinstance(file_data, dict):
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
        file_index = self.app.tree.index(item)
        if file_index < 0 or file_index >= len(self.app.files):
            return
        
        file_data = self.app.files[file_index]
        old_name = None
        extension = None
        
        if hasattr(file_data, 'old_name'):
            old_name = file_data.old_name
            extension = file_data.extension
        elif isinstance(file_data, dict):
            old_name = file_data.get('old_name', '')
            extension = file_data.get('extension', '')
        
        new_name = simpledialog.askstring(
            "Переименовать файл",
            f"Введите новое имя для файла:",
            initialvalue=old_name
        )
        
        if new_name and new_name.strip():
            new_name = new_name.strip()
            if hasattr(file_data, 'new_name'):
                file_data.new_name = new_name
                file_data.extension = extension
            elif isinstance(file_data, dict):
                file_data['new_name'] = new_name
                file_data['extension'] = extension
            self.app.file_list_manager.refresh_treeview()
            self.app.log(f"Имя файла изменено вручную: {old_name} -> {new_name}")
    
    def copy_file_path(self) -> None:
        """Копирование пути файла в буфер обмена."""
        selected = self.app.tree.selection()
        if not selected:
            return
        
        try:
            item = selected[0]
            file_index = self.app.tree.index(item)
            if file_index >= 0 and file_index < len(self.app.files):
                file_data = self.app.files[file_index]
                file_path = None
                if hasattr(file_data, 'full_path'):
                    file_path = file_data.full_path
                elif isinstance(file_data, dict):
                    file_path = file_data.get('full_path') or file_data.get('path', '')
                if file_path:
                    self.app.root.clipboard_clear()
                    self.app.root.clipboard_append(file_path)
                    self.app.log(f"Путь скопирован в буфер обмена: {file_path}")
        except Exception as e:
            logger.error(f"Ошибка копирования пути: {e}", exc_info=True)
    
    def apply_to_selected(self) -> None:
        """Применение методов только к выбранным файлам."""
        from tkinter import messagebox
        from core.re_file_methods import check_conflicts, validate_filename
        
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
                old_name = None
                extension = None
                file_path = None
                
                if hasattr(file_data, 'old_name'):
                    old_name = file_data.old_name
                    extension = file_data.extension
                    file_path = file_data.full_path or (str(file_data.path) if hasattr(file_data, 'path') else '')
                elif isinstance(file_data, dict):
                    old_name = file_data.get('old_name', '')
                    extension = file_data.get('extension', '')
                    file_path = file_data.get('full_path') or file_data.get('path', '')
                
                new_name, extension = self.app.methods_manager.apply_methods(
                    old_name,
                    extension,
                    file_path
                )
                
                if hasattr(file_data, 'new_name'):
                    file_data.new_name = new_name
                    file_data.extension = extension
                elif isinstance(file_data, dict):
                    file_data['new_name'] = new_name
                    file_data['extension'] = extension
                
                # Валидация
                path_for_validation = file_path
                if hasattr(file_data, 'path'):
                    path_for_validation = str(file_data.path) if hasattr(file_data, 'path') else file_path
                elif isinstance(file_data, dict):
                    path_for_validation = file_data.get('path') or file_path
                
                status = validate_filename(new_name, extension, path_for_validation, 0)
                
                if hasattr(file_data, 'status'):
                    file_data.status = status
                elif isinstance(file_data, dict):
                    file_data['status'] = status
            except Exception as e:
                status_error = f"Ошибка: {str(e)}"
                if hasattr(file_data, 'status'):
                    file_data.status = status_error
                elif isinstance(file_data, dict):
                    file_data['status'] = status_error
                logger.error(f"Ошибка применения методов к файлу: {e}", exc_info=True)
        
        # Проверка конфликтов
        check_conflicts(selected_files)
        self.app.file_list_manager.refresh_treeview()
        self.app.log(f"Методы применены к {len(selected_files)} выбранным файлам")
    
    def show_file_context_menu(self, event) -> None:
        """Показ контекстного меню для файла."""
        import tkinter as tk
        
        item = self.app.tree.identify_row(event.y)
        if not item:
            return
        
        # Выделяем элемент, если он не выделен
        if item not in self.app.tree.selection():
            self.app.tree.selection_set(item)
        
        # Создаем контекстное меню
        context_menu = tk.Menu(
            self.app.root,
            tearoff=0,
            bg=self.app.colors.get('bg_main', '#ffffff'),
            fg=self.app.colors.get('text_primary', '#000000'),
            activebackground=self.app.colors.get('primary', '#4a90e2'),
            activeforeground='white'
        )
        
        context_menu.add_command(label="Удалить из списка", command=self.app.file_list_manager.delete_selected)
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


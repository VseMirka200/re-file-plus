"""Модуль контекстного меню для вкладки конвертации."""

import logging
import os
import subprocess
import sys
import tkinter as tk

logger = logging.getLogger(__name__)


class ConverterContextMenu:
    """Класс для управления контекстным меню конвертации."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def show_context_menu(self, event):
        """Показ контекстного меню для файла в конвертации."""
        item = self.app.converter_tree.identify_row(event.y)
        if not item:
            return
        
        tags = self.app.converter_tree.item(item, 'tags')
        if tags and 'path_row' in tags:
            return
        
        if item not in self.app.converter_tree.selection():
            self.app.converter_tree.selection_set(item)
        
        context_menu = tk.Menu(self.app.root, tearoff=0, 
                              bg=self.app.colors.get('bg_main', '#ffffff'),
                              fg=self.app.colors.get('text_primary', '#000000'),
                              activebackground=self.app.colors.get('primary', '#4a90e2'),
                              activeforeground='white')
        
        context_menu.add_command(label="Удалить из списка", command=self.app.converter_tab_handler.remove_selected_converter_files)
        context_menu.add_separator()
        context_menu.add_command(label="Открыть файл", command=self.open_file)
        context_menu.add_command(label="Открыть путь", command=self.open_file_folder)
        context_menu.add_separator()
        context_menu.add_command(label="Копировать путь", command=self.copy_file_path)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def open_file(self):
        """Открытие файла конвертации в программе по умолчанию."""
        selected_items = self.app.tree.selection()
        if not selected_items:
            return
        
        for item in selected_items:
            values = self.app.tree.item(item, 'values')
            if not values or len(values) < 1:
                continue
            
            file_name = values[0]
            file_path = None
            for f in self.app.files:
                if os.path.basename(f) == file_name:
                    file_path = f
                    break
            
            file_info = None
            if file_path and hasattr(self.app, 'converter_files_metadata'):
                file_info = self.app.converter_files_metadata.get(file_path)
            
            if file_info:
                file_path = file_info.get('path', '')
                if file_path and os.path.exists(file_path):
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
    
    def open_file_folder(self):
        """Открытие папки с выбранным файлом конвертации."""
        selected_items = self.app.converter_tree.selection()
        if not selected_items:
            return
        
        try:
            import platform
            
            item = selected_items[0]
            values = self.app.converter_tree.item(item, 'values')
            if not values or len(values) < 1:
                return
            
            file_name = values[0]
            file_info = None
            for f in self.app.converter_files:
                if os.path.basename(f.get('path', '')) == file_name:
                    file_info = f
                    break
            
            if file_info:
                file_path = file_info.get('path', '')
                if file_path:
                    folder_path = os.path.dirname(file_path)
                    if platform.system() == 'Windows':
                        subprocess.Popen(f'explorer "{folder_path}"')
                    elif platform.system() == 'Darwin':
                        subprocess.Popen(['open', folder_path])
                    else:
                        subprocess.Popen(['xdg-open', folder_path])
                    self.app.log(f"Открыта папка: {folder_path}")
        except Exception as e:
            logger.error(f"Ошибка открытия папки: {e}", exc_info=True)
            self.app.log(f"Не удалось открыть папку: {e}")
    
    def copy_file_path(self):
        """Копирование пути файла конвертации в буфер обмена."""
        selected_items = self.app.converter_tree.selection()
        if not selected_items:
            return
        
        paths = []
        for item in selected_items:
            values = self.app.converter_tree.item(item, 'values')
            if not values or len(values) < 1:
                continue
            
            file_name = values[0]
            file_info = None
            for f in self.app.converter_files:
                if os.path.basename(f.get('path', '')) == file_name:
                    file_info = f
                    break
            
            if file_info:
                file_path = file_info.get('path', '')
                if file_path:
                    paths.append(file_path)
        
        if paths:
            try:
                self.app.root.clipboard_clear()
                self.app.root.clipboard_append('\n'.join(paths))
                path_word = 'и' if len(paths) > 1 else ''
                copied_word = 'ы' if len(paths) > 1 else ''
                self.app.log(f"Путь{path_word} скопирован{copied_word} в буфер обмена")
            except Exception as e:
                logger.error(f"Ошибка копирования пути: {e}", exc_info=True)


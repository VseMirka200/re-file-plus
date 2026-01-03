"""Модуль управления прогрессом конвертации."""

import logging
import os
import tkinter as tk
from typing import Optional, Dict, Any, List, Union

from utils.path_processing import normalize_path

logger = logging.getLogger(__name__)


class ConverterProgress:
    """Класс для управления прогрессом конвертации."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def update_progress(self, current: int, total: int, filename: str):
        """Обновление прогресса конвертации.
        
        Args:
            current: Текущий номер файла
            total: Всего файлов
            filename: Имя текущего файла
        """
        if hasattr(self.app, 'converter_progress_bar'):
            self.app.converter_progress_bar['value'] = current
        
        if hasattr(self.app, 'converter_progress_label'):
            self.app.converter_progress_label.config(
                text=f"Обработка: {current} / {total}"
            )
        
        if hasattr(self.app, 'converter_current_file_label'):
            self.app.converter_current_file_label.config(
                text=f"Текущий файл: {filename}"
            )
    
    def _get_file_path_from_item(self, file_item: Union[Dict[str, Any], Any]) -> Optional[str]:
        """Извлекает путь к файлу из элемента списка.
        
        Args:
            file_item: Элемент из списка файлов (dict или объект)
            
        Returns:
            Путь к файлу или None
        """
        if isinstance(file_item, dict):
            return file_item.get('path', '')
        elif hasattr(file_item, 'full_path'):
            return file_item.full_path
        return None
    
    def _find_file_in_list(self, files: List[Union[Dict[str, Any], Any]], target_path: str) -> Optional[Union[Dict[str, Any], Any]]:
        """Находит файл в списке по пути.
        
        Args:
            files: Список файлов
            target_path: Путь к файлу для поиска
            
        Returns:
            Найденный элемент списка или None
        """
        target_normalized = normalize_path(target_path)
        for file_item in files:
            item_path = self._get_file_path_from_item(file_item)
            if item_path and normalize_path(item_path) == target_normalized:
                return file_item
        return None
    
    def set_file_in_progress(self, file_path: str):
        """Установка файла в статус 'в работе'.
        
        Args:
            file_path: Путь к файлу
        """
        tree = getattr(self.app, 'converter_tree', None) or getattr(self.app, 'tree', None)
        files = getattr(self.app, 'converter_files', None) or getattr(self.app, 'files', [])
        
        if not tree:
            return
        
        try:
            # Обновляем статус в файле для сохранения при перерисовке
            file_item = self._find_file_in_list(files, file_path)
            if file_item and isinstance(file_item, dict):
                file_item['status'] = 'В работе...'
            
            file_name = os.path.basename(file_path)
            file_name_lower = file_name.lower()
            
            for item in tree.get_children():
                values = tree.item(item, 'values')
                if not values or len(values) == 0:
                    continue
                
                # Проверяем первую колонку (имя файла)
                display_value = values[0] if values else ''
                # Убираем возможные префиксы типа "старое → новое"
                if ' → ' in display_value:
                    display_value = display_value.split(' → ')[0].strip()
                # Убираем "[Папка]" метку если есть
                display_value = display_value.replace(' [Папка]', '').strip()
                
                # Сравниваем имена файлов (без учета регистра)
                if display_value.lower() == file_name_lower or display_value == file_name:
                    try:
                        tree.set(item, 'status', 'В работе...')
                    except (tk.TclError, AttributeError):
                        pass
                    tree.item(item, tags=('in_progress',))
                    break
        except (tk.TclError, AttributeError, RuntimeError, TypeError):
            # Игнорируем ошибки UI операций (не критично)
            pass
    
    def update_status(self, index: int, success: bool, message: str, output_path=None, file_path=None):
        """Обновление статуса файла после конвертации.
        
        Args:
            index: Индекс файла в списке (может быть None)
            success: Успешность конвертации
            message: Сообщение о статусе
            output_path: Путь к выходному файлу (опционально)
            file_path: Путь к исходному файлу (опционально, используется если index неправильный)
        """
        tree = getattr(self.app, 'converter_tree', None) or getattr(self.app, 'tree', None)
        files = getattr(self.app, 'converter_files', None) or getattr(self.app, 'files', [])
        
        if not tree:
            return
        
        try:
            file_item = None
            found_file_path = None
            
            # Если индекс валиден, используем его
            if index is not None and index >= 0 and index < len(files):
                file_item = files[index]
                found_file_path = self._get_file_path_from_item(file_item)
            
            # Если файл не найден по индексу, пытаемся найти по file_path
            if not found_file_path and file_path:
                file_item = self._find_file_in_list(files, file_path)
                if file_item:
                    found_file_path = self._get_file_path_from_item(file_item)
            
            # Если файл все еще не найден, пытаемся найти по output_path
            if not found_file_path and output_path:
                output_dir = os.path.dirname(output_path)
                output_name = os.path.splitext(os.path.basename(output_path))[0]
                for f_item in files:
                    f_path = self._get_file_path_from_item(f_item)
                    if f_path:
                        f_dir = os.path.dirname(f_path)
                        f_name = os.path.splitext(os.path.basename(f_path))[0]
                        if f_dir == output_dir and f_name == output_name:
                            file_item = f_item
                            found_file_path = f_path
                            break
            
            if not found_file_path or not file_item:
                # Попробуем найти по имени файла (последняя попытка)
                if file_path:
                    file_name = os.path.basename(file_path)
                    for f_item in files:
                        f_path = self._get_file_path_from_item(f_item)
                        if f_path and os.path.basename(f_path) == file_name:
                            file_item = f_item
                            found_file_path = f_path
                            break
                
                if not found_file_path or not file_item:
                    return
            
            file_path = found_file_path
            
            # Обновляем статус в файле для сохранения при перерисовке
            if isinstance(file_item, dict):
                if success:
                    file_item['status'] = 'Готов (конвертирован)'
                else:
                    file_item['status'] = message
                if output_path:
                    file_item['output_path'] = output_path
            
            file_name = os.path.basename(file_path)
            file_name_lower = file_name.lower()
            
            found = False
            for item in tree.get_children():
                values = tree.item(item, 'values')
                if not values or len(values) == 0:
                    continue
                
                # Проверяем первую колонку (имя файла)
                display_value = values[0] if values else ''
                # Убираем возможные префиксы типа "старое → новое"
                if ' → ' in display_value:
                    display_value = display_value.split(' → ')[0].strip()
                # Убираем "[Папка]" метку если есть
                display_value = display_value.replace(' [Папка]', '').strip()
                
                # Сравниваем имена файлов (без учета регистра)
                if display_value.lower() == file_name_lower or display_value == file_name:
                    found = True
                    if success:
                        # Обновляем статус в колонке, если есть колонка status
                        try:
                            tree.set(item, 'status', 'Готов')
                        except (tk.TclError, AttributeError):
                            pass
                        # Применяем зеленый тег
                        tree.item(item, tags=('ready',))  # Зеленый - сконвертирован
                        tree.update_idletasks()
                    else:
                        try:
                            tree.set(item, 'status', message)
                        except (tk.TclError, AttributeError):
                            pass
                        tree.item(item, tags=('error',))
                        tree.update_idletasks()
                    break
            
            # Вызываем refresh_treeview для применения тегов при перерисовке
            if hasattr(self.app, 'file_list_manager') and hasattr(self.app.file_list_manager, 'refresh_treeview'):
                self.app.root.after_idle(lambda: self.app.file_list_manager.refresh_treeview())
        except (tk.TclError, AttributeError, RuntimeError, TypeError):
            # Игнорируем ошибки UI операций (не критично)
            pass
    
    def update_file_status_in_treeview(self, file_path: str, success: bool, message: str):
        """Обновление статуса файла в treeview.
        
        Args:
            file_path: Путь к файлу
            success: Успешность конвертации
            message: Сообщение о статусе
        """
        tree = getattr(self.app, 'converter_tree', None) or getattr(self.app, 'tree', None)
        if not tree:
            return
        
        try:
            file_name = os.path.basename(file_path)
            file_name_lower = file_name.lower()
            
            for item in tree.get_children():
                values = tree.item(item, 'values')
                if not values or len(values) == 0:
                    continue
                
                # Проверяем первую колонку (имя файла)
                display_value = values[0] if values else ''
                # Убираем возможные префиксы типа "старое → новое"
                if ' → ' in display_value:
                    display_value = display_value.split(' → ')[0].strip()
                # Убираем "[Папка]" метку если есть
                display_value = display_value.replace(' [Папка]', '').strip()
                
                # Сравниваем имена файлов (без учета регистра)
                if display_value.lower() == file_name_lower or display_value == file_name:
                    if success:
                        try:
                            tree.set(item, 'status', 'Готов')
                        except (tk.TclError, AttributeError):
                            pass
                        # Применяем зеленый тег
                        tree.item(item, tags=('ready',))  # Зеленый - сконвертирован
                        # Обновляем дерево, чтобы изменения применились
                        tree.update_idletasks()
                    else:
                        try:
                            tree.set(item, 'status', message)
                        except (tk.TclError, AttributeError):
                            pass
                        tree.item(item, tags=('error',))
                        tree.update_idletasks()
                    break
            
            # Вызываем refresh_treeview для применения тегов при перерисовке
            # Используем after_idle для гарантированного обновления после всех изменений
            if hasattr(self.app, 'file_list_manager') and hasattr(self.app.file_list_manager, 'refresh_treeview'):
                self.app.root.after_idle(lambda: self.app.file_list_manager.refresh_treeview())
        except (tk.TclError, AttributeError, RuntimeError, TypeError):
            # Игнорируем ошибки UI операций (не критично)
            pass


"""Модуль отображения списка файлов в Treeview."""

import logging
import os
import re
import tkinter as tk
from tkinter import ttk
from typing import Tuple

from utils.path_processing import normalize_path

logger = logging.getLogger(__name__)


class TreeViewManager:
    """Класс для управления отображением файлов в Treeview.
    
    Обеспечивает:
    - Создание и настройку Treeview виджета
    - Обновление отображения списка файлов с кешированием
    - Группировку файлов по папкам
    - Фильтрацию по поисковому запросу (обычный текст и regex)
    - Оптимизацию производительности через кеширование проверок путей
    
    Attributes:
        app: Экземпляр главного приложения
    """
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def create_treeview(self, parent):
        """Создание Treeview виджета для отображения списка файлов.
        
        Args:
            parent: Родительский контейнер для списка файлов
        """
        # Создаем Frame для treeview
        tree_frame = tk.Frame(parent, bg=self.app.colors.get('bg_main', '#2b2b2b'))
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создаем Treeview
        # Колонка "status" создается, но скрывается для переименовщика
        tree = ttk.Treeview(
            tree_frame,
            columns=("files", "new_name", "path", "status"),
            show="headings",
            style='Custom.Treeview'
        )
        tree.heading("files", text="Имя файла")
        tree.heading("new_name", text="Новое имя")
        tree.heading("path", text="Путь")
        tree.heading("status", text="Статус")
        tree.column("files", width=250, minwidth=150, stretch=True)
        tree.column("new_name", width=250, minwidth=150, stretch=True)
        tree.column("path", width=250, minwidth=200, stretch=True)
        tree.column("status", width=0, minwidth=0, stretch=tk.NO)  # Скрыта по умолчанию
        
        # Настройка тегов для цветового выделения (для конвертера)
        tree.tag_configure('ready', background='#D1FAE5', foreground='#065F46')  # Зеленый - готов
        tree.tag_configure('in_progress', background='#FEF3C7', foreground='#92400E')  # Желтый - в работе
        tree.tag_configure('success', background='#D1FAE5', foreground='#065F46')
        tree.tag_configure('error', background='#FEE2E2', foreground='#991B1B')
        
        # Создаем скроллбар
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # Размещаем виджеты
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Сохраняем ссылки в приложении
        self.app.tree = tree
        self.app.list_frame = tree_frame
    
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
        
        # Компилируем regex паттерн (с кешированием для оптимизации)
        search_pattern = None
        if search_text and use_regex:
            try:
                # Кешируем скомпилированный паттерн для повторного использования
                # (если текст поиска не изменился, используем тот же паттерн)
                if not hasattr(self, '_cached_search_pattern') or self._cached_search_pattern[0] != search_text:
                    search_pattern = re.compile(search_text, re.IGNORECASE)
                    self._cached_search_pattern = (search_text, search_pattern)
                else:
                    search_pattern = self._cached_search_pattern[1]
            except re.error:
                use_regex = False
                # Очищаем кеш при ошибке
                if hasattr(self, '_cached_search_pattern'):
                    delattr(self, '_cached_search_pattern')
        
        # Группируем файлы по папкам
        files_by_path = {}
        # Используем глобальный кеш для проверок путей (оптимизация производительности)
        path_cache = {}
        
        def get_path_info(path: str) -> Tuple[bool, bool, bool]:
            """Получает информацию о пути с кешированием.
            
            Использует локальный кеш для текущего обновления и глобальный кеш
            для проверок существования файлов между обновлениями.
            
            Args:
                path: Путь к файлу или директории
                
            Returns:
                Tuple[существует, является_файлом, является_директорией]
            """
            if path not in path_cache:
                # Пробуем использовать глобальный кеш для проверки существования
                try:
                    from utils.file_cache import is_file_cached, is_dir_cached
                    exists = is_file_cached(path) or is_dir_cached(path)
                    isfile = is_file_cached(path) if exists else False
                    isdir = is_dir_cached(path) if exists else False
                except ImportError:
                    # Fallback если кеш недоступен
                    exists = os.path.exists(path)
                    isfile = os.path.isfile(path) if exists else False
                    isdir = os.path.isdir(path) if exists else False
                
                path_cache[path] = (exists, isfile, isdir)
            return path_cache[path]
        
        # Используем файлы конвертера, если используется converter_tree
        files_to_display = self.app.files
        # Проверяем, используется ли общий tree для конвертера
        if (hasattr(self.app, 'converter_tree') and 
            hasattr(self.app, 'converter_files') and 
            self.app.converter_files and
            self.app.converter_tree is self.app.tree):
            # Если converter_tree указывает на тот же tree, используем converter_files
            files_to_display = self.app.converter_files
        
        for file_data in files_to_display:
            # Получаем путь к папке файла
            folder_path = None
            
            if hasattr(file_data, 'old_name'):
                full_path = file_data.full_path or str(file_data.path)
                exists, isfile, isdir = get_path_info(full_path)
                if exists:
                    if isfile:
                        folder_path = os.path.dirname(full_path)
                    elif isdir:
                        folder_path = full_path
                else:
                    path = str(file_data.path.parent) if hasattr(file_data.path, 'parent') else str(file_data.path)
                    _, path_isfile, _ = get_path_info(path)
                    folder_path = os.path.dirname(path) if path_isfile else path
            else:
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
                folder_path = normalize_path(folder_path)
                if folder_path not in files_by_path:
                    files_by_path[folder_path] = []
                files_by_path[folder_path].append(file_data)
        
        # Сортируем пути
        sorted_paths = sorted(files_by_path.keys())
        
        # Добавляем файлы, группируя по папкам
        for folder_path in sorted_paths:
            files_in_folder = files_by_path[folder_path]
            
            for file_data in files_in_folder:
                # Получаем данные файла/папки
                if hasattr(file_data, 'old_name'):
                    old_name = file_data.old_name or ''
                    if hasattr(file_data, 'new_name') and file_data.new_name is not None:
                        new_name = file_data.new_name
                    else:
                        new_name = old_name
                    extension = file_data.extension or ''
                    full_path = file_data.full_path or str(file_data.path) if hasattr(file_data, 'path') else ''
                    is_folder = (file_data.metadata and file_data.metadata.get('is_folder', False)) or (
                        not extension and os.path.isdir(full_path) if os.path.exists(full_path) else False
                    )
                else:
                    old_name = file_data.get('old_name', '')
                    new_name = file_data.get('new_name', '')
                    extension = file_data.get('extension', '')
                    full_path = file_data.get('full_path', '')
                    is_folder = file_data.get('is_folder', False) or (
                        not extension and full_path and os.path.isdir(full_path) if os.path.exists(full_path) else False
                    )
                
                # Фильтрация по поисковому запросу
                if search_text:
                    if use_regex and search_pattern:
                        full_text = f"{old_name} {new_name} {folder_path} {extension}"
                        if not search_pattern.search(full_text):
                            continue
                    else:
                        search_lower = search_text.lower()
                        if (search_lower not in old_name.lower() and 
                            search_lower not in new_name.lower() and 
                            search_lower not in folder_path.lower() and 
                            search_lower not in extension.lower()):
                            continue
                
                # Формируем имена для отображения
                if not new_name:
                    if hasattr(file_data, 'old_name'):
                        if not hasattr(file_data, 'new_name') or file_data.new_name is None or file_data.new_name == '':
                            new_name = old_name
                        else:
                            new_name = file_data.new_name
                    else:
                        if 'new_name' not in file_data or not file_data.get('new_name'):
                            new_name = old_name
                        else:
                            new_name = file_data.get('new_name', old_name)
                
                folder_label = " [Папка]" if is_folder else ""
                old_full_name = f"{old_name}{extension}" if extension else old_name
                new_full_name = f"{new_name}{extension}" if extension else new_name
                
                old_display_name = f"{old_full_name}{folder_label}"
                new_display_name = new_full_name
                
                if old_display_name != new_display_name:
                    display_text = f"{old_display_name} → {new_display_name}"
                else:
                    display_text = old_display_name
                
                file_path_display = folder_path
                
                # Определяем статус для отображения (только для конвертера)
                status_text = ""
                tags = ()
                
                # Проверяем, используется ли конвертер (current_tab == 'convert')
                current_tab = getattr(self.app, 'current_tab', 'files')
                is_converter = current_tab == 'convert'
                
                # Для конвертера проверяем статус и применяем цветовую индикацию
                if is_converter and (hasattr(file_data, 'status') or (isinstance(file_data, dict) and 'status' in file_data)):
                    status = file_data.status if hasattr(file_data, 'status') else file_data.get('status', '')
                    if status:
                        status_text = status
                        # Применяем теги для конвертера на основе статуса
                        status_lower = status.lower() if status else ''
                        if 'конвертирован' in status_lower or (status == 'Готов' and isinstance(file_data, dict) and file_data.get('output_path')):
                            tags = ('ready',)  # Зеленый - успешно сконвертирован
                        elif status == 'В работе...' or 'В работе' in status:
                            tags = ('in_progress',)  # Желтый - конвертируется
                        elif status.startswith('Ошибка') or status.startswith('Не поддерживается'):
                            tags = ('error',)
                
                # Вставляем имя файла, новое имя, путь и статус
                # Для переименовщика статус будет пустым, колонка скрыта
                new_display_name_full = new_full_name if new_full_name != old_full_name else ""
                self.app.tree.insert("", tk.END, values=(old_display_name, new_display_name_full, file_path_display, status_text), tags=tags)
        
        # Обновляем видимость скроллбаров
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
    
    def update_status(self) -> None:
        """Обновление статусной строки.
        
        Отображает количество файлов в списке и другую статистику.
        """
        count = len(self.app.files)
        if hasattr(self.app, 'left_panel'):
            self.app.left_panel.config(text=f"Список файлов (Файлов: {count})")
    
    def sort_column(self, col: str) -> None:
        """Сортировка по колонке.
        
        Args:
            col: Имя колонки для сортировки ("files", "new_name" или "path")
        """
        if not hasattr(self.app, 'tree') or not self.app.tree:
            return
        
        if col in ("files", "new_name", "path"):
            sort_col = col
        else:
            sort_col = "files"
        
        items = [
            (self.app.tree.set(item, sort_col), item)
            for item in self.app.tree.get_children("")
        ]
        
        if self.app.sort_column_name == sort_col:
            self.app.sort_reverse = not self.app.sort_reverse
        else:
            self.app.sort_column_name = sort_col
            self.app.sort_reverse = False
        
        items.sort(reverse=self.app.sort_reverse)
        
        for index, (val, item) in enumerate(items):
            self.app.tree.move(item, "", index)


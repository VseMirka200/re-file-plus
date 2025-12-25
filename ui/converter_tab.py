"""Модуль для вкладки конвертации файлов.

Обеспечивает интерфейс для конвертации файлов между различными форматами
с поддержкой выбора формата, настроек качества и отслеживания прогресса.
"""

# Стандартная библиотека
import logging
import os
import re
import subprocess
import sys
import threading
from typing import Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

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

# Опциональные импорты
HAS_TKINTERDND2 = False
try:
    from tkinterdnd2 import DND_FILES
    HAS_TKINTERDND2 = True
except ImportError:
    pass


class ConverterTab:
    """Класс для управления вкладкой конвертации файлов."""
    
    def __init__(self, app) -> None:
        """Инициализация вкладки конвертации.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
    
    def create_tab(self):
        """Создание вкладки конвертации файлов на главном экране"""
        converter_tab = tk.Frame(self.app.main_notebook, bg=self.app.colors['bg_main'])
        converter_tab.columnconfigure(0, weight=1)
        converter_tab.rowconfigure(0, weight=1)
        self.app.main_notebook.add(converter_tab, text="Конвертация файлов")
        
        # Основной контейнер (как во вкладке "Файлы")
        main_container = tk.Frame(converter_tab, bg=self.app.colors['bg_main'])
        main_container.grid(row=0, column=0, sticky="nsew")
        # Левая панель занимает 60%, правая - 40%
        main_container.columnconfigure(0, weight=6, uniform="panels")
        main_container.columnconfigure(1, weight=4, uniform="panels")
        main_container.rowconfigure(0, weight=1)
        
        # Левая часть - список файлов (как во вкладке "Файлы")
        files_count = len(self.app.converter_files) if hasattr(self.app, 'converter_files') else 0
        left_panel = ttk.LabelFrame(
            main_container,
            text=f"Список файлов (Файлов: {files_count})",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)  # (left, top, right, bottom) - увеличены верхний и нижний отступы
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=(20, 20))
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(1, weight=1)  # Строка с таблицей файлов
        
        # Сохраняем ссылку на left_panel для обновления заголовка
        self.app.converter_left_panel = left_panel
        
        # Кнопки управления под заголовком "Список файлов"
        buttons_frame_left = tk.Frame(left_panel, bg=self.app.colors['bg_card'])
        buttons_frame_left.pack(fill=tk.X, pady=(0, 12))
        
        # Настраиваем равномерное распределение кнопок
        buttons_frame_left.columnconfigure(0, weight=1, uniform="buttons")
        buttons_frame_left.columnconfigure(1, weight=1, uniform="buttons")
        
        btn_add_files_left = self.app.create_rounded_button(
            buttons_frame_left, "Добавить файлы", self.add_files_for_conversion,
            self.app.colors['primary'], 'white', 
            font=('Robot', 9, 'bold'), padx=10, pady=6,
            active_bg=self.app.colors['primary_hover'])
        btn_add_files_left.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        btn_clear_left = self.app.create_rounded_button(
            buttons_frame_left, "Очистить", self.clear_converter_files_list,
            self.app.colors['warning'], 'white',
            font=('Robot', 9, 'bold'), padx=10, pady=6,
            active_bg=self.app.colors['warning_hover'])
        btn_clear_left.grid(row=0, column=1, sticky="ew")
        
        # Таблица файлов
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создание таблицы с прокруткой
        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        
        columns = ('file', 'status')
        tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            style='Custom.Treeview'
        )
        
        scrollbar_y.config(command=tree.yview)
        scrollbar_x.config(command=tree.xview)
        
        # Настройка колонок с равной шириной
        tree.heading("file", text="Файл")
        tree.heading("status", text="Статус")
        
        # Столбцы будут занимать равную ширину (50% каждый)
        tree.column("file", width=300, anchor='w', minwidth=150, stretch=tk.YES)
        tree.column("status", width=300, anchor='center', minwidth=150, stretch=tk.YES)
        
        # Настройка тегов для цветового выделения
        tree.tag_configure('ready', background='#FEF3C7', foreground='#92400E')  # Желтый - готов к конвертации
        tree.tag_configure('success', background='#D1FAE5', foreground='#065F46')  # Зеленый - успешно конвертирован
        tree.tag_configure('error', background='#FEE2E2', foreground='#991B1B')  # Красный - ошибка
        
        # Размещение таблицы и скроллбаров
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Сохраняем ссылки на tree и скроллбары
        self.app.converter_tree = tree
        self.app.converter_scrollbar_y = scrollbar_y
        self.app.converter_scrollbar_x = scrollbar_x
        self.app.converter_list_frame = list_frame
        
        # Привязываем обновление колонок при изменении размера окна
        def update_converter_columns(event=None):
            """Обновление ширины колонок для равномерного распределения"""
            if hasattr(self.app, 'converter_list_frame') and hasattr(self.app, 'converter_tree'):
                try:
                    frame_width = self.app.converter_list_frame.winfo_width()
                    if frame_width > 100:  # Минимальная ширина для расчетов
                        available_width = max(frame_width - 30, 200)  # Вычитаем ширину скроллбара
                        # Равная ширина для обеих колонок (50% каждая)
                        column_width = int(available_width / 2)
                        self.app.converter_tree.column("file", width=column_width, minwidth=150)
                        self.app.converter_tree.column("status", width=column_width, minwidth=150)
                except (AttributeError, tk.TclError):
                    pass
        
        # Привязываем к событию изменения размера
        list_frame.bind('<Configure>', update_converter_columns)
        # Также обновляем после небольшой задержки при создании
        self.app.root.after(200, update_converter_columns)
        self.app.converter_scrollbar_x = scrollbar_x
        if not hasattr(self.app, 'converter_files'):
            self.app.converter_files = []
        
        
        # Привязка прокрутки колесом мыши
        self.app.bind_mousewheel(tree, tree)
        
        # Контекстное меню для файлов конвертации
        tree.bind('<Button-3>', self.show_converter_context_menu)
        
        # Автоматическое управление видимостью скроллбаров для Treeview конвертера
        def update_converter_scrollbars(*args):
            if (hasattr(self.app, 'converter_tree') and
                    hasattr(self.app, 'converter_scrollbar_y') and
                    hasattr(self.app, 'converter_scrollbar_x')):
                self.app.update_scrollbar_visibility(
                    self.app.converter_tree,
                    self.app.converter_scrollbar_y,
                    'vertical'
                )
                self.app.update_scrollbar_visibility(
                    self.app.converter_tree,
                    self.app.converter_scrollbar_x,
                    'horizontal'
                )
        
        # Привязываем обновление скроллбаров к событиям дерева
        tree.bind('<<TreeviewSelect>>', lambda e: (self.update_available_formats(), update_converter_scrollbars()))
        tree.bind('<Configure>', lambda e: update_converter_scrollbars())
        
        # Обновляем видимость скроллбаров после создания виджетов
        self.app.root.after(200, update_converter_scrollbars)
        
        # Полоска отображения пути файлов (под таблицей файлов)
        converter_path_frame = tk.Frame(left_panel, bg=self.app.colors['bg_card'], relief=tk.FLAT, bd=1)
        converter_path_frame.pack(fill=tk.X, pady=(6, 0))
        
        converter_path_label = tk.Label(converter_path_frame, 
                                       text="Путь: ",
                                       font=('Robot', 9, 'bold'),
                                       bg=self.app.colors['bg_card'],
                                       fg=self.app.colors['text_primary'],
                                       anchor='w')
        converter_path_label.pack(side=tk.LEFT, padx=(6, 4))
        
        self.app.converter_path_label = tk.Label(converter_path_frame,
                                                  text="",
                                                  font=('Robot', 9),
                                                  bg=self.app.colors['bg_card'],
                                                  fg=self.app.colors['text_secondary'],
                                                  anchor='w',
                                                  wraplength=500)
        self.app.converter_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        
        # Функция для обновления пути конвертера
        def update_converter_path():
            if not hasattr(self.app, 'converter_files') or not self.app.converter_files:
                self.app.converter_path_label.config(text="")
                return
            
            # Получаем пути всех файлов
            paths = []
            for file_data in self.app.converter_files:
                path = file_data.get('path', '')
                if path:
                    # Нормализуем путь
                    path = os.path.normpath(os.path.abspath(path))
                    # Если это файл, берем директорию, если папка - оставляем как есть
                    if os.path.isfile(path):
                        paths.append(os.path.dirname(path))
                    elif os.path.isdir(path):
                        paths.append(path)
                    else:
                        # Если путь не существует, пробуем взять директорию
                        paths.append(os.path.dirname(path))
            
            if not paths:
                self.app.converter_path_label.config(text="")
                return
            
            # Находим общий путь
            try:
                if len(paths) > 1:
                    # Нормализуем все пути для корректного сравнения
                    normalized_paths = [os.path.normpath(p) for p in paths]
                    common_path = os.path.commonpath(normalized_paths)
                else:
                    common_path = paths[0] if paths else ""
                
                # Проверяем, что путь существует и это директория
                if common_path and os.path.exists(common_path) and os.path.isdir(common_path):
                    pass  # Путь корректен
                elif common_path:
                    # Если путь не существует или это файл, берем родительскую директорию
                    parent = os.path.dirname(common_path)
                    if parent and os.path.isdir(parent):
                        common_path = parent
                    else:
                        # Используем первый путь
                        common_path = paths[0] if paths else ""
            except (ValueError, OSError):
                # Если пути на разных дисках или ошибка, показываем первый путь
                common_path = paths[0] if paths else ""
            
            # Обновляем текст
            if common_path:
                # Нормализуем для отображения
                common_path = os.path.normpath(common_path)
                self.app.converter_path_label.config(text=common_path)
            else:
                self.app.converter_path_label.config(text="")
        
        # Сохраняем функцию для обновления
        self.app.update_converter_path = update_converter_path
        # Обновляем путь при создании
        self.app.root.after(100, update_converter_path)
        
        # Прогресс-бар внизу
        progress_container = tk.Frame(left_panel, bg=self.app.colors['bg_card'])
        progress_container.pack(fill=tk.X, pady=(6, 0))
        # Настраиваем колонки для растягивания прогресс-бара на всю ширину
        progress_container.columnconfigure(0, weight=0)  # Метка "Прогресс:" не растягивается
        progress_container.columnconfigure(1, weight=1)  # Прогресс-бар растягивается на всю доступную ширину
        
        # Название прогресс-бара и прогресс-бар на одной строке
        progress_title = tk.Label(progress_container, text="Прогресс:",
                                 font=('Robot', 9, 'bold'),
                                 bg=self.app.colors['bg_card'],
                                 fg=self.app.colors['text_primary'],
                                 anchor='w')
        progress_title.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        self.app.converter_progress_bar = ttk.Progressbar(progress_container, mode='determinate')
        # Прогресс-бар растягивается на всю доступную ширину контейнера (без правого отступа)
        self.app.converter_progress_bar.grid(row=0, column=1, sticky="ew")
        self.app.converter_progress_bar['value'] = 0
        
        self.app.converter_progress_label = tk.Label(progress_container, text="",
                                                font=('Robot', 8),
                                                bg=self.app.colors['bg_card'],
                                                fg=self.app.colors['text_secondary'],
                                                anchor='w')
        self.app.converter_progress_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        
        # Настройка drag and drop для вкладки конвертации
        self.setup_converter_drag_drop(list_frame, tree, converter_tab)
        
        # === ПРАВАЯ ПАНЕЛЬ (настройки конвертации) ===
        right_panel = ttk.LabelFrame(
            main_container,
            text="Настройки конвертации",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)
        )
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(2, 0), pady=(20, 20))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)  # Настройки теперь в строке 0
        
        # Внутренний Frame для содержимого (настройки сверху)
        settings_frame = tk.Frame(right_panel, bg=self.app.colors['bg_card'])
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        
        # Фильтр по типу файла
        filter_label = tk.Label(settings_frame, text="Фильтр по типу:",
                               font=('Robot', 9, 'bold'),
                               bg=self.app.colors['bg_card'],
                               fg=self.app.colors['text_primary'],
                               anchor='w')
        filter_label.pack(anchor=tk.W, pady=(0, 6))
        
        # Combobox для фильтра по типу файла
        filter_var = tk.StringVar(value="Все")
        filter_combo = ttk.Combobox(
            settings_frame,
            textvariable=filter_var,
            values=[
                "Все",
                "Изображения",
                "Документы",
                "Таблицы",
                "Презентации",
                "Аудио",
                "Видео"
            ],
            state='readonly',
            width=15
        )
        filter_combo.pack(fill=tk.X, pady=(0, 10))
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.filter_converter_files_by_type())
        self.app.converter_filter_var = filter_var
        self.app.converter_filter_combo = filter_combo
        
        # Применяем фильтр при инициализации
        self.app.root.after(100, lambda: self.filter_converter_files_by_type())
        
        # Выбор формата
        format_label = tk.Label(settings_frame, text="Целевой формат:",
                               font=('Robot', 9, 'bold'),
                               bg=self.app.colors['bg_card'],
                               fg=self.app.colors['text_primary'],
                               anchor='w')
        format_label.pack(anchor=tk.W, pady=(0, 12))
        
        # Combobox для выбора формата
        formats = self.app.file_converter.get_supported_formats()
        format_var = tk.StringVar(value=formats[0] if formats else '.png')
        format_combo = ttk.Combobox(settings_frame, textvariable=format_var,
                                   values=formats, state='readonly', width=15)
        format_combo.pack(fill=tk.X, pady=(0, 10))
        self.app.converter_format_var = format_var
        self.app.converter_format_combo = format_combo
        
        # Чекбокс для сжатия PDF (показывается только для PDF)
        compress_pdf_var = tk.BooleanVar(value=False)
        compress_pdf_check = tk.Checkbutton(
            settings_frame, 
            text="Сжимать PDF после конвертации",
            variable=compress_pdf_var,
            bg=self.app.colors['bg_card'],
            fg=self.app.colors['text_primary'],
            font=('Robot', 9),
            anchor='w'
        )
        compress_pdf_check.pack(fill=tk.X, pady=(0, 10))
        self.app.compress_pdf_var = compress_pdf_var
        self.app.compress_pdf_check = compress_pdf_check
        
        # Функция для обновления видимости чекбокса сжатия
        def update_compress_checkbox(*args):
            target_format = format_var.get()
            if target_format == '.pdf':
                compress_pdf_check.pack(fill=tk.X, pady=(0, 10))
            else:
                compress_pdf_check.pack_forget()
        
        format_var.trace('w', update_compress_checkbox)
        update_compress_checkbox()  # Вызываем сразу для установки начального состояния
        
        # Разделитель перед кнопками
        separator_buttons = tk.Frame(right_panel, height=2, bg=self.app.colors['border'])
        separator_buttons.pack(fill=tk.X, padx=6, pady=(6, 0))
        
        # Кнопки управления в правой панели (внизу)
        buttons_frame = tk.Frame(right_panel, bg=self.app.colors['bg_card'])
        buttons_frame.pack(fill=tk.X, padx=6, pady=(6, 0))
        
        btn_convert = self.app.create_rounded_button(
            buttons_frame, "Конвертировать", self.convert_files,
            self.app.colors['success'], 'white',
            font=('Robot', 9, 'bold'), padx=10, pady=6,
            active_bg=self.app.colors['success_hover'])
        btn_convert.pack(fill=tk.X)
    
    def process_files_from_args(self):
        """Обработка файлов из аргументов командной строки"""
        if not self.app.files_from_args:
            self.app.log("Нет файлов для обработки из аргументов")
            return
        
        self.app.log(f"Начинаем обработку {len(self.app.files_from_args)} файлов из контекстного меню")
        
        # Переключаемся на вкладку конвертации
        if hasattr(self.app, 'main_notebook') and self.app.main_notebook:
            # Находим индекс вкладки "Конвертация файлов"
            tab_found = False
            for i in range(self.app.main_notebook.index('end')):
                tab_text = self.app.main_notebook.tab(i, 'text')
                if tab_text == 'Конвертация файлов':
                    self.app.main_notebook.select(i)
                    tab_found = True
                    self.app.log("Переключились на вкладку 'Конвертация файлов'")
                    break
            
            if not tab_found:
                self.app.log("Вкладка 'Конвертация файлов' не найдена!")
                # Пробуем найти по другому названию или создаем заново
                for i in range(self.app.main_notebook.index('end')):
                    tab_text = self.app.main_notebook.tab(i, 'text')
                    self.app.log(f"Найдена вкладка: {tab_text}")
        else:
            self.app.log("main_notebook не найден!")
        
        # Добавляем файлы
        for file_path in self.app.files_from_args:
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                continue
            
            if not hasattr(self.app, 'converter_files'):
                self.app.converter_files = []
            
            # Проверяем, что файл еще не добавлен
            normalized_path = os.path.normpath(os.path.abspath(file_path))
            if any(os.path.normpath(os.path.abspath(f.get('path', ''))) == normalized_path 
                   for f in self.app.converter_files):
                continue
            
            ext = os.path.splitext(file_path)[1].lower()
            
            # Определяем доступные форматы конвертации
            available_formats = []
            all_formats = self.app.file_converter.get_supported_formats()
            for target_format in all_formats:
                if self.app.file_converter.can_convert(file_path, target_format):
                    available_formats.append(target_format)
            
            # Определяем категорию файла автоматически
            file_category = self.app.file_converter.get_file_type_category(file_path)
            
            # Определяем статус файла
            # Проверяем, был ли файл уже конвертирован
            status = self._check_if_file_already_converted(file_path, available_formats)
            if not status:
                if available_formats:
                    status = 'Готов'
                else:
                    status = 'Не поддерживается'
            
            file_data = {
                'path': file_path,
                'format': ext,
                'status': status,
                'available_formats': available_formats,
                'category': file_category
            }
            self.app.converter_files.append(file_data)
            
            # Автоматически устанавливаем фильтр по типу файла при первом добавлении
            if hasattr(self.app, 'converter_filter_var') and self.app.converter_filter_var.get() == "Все":
                category_mapping = {
                    'image': 'Изображения',
                    'document': 'Документы',
                    'spreadsheet': 'Таблицы',
                    'presentation': 'Презентации',
                    'audio': 'Аудио',
                    'video': 'Видео'
                }
                filter_name = category_mapping.get(file_category)
                if filter_name:
                    self.app.converter_filter_var.set(filter_name)
                    # Обновляем список форматов для этого типа
                    self.update_available_formats()
        
        # Обновляем заголовок панели
        if hasattr(self.app, 'converter_left_panel'):
            count = len(self.app.converter_files)
            self.app.converter_left_panel.config(text=f"Список файлов (Файлов: {count})")
        
        # Применяем фильтр и обновляем отображение
        if hasattr(self.app, 'converter_tab_handler'):
            self.app.converter_tab_handler.filter_converter_files_by_type()
        
        added_count = len(self.app.converter_files) if hasattr(self.app, 'converter_files') else 0
        self.app.log(f"Добавлено файлов из контекстного меню: {added_count} из {len(self.app.files_from_args)}")
    
    def add_files_for_conversion(self):
        """Добавление файлов для конвертации"""
        logger.info("Открыт диалог выбора файлов для конвертации")
        files = filedialog.askopenfilenames(
            title="Выберите файлы для конвертации",
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
                ("Аудио", "*.mp3 *.wav *.flac *.aac *.ogg *.m4a *.wma *.opus"),
                ("Видео", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.mpg *.mpeg *.3gp"),
            ]
        )
        if files:
            log_batch_action(
                logger=logger,
                action='CONVERTER_FILES_SELECTED',
                message=f"Выбрано файлов для конвертации: {len(files)}",
                file_count=len(files),
                method_name='add_files_for_conversion'
            )
            added_count = 0
            skipped_count = 0
            for file_path in files:
                if not hasattr(self.app, 'converter_files'):
                    self.app.converter_files = []
                # Проверяем, что файл еще не добавлен
                normalized_path = os.path.normpath(os.path.abspath(file_path))
                if any(os.path.normpath(os.path.abspath(f.get('path', ''))) == normalized_path 
                       for f in self.app.converter_files):
                    log_file_action(
                        logger=logger,
                        action='CONVERTER_FILE_SKIPPED',
                        message=f"Файл уже в списке конвертации, пропущен",
                        file_path=file_path,
                        method_name='add_files_for_conversion'
                    )
                    skipped_count += 1
                    continue
                
                log_file_action(
                    logger=logger,
                    action='CONVERTER_FILE_ADDED',
                    message=f"Добавление файла в список конвертации",
                    file_path=file_path,
                    method_name='add_files_for_conversion'
                )
                added_count += 1
                
                ext = os.path.splitext(file_path)[1].lower()
                
                # Определяем доступные форматы конвертации
                available_formats = []
                all_formats = self.app.file_converter.get_supported_formats()
                for target_format in all_formats:
                    if self.app.file_converter.can_convert(file_path, target_format):
                        available_formats.append(target_format)
                
                # Определяем категорию файла автоматически
                file_category = self.app.file_converter.get_file_type_category(file_path)
                
                # Определяем статус файла
                if available_formats:
                    status = 'Готов'
                else:
                    status = 'Не поддерживается'
                
                file_data = {
                    'path': file_path,
                    'format': ext,
                    'status': status,
                    'available_formats': available_formats,  # Сохраняем список форматов, а не строку
                    'category': file_category  # Сохраняем категорию файла
                }
                self.app.converter_files.append(file_data)
            
            # Автоматически устанавливаем фильтр по типу первого добавленного файла
            if self.app.converter_files and hasattr(self.app, 'converter_filter_var'):
                first_file_category = self.app.converter_files[0].get('category')
                if first_file_category and self.app.converter_filter_var.get() == "Все":
                    category_mapping = {
                        'image': 'Изображения',
                        'document': 'Документы',
                        'spreadsheet': 'Таблицы',
                        'presentation': 'Презентации',
                        'audio': 'Аудио',
                        'video': 'Видео'
                    }
                    filter_name = category_mapping.get(first_file_category)
                    if filter_name:
                        self.app.converter_filter_var.set(filter_name)
            
            # Обновляем заголовок панели
            if hasattr(self.app, 'converter_left_panel'):
                count = len(self.app.converter_files)
                self.app.converter_left_panel.config(text=f"Список файлов (Файлов: {count})")
            # Применяем фильтр - это обновит treeview и доступные форматы
            self.filter_converter_files_by_type()
            # Обновляем путь
            if hasattr(self.app, 'update_converter_path'):
                self.app.root.after_idle(self.app.update_converter_path)
            logger.info(f"Добавлено файлов в список конвертации: {added_count}, пропущено: {skipped_count}")
            self.app.log(f"Добавлено файлов для конвертации: {len(files)}")
    
    def update_available_formats(self):
        """Обновление списка доступных форматов в combobox на основе фильтра типа"""
        if not hasattr(self.app, 'converter_format_combo') or not self.app.converter_format_combo:
            return
        
        # Всегда используем фильтр типа для определения форматов
        # Не фильтруем по добавленным файлам - показываем все форматы выбранного типа
        filter_type = self.app.converter_filter_var.get() if hasattr(self.app, 'converter_filter_var') else "Все"
        
        # Получаем все поддерживаемые форматы
        all_supported_formats = self.app.file_converter.get_supported_formats()
        
        # Маппинг типов фильтра на категории
        filter_mapping = {
            "Все": None,
            "Изображения": "image",
            "Документы": "document",
            "Таблицы": "spreadsheet",
            "Презентации": "presentation",
            "Аудио": "audio",
            "Видео": "video"
        }
        
        target_category = filter_mapping.get(filter_type)
        
        # Формируем список форматов в зависимости от типа фильтра
        if target_category == "image":
            image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif',
                           '.ico', '.svg', '.heic', '.heif', '.avif', '.dng', '.cr2', '.nef', '.raw']
            final_formats = [f for f in all_supported_formats if f in image_formats]
        elif target_category == "document":
            # Для документов показываем форматы документов Word и форматы изображений (JPG, PNG)
            doc_formats = list(self.app.file_converter.supported_document_formats.keys())
            # Добавляем JPG и PNG для конвертации документов в изображения
            image_formats_for_docs = ['.jpg', '.jpeg', '.png']
            final_formats = [f for f in all_supported_formats if f in doc_formats or f in image_formats_for_docs]
        elif target_category == "spreadsheet":
            spreadsheet_formats = list(self.app.file_converter.supported_spreadsheet_formats.keys())
            final_formats = [f for f in all_supported_formats if f in spreadsheet_formats]
        elif target_category == "presentation":
            presentation_formats = list(self.app.file_converter.supported_presentation_formats.keys())
            final_formats = [f for f in all_supported_formats if f in presentation_formats]
        elif target_category == "audio":
            audio_formats = list(self.app.file_converter.supported_audio_formats.keys())
            final_formats = [f for f in all_supported_formats if f in audio_formats]
        elif target_category == "video":
            video_formats = list(self.app.file_converter.supported_video_formats.keys())
            final_formats = [f for f in all_supported_formats if f in video_formats]
        else:
            # Для "Все" показываем все поддерживаемые форматы
            final_formats = all_supported_formats
        
        self.app.converter_format_combo['values'] = final_formats
        
        # Убираем автоматическую установку формата - пользователь должен выбрать сам
        # Просто очищаем значение, если текущее не в списке
        current_value = self.app.converter_format_var.get()
        if current_value not in final_formats:
            self.app.converter_format_var.set('')
    
    def filter_converter_files_by_type(self):
        """Фильтрация файлов в конвертере по типу"""
        if not hasattr(self.app, 'converter_tree') or not hasattr(self.app, 'converter_files'):
            return
        
        filter_type = self.app.converter_filter_var.get()
        
        # Очищаем дерево
        for item in self.app.converter_tree.get_children():
            self.app.converter_tree.delete(item)
        
        # Маппинг типов фильтра на категории
        filter_mapping = {
            "Все": None,
            "Изображения": "image",
            "Документы": "document",
            "Таблицы": "spreadsheet",
            "Презентации": "presentation",
            "Аудио": "audio",
            "Видео": "video"
        }
        
        target_category = filter_mapping.get(filter_type)
        
        # Добавляем только файлы, соответствующие фильтру
        visible_count = 0
        visible_files = []
        for file_data in self.app.converter_files:
            file_category = file_data.get('category')
            
            # Если фильтр "Все" или категория совпадает
            if target_category is None or file_category == target_category:
                file_name = os.path.basename(file_data['path'])
                # Определяем тег в зависимости от статуса
                status = file_data.get('status', 'Готов')
                if status == 'Готов':
                    tag = 'ready'
                elif status == 'Конвертирован':
                    tag = 'success'
                elif 'Ошибка' in status or 'ошибка' in status:
                    tag = 'error'
                else:
                    tag = 'ready'
                
                self.app.converter_tree.insert("", tk.END, values=(file_name, status), tags=(tag,))
                visible_count += 1
                visible_files.append(file_data)
        
        # Обновляем видимость скроллбаров после обновления содержимого
        if hasattr(self.app, 'converter_scrollbar_y') and hasattr(self.app, 'converter_scrollbar_x'):
            self.app.root.after_idle(lambda: self.app.update_scrollbar_visibility(
                self.app.converter_tree, self.app.converter_scrollbar_y, 'vertical'))
            self.app.root.after_idle(lambda: self.app.update_scrollbar_visibility(
                self.app.converter_tree, self.app.converter_scrollbar_x, 'horizontal'))
        
        # Обновляем доступные форматы на основе фильтра типа
        if hasattr(self.app, 'converter_format_combo'):
            # Получаем все поддерживаемые форматы
            all_supported_formats = self.app.file_converter.get_supported_formats()
            
            # Формируем список форматов в зависимости от типа фильтра
            if target_category == "image":
                # Для изображений показываем только форматы изображений
                image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif',
                               '.ico', '.svg', '.heic', '.heif', '.avif', '.dng', '.cr2', '.nef', '.raw']
                filtered_formats = [f for f in all_supported_formats if f in image_formats]
            elif target_category == "document":
                # Для документов показываем форматы документов Word и форматы изображений (JPG, PNG)
                doc_formats = list(self.app.file_converter.supported_document_formats.keys())
                # Добавляем JPG и PNG для конвертации документов в изображения
                image_formats_for_docs = ['.jpg', '.jpeg', '.png']
                filtered_formats = [f for f in all_supported_formats if f in doc_formats or f in image_formats_for_docs]
            elif target_category == "spreadsheet":
                # Для таблиц показываем только форматы таблиц Excel
                spreadsheet_formats = list(self.app.file_converter.supported_spreadsheet_formats.keys())
                filtered_formats = [f for f in all_supported_formats if f in spreadsheet_formats]
            elif target_category == "presentation":
                # Для презентаций показываем только форматы презентаций PowerPoint
                presentation_formats = list(self.app.file_converter.supported_presentation_formats.keys())
                filtered_formats = [f for f in all_supported_formats if f in presentation_formats]
            elif target_category == "audio":
                # Для аудио показываем только форматы аудио (если они поддерживаются)
                # Используем все форматы из file_converter, а не хардкод
                audio_formats = list(self.app.file_converter.supported_audio_formats.keys())
                filtered_formats = [f for f in all_supported_formats if f in audio_formats]
            elif target_category == "video":
                # Для видео показываем только форматы видео (если они поддерживаются)
                # Используем все форматы из file_converter, а не хардкод
                video_formats = list(self.app.file_converter.supported_video_formats.keys())
                filtered_formats = [f for f in all_supported_formats if f in video_formats]
            else:
                # Для "Все" показываем все поддерживаемые форматы
                filtered_formats = all_supported_formats.copy()
            
            # Убираем дополнительную фильтрацию по доступным форматам файлов
            # Всегда показываем все форматы, соответствующие выбранному фильтру типа
            # Пользователь может выбрать любой формат, даже если он не подходит для добавленных файлов
            if target_category is None:
                # Для "Все" показываем все поддерживаемые форматы
                final_formats = all_supported_formats
            else:
                # Для конкретного типа показываем отфильтрованные форматы (даже если пусто)
                final_formats = filtered_formats if filtered_formats else []
            
            self.app.converter_format_combo['values'] = final_formats
            
            # Убираем автоматическую установку формата - пользователь должен выбрать сам
            # Просто очищаем значение, если текущее не в списке
            current_value = self.app.converter_format_var.get()
            if current_value not in final_formats:
                self.app.converter_format_var.set('')
        
        # Обновляем заголовок панели
        if hasattr(self.app, 'converter_left_panel'):
            total_count = len(self.app.converter_files)
            if filter_type == "Все":
                self.app.converter_left_panel.config(text=f"Список файлов (Файлов: {total_count})")
            else:
                self.app.converter_left_panel.config(text=f"Список файлов (Файлов: {visible_count} / {total_count})")
        
        # Обновляем путь файлов
        if hasattr(self.app, 'update_converter_path'):
            self.app.root.after_idle(self.app.update_converter_path)
    
    def convert_files(self):
        """Конвертация выбранных файлов"""
        # Защита от повторных вызовов
        if hasattr(self.app, '_converting_files') and self.app._converting_files:
            return
        
        if not hasattr(self.app, 'converter_files') or not self.app.converter_files:
            messagebox.showwarning("Предупреждение", "Список файлов пуст")
            return
        
        target_format = self.app.converter_format_var.get()
        if not target_format:
            messagebox.showwarning("Предупреждение", "Выберите целевой формат")
            return
        
        selected_items = self.app.converter_tree.selection()
        files_to_convert = self.app.converter_files
        
        # Если ничего не выбрано, конвертируем все
        if not selected_items:
            log_batch_action(
                logger=logger,
                action='CONVERT_STARTED',
                message=f"Начало конвертации всех файлов в формат {target_format}",
                file_count=len(files_to_convert),
                method_name='convert_files',
                details={'target_format': target_format, 'selection': 'all'}
            )
            if not messagebox.askyesno("Подтверждение", 
                                      f"Конвертировать все {len(files_to_convert)} файл(ов) в {target_format}?"):
                log_action(
                    logger=logger,
                    level=logging.INFO,
                    action='CONVERT_CANCELLED',
                    message="Конвертация отменена пользователем",
                    method_name='convert_files',
                    file_count=len(files_to_convert)
                )
                return
        else:
            log_batch_action(
                logger=logger,
                action='CONVERT_STARTED',
                message=f"Начало конвертации выбранных файлов в формат {target_format}",
                file_count=len(selected_items),
                method_name='convert_files',
                details={'target_format': target_format, 'selection': 'selected'}
            )
            confirm_msg = (
                f"Конвертировать {len(selected_items)} "
                f"файл(ов) в {target_format}?"
            )
            if not messagebox.askyesno("Подтверждение", confirm_msg):
                log_action(
                    logger=logger,
                    level=logging.INFO,
                    action='CONVERT_CANCELLED',
                    message="Конвертация отменена пользователем",
                    method_name='convert_files',
                    file_count=len(selected_items)
                )
                return
            # Фильтруем только выбранные файлы
            indices = [self.app.converter_tree.index(item) for item in selected_items]
            files_to_convert = [self.app.converter_files[i] for i in indices if 0 <= i < len(self.app.converter_files)]
        
        # Устанавливаем флаг обработки
        self.app._converting_files = True
        log_batch_action(
            logger=logger,
            action='CONVERT_PROCESSING',
            message=f"Начало конвертации файлов в формат {target_format}",
            file_count=len(files_to_convert),
            method_name='convert_files',
            details={'target_format': target_format}
        )
        
        # Инициализируем прогресс-бар
        total_files = len(files_to_convert)
        self.app.root.after(
            0,
            lambda: self.app.converter_progress_bar.config(
                maximum=total_files,
                value=0
            )
        )
        self.app.root.after(
            0,
            lambda: self.app.converter_progress_label.config(
                text=f"Обработка файлов: 0 / {total_files}"
            )
        )
        
        # Обрабатываем файлы в отдельном потоке
        def process_files():
            import time
            start_time = time.time()
            log_batch_action(
                logger=logger,
                action='CONVERT_PROCESSING_STARTED',
                message=f"Начало обработки файлов для конвертации",
                file_count=len(files_to_convert),
                method_name='process_files',
                details={'target_format': target_format}
            )
            success_count = 0
            error_count = 0
            processed = 0
            files_to_remove = []  # Список файлов для удаления после конвертации
            
            for file_data in files_to_convert:
                file_path = file_data['path']
                file_start_time = time.time()
                log_file_action(
                    logger=logger,
                    action='CONVERT_FILE_STARTED',
                    message=f"Конвертация файла {processed + 1}/{len(files_to_convert)}",
                    file_path=file_path,
                    method_name='process_files',
                    details={
                        'file_number': processed + 1,
                        'total_files': len(files_to_convert),
                        'target_format': target_format
                    }
                )
                
                # Обновляем прогресс
                processed += 1
                file_name = os.path.basename(file_path)
                self.app.root.after(0, lambda p=processed, t=total_files, fn=file_name: 
                               self.update_converter_progress(p, t, fn))
                
                # Получаем значение чекбокса сжатия PDF
                compress_pdf = getattr(self.app, 'compress_pdf_var', tk.BooleanVar(value=False)).get()
                success, message, output_path = self.app.file_converter.convert(
                    file_path, target_format, compress_pdf=compress_pdf
                )
                file_duration = (time.time() - file_start_time) * 1000  # в миллисекундах
                
                # Находим индекс файла
                try:
                    index = self.app.converter_files.index(file_data)
                except ValueError:
                    index = -1
                
                # Обновляем статус в UI
                if index >= 0:
                    self.app.root.after(0, lambda idx=index, s=success, m=message, op=output_path: 
                                       self.update_converter_status(idx, s, m, op))
                
                if success:
                    success_count += 1
                    log_file_action(
                        logger=logger,
                        action='CONVERT_FILE_SUCCESS',
                        message=f"Файл успешно конвертирован",
                        file_path=file_path,
                        old_name=os.path.basename(file_path),
                        new_name=os.path.basename(output_path) if output_path else None,
                        method_name='process_files',
                        duration_ms=file_duration,
                        details={'output_path': output_path, 'target_format': target_format}
                    )
                    output_name = (
                        os.path.basename(output_path)
                        if output_path
                        else 'N/A'
                    )
                    self.app.log(
                        f"Файл конвертирован: "
                        f"{os.path.basename(file_path)} -> {output_name}"
                    )
                    
                    # Добавляем файл в список для удаления после завершения конвертации
                    if hasattr(self.app, 'remove_files_after_operation_var'):
                        if self.app.remove_files_after_operation_var.get():
                            files_to_remove.append(file_data)
                else:
                    error_count += 1
                    log_file_action(
                        logger=logger,
                        action='CONVERT_FILE_ERROR',
                        message=f"Ошибка при конвертации файла: {message}",
                        file_path=file_path,
                        method_name='process_files',
                        duration_ms=file_duration,
                        details={'error_message': message, 'target_format': target_format}
                    )
                    logger.error(f"Ошибка при конвертации файла {file_path}: {message}")
                    self.app.log(f"Ошибка при конвертации {os.path.basename(file_path)}: {message}")
            
            # Сбрасываем прогресс-бар
            self.app.root.after(0, lambda: self.app.converter_progress_bar.config(value=0))
            self.app.root.after(0, lambda: self.app.converter_progress_label.config(text=""))
            
            total_duration = (time.time() - start_time) * 1000  # в миллисекундах
            log_batch_action(
                logger=logger,
                action='CONVERT_COMPLETED',
                message=f"Конвертация завершена",
                file_count=success_count + error_count,
                success_count=success_count,
                error_count=error_count,
                method_name='process_files',
                duration_ms=total_duration,
                details={'target_format': target_format}
            )
            
            # Удаляем файлы из списка после завершения конвертации всех файлов
            if files_to_remove:
                def remove_files():
                    try:
                        for file_data in files_to_remove:
                            if file_data in self.app.converter_files:
                                self.app.converter_files.remove(file_data)
                        # Обновляем интерфейс один раз после удаления всех файлов
                        self.filter_converter_files_by_type()
                    except (ValueError, AttributeError):
                        pass
                self.app.root.after(0, remove_files)
            
            # Показываем результат только один раз
            if success_count + error_count > 0:
                def show_converter_result():
                    # Проверяем, не было ли уже показано сообщение
                    if not hasattr(self.app, '_converter_result_shown'):
                        self.app._converter_result_shown = True
                        messagebox.showinfo(
                            "Результат",
                            f"Обработано файлов: {success_count + error_count}\n"
                            f"Успешно: {success_count}\n"
                            f"Ошибок: {error_count}"
                        )
                        # Сбрасываем флаг показа сообщения
                        self.app.root.after(100, lambda: setattr(self.app, '_converter_result_shown', False))
                    # Сбрасываем флаг обработки
                    self.app._converting_files = False
                
                self.app.root.after(0, show_converter_result)
            else:
                # Если не было файлов для обработки, сбрасываем флаг
                logger.info(f"Конвертация завершена: успешно {success_count}, ошибок {error_count}")
                self.app._converting_files = False
        
        thread = threading.Thread(target=process_files, daemon=True)
        thread.start()
        logger.info("Поток конвертации файлов запущен")
    
    def update_converter_progress(self, current: int, total: int, filename: str):
        """Обновление прогресс-бара конвертации"""
        try:
            self.app.converter_progress_bar['value'] = current
            self.app.converter_progress_label.config(text=f"Обработка: {current} / {total} - {filename[:50]}")
        except Exception:
            pass
    
    def update_converter_status(self, index: int, success: bool, message: str, output_path: Optional[str]):
        """Обновление статуса файла в списке конвертации"""
        if not hasattr(self.app, 'converter_tree'):
            return
        
        # Обновляем статус в данных файла
        status_text = ''
        if 0 <= index < len(self.app.converter_files):
            file_data = self.app.converter_files[index]
            if success:
                file_data['status'] = 'Конвертирован'
                status_text = 'Конвертирован'
            else:
                file_data['status'] = f"Ошибка: {message[:50]}"
                status_text = f"Ошибка: {message[:50]}"
        
        # Обновляем отображение в дереве
        items = self.app.converter_tree.get_children()
        if 0 <= index < len(items):
            item = items[index]
            # Получаем текущие значения
            current_values = self.app.converter_tree.item(item, 'values')
            file_name = current_values[0] if current_values else ''
            
            # Определяем тег в зависимости от статуса
            if success:
                tag = 'success'
            else:
                tag = 'error'
            
            # Обновляем элемент с новым статусом
            self.app.converter_tree.item(item, values=(file_name, status_text), tags=(tag,))
            
            # Обновляем фильтр для отображения изменений
            self.filter_converter_files_by_type()
    
    def _check_if_file_already_converted(self, file_path: str, available_formats: list) -> Optional[str]:
        """Проверка, был ли файл уже конвертирован.
        
        Args:
            file_path: Путь к файлу
            available_formats: Список доступных форматов для конвертации
            
        Returns:
            'Конвертирован' если файл уже конвертирован, None иначе
        """
        if not available_formats:
            return None
        
        try:
            file_dir = os.path.dirname(file_path)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Проверяем наличие конвертированных версий для всех доступных форматов
            for target_format in available_formats:
                # Формируем путь к возможному выходному файлу
                target_ext = target_format.lower()
                if not target_ext.startswith('.'):
                    target_ext = '.' + target_ext
                
                output_path = os.path.join(file_dir, base_name + target_ext)
                
                # Если выходной файл существует и отличается от исходного
                if os.path.exists(output_path) and os.path.isfile(output_path):
                    source_ext = os.path.splitext(file_path)[1].lower()
                    if output_path.lower() != file_path.lower():
                        return 'Конвертирован'
        except Exception as e:
            logger.debug(f"Ошибка при проверке конвертированных файлов: {e}")
        
        return None
    
    def clear_converter_files_list(self):
        """Очистка списка файлов для конвертации"""
        if not hasattr(self.app, 'converter_tree'):
            return
        
        if messagebox.askyesno("Подтверждение", "Очистить список файлов?"):
            files_count = len(self.app.converter_files) if hasattr(self.app, 'converter_files') else 0
            logger.info(f"Очистка списка файлов для конвертации: удалено {files_count} файлов")
            self.app.converter_tree.delete(*self.app.converter_tree.get_children())
            self.app.converter_files = []
            # Обновляем заголовок панели
            if hasattr(self.app, 'converter_left_panel'):
                self.app.converter_left_panel.config(text=f"Список файлов (Файлов: 0)")
            # Обновляем путь
            if hasattr(self.app, 'update_converter_path'):
                self.app.root.after_idle(self.app.update_converter_path)
            # Обновляем видимость скроллбаров после очистки
            if hasattr(self.app, 'converter_scrollbar_y') and hasattr(self.app, 'converter_scrollbar_x'):
                self.app.root.after_idle(lambda: self.app.update_scrollbar_visibility(
                    self.app.converter_tree, self.app.converter_scrollbar_y, 'vertical'))
                self.app.root.after_idle(lambda: self.app.update_scrollbar_visibility(
                    self.app.converter_tree, self.app.converter_scrollbar_x, 'horizontal'))
            self.app.log("Список файлов для конвертации очищен")
    
    def setup_converter_drag_drop(self, list_frame, tree, tab_frame):
        """Настройка drag and drop для вкладки конвертации"""
        if not HAS_TKINTERDND2:
            return
        
        try:
            # Регистрируем фрейм списка файлов
            if hasattr(list_frame, 'drop_target_register'):
                list_frame.drop_target_register(DND_FILES)
                list_frame.dnd_bind('<<Drop>>', lambda e: self.on_drop_converter_files(e))
            
            # Регистрируем treeview
            if hasattr(tree, 'drop_target_register'):
                tree.drop_target_register(DND_FILES)
                tree.dnd_bind('<<Drop>>', lambda e: self.on_drop_converter_files(e))
            
            # Регистрируем всю вкладку
            if hasattr(tab_frame, 'drop_target_register'):
                tab_frame.drop_target_register(DND_FILES)
                tab_frame.dnd_bind('<<Drop>>', lambda e: self.on_drop_converter_files(e))
        except Exception as e:
            logger.debug(f"Не удалось настроить drag and drop для вкладки конвертации: {e}")
    
    def on_drop_converter_files(self, event):
        """Обработка перетаскивания файлов на вкладку конвертации"""
        try:
            data = event.data
            if not data:
                return
            
            # Используем надежную логику парсинга из ui/drag_drop.py
            file_paths = []
            
            # Обрабатываем строку с путями (формат зависит от платформы)
            if sys.platform == 'win32':
                # Windows: пути могут быть в фигурных скобках {path1} {path2}
                # Используем regex для более надежного парсинга
                file_paths = re.findall(r'\{([^}]+)\}', data)
                if not file_paths:
                    # Если нет фигурных скобок, пробуем разделить по пробелам
                    # Но это может быть проблематично для путей с пробелами
                    file_paths = data.split()
            else:
                # Linux/Mac: пути разделены пробелами
                file_paths = data.split()
            
            # Очищаем пути от лишних пробелов и кавычек
            file_paths = [f.strip().strip('"').strip("'") for f in file_paths if f.strip()]
            
            # Фильтруем только существующие файлы
            valid_file_paths = [f for f in file_paths if os.path.exists(f) and os.path.isfile(f)]
            
            # Обрабатываем файлы
            added_count = 0
            for file_path in valid_file_paths:
                if not file_path:
                    continue
                
                try:
                    if not os.path.isabs(file_path):
                        file_path = os.path.abspath(file_path)
                    else:
                        file_path = os.path.normpath(file_path)
                except Exception:
                    continue
                
                if not os.path.exists(file_path) or not os.path.isfile(file_path):
                    continue
                
                # Проверяем, что файл еще не добавлен
                normalized_path = os.path.normpath(os.path.abspath(file_path))
                if any(os.path.normpath(os.path.abspath(f.get('path', ''))) == normalized_path 
                       for f in self.app.converter_files):
                    continue
                
                ext = os.path.splitext(file_path)[1].lower()
                
                # Определяем доступные форматы конвертации
                available_formats = []
                all_formats = self.app.file_converter.get_supported_formats()
                for target_format in all_formats:
                    if self.app.file_converter.can_convert(file_path, target_format):
                        available_formats.append(target_format)
                
                # Определяем категорию файла
                file_category = self.app.file_converter.get_file_type_category(file_path)
                
                # Определяем статус файла
                # Проверяем, был ли файл уже конвертирован
                status = self._check_if_file_already_converted(file_path, available_formats)
                if not status:
                    if available_formats:
                        status = 'Готов'
                    else:
                        status = 'Не поддерживается'
                
                file_data = {
                    'path': file_path,
                    'format': ext,
                    'status': status,
                    'available_formats': available_formats,  # Сохраняем список форматов, а не строку
                    'category': file_category  # Сохраняем категорию файла
                }
                self.app.converter_files.append(file_data)
                
                # Автоматически устанавливаем фильтр по типу файла при первом добавлении
                if hasattr(self.app, 'converter_filter_var') and self.app.converter_filter_var.get() == "Все":
                    category_mapping = {
                        'image': 'Изображения',
                        'document': 'Документы',
                        'spreadsheet': 'Таблицы',
                        'presentation': 'Презентации',
                        'audio': 'Аудио',
                        'video': 'Видео'
                    }
                    filter_name = category_mapping.get(file_category)
                    if filter_name:
                        self.app.converter_filter_var.set(filter_name)
                        # Обновляем список форматов для этого типа
                        self.update_available_formats()
                
                added_count += 1
            
            if added_count > 0:
                # Обновляем заголовок панели
                if hasattr(self.app, 'converter_left_panel'):
                    count = len(self.app.converter_files)
                    self.app.converter_left_panel.config(text=f"Список файлов (Файлов: {count})")
                # Применяем фильтр - это обновит treeview и доступные форматы
                self.filter_converter_files_by_type()
                # Обновляем путь
                if hasattr(self.app, 'update_converter_path'):
                    self.app.root.after_idle(self.app.update_converter_path)
                self.app.log(f"Добавлено файлов для конвертации перетаскиванием: {added_count}")
        except Exception as e:
            logger.error(f"Ошибка при обработке перетаскивания файлов для конвертации: {e}", exc_info=True)
    
    def show_converter_context_menu(self, event):
        """Показ контекстного меню для файла в конвертации"""
        item = self.app.converter_tree.identify_row(event.y)
        if not item:
            return
        
        # Выделяем элемент, если он не выделен
        if item not in self.app.converter_tree.selection():
            self.app.converter_tree.selection_set(item)
        
        # Создаем контекстное меню (такое же оформление как в файлах)
        context_menu = tk.Menu(self.app.root, tearoff=0, 
                              bg=self.app.colors.get('bg_card', '#ffffff'),
                              fg=self.app.colors.get('text_primary', '#000000'),
                              activebackground=self.app.colors.get('primary', '#4a90e2'),
                              activeforeground='white')
        
        context_menu.add_command(label="Удалить из списка", command=self.remove_selected_converter_files)
        context_menu.add_separator()
        context_menu.add_command(label="Открыть файл", command=self.open_converter_file)
        context_menu.add_command(label="Открыть путь", command=self.open_converter_file_folder)
        context_menu.add_separator()
        context_menu.add_command(label="Копировать путь", command=self.copy_converter_file_path)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def open_converter_file(self):
        """Открытие файла конвертации в программе по умолчанию"""
        selected_items = self.app.converter_tree.selection()
        if not selected_items:
            return
        
        for item in selected_items:
            values = self.app.converter_tree.item(item, 'values')
            if not values or len(values) < 1:
                continue
            
            file_name = values[0]
            # Находим файл в списке
            file_info = None
            for f in self.app.converter_files:
                if os.path.basename(f.get('path', '')) == file_name:
                    file_info = f
                    break
            
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
    
    def open_converter_file_folder(self):
        """Открытие папки с выбранным файлом конвертации"""
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
            # Находим файл в списке
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
    
    def copy_converter_file_path(self):
        """Копирование пути файла конвертации в буфер обмена"""
        selected_items = self.app.converter_tree.selection()
        if not selected_items:
            return
        
        paths = []
        for item in selected_items:
            values = self.app.converter_tree.item(item, 'values')
            if not values or len(values) < 1:
                continue
            
            file_name = values[0]
            # Находим файл в списке
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
                self.app.log(
                    f"Путь{path_word} скопирован{copied_word} "
                    f"в буфер обмена"
                )
            except Exception as e:
                logger.error(f"Ошибка копирования пути: {e}", exc_info=True)
    
    def remove_selected_converter_files(self):
        """Удаление выбранных файлов из списка конвертации"""
        selected_items = self.app.converter_tree.selection()
        if not selected_items:
            return
        
        # Получаем имена файлов для удаления
        files_to_remove = []
        for item in selected_items:
            values = self.app.converter_tree.item(item, 'values')
            if values and len(values) > 0:
                files_to_remove.append(values[0])
        
        # Удаляем файлы из списка
        if hasattr(self.app, 'converter_files'):
            self.app.converter_files = [f for f in self.app.converter_files 
                                        if os.path.basename(f.get('path', '')) not in files_to_remove]
        
        # Обновляем отображение
        self.filter_converter_files_by_type()
        # Обновляем путь
        if hasattr(self.app, 'update_converter_path'):
            self.app.root.after_idle(self.app.update_converter_path)
        self.app.log(f"Удалено файлов из списка конвертации: {len(files_to_remove)}")


if __name__ == "__main__":
    """Точка входа для прямого запуска модуля."""
    import sys
    import os
    
    # Добавляем корневую директорию проекта в путь
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Запускаем главное приложение
    try:
        from file_renamer import main
        main()
    except ImportError as e:
        print(f"Ошибка импорта: {e}")
        print("Убедитесь, что вы запускаете из корневой директории проекта")
        sys.exit(1)
    except Exception as e:
        print(f"Ошибка при запуске: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

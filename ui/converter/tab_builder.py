"""Модуль для создания UI вкладки конвертации.

Содержит классы для построения интерфейса вкладки конвертации файлов.
"""

import tkinter as tk
from tkinter import ttk


class ConverterTabBuilder:
    """Класс для построения UI вкладки конвертации."""
    
    def __init__(self, app, converter_tab):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
            converter_tab: Экземпляр ConverterTab для доступа к методам
        """
        self.app = app
        self.converter_tab = converter_tab
    
    def create_tab(self):
        """Создание вкладки конвертации файлов на главном экране (старый метод для обратной совместимости)"""
        # Если используется новая структура с content_container, создаем содержимое там
        if hasattr(self.app, 'content_container') and self.app.content_container:
            self.create_tab_content(self.app.content_container)
            return
        
        # Старая структура с Notebook (для обратной совместимости)
        if not hasattr(self.app, 'main_notebook') or not self.app.main_notebook:
            return
        
        converter_tab = tk.Frame(self.app.main_notebook, bg=self.app.colors['bg_main'])
        converter_tab.columnconfigure(0, weight=1)
        converter_tab.rowconfigure(0, weight=1)
        self.app.main_notebook.add(converter_tab, text="Конвертация файлов")
        
        # Используем общий treeview (не создаем отдельное дерево)
        if hasattr(self.app, 'tree'):
            self.app.converter_tree = self.app.tree
            self.app.converter_scrollbar_y = self.app.tree_scrollbar_y
            self.app.converter_scrollbar_x = self.app.tree_scrollbar_x
            self.app.converter_list_frame = self.app.list_frame
        
        # Основной контейнер (как во вкладке "Файлы")
        main_container = tk.Frame(converter_tab, bg=self.app.colors['bg_main'])
        main_container.grid(row=0, column=0, sticky="nsew")
        # Левая панель занимает 60%, правая - 40%
        main_container.columnconfigure(0, weight=6, uniform="panels")
        main_container.columnconfigure(1, weight=4, uniform="panels")
        main_container.rowconfigure(0, weight=1)
        
        # Создаем только правую панель (левая панель с общим деревом уже существует)
        self._create_right_panel(main_container)
    
    def _create_left_panel(self, main_container, converter_tab):
        """Создание левой панели со списком файлов."""
        # Левая часть - список файлов (как во вкладке "Файлы")
        files_count = len(self.app.converter_files) if hasattr(self.app, 'converter_files') else 0
        left_panel = ttk.LabelFrame(
            main_container,
            text=f"Список файлов (Файлов: {files_count})",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=(20, 20))
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(1, weight=1)
        
        # Сохраняем ссылку на left_panel для обновления заголовка
        self.app.converter_left_panel = left_panel
        
        # Кнопки управления
        self._create_left_panel_buttons(left_panel)
        
        # Таблица файлов
        list_frame, tree = self._create_file_tree(left_panel)
        
        # Настройка drag and drop
        self.converter_tab.setup_converter_drag_drop(list_frame, tree, converter_tab)
        
        # Инициализация списка файлов
        if not hasattr(self.app, 'converter_files'):
            self.app.converter_files = []
    
    def _create_left_panel_buttons(self, left_panel):
        """Создание кнопок управления в левой панели."""
        buttons_frame_left = tk.Frame(left_panel, bg=self.app.colors['bg_main'])
        buttons_frame_left.pack(fill=tk.X, pady=(0, 12))
        
        buttons_frame_left.columnconfigure(0, weight=1, uniform="buttons")
        buttons_frame_left.columnconfigure(1, weight=1, uniform="buttons")
        
        btn_add_files_left = self.app.create_rounded_button(
            buttons_frame_left, "➕ Добавить файлы", self.converter_tab.add_files_for_conversion,
            self.app.colors['primary'], 'white', 
            font=('Robot', 9, 'bold'), padx=10, pady=6,
            active_bg=self.app.colors['primary_hover'])
        btn_add_files_left.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        btn_clear_left = self.app.create_rounded_button(
            buttons_frame_left, "🗑️ Очистить", self.converter_tab.clear_converter_files_list,
            self.app.colors['warning'], 'white',
            font=('Robot', 9, 'bold'), padx=10, pady=6,
            active_bg=self.app.colors['warning_hover'])
        btn_clear_left.grid(row=0, column=1, sticky="ew")
    
    def _create_file_tree(self, left_panel):
        """Создание таблицы файлов с прокруткой."""
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
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
        
        # Настройка колонок
        tree.heading("file", text="Файл")
        tree.heading("status", text="Статус")
        tree.column("file", width=300, anchor='w', minwidth=100, stretch=tk.YES)
        tree.column("status", width=300, anchor='w', minwidth=100, stretch=tk.YES)
        
        # Настройка тегов для цветового выделения
        tree.tag_configure('ready', background='#D1FAE5', foreground='#065F46')  # Зеленый - готов
        tree.tag_configure('in_progress', background='#FEF3C7', foreground='#92400E')  # Желтый - в работе
        tree.tag_configure('success', background='#D1FAE5', foreground='#065F46')
        tree.tag_configure('error', background='#FEE2E2', foreground='#991B1B')
        tree.tag_configure('path_row', 
                          background=self.app.colors.get('bg_main', '#F3F4F6'),
                          foreground=self.app.colors.get('text_secondary', '#6B7280'),
                          font=('Robot', 8))
        
        # Размещение
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Сохраняем ссылки
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
                    if frame_width > 100:
                        available_width = max(frame_width - 30, 200)
                        column_width = int(available_width / 2)
                        self.app.converter_tree.column("file", width=column_width, minwidth=150)
                        self.app.converter_tree.column("status", width=column_width, minwidth=150)
                except (AttributeError, tk.TclError):
                    pass
        
        list_frame.bind('<Configure>', update_converter_columns)
        self.app.root.after(200, update_converter_columns)
        
        # Привязка прокрутки колесом мыши
        self.app.bind_mousewheel(tree, tree)
        
        # Контекстное меню
        tree.bind('<Button-3>', self.converter_tab.show_converter_context_menu)
        
        # Автоматическое управление видимостью скроллбаров
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
        
        tree.bind('<<TreeviewSelect>>', lambda e: (self.converter_tab.update_available_formats(), update_converter_scrollbars()))
        tree.bind('<Configure>', lambda e: update_converter_scrollbars())
        self.app.root.after(200, update_converter_scrollbars)
        
        return list_frame, tree
    
    def _create_right_panel(self, main_container):
        """Создание правой панели с настройками конвертации."""
        right_panel = ttk.LabelFrame(
            main_container,
            text="Настройки конвертации",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)
        )
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(2, 0), pady=(20, 20))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        settings_frame = tk.Frame(right_panel, bg=self.app.colors['bg_main'])
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        
        # Фильтр по типу файла
        self._create_filter_combobox(settings_frame)
        
        # Выбор формата
        self._create_format_combobox(settings_frame)
        
        # Разделитель перед кнопками
        separator_buttons = tk.Frame(right_panel, height=2, bg=self.app.colors['border'])
        separator_buttons.pack(fill=tk.X, padx=6, pady=(6, 0))
        
        # Кнопка конвертации
        buttons_frame = tk.Frame(right_panel, bg=self.app.colors['bg_main'])
        buttons_frame.pack(fill=tk.X, padx=6, pady=(6, 0))
        
        btn_convert = self.app.create_rounded_button(
            buttons_frame, "🔄 Конвертировать", self.converter_tab.convert_files,
            self.app.colors['success'], 'white',
            font=('Robot', 9, 'bold'), padx=10, pady=6,
            active_bg=self.app.colors['success_hover'])
        btn_convert.pack(fill=tk.X)
    
    def _create_filter_combobox(self, settings_frame):
        """Создание combobox для фильтра по типу файла."""
        filter_label = tk.Label(settings_frame, text="Фильтр по типу:",
                               font=('Robot', 9, 'bold'),
                               bg=self.app.colors['bg_main'],
                               fg=self.app.colors['text_primary'],
                               anchor='w')
        filter_label.pack(anchor=tk.W, pady=(0, 6))
        
        filter_var = tk.StringVar(value="Все")
        filter_combo = ttk.Combobox(
            settings_frame,
            textvariable=filter_var,
            values=["Все", "Изображения", "Документы", "Презентации"],
            state='readonly',
            width=15
        )
        filter_combo.pack(fill=tk.X, pady=(0, 10))
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.converter_tab.filter_converter_files_by_type())
        
        self.app.converter_filter_var = filter_var
        self.app.converter_filter_combo = filter_combo
        
        # Применяем фильтр при инициализации
        self.app.root.after(100, lambda: self.converter_tab.filter_converter_files_by_type())
    
    def _create_format_combobox(self, settings_frame):
        """Создание combobox для выбора формата."""
        format_label = tk.Label(settings_frame, text="Целевой формат:",
                               font=('Robot', 9, 'bold'),
                               bg=self.app.colors['bg_main'],
                               fg=self.app.colors['text_primary'],
                               anchor='w')
        format_label.pack(anchor=tk.W, pady=(0, 12))
        
        formats = self.app.file_converter.get_supported_formats()
        format_var = tk.StringVar(value=formats[0] if formats else '.png')
        format_combo = ttk.Combobox(settings_frame, textvariable=format_var,
                                   values=formats, state='readonly', width=15)
        format_combo.pack(fill=tk.X, pady=(0, 10))
        
        self.app.converter_format_var = format_var
        self.app.converter_format_combo = format_combo
    
    def create_tab_content(self, parent):
        """Создание содержимого вкладки конвертации (только правая панель с настройками).
        Список файлов используется общий из files_container.
        
        Args:
            parent: Родительский контейнер для размещения содержимого
        """
        convert_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        convert_frame.grid(row=0, column=0, sticky="nsew")
        convert_frame.columnconfigure(0, weight=1)
        convert_frame.rowconfigure(0, weight=1)
        
        self.app.tab_contents["convert"] = convert_frame
        
        # Используем общий список файлов для конвертации
        if hasattr(self.app, 'tree'):
            self.app.converter_tree = self.app.tree
            self.app.converter_scrollbar_y = self.app.tree_scrollbar_y
            self.app.converter_scrollbar_x = self.app.tree_scrollbar_x
            self.app.converter_list_frame = self.app.list_frame
        
        # Создаем правую панель
        self._create_right_panel_content(convert_frame)
    
    def _create_right_panel_content(self, convert_frame):
        """Создание правой панели для новой структуры."""
        right_panel = ttk.LabelFrame(
            convert_frame,
            text="Настройки конвертации",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)
        )
        right_panel.grid(row=0, column=0, sticky="nsew", padx=(2, 0), pady=(20, 20))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        settings_frame = tk.Frame(right_panel, bg=self.app.colors['bg_main'])
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        
        # Фильтр по типу файла
        self._create_filter_combobox(settings_frame)
        
        # Выбор формата
        self._create_format_combobox(settings_frame)
        
        # Разделитель перед кнопками
        separator_buttons = tk.Frame(right_panel, height=2, bg=self.app.colors['border'])
        separator_buttons.pack(fill=tk.X, padx=6, pady=(6, 0))
        
        # Кнопка конвертации
        buttons_frame = tk.Frame(right_panel, bg=self.app.colors['bg_main'])
        buttons_frame.pack(fill=tk.X, padx=6, pady=(6, 0))
        
        btn_convert = self.app.create_rounded_button(
            buttons_frame, "🔄 Конвертировать", self.converter_tab.convert_files,
            self.app.colors['success'], 'white',
            font=('Robot', 9, 'bold'), padx=10, pady=6,
            active_bg=self.app.colors['success_hover'])
        btn_convert.pack(fill=tk.X)


"""UI компоненты вкладки конвертации."""

import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)


class ConverterUI:
    """Класс для создания UI компонентов вкладки конвертации."""
    
    def __init__(self, app, parent_frame):
        """Инициализация UI компонентов.
        
        Args:
            app: Экземпляр приложения
            parent_frame: Родительский фрейм для вкладки
        """
        self.app = app
        self.parent_frame = parent_frame
        self._create_ui()
    
    def _create_ui(self):
        """Создание UI компонентов."""
        # Основной контейнер
        main_container = tk.Frame(self.parent_frame, bg=self.app.colors['bg_main'])
        main_container.grid(row=0, column=0, sticky="nsew")
        main_container.columnconfigure(0, weight=6, uniform="panels")
        main_container.columnconfigure(1, weight=4, uniform="panels")
        main_container.rowconfigure(0, weight=1)
        
        # Левая панель - список файлов
        self._create_left_panel(main_container)
        
        # Правая панель - настройки
        self._create_right_panel(main_container)
    
    def _create_left_panel(self, parent):
        """Создание левой панели со списком файлов."""
        files_count = len(self.app.converter_files) if hasattr(self.app, 'converter_files') else 0
        left_panel = ttk.LabelFrame(
            parent,
            text=f"Список файлов (Файлов: {files_count})",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=(20, 20))
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(1, weight=1)
        
        self.app.converter_left_panel = left_panel
        
        # Кнопки управления
        buttons_frame = tk.Frame(left_panel, bg=self.app.colors['bg_card'])
        buttons_frame.pack(fill=tk.X, pady=(0, 6))
        buttons_frame.columnconfigure(0, weight=1, uniform="buttons")
        buttons_frame.columnconfigure(1, weight=1, uniform="buttons")
        
        # Кнопки будут привязаны в основном классе
        self.buttons_frame = buttons_frame
        
        # Таблица файлов
        self._create_file_tree(left_panel)
        
        # Прогресс-бар
        self._create_progress_bar(left_panel)
    
    def _create_file_tree(self, parent):
        """Создание таблицы файлов."""
        list_frame = ttk.Frame(parent)
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
        
        tree.heading("file", text="Файл")
        tree.heading("status", text="Статус")
        tree.column("file", width=300, anchor='w', minwidth=150, stretch=tk.YES)
        tree.column("status", width=300, anchor='center', minwidth=150, stretch=tk.YES)
        
        # Теги для цветового выделения
        tree.tag_configure('ready', background='#FEF3C7', foreground='#92400E')
        tree.tag_configure('success', background='#D1FAE5', foreground='#065F46')
        tree.tag_configure('error', background='#FEE2E2', foreground='#991B1B')
        
        tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        self.app.converter_tree = tree
        self.app.converter_scrollbar_y = scrollbar_y
        self.app.converter_scrollbar_x = scrollbar_x
        self.app.converter_list_frame = list_frame
    
    def _create_progress_bar(self, parent):
        """Создание прогресс-бара."""
        progress_container = tk.Frame(parent, bg=self.app.colors['bg_card'])
        progress_container.pack(fill=tk.X, pady=(6, 0))
        progress_container.columnconfigure(0, weight=0)
        progress_container.columnconfigure(1, weight=1)
        
        progress_title = tk.Label(
            progress_container,
            text="Прогресс:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_card'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        progress_title.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        progress_bar = ttk.Progressbar(progress_container, mode='determinate')
        progress_bar.grid(row=0, column=1, sticky="ew")
        progress_bar['value'] = 0
        
        progress_label = tk.Label(
            progress_container,
            text="",
            font=('Robot', 8),
            bg=self.app.colors['bg_card'],
            fg=self.app.colors['text_secondary'],
            anchor='w'
        )
        progress_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        
        self.app.converter_progress_bar = progress_bar
        self.app.converter_progress_label = progress_label
    
    def _create_right_panel(self, parent):
        """Создание правой панели с настройками."""
        right_panel = ttk.LabelFrame(
            parent,
            text="Настройки конвертации",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)
        )
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(2, 0), pady=(20, 20))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        settings_frame = tk.Frame(right_panel, bg=self.app.colors['bg_card'])
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        
        # Фильтр по типу
        self._create_filter_combo(settings_frame)
        
        # Выбор формата
        self._create_format_combo(settings_frame)
        
        # Чекбокс сжатия PDF
        self._create_compress_checkbox(settings_frame)
        
        # Кнопки управления
        self._create_action_buttons(right_panel)
    
    def _create_filter_combo(self, parent):
        """Создание комбобокса фильтра."""
        filter_label = tk.Label(
            parent,
            text="Фильтр по типу:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_card'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        filter_label.pack(anchor=tk.W, pady=(0, 6))
        
        filter_var = tk.StringVar(value="Все")
        filter_combo = ttk.Combobox(
            parent,
            textvariable=filter_var,
            values=["Все", "Изображения", "Документы", "Таблицы", "Презентации", "Аудио", "Видео"],
            state='readonly',
            width=15
        )
        filter_combo.pack(fill=tk.X, pady=(0, 10))
        
        self.app.converter_filter_var = filter_var
        self.app.converter_filter_combo = filter_combo
    
    def _create_format_combo(self, parent):
        """Создание комбобокса формата."""
        format_label = tk.Label(
            parent,
            text="Целевой формат:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_card'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        format_label.pack(anchor=tk.W, pady=(0, 12))
        
        formats = self.app.file_converter.get_supported_formats()
        format_var = tk.StringVar(value=formats[0] if formats else '.png')
        format_combo = ttk.Combobox(
            parent,
            textvariable=format_var,
            values=formats,
            state='readonly',
            width=15
        )
        format_combo.pack(fill=tk.X, pady=(0, 10))
        
        self.app.converter_format_var = format_var
        self.app.converter_format_combo = format_combo
    
    def _create_compress_checkbox(self, parent):
        """Создание чекбокса сжатия PDF."""
        compress_pdf_var = tk.BooleanVar(value=False)
        compress_pdf_check = tk.Checkbutton(
            parent,
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
    
    def _create_action_buttons(self, parent):
        """Создание кнопок действий."""
        separator = tk.Frame(parent, height=2, bg=self.app.colors['border'])
        separator.pack(fill=tk.X, padx=6, pady=(6, 0))
        
        buttons_frame = tk.Frame(parent, bg=self.app.colors['bg_card'])
        buttons_frame.pack(fill=tk.X, padx=6, pady=(6, 0))
        
        # Кнопка будет привязана в основном классе
        self.action_buttons_frame = buttons_frame


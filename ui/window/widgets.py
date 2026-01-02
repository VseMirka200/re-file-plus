"""Модуль для создания основных виджетов главного окна."""

import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)


class MainWindowWidgets:
    """Класс для создания основных виджетов главного окна.
    
    Отвечает за создание и настройку основных виджетов интерфейса:
    - Главное окно и его структура
    - Вкладки (Notebook)
    - Контейнеры для содержимого
    - Список файлов (Treeview)
    - Панели действий
    
    Используется как часть модульной архитектуры главного окна,
    работая совместно с другими модулями (tabs, actions, resize).
    """
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения (ReFilePlusApp)
        """
        self.app = app
    
    def create_widgets(self) -> None:
        """Создание всех виджетов интерфейса.
        
        Создает главное окно с вкладками вверху, общим списком файлов слева
        и содержимым вкладок справа.
        """
        # Настраиваем стиль для выравнивания высоты полей ввода с кнопками
        # ВАЖНО: сохраняем все параметры стиля, включая borderwidth и relief
        # Используем borderwidth=1 и padding=(2, 2) для правильного отображения
        self.app.style.configure('TCombobox',
                                 fieldbackground=self.app.colors['bg_main'],
                                 foreground=self.app.colors['text_primary'],
                                 borderwidth=1,
                                 relief='solid',
                                 padding=(2, 2),
                                 font=('Robot', 9))
        # Сохраняем настройки bordercolor для правильного отображения рамок
        self.app.style.map('TCombobox',
                          bordercolor=[('focus', self.app.colors['border_focus']),
                                     ('!focus', self.app.colors['border'])],
                          selectbackground=[('focus', self.app.colors['bg_main'])],
                          selectforeground=[('focus', self.app.colors['text_primary'])])
        
        # Основной контейнер: вкладки вверху, содержимое вкладок ниже
        main_container = tk.Frame(self.app.root, bg=self.app.colors['bg_main'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        main_container.columnconfigure(0, weight=1)
        main_container.rowconfigure(0, weight=0)  # Верхние вкладки (не растягиваются)
        main_container.rowconfigure(1, weight=1)  # Содержимое вкладок (растягивается)
        
        # ========================================================================
        # СТРОКА 0: ВЕРХНИЕ ВКЛАДКИ (Файлы, Сортировка, Настройки)
        # ========================================================================
        
        # Панель с верхними вкладками
        top_tabs_panel = tk.Frame(main_container, bg=self.app.colors['bg_main'])
        top_tabs_panel.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 2))
        top_tabs_panel.columnconfigure(0, weight=1)
        
        # Словарь для хранения кнопок вкладок
        self.app.tab_buttons = {}
        self.app.top_tab_buttons = {}  # Верхние вкладки
        self.app.current_tab = "files"  # Текущая активная вкладка (по умолчанию "Переименовщик")
        
        # Верхние вкладки (Переименовщик, Конвертация, Сортировка, Настройки)
        top_tabs_list = [
            ("files", "Переименовщик"),
            ("convert", "Конвертация"),
            ("sort", "Сортировка"),
            ("settings", "Настройки"),
        ]
        
        # Создаем кнопки для верхних вкладок
        top_buttons_frame = tk.Frame(top_tabs_panel, bg=self.app.colors['bg_main'])
        top_buttons_frame.pack(fill=tk.X, padx=0, pady=0)
        
        for tab_id, tab_text in top_tabs_list:
            btn_frame = self.app.create_rounded_top_tab_button(
                top_buttons_frame,
                text=tab_text,
                command=lambda t=tab_id: self.app.main_window_handler.switch_tab(t),
                bg_color=self.app.colors['bg_main'],
                fg_color=self.app.colors['text_primary'],
                font=('Robot', 11, 'bold'),
                padx=6,
                pady=4,
                active_bg=self.app.colors['primary'],
                active_fg='white',
                radius=8
            )
            btn_frame.pack(side=tk.LEFT, fill=tk.Y)
            # Сохраняем canvas для изменения цвета
            canvas = btn_frame.winfo_children()[0]  # Canvas - первый и единственный дочерний элемент
            self.app.top_tab_buttons[tab_id] = canvas
            self.app.tab_buttons[tab_id] = canvas
        
        # ========================================================================
        # СТРОКА 1: КОНТЕЙНЕР ДЛЯ СОДЕРЖИМОГО ВКЛАДОК
        # ========================================================================
        
        # Контейнер для содержимого всех вкладок
        content_container = tk.Frame(main_container, bg=self.app.colors['bg_main'])
        content_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        content_container.columnconfigure(0, weight=1)
        content_container.rowconfigure(0, weight=1)
        self.app.content_container = content_container
        
        # ========================================================================
        # КОНТЕЙНЕР ДЛЯ ВКЛАДКИ "ПЕРЕИМЕНОВЩИК"
        # ========================================================================
        
        # Контейнер для вкладки "Переименовщик" (панель действий + список файлов)
        files_tab_container = tk.Frame(content_container, bg=self.app.colors['bg_main'])
        files_tab_container.grid(row=0, column=0, sticky="nsew")
        files_tab_container.columnconfigure(0, weight=1)
        files_tab_container.rowconfigure(1, weight=1)  # Список файлов растягивается
        files_tab_container.rowconfigure(0, weight=0)  # Панель действий не растягивается
        self.app.files_tab_container = files_tab_container
        
        # Панель для вкладки "Переименовщик" (кнопки и шаблон)
        actions_panel = tk.Frame(files_tab_container, bg=self.app.colors['bg_main'])
        actions_panel.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 1))
        # Настраиваем равномерное распределение колонок
        actions_panel.columnconfigure(1, weight=1)  # Контейнер для шаблона растягивается
        # Сохраняем ссылку на actions_panel для управления видимостью
        self.app.actions_panel = actions_panel
        
        # Контейнер для кнопок слева
        buttons_left_container = tk.Frame(actions_panel, bg=self.app.colors['bg_main'])
        buttons_left_container.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=5)
        
        # Кнопка "Добавить" (квадратная, со значком "+")
        btn_add = self.app.create_square_icon_button(
            buttons_left_container,
            "+",
            self.app.add_files,
            bg_color=self.app.colors['success'],
            size=28,
            active_bg=self.app.colors['success_hover']
        )
        btn_add.grid(row=0, column=0, padx=(0, 5), pady=0)
        
        # Кнопка "Очистить" (квадратная, со значком корзинки)
        btn_clear = self.app.create_square_icon_button(
            buttons_left_container,
            "🗑️",
            self.app.clear_files,
            bg_color=self.app.colors['danger'],
            size=28,
            active_bg=self.app.colors['danger_hover']
        )
        btn_clear.grid(row=0, column=1, padx=(0, 0), pady=0)
        
        # Контейнер для содержимого переименования (шаблон и кнопки)
        action_content_frame = tk.Frame(actions_panel, bg=self.app.colors['bg_main'])
        action_content_frame.grid(row=0, column=1, sticky="ew", padx=0, pady=5)
        action_content_frame.columnconfigure(0, weight=1)
        self.app.action_content_frame = action_content_frame
        
        # Сохраняем ссылку на main_container для обновления размеров
        self.app.main_container = main_container
        
        # Обработчик изменения размера главного окна
        def on_root_resize(event=None):
            if hasattr(self.app, 'update_tree_columns'):
                self.app.root.after(100, self.app.main_window_handler.update_tree_columns)
            # Обновляем размер canvas в правой панели методов
            if hasattr(self.app, 'settings_canvas') and self.app.settings_canvas:
                try:
                    canvas_width = self.app.settings_canvas.winfo_width()
                    if canvas_width > 1 and hasattr(self.app, 'settings_canvas_window'):
                        self.app.settings_canvas.itemconfig(
                            self.app.settings_canvas_window,
                            width=canvas_width
                        )
                    # Обновляем видимость скроллбара при изменении размера окна
                    if hasattr(self.app, 'update_scroll_region'):
                        self.app.root.after(150, self.app.update_scroll_region)
                except (tk.TclError, AttributeError):
                    pass
        
        self.app.root.bind('<Configure>', on_root_resize)
        
        # Обработчик изменения размера для обновления колонок таблицы
        def on_resize(event=None):
            if hasattr(self.app, 'main_window_handler'):
                self.app.root.after(50, self.app.main_window_handler.update_tree_columns)
            # Обновляем размер canvas в правой панели
            if hasattr(self.app, 'settings_canvas') and self.app.settings_canvas:
                try:
                    canvas_width = self.app.settings_canvas.winfo_width()
                    if canvas_width > 1:
                        self.app.settings_canvas.itemconfig(self.app.settings_canvas_window, width=canvas_width)
                    # Обновляем видимость скроллбара при изменении размера
                    if hasattr(self.app, 'update_scroll_region'):
                        self.app.root.after(100, self.app.update_scroll_region)
                except (AttributeError, tk.TclError):
                    pass
        
        main_container.bind('<Configure>', on_resize)  # При изменении размера
        
        # Контейнер для списка файлов (внутри files_tab_container)
        files_container = tk.Frame(files_tab_container, bg=self.app.colors['bg_main'])
        files_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        files_container.columnconfigure(0, weight=1)
        files_container.rowconfigure(0, weight=1)
        
        # Сохраняем ссылку на контейнер списка файлов
        self.app.files_container = files_container
        
        # Создаем список файлов внутри files_container
        self._create_files_list_in_container(files_container)
        
        # Изначально files_container находится на уровне content_container
        # Будет перемещаться между контейнерами вкладок через grid_forget/grid
        
        # Словарь для хранения содержимого действий
        if not hasattr(self.app, 'tab_contents'):
            self.app.tab_contents = {}
        
        # Создаем содержимое для переименования (по умолчанию)
        self.app.main_window_handler.create_re_file_action_content(action_content_frame)
        
        # Выбираем вкладку "Файлы" по умолчанию
        self.app.main_window_handler.switch_tab("files")
        
        # Обработка файлов из аргументов командной строки
        if self.app.files_from_args:
            self.app.root.after(1000, self.app._process_files_from_args)
            self.app.log(f"Получено файлов из аргументов: {len(self.app.files_from_args)}")
            for f in self.app.files_from_args[:5]:
                self.app.log(f"  - {f}")
    
    def _create_files_list_in_container(self, parent):
        """Создание списка файлов в контейнере.
        
        Args:
            parent: Родительский контейнер для списка файлов
        """
        # Используем FileListManager для создания списка файлов
        if hasattr(self.app, 'file_list_manager'):
            self.app.file_list_manager.create_treeview(parent)
        else:
            logger.warning("FileListManager не найден, создаем базовый список файлов")
            # Fallback: создаем базовый Treeview
            tree_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
            tree_frame.pack(fill=tk.BOTH, expand=True)
            
            tree = ttk.Treeview(
                tree_frame,
                columns=("files", "path"),
                show="headings",
                style='Custom.Treeview'
            )
            tree.heading("files", text="Имя файла")
            tree.heading("path", text="Путь")
            tree.column("files", width=300, minwidth=150, stretch=False)
            tree.column("path", width=400, minwidth=200, stretch=True)
            
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            self.app.tree = tree
            self.app.list_frame = tree_frame


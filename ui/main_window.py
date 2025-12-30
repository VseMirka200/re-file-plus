"""Модуль для создания главного окна и базовых виджетов.

Содержит обработчики пользовательского ввода: горячие клавиши и поиск.
"""

# Стандартная библиотека
import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)


class MainWindow:
    """Класс для управления главным окном и базовыми виджетами."""
    
    def __init__(self, app) -> None:
        """Инициализация главного окна.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
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
        self.app.current_tab = "files"  # Текущая активная вкладка (по умолчанию "Файлы")
        
        # Верхние вкладки (Файлы - первая, затем Сортировка, Настройки, О программе)
        top_tabs_list = [
            ("files", "Файлы"),
            ("sort", "Сортировка"),
            ("settings", "Настройки"),
            ("about", "О программе"),
        ]
        
        # Создаем кнопки для верхних вкладок
        top_buttons_frame = tk.Frame(top_tabs_panel, bg=self.app.colors['bg_main'])
        top_buttons_frame.pack(fill=tk.X, padx=0, pady=0)
        
        for tab_id, tab_text in top_tabs_list:
            btn_frame = self.app.create_rounded_top_tab_button(
                top_buttons_frame,
                text=tab_text,
                command=lambda t=tab_id: self.switch_tab(t),
                bg_color=self.app.colors['bg_main'],
                fg_color=self.app.colors['text_primary'],
                font=('Robot', 11, 'bold'),
                padx=10,
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
        # КОНТЕЙНЕР ДЛЯ ВКЛАДКИ "ФАЙЛЫ"
        # ========================================================================
        
        # Контейнер для вкладки "Файлы" (панель действий + список файлов)
        files_tab_container = tk.Frame(content_container, bg=self.app.colors['bg_main'])
        files_tab_container.grid(row=0, column=0, sticky="nsew")
        files_tab_container.columnconfigure(0, weight=1)
        files_tab_container.rowconfigure(1, weight=1)  # Список файлов растягивается
        files_tab_container.rowconfigure(0, weight=0)  # Панель действий не растягивается
        self.app.files_tab_container = files_tab_container
        
        # Панель действий для вкладки "Файлы"
        actions_panel = tk.Frame(files_tab_container, bg=self.app.colors['bg_main'])
        actions_panel.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 1))
        # Настраиваем равномерное распределение колонок
        actions_panel.columnconfigure(1, weight=1)  # Контейнер для содержимого действий растягивается
        
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
        
        # Контейнер для динамического содержимого действий (выбор действия + поля ввода и кнопки)
        action_content_frame = tk.Frame(actions_panel, bg=self.app.colors['bg_main'])
        action_content_frame.grid(row=0, column=1, sticky="ew", padx=0, pady=5)
        action_content_frame.columnconfigure(1, weight=1)
        self.app.action_content_frame = action_content_frame
        
        # Контейнер для выбора действия
        action_select_container = tk.Frame(action_content_frame, bg=self.app.colors['bg_main'])
        action_select_container.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=5)
        
        # Метка для выбора действия - слева от поля
        action_label = tk.Label(
            action_select_container,
            text="Действие:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        action_label.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        # Frame для Combobox с фиксированной высотой 28px (как у кнопок)
        action_combo_frame = tk.Frame(action_select_container, bg=self.app.colors['bg_main'], height=28, width=120)
        action_combo_frame.grid(row=0, column=1, sticky="ew")
        action_combo_frame.grid_propagate(False)
        action_combo_frame.pack_propagate(False)
        
        # Выпадающее меню с выбором действия
        # Восстанавливаем сохраненное значение, если есть, иначе "Переименовать"
        saved_action = getattr(self.app, '_saved_action', "Переименовать")
        action_var = tk.StringVar(value=saved_action)
        # Сохраняем начальное значение
        self.app._saved_action = saved_action
        action_combo = ttk.Combobox(
            action_combo_frame,
            textvariable=action_var,
            values=["Переименовать", "Конвертировать"],
            state='readonly',  # Только выпадающее меню, ввод текста запрещен
            width=15,
            font=('Robot', 9)  # Обычный шрифт без жирного начертания
        )
        # Заполняем весь Frame без отступов для правильной высоты 28px
        action_combo.pack(fill=tk.BOTH, expand=True)
        
        # Убеждаемся, что поле только выпадающее - блокируем любые попытки изменить состояние
        def ensure_readonly(event=None):
            if action_combo.cget('state') != 'readonly':
                action_combo.config(state='readonly')
        
        # Привязываем обработчик для поддержания состояния readonly
        action_combo.bind('<FocusIn>', ensure_readonly)
        action_combo.bind('<Button-1>', ensure_readonly)
        
        # Сохраняем выбранное действие при изменении
        def on_action_combo_changed(event=None):
            selected = action_var.get()
            self.app._saved_action = selected
            self.on_action_changed(selected)
        
        action_combo.bind('<<ComboboxSelected>>', on_action_combo_changed)
        self.app.action_var = action_var
        self.app.action_combo = action_combo
        
        # Сохраняем ссылку на main_container для обновления размеров
        self.app.main_container = main_container
        
        # Обработчик изменения размера главного окна
        def on_root_resize(event=None):
            if hasattr(self.app, 'update_tree_columns'):
                self.app.root.after(100, self.app.update_tree_columns)
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
        
        # Словарь для хранения содержимого действий
        if not hasattr(self.app, 'tab_contents'):
            self.app.tab_contents = {}
        
        # Создаем содержимое для действия "Переименовать" (по умолчанию)
        self.create_re_file_action_content(action_content_frame)
        
        # Инициализируем содержимое для других действий как None (будет создано при переключении)
        self.app.tab_contents["convert"] = None
        
        # Выбираем вкладку "Файлы" по умолчанию
        self.switch_tab("files")
        
        # Обработка файлов из аргументов командной строки
        if self.app.files_from_args:
            self.app.root.after(1000, self.app._process_files_from_args)
            self.app.log(f"Получено файлов из аргументов: {len(self.app.files_from_args)}")
            for f in self.app.files_from_args[:5]:
                self.app.log(f"  - {f}")
    
    def switch_tab(self, tab_id: str) -> None:
        """Переключение между вкладками.
        
        Args:
            tab_id: Идентификатор вкладки ('files', 'sort', 'settings', 'about')
        """
        # Обновляем стиль кнопок верхних вкладок (canvas для закругленных вкладок)
        for tid, canvas in self.app.top_tab_buttons.items():
            if tid == tab_id:
                canvas.btn_bg = self.app.colors['primary']
                canvas.btn_fg = 'white'
                canvas.btn_active_bg = self.app.colors['primary']
                canvas.btn_active_fg = 'white'
                canvas.btn_state = 'active'
            else:
                canvas.btn_bg = self.app.colors['bg_main']
                canvas.btn_fg = self.app.colors['text_primary']
                canvas.btn_active_bg = self.app.colors['bg_main']
                canvas.btn_active_fg = self.app.colors['text_primary']
                canvas.btn_state = 'normal'
            # Перерисовываем кнопку
            if hasattr(canvas, 'draw_button'):
                canvas.draw_button(canvas.btn_state)
            else:
                canvas.event_generate('<Configure>')
        
        # Скрываем все контейнеры вкладок
        if hasattr(self.app, 'files_tab_container'):
            self.app.files_tab_container.grid_remove()
        if hasattr(self.app, 'sort_tab_container'):
            self.app.sort_tab_container.grid_remove()
        if hasattr(self.app, 'settings_tab_container'):
            self.app.settings_tab_container.grid_remove()
        if hasattr(self.app, 'about_tab_container'):
            self.app.about_tab_container.grid_remove()
        
        # Показываем содержимое для выбранной вкладки
        if tab_id == "files":
            # Показываем вкладку "Файлы" (панель действий + список файлов)
            if hasattr(self.app, 'files_tab_container'):
                self.app.files_tab_container.grid(row=0, column=0, sticky="nsew")
            # Всегда показываем action_content_frame при переключении на вкладку "Файлы"
            if hasattr(self.app, 'action_content_frame'):
                self.app.action_content_frame.grid(row=0, column=1, sticky="ew", padx=(5, 10), pady=5)
            # Вызываем on_action_changed для активации текущего действия
            if hasattr(self.app, 'action_var'):
                self.on_action_changed(self.app.action_var.get())
        elif tab_id == "sort":
            # Создаем контейнер для сортировки при первом переключении
            if not hasattr(self.app, 'sort_tab_container'):
                sort_container = tk.Frame(self.app.content_container, bg=self.app.colors['bg_main'])
                sort_container.grid(row=0, column=0, sticky="nsew")
                sort_container.columnconfigure(0, weight=1)
                sort_container.rowconfigure(0, weight=1)
                self.app.sort_tab_container = sort_container
                # Создаем содержимое вкладки сортировки
                if hasattr(self.app, 'sorter_tab_handler'):
                    self.app.sorter_tab_handler.create_tab_content(sort_container)
            else:
                self.app.sort_tab_container.grid(row=0, column=0, sticky="nsew")
        elif tab_id == "settings":
            # Создаем контейнер для настроек при первом переключении
            if not hasattr(self.app, 'settings_tab_container'):
                settings_container = tk.Frame(self.app.content_container, bg=self.app.colors['bg_main'])
                settings_container.grid(row=0, column=0, sticky="nsew")
                settings_container.columnconfigure(0, weight=1)
                settings_container.rowconfigure(0, weight=1)
                self.app.settings_tab_container = settings_container
                # Создаем содержимое вкладки настроек
                if hasattr(self.app, 'settings_tab_handler'):
                    self.app.settings_tab_handler.create_tab_content_for_main(settings_container)
            else:
                self.app.settings_tab_container.grid(row=0, column=0, sticky="nsew")
        elif tab_id == "about":
            # Создаем контейнер для "О программе" при первом переключении
            if not hasattr(self.app, 'about_tab_container'):
                about_container = tk.Frame(self.app.content_container, bg=self.app.colors['bg_main'])
                about_container.grid(row=0, column=0, sticky="nsew")
                about_container.columnconfigure(0, weight=1)
                about_container.rowconfigure(0, weight=1)
                self.app.about_tab_container = about_container
                # Создаем содержимое вкладки "О программе"
                self._create_about_tab_content(about_container)
            else:
                self.app.about_tab_container.grid(row=0, column=0, sticky="nsew")
        
        # Обновляем текущую вкладку
        self.app.current_tab = tab_id
    
    def _create_files_list_in_container(self, parent):
        """Создание панели со списком файлов в контейнере.
        
        Этот список файлов является ОБЩИМ для всех действий:
        переименования и конвертации. Он создается один раз
        и используется всеми действиями.
        
        Args:
            parent: Родительский контейнер (files_container)
        """
        # Список файлов - общий для всех действий (переименование, конвертация)
        files_count = len(self.app.files)
        left_panel = ttk.LabelFrame(
            parent,
            text=f"Список файлов (Файлов: {files_count})",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)
        )
        left_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(0, weight=1)  # Строка с таблицей файлов
        
        # Сохраняем ссылку на left_panel для обновления заголовка
        self.app.left_panel = left_panel
        
        # Таблица файлов (кнопки управления теперь в панели действий выше)
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создание таблицы с прокруткой
        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        
        columns = ("files", "path")
        self.app.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            style='Custom.Treeview'
        )
        
        scrollbar_y.config(command=self.app.tree.yview)
        scrollbar_x.config(command=self.app.tree.xview)
        
        # Настройка колонок
        self.app.tree.heading("files", text="Добавленные файлы", command=lambda: self.app.file_list_manager.sort_column("files"))
        self.app.tree.heading("path", text="Путь", command=lambda: self.app.file_list_manager.sort_column("path"))
        
        # Настройка ширины колонок
        self.app.tree.column("files", width=300, anchor='w', minwidth=150, stretch=tk.YES)
        self.app.tree.column("path", width=400, anchor='w', minwidth=200, stretch=tk.YES)
        
        # Тег для строки с путем (занимает обе колонки)
        self.app.tree.tag_configure('path_row', 
                                    background=self.app.colors.get('bg_main', '#FFFFFF'),
                                    foreground=self.app.colors.get('text_secondary', '#6B7280'),
                                    font=('Robot', 8))
        
        # Настройка тегов для цветового выделения
        self.app.tree.tag_configure('ready', background='#D1FAE5', foreground='#065F46')  # Зеленый - готово
        self.app.tree.tag_configure('error', background='#FEE2E2', foreground='#991B1B')  # Красный - ошибка
        self.app.tree.tag_configure('conflict', background='#FEF3C7', foreground='#92400E')  # Желтый - конфликт
        self.app.tree.tag_configure('changed', foreground='#1E40AF')
        self.app.tree.tag_configure('converted', background='#D1FAE5', foreground='#065F46')  # Зеленый - конвертировано
        self.app.tree.tag_configure('in_progress', background='#FEF3C7', foreground='#92400E')  # Желтый - в работе
        
        # Восстановление состояния сортировки
        if hasattr(self.app, 'settings_manager'):
            saved_sort = self.app.settings_manager.get('sort_column')
            saved_reverse = self.app.settings_manager.get('sort_reverse', False)
            if saved_sort:
                self.app.sort_column_name = saved_sort
                self.app.sort_reverse = saved_reverse
        
        # Обновляем колонки после инициализации
        self.app.root.after(200, self.update_tree_columns)
        
        # Сохраняем ссылку на list_frame для обновления размеров
        self.app.list_frame = list_frame
        
        # Размещение виджетов
        self.app.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        # Сохраняем ссылки на скроллбары для автоматического управления
        self.app.tree_scrollbar_y = scrollbar_y
        self.app.tree_scrollbar_x = scrollbar_x
        
        list_frame.grid_rowconfigure(0, weight=1)  # Таблица растягивается
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Привязка прокрутки колесом мыши для таблицы
        self.app.bind_mousewheel(self.app.tree, self.app.tree)
        
        # Автоматическое управление видимостью скроллбаров для Treeview
        def update_tree_scrollbars(*args):
            self.update_scrollbar_visibility(self.app.tree, scrollbar_y, 'vertical')
            self.update_scrollbar_visibility(self.app.tree, scrollbar_x, 'horizontal')
        
        # Обработчики событий
        def on_tree_event(event=None):
            self.app.root.after_idle(update_tree_scrollbars)
        
        self.app.tree.bind('<<TreeviewSelect>>', on_tree_event)
        self.app.tree.bind('<Configure>', on_tree_event)
        
        # Обновляем видимость скроллбаров после создания виджетов
        self.app.root.after(200, update_tree_scrollbars)
        
        # Контекстное меню для таблицы файлов
        self.app.tree.bind('<Button-3>', self.app.show_file_context_menu)
        
        # Привязка сортировки
        self.app.sort_column_name = None
        self.app.sort_reverse = False
        self.app.tree.heading("files", command=lambda: self.app.sort_column("files"))
        
        # Функция для обновления путей в таблице (для обратной совместимости)
        # Удалена как неиспользуемая
        
    
    def create_rename_tab_content(self, parent) -> None:
        """Создание содержимого вкладки переименования (только правая панель с методами).
        
        Args:
            parent: Родительский контейнер (action_content_frame)
        """
        # Создаем Frame для содержимого вкладки переименования (только правая панель)
        re_file_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        re_file_frame.grid(row=0, column=0, sticky="nsew")
        re_file_frame.columnconfigure(0, weight=1)
        re_file_frame.rowconfigure(0, weight=1)
        
        # Сохраняем ссылку
        self.app.tab_contents["re_file"] = re_file_frame
        
        # Правая панель (только методы)
        right_panel = ttk.LabelFrame(
            re_file_frame,
            text="Методы переименования",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)
        )
        right_panel.grid(row=0, column=0, sticky="nsew", padx=(2, 0), pady=(20, 20))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        # Сохраняем ссылку на панель
        self.app.right_panel = right_panel
        
        # Внутренний Frame для содержимого
        methods_frame = tk.Frame(right_panel, bg=self.app.colors['bg_main'])
        self.app.methods_frame = methods_frame
        methods_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        methods_frame.columnconfigure(0, weight=1)
        methods_frame.rowconfigure(1, weight=1)
        
        # Устанавливаем метод "Новое имя" по умолчанию
        self.app.method_var = tk.StringVar()
        self.app.method_var.set("Новое имя")
        
        # Область настроек метода с прокруткой
        settings_container = tk.Frame(methods_frame, bg=self.app.colors['bg_main'])
        settings_container.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        settings_container.columnconfigure(0, weight=1)
        settings_container.rowconfigure(0, weight=1)
        
        # Canvas для прокрутки настроек
        settings_canvas = tk.Canvas(settings_container, bg=self.app.colors['bg_main'], 
                                    highlightthickness=0)
        settings_scrollbar = ttk.Scrollbar(settings_container, orient="vertical", 
                                           command=settings_canvas.yview)
        scrollable_frame = tk.Frame(settings_canvas, bg=self.app.colors['bg_main'])
        
        # Флаг для предотвращения бесконечных циклов
        _updating_scroll = False
        _needs_scrolling_settings = True
        
        def update_scroll_region():
            """Обновление области прокрутки и видимости скроллбара"""
            nonlocal _updating_scroll, _needs_scrolling_settings
            if _updating_scroll:
                return
            _updating_scroll = True
            try:
                settings_canvas.update_idletasks()
                bbox = settings_canvas.bbox("all")
                if bbox:
                    canvas_height = settings_canvas.winfo_height()
                    if canvas_height > 1:
                        content_height = bbox[3] - bbox[1]
                        if content_height <= canvas_height + 2:
                            settings_canvas.configure(scrollregion=(0, 0, bbox[2], canvas_height))
                            settings_canvas.yview_moveto(0)
                            _needs_scrolling_settings = False
                            try:
                                if settings_scrollbar.winfo_viewable():
                                    settings_scrollbar.grid_remove()
                            except (tk.TclError, AttributeError):
                                pass
                        else:
                            settings_canvas.configure(scrollregion=bbox)
                            _needs_scrolling_settings = True
                            try:
                                if not settings_scrollbar.winfo_viewable():
                                    settings_scrollbar.grid(row=0, column=1, sticky="ns")
                            except (tk.TclError, AttributeError):
                                pass
                            self.update_scrollbar_visibility(settings_canvas, settings_scrollbar, 'vertical')
                else:
                    settings_scrollbar.grid_remove()
            except (AttributeError, tk.TclError):
                pass
            finally:
                _updating_scroll = False
        
        def on_frame_configure(event):
            self.app.root.after_idle(update_scroll_region)
        
        scrollable_frame.bind("<Configure>", on_frame_configure)
        
        settings_canvas_window = settings_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def on_canvas_configure(event):
            if event.widget == settings_canvas:
                try:
                    canvas_width = event.width
                    if canvas_width > 1:
                        settings_canvas.itemconfig(settings_canvas_window, width=canvas_width)
                    self.app.root.after_idle(update_scroll_region)
                except (AttributeError, tk.TclError):
                    pass
        
        settings_canvas.bind('<Configure>', on_canvas_configure)
        
        def on_scroll(*args):
            settings_scrollbar.set(*args)
        
        settings_canvas.configure(yscrollcommand=on_scroll)
        
        # Сохраняем функцию обновления для использования извне
        self.app.update_scroll_region = update_scroll_region
        
        # Сохраняем ссылки для обновления размеров
        self.app.settings_canvas = settings_canvas
        self.app.settings_canvas_window = settings_canvas_window
        
        # Кастомная функция прокрутки
        def on_mousewheel_settings(event):
            if not _needs_scrolling_settings:
                return
            scroll_amount = int(-1 * (event.delta / 120))
            settings_canvas.yview_scroll(scroll_amount, "units")
        
        def on_mousewheel_linux_settings(event):
            if not _needs_scrolling_settings:
                return
            if event.num == 4:
                settings_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                settings_canvas.yview_scroll(1, "units")
        
        settings_canvas.bind("<MouseWheel>", on_mousewheel_settings)
        settings_canvas.bind("<Button-4>", on_mousewheel_linux_settings)
        settings_canvas.bind("<Button-5>", on_mousewheel_linux_settings)
        
        def bind_to_children_settings(parent):
            for child in parent.winfo_children():
                try:
                    child.bind("<MouseWheel>", on_mousewheel_settings)
                    child.bind("<Button-4>", on_mousewheel_linux_settings)
                    child.bind("<Button-5>", on_mousewheel_linux_settings)
                    bind_to_children_settings(child)
                except (AttributeError, tk.TclError):
                    pass
        
        bind_to_children_settings(scrollable_frame)
        
        settings_canvas.grid(row=0, column=0, sticky="nsew")
        settings_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.app.settings_frame = scrollable_frame
        
        # Объединенная группа кнопок
        self.app.method_buttons_frame = tk.Frame(methods_frame, bg=self.app.colors['bg_main'])
        self.app.method_buttons_frame.pack(fill=tk.X, pady=(0, 0))
        
        # Кнопка "Начать переименование"
        btn_start_rename = self.app.create_rounded_button(
            self.app.method_buttons_frame, "▶️ Начать переименование", self.app.start_re_file,
            self.app.colors['success'], 'white',
            font=('Robot', 9, 'bold'), padx=6, pady=8,
            active_bg=self.app.colors['success_hover'], expand=True)
        btn_start_rename.pack(fill=tk.X, pady=(6, 0))
        
        # Скрытый listbox для внутреннего использования методов
        self.app.methods_listbox = tk.Listbox(methods_frame, height=0)
        self.app.methods_listbox.pack_forget()
        
        # Создаем log_text для логирования
        self.app.logger.set_log_widget(None)
        
        # Инициализация первого метода (Новое имя)
        self.app.on_method_selected()
        
        # Создание вкладок для сортировки и настроек (в старой структуре с Notebook)
        # Создаем скрытый Notebook для этих вкладок (они работают в старой структуре)
        hidden_notebook_frame = tk.Frame(self.app.root)
        hidden_notebook_frame.pack_forget()  # Скрываем, но создаем для обратной совместимости
        
        if not hasattr(self.app, 'main_notebook'):
            self.app.main_notebook = ttk.Notebook(hidden_notebook_frame)
            self.app.main_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Создаем вкладки для сортировки и настроек
        self.app.sorter_tab_handler.create_tab()
        self.app.settings_tab_handler.create_tab()
    
    def on_action_changed(self, action: str) -> None:
        """Обработка изменения выбранного действия.
        
        Args:
            action: Название действия ("Переименовать", "Конвертировать")
        """
        # Убеждаемся, что мы находимся во вкладке "Файлы"
        # Если мы не во вкладке "Файлы", ничего не делаем
        if not hasattr(self.app, 'current_tab') or self.app.current_tab != "files":
            return
        
        # Используем action_content_frame для размещения содержимого действий
        parent = self.app.action_content_frame if hasattr(self.app, 'action_content_frame') else None
        if not parent:
            return
        
        # Скрываем текущее содержимое действий
        for key in ["re_file", "convert"]:
            if key in self.app.tab_contents and self.app.tab_contents[key]:
                frame = self.app.tab_contents[key]
                # Проверяем, что это не сам parent и frame существует
                if frame != parent:
                    try:
                        if frame.winfo_exists():
                            frame.grid_remove()
                    except (tk.TclError, AttributeError):
                        # Frame уже уничтожен, удаляем из словаря
                        self.app.tab_contents[key] = None
        
        if action == "Переименовать":
            if "re_file" not in self.app.tab_contents or self.app.tab_contents["re_file"] is None:
                self.create_re_file_action_content(parent)
            frame = self.app.tab_contents.get("re_file")
            if frame:
                try:
                    if frame.winfo_exists():
                        frame.grid(row=0, column=1, sticky="ew")
                    else:
                        # Frame уничтожен, создаем заново
                        self.create_re_file_action_content(parent)
                        self.app.tab_contents["re_file"].grid(row=0, column=1, sticky="ew")
                except (tk.TclError, AttributeError):
                    # Frame не существует, создаем заново
                    self.create_re_file_action_content(parent)
                    self.app.tab_contents["re_file"].grid(row=0, column=1, sticky="ew")
            # Обновляем колонки для переименования
            self.app.root.after(100, lambda act="re_file": self.update_tree_columns_for_action(act))
        elif action == "Конвертировать":
            if "convert" not in self.app.tab_contents or self.app.tab_contents["convert"] is None:
                self.create_convert_action_content(parent)
            frame = self.app.tab_contents.get("convert")
            if frame:
                try:
                    if frame.winfo_exists():
                        frame.grid(row=0, column=1, sticky="ew")
                    else:
                        # Frame уничтожен, создаем заново
                        self.create_convert_action_content(parent)
                        self.app.tab_contents["convert"].grid(row=0, column=1, sticky="ew")
                except (tk.TclError, AttributeError):
                    # Frame не существует, создаем заново
                    self.create_convert_action_content(parent)
                    self.app.tab_contents["convert"].grid(row=0, column=1, sticky="ew")
            # Обновляем колонки для конвертации
            self.app.root.after(100, lambda act="convert": self.update_tree_columns_for_action(act))
            # Автоматически определяем тип файла и обновляем форматы, если есть файлы
            if hasattr(self.app, 'converter_tab_handler'):
                self.app.root.after(150, lambda: self.app.converter_tab_handler.update_available_formats())
    
    def create_re_file_action_content(self, parent) -> None:
        """Создание содержимого для действия 'Переименовать' в одну линию.
        
        Args:
            parent: Родительский контейнер (action_content_frame)
        """
        # Удаляем старый frame, если он существует
        if "re_file" in self.app.tab_contents and self.app.tab_contents["re_file"]:
            old_frame = self.app.tab_contents["re_file"]
            try:
                if old_frame.winfo_exists():
                    old_frame.destroy()
            except (tk.TclError, AttributeError):
                pass
        
        # Создаем Frame для содержимого действия переименования
        re_file_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        re_file_frame.grid(row=0, column=1, sticky="ew", padx=0, pady=0)
        # Настраиваем веса колонок для правильного растяжения
        re_file_frame.columnconfigure(1, weight=1)  # Поле шаблона растягивается
        
        # Сохраняем ссылку
        self.app.tab_contents["re_file"] = re_file_frame
        
        # Метка "Шаблон:" слева от поля
        template_label = tk.Label(
            re_file_frame,
            text="Шаблон:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        template_label.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=0)
        
        # Поле ввода шаблона (простое Entry без выпадающего списка)
        if not hasattr(self.app, 'new_name_template'):
            self.app.new_name_template = tk.StringVar()
        
        # Frame для Entry с фиксированной высотой 28px (как у кнопок)
        template_entry_frame = tk.Frame(re_file_frame, bg=self.app.colors['bg_main'], height=28)
        template_entry_frame.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        template_entry_frame.grid_propagate(False)
        template_entry_frame.pack_propagate(False)
        
        # Поле ввода шаблона (используем обычный Entry вместо ttk для лучшей видимости)
        template_entry = tk.Entry(
            template_entry_frame,
            textvariable=self.app.new_name_template,
            width=30,
            font=('Robot', 9),
            bg='white',
            fg=self.app.colors['text_primary'],
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.app.colors['border'],
            highlightcolor=self.app.colors['border_focus']
        )
        template_entry.pack(fill=tk.BOTH, expand=True)
        
        # Функции для работы с буфером обмена (для контекстного меню)
        def on_copy(event=None):
            try:
                text = template_entry.selection_get()
                if text:
                    self.app.root.clipboard_clear()
                    self.app.root.clipboard_append(text)
            except tk.TclError:
                pass
        
        def on_paste(event=None):
            try:
                # Удаляем выделенный текст перед вставкой, если есть
                try:
                    if template_entry.selection_present():
                        template_entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
                except tk.TclError:
                    pass
                # Используем root.clipboard_get() для более надежного получения данных из буфера обмена
                text = self.app.root.clipboard_get()
                if text:
                    template_entry.insert(tk.INSERT, text)
                    # После вставки применяем шаблон
                    if hasattr(self.app, '_apply_template_immediate'):
                        self.app.root.after(50, self.app._apply_template_immediate)
            except (tk.TclError, Exception) as e:
                logger.debug(f"Ошибка при вставке: {e}")
                pass
        
        def on_cut(event=None):
            try:
                text = template_entry.selection_get()
                if text:
                    self.app.root.clipboard_clear()
                    self.app.root.clipboard_append(text)
                    template_entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
        
        def on_select_all(event=None):
            template_entry.selection_range(0, tk.END)
            template_entry.icursor(tk.END)
        
        # В Tkinter Entry виджеты поддерживают стандартные горячие клавиши по умолчанию
        # Но мы переопределяем их для использования наших функций, которые работают с контекстным меню
        def handle_copy(event):
            on_copy()
            return "break"
        
        def handle_paste(event):
            nonlocal _is_paste_operation
            _is_paste_operation = True
            on_paste()
            # Возвращаем "break" чтобы предотвратить дальнейшую обработку события
            # и стандартную вставку Tkinter
            return "break"
        
        def handle_cut(event):
            on_cut()
            return "break"
        
        def handle_select_all(event):
            on_select_all()
            return "break"
        
        # Привязка горячих клавиш напрямую к этому виджету
        template_entry.bind('<Control-c>', handle_copy)
        template_entry.bind('<Control-C>', handle_copy)
        template_entry.bind('<Control-v>', handle_paste)
        template_entry.bind('<Control-V>', handle_paste)
        template_entry.bind('<Control-x>', handle_cut)
        template_entry.bind('<Control-X>', handle_cut)
        template_entry.bind('<Control-a>', handle_select_all)
        template_entry.bind('<Control-A>', handle_select_all)
        
        # Привязка правой кнопки мыши для контекстного меню
        def show_context_menu(event):
            """Показ контекстного меню для копирования/вставки"""
            try:
                # Устанавливаем фокус на поле ввода
                template_entry.focus_set()
                
                context_menu = tk.Menu(template_entry, tearoff=0)
                
                # Проверяем, есть ли выделенный текст
                try:
                    template_entry.selection_get()
                    has_selection = True
                except tk.TclError:
                    has_selection = False
                
                if has_selection:
                    context_menu.add_command(label="Копировать  Ctrl+C", command=lambda: on_copy(None))
                    context_menu.add_command(label="Вырезать  Ctrl+X", command=lambda: on_cut(None))
                else:
                    context_menu.add_command(label="Копировать  Ctrl+C", command=lambda: on_copy(None), state='disabled')
                    context_menu.add_command(label="Вырезать  Ctrl+X", command=lambda: on_cut(None), state='disabled')
                
                context_menu.add_command(label="Вставить  Ctrl+V", command=lambda: on_paste(None))
                context_menu.add_separator()
                context_menu.add_command(label="Выделить всё  Ctrl+A", command=lambda: on_select_all(None))
                
                try:
                    context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    context_menu.grab_release()
            except Exception:
                pass
        
        template_entry.bind('<Button-3>', show_context_menu)  # Правая кнопка мыши (Windows/Linux)
        template_entry.bind('<Button-2>', show_context_menu)  # Средняя кнопка (для совместимости)
        
        # Флаг для отслеживания операций вставки/копирования/вырезания
        _is_paste_operation = False
        
        # Привязка обработчика изменения шаблона в поле ввода
        # Используем KeyRelease и проверяем, что это не горячие клавиши
        def on_template_entry_change(event=None):
            nonlocal _is_paste_operation
            if event is None:
                return
            # Если это была операция вставки, пропускаем обработку
            if _is_paste_operation:
                _is_paste_operation = False
                # Но все равно применяем шаблон после вставки
                if hasattr(self.app, '_apply_template_immediate'):
                    self.app.root.after(50, self.app._apply_template_immediate)
                return
            # Пропускаем горячие клавиши Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A
            # Проверяем как через state, так и через keysym для надежности
            key = event.keysym.lower()
            # Проверяем, нажата ли Control (0x4) или это комбинация клавиш
            if event.state & 0x4:  # Control key pressed
                if key in ('c', 'v', 'x', 'a', 'control_l', 'control_r'):
                    return
            # Также проверяем комбинации напрямую через keysym
            if key in ('control-c', 'control-v', 'control-x', 'control-a'):
                return
            # Применяем шаблон сразу же с минимальной задержкой для стабильности
            if hasattr(self.app, '_apply_template_immediate'):
                # Используем небольшую задержку (50 мс) для предотвращения проблем при быстром вводе
                self.app.root.after(50, self.app._apply_template_immediate)
        template_entry.bind('<KeyRelease>', on_template_entry_change)
        
        # Также применяем шаблон при потере фокуса
        def on_template_focus_out(event=None):
            if hasattr(self.app, '_apply_template_immediate'):
                self.app._apply_template_immediate()
        template_entry.bind('<FocusOut>', on_template_focus_out)
        
        # Кнопка руководства по шаблонам "?" (квадратная)
        btn_guide = self.app.create_square_icon_button(
            re_file_frame,
            "?",
            self.show_templates_guide,
            bg_color=self.app.colors['info'],
            size=28,
            active_bg=self.app.colors['info_hover']
        )
        btn_guide.grid(row=0, column=2, padx=(0, 5), pady=0, sticky="n")
        self.app.templates_btn_guide = btn_guide
        
        # Кнопка "Начать переименовку" (квадратная, со значком галочки)
        btn_start = self.app.create_square_icon_button(
            re_file_frame,
            "✓",
            self.app.start_re_file,
            bg_color=self.app.colors['success'],
            size=28,
            active_bg=self.app.colors['success_hover']
        )
        btn_start.grid(row=0, column=3, padx=(0, 0), pady=0, sticky="n")
        self.app.rename_btn_start = btn_start
    
    def show_templates_guide(self):
        """Показ окна руководства по шаблонам с возможностью копирования"""
        # Проверяем, не открыто ли уже окно руководства
        if hasattr(self.app, '_templates_guide_window'):
            try:
                if self.app._templates_guide_window.winfo_exists():
                    # Окно уже открыто, просто поднимаем его на передний план
                    self.app._templates_guide_window.lift()
                    self.app._templates_guide_window.focus_force()
                    return
            except (tk.TclError, AttributeError):
                # Окно было закрыто, но ссылка осталась
                pass
        
        guide_window = tk.Toplevel(self.app.root)
        guide_window.title("Руководство по шаблонам")
        guide_window.geometry("800x700")
        guide_window.configure(bg=self.app.colors['bg_main'])
        guide_window.transient(self.app.root)
        
        # Сохраняем ссылку на окно
        self.app._templates_guide_window = guide_window
        
        # Флаг для предотвращения двойного закрытия
        _closing = [False]
        
        # Обработчик закрытия по Escape и кнопке X
        def on_close(event=None):
            if _closing[0]:
                return
            _closing[0] = True
            try:
                if guide_window.winfo_exists():
                    guide_window.destroy()
                # Удаляем ссылку на окно после закрытия
                if hasattr(self.app, '_templates_guide_window'):
                    del self.app._templates_guide_window
            except (tk.TclError, AttributeError):
                # Удаляем ссылку даже при ошибке
                if hasattr(self.app, '_templates_guide_window'):
                    try:
                        del self.app._templates_guide_window
                    except:
                        pass
        
        guide_window.bind('<Escape>', on_close)
        guide_window.protocol("WM_DELETE_WINDOW", on_close)
        guide_window.focus_set()
        
        try:
            from ui.ui_components import set_window_icon
            set_window_icon(guide_window, self.app._icon_photos)
        except Exception:
            pass
        
        # Заголовок
        header = tk.Label(
            guide_window,
            text="Руководство по шаблонам переименования",
            font=('Robot', 14, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        header.pack(pady=(15, 10))
        
        # Контейнер с прокруткой
        canvas = tk.Canvas(guide_window, bg=self.app.colors['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(guide_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.app.colors['bg_main'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def on_canvas_configure(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        canvas.bind('<Configure>', on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Функция для создания кликабельного блока с переменной
        def create_variable_block(parent, var_name, description, category=""):
            """Создание блока с переменной, которую можно скопировать"""
            var_frame = tk.Frame(parent, bg=self.app.colors['bg_main'], relief=tk.SOLID, borderwidth=1)
            var_frame.pack(fill=tk.X, padx=10, pady=2)
            
            # Внутренний фрейм для содержимого
            inner_frame = tk.Frame(var_frame, bg=self.app.colors['bg_main'])
            inner_frame.pack(fill=tk.X, padx=8, pady=6)
            
            # Переменная (кликабельная для копирования)
            var_label = tk.Label(
                inner_frame,
                text=var_name,
                font=('Courier New', 11, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['primary'],
                cursor="hand2"
            )
            var_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Описание
            desc_label = tk.Label(
                inner_frame,
                text=description,
                font=('Robot', 10),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary'],
                anchor='w'
            )
            desc_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Функция копирования
            def copy_var(e=None):
                guide_window.clipboard_clear()
                guide_window.clipboard_append(var_name)
                guide_window.update()
                # Визуальная обратная связь
                var_label.config(fg=self.app.colors['success'])
                guide_window.after(200, lambda: var_label.config(fg=self.app.colors['primary']))
            
            var_label.bind("<Button-1>", copy_var)
            inner_frame.bind("<Button-1>", copy_var)
            desc_label.bind("<Button-1>", copy_var)
            var_frame.bind("<Button-1>", copy_var)
            
            # Изменение курсора при наведении
            for widget in [var_label, inner_frame, desc_label, var_frame]:
                widget.bind("<Enter>", lambda e, w=var_label: w.config(fg=self.app.colors['primary_hover']))
                widget.bind("<Leave>", lambda e, w=var_label: w.config(fg=self.app.colors['primary']))
        
        # Основные переменные
        basic_label = tk.Label(
            scrollable_frame,
            text="Основные переменные:",
            font=('Robot', 12, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        basic_label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        basic_vars = [
            ("{name}", "исходное имя файла (без расширения)"),
            ("{ext}", "расширение файла"),
            ("{n}", "порядковый номер файла (использует настройки по умолчанию из 'Настройки' → 'Настройки нумерации')"),
            ("{n:10}", "номер файла с указанным начальным номером (например: {n:10} начнется с 10, 11, 12...)"),
            ("{n:1:3}", "номер файла с начальным номером и количеством ведущих нулей (например: {n:1:3} → 001, 002, 003...)"),
            ("{filename}", "полное имя файла (с расширением)"),
            ("{dirname}", "имя папки, содержащей файл"),
            ("{format}", "формат файла (расширение без точки, заглавными)")
        ]
        
        for var, desc in basic_vars:
            create_variable_block(scrollable_frame, var, desc)
        
        # Даты и время
        date_label = tk.Label(
            scrollable_frame,
            text="Даты и время:",
            font=('Robot', 12, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        date_label.pack(anchor=tk.W, padx=10, pady=(15, 5))
        
        date_vars = [
            ("{date_created}", "дата создания (YYYY-MM-DD)"),
            ("{date_modified}", "дата изменения (YYYY-MM-DD)"),
            ("{date_created_time}", "дата и время создания (YYYY-MM-DD_HH-MM-SS)"),
            ("{date_modified_time}", "дата и время изменения (YYYY-MM-DD_HH-MM-SS)"),
            ("{year}", "год создания"),
            ("{month}", "месяц создания (01-12)"),
            ("{day}", "день создания (01-31)"),
            ("{hour}", "час создания (00-23)"),
            ("{minute}", "минута создания (00-59)"),
            ("{second}", "секунда создания (00-59)")
        ]
        
        for var, desc in date_vars:
            create_variable_block(scrollable_frame, var, desc)
        
        # Метаданные изображений
        image_label = tk.Label(
            scrollable_frame,
            text="Метаданные изображений:",
            font=('Robot', 12, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        image_label.pack(anchor=tk.W, padx=10, pady=(15, 5))
        
        image_vars = [
            ("{width}", "ширина изображения"),
            ("{height}", "высота изображения"),
            ("{width}x{height}", "размеры изображения (например, 1920x1080)"),
            ("{camera}", "модель камеры (из EXIF)"),
            ("{iso}", "ISO (из EXIF)"),
            ("{focal_length}", "фокусное расстояние (из EXIF)"),
            ("{aperture}", "диафрагма (из EXIF)"),
            ("{exposure_time}", "выдержка (из EXIF)")
        ]
        
        for var, desc in image_vars:
            create_variable_block(scrollable_frame, var, desc)
        
        # Метаданные аудио
        audio_label = tk.Label(
            scrollable_frame,
            text="Метаданные аудио:",
            font=('Robot', 12, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        audio_label.pack(anchor=tk.W, padx=10, pady=(15, 5))
        
        audio_vars = [
            ("{artist}", "исполнитель"),
            ("{title}", "название трека"),
            ("{album}", "альбом"),
            ("{audio_year}", "год выпуска"),
            ("{track}", "номер трека"),
            ("{genre}", "жанр"),
            ("{duration}", "длительность (MM:SS или HH:MM:SS)"),
            ("{bitrate}", "битрейт (kbps)")
        ]
        
        for var, desc in audio_vars:
            create_variable_block(scrollable_frame, var, desc)
        
        # Общие
        general_label = tk.Label(
            scrollable_frame,
            text="Общие:",
            font=('Robot', 12, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        general_label.pack(anchor=tk.W, padx=10, pady=(15, 5))
        
        general_vars = [
            ("{file_size}", "размер файла (B, KB, MB, GB)")
        ]
        
        for var, desc in general_vars:
            create_variable_block(scrollable_frame, var, desc)
        
        # Сохранение шаблона
        save_template_label = tk.Label(
            scrollable_frame,
            text="Сохранить свой шаблон:",
            font=('Robot', 12, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        save_template_label.pack(anchor=tk.W, padx=10, pady=(15, 5))
        
        save_template_frame = tk.Frame(scrollable_frame, bg=self.app.colors['bg_main'], relief=tk.SOLID, borderwidth=1)
        save_template_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        save_template_inner = tk.Frame(save_template_frame, bg=self.app.colors['bg_main'])
        save_template_inner.pack(fill=tk.X, padx=12, pady=10)
        
        # Поле ввода шаблона
        template_entry_frame = tk.Frame(save_template_inner, bg=self.app.colors['bg_main'])
        template_entry_frame.pack(fill=tk.X, pady=(0, 8))
        
        template_entry_label = tk.Label(
            template_entry_frame,
            text="Шаблон:",
            font=('Robot', 10),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        template_entry_label.pack(side=tk.LEFT, padx=(0, 5))
        
        template_entry_var = tk.StringVar()
        template_entry = tk.Entry(
            template_entry_frame,
            textvariable=template_entry_var,
            font=('Courier New', 10),
            bg='white',
            fg=self.app.colors['text_primary'],
            relief=tk.SOLID,
            borderwidth=1
        )
        template_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Кнопка сохранения
        def save_template_from_guide():
            template = template_entry_var.get().strip()
            if not template:
                from tkinter import messagebox
                messagebox.showwarning("Предупреждение", "Введите шаблон для сохранения")
                return
            
            # Запрашиваем имя для шаблона
            from tkinter import simpledialog, messagebox
            template_name = simpledialog.askstring(
                "Сохранить шаблон",
                "Введите имя для шаблона:",
                initialvalue=template[:30] if len(template) > 30 else template
            )
            
            if template_name:
                template_name = template_name.strip()
                if template_name:
                    # Получаем начальный номер из настроек
                    start_number = self.app.settings_manager.get('numbering_start_number', '1')
                    
                    # Получаем количество нулей из настроек
                    zeros_count = self.app.settings_manager.get('numbering_zeros_count', '0')
                    
                    # Сохраняем шаблон
                    if not hasattr(self.app, 'saved_templates'):
                        self.app.saved_templates = {}
                    
                    self.app.saved_templates[template_name] = {
                        'template': template,
                        'start_number': start_number,
                        'zeros_count': zeros_count
                    }
                    
                    # Обновляем в менеджере шаблонов
                    if hasattr(self.app, 'templates_manager'):
                        self.app.templates_manager.templates = self.app.saved_templates
                        self.app.save_templates()
                        self.app.templates_manager.save_templates(self.app.saved_templates)
                    
                    self.app.log(f"Шаблон '{template_name}' сохранен")
                    messagebox.showinfo("Успех", f"Шаблон '{template_name}' успешно сохранен!")
                    # Очищаем поле ввода
                    template_entry_var.set("")
        
        save_btn = self.app.create_rounded_button(
            template_entry_frame,
            "💾 Сохранить",
            save_template_from_guide,
            bg_color=self.app.colors['primary'],
            fg_color='white',
            font=('Robot', 9, 'bold'),
            padx=12,
            pady=6,
            active_bg=self.app.colors['primary_hover'],
            expand=False
        )
        save_btn.pack(side=tk.LEFT)
        
        # Подсказка
        hint_label = tk.Label(
            scrollable_frame,
            text="💡 Подсказка: Кликните на любую переменную, чтобы скопировать её в буфер обмена. Введите свой шаблон выше и сохраните его.",
            font=('Robot', 9, 'italic'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_secondary']
        )
        hint_label.pack(anchor=tk.W, padx=10, pady=(15, 10))
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_convert_action_content(self, parent) -> None:
        """Создание содержимого для действия 'Конвертировать'.
        
        Args:
            parent: Родительский контейнер (action_content_frame)
        """
        # Удаляем старый frame, если он существует
        if "convert" in self.app.tab_contents and self.app.tab_contents["convert"]:
            old_frame = self.app.tab_contents["convert"]
            try:
                if old_frame.winfo_exists():
                    old_frame.destroy()
            except (tk.TclError, AttributeError):
                pass
        
        # Создаем Frame для содержимого действия конвертации
        convert_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        convert_frame.grid(row=0, column=1, sticky="ew", padx=0, pady=0)
        convert_frame.columnconfigure(3, weight=1)  # Поле формата растягивается
        
        # Сохраняем ссылку на frame
        self.app.tab_contents["convert"] = convert_frame
        
        # Метка "Тип:"
        type_label = tk.Label(
            convert_frame,
            text="Тип:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        type_label.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=5)
        
        # Frame для Combobox с фиксированной высотой 40px (как у кнопок)
        filter_combo_frame = tk.Frame(convert_frame, bg=self.app.colors['bg_main'], height=40)
        filter_combo_frame.grid(row=0, column=1, sticky="ew", padx=(0, 5), pady=5)
        filter_combo_frame.grid_propagate(False)
        
        # Выпадающее меню с типами файлов
        filter_var = tk.StringVar(value="Все")
        filter_combo = ttk.Combobox(
            filter_combo_frame,
            textvariable=filter_var,
            values=["Все", "Изображения", "Документы", "Презентации", "Аудио", "Видео"],
            state='readonly',
            width=12,
            font=('Robot', 9)
        )
        # Настраиваем стиль для поля "Тип" с увеличенным padding для высоты 40px
        self.app.style.configure('Tall.TCombobox',
                                 fieldbackground=self.app.colors['bg_main'],
                                 foreground=self.app.colors['text_primary'],
                                 borderwidth=1,
                                 relief='solid',
                                 padding=(5, 5),
                                 font=('Robot', 9))
        self.app.style.map('Tall.TCombobox',
                          bordercolor=[('focus', self.app.colors['border_focus']),
                                     ('!focus', self.app.colors['border'])],
                          selectbackground=[('focus', self.app.colors['bg_main'])],
                          selectforeground=[('focus', self.app.colors['text_primary'])])
        filter_combo.configure(style='Tall.TCombobox')
        # Заполняем весь Frame без отступов для правильной высоты 40px
        filter_combo.pack(expand=True, fill=tk.BOTH)
        self.app.converter_filter_var = filter_var
        self.app.converter_filter_combo = filter_combo
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.app.converter_tab_handler.filter_converter_files_by_type() if hasattr(self.app, 'converter_tab_handler') else None)
        
        # Метка "Формат:"
        format_label = tk.Label(
            convert_frame,
            text="Формат:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        format_label.grid(row=0, column=2, sticky="w", padx=(0, 5), pady=5)
        
        # Frame для Combobox формата с фиксированной высотой 28px (как у кнопок)
        format_combo_frame = tk.Frame(convert_frame, bg=self.app.colors['bg_main'], height=28)
        format_combo_frame.grid(row=0, column=3, sticky="ew", padx=(0, 5), pady=5)
        format_combo_frame.grid_propagate(False)
        format_combo_frame.pack_propagate(False)
        convert_frame.columnconfigure(3, weight=1)  # Поле формата растягивается
        
        # Выпадающее меню с форматами
        formats = self.app.file_converter.get_supported_formats() if hasattr(self.app, 'file_converter') else []
        format_var = tk.StringVar(value=formats[0] if formats else '.png')
        format_combo = ttk.Combobox(
            format_combo_frame,
            textvariable=format_var,
            values=formats,
            state='readonly',
            width=15,
            font=('Robot', 9)
        )
        # Заполняем весь Frame без отступов для правильной высоты 28px
        format_combo.pack(fill=tk.BOTH, expand=True)
        self.app.converter_format_var = format_var
        self.app.converter_format_combo = format_combo
        
        # Чекбокс для сжатия PDF (в одной линии)
        # compress_pdf_var = tk.BooleanVar(value=False)
        # compress_pdf_check = tk.Checkbutton(
        #     convert_frame,
        #     text="Сжимать PDF",
        #     variable=compress_pdf_var,
        #     bg=self.app.colors['bg_main'],
        #     fg=self.app.colors['text_primary'],
        #     font=('Robot', 9),
        #     anchor='w'
        # )
        # compress_pdf_check.grid(row=0, column=4, sticky="w", padx=(0, 5), pady=5)
        # self.app.compress_pdf_var = compress_pdf_var
        # self.app.compress_pdf_check = compress_pdf_check
        # 
        # # Функция для обновления видимости чекбокса сжатия
        # def update_compress_checkbox(*args):
        #     target_format = format_var.get()
        #     if target_format == '.pdf':
        #         compress_pdf_check.grid(row=0, column=4, sticky="w", padx=(0, 5), pady=5)
        #     else:
        #         compress_pdf_check.grid_remove()
        # 
        # format_var.trace('w', update_compress_checkbox)
        # update_compress_checkbox()
        
        # Кнопка "Начать конвертацию" (квадратная, со значком галочки)
        def start_convert():
            if hasattr(self.app, 'converter_tab_handler'):
                self.app.converter_tab_handler.convert_files()
        
        btn_start = self.app.create_square_icon_button(
            convert_frame,
            "✓",
            start_convert,
            bg_color=self.app.colors['success'],
            size=28,
            active_bg=self.app.colors['success_hover']
        )
        btn_start.grid(row=0, column=5, padx=(0, 0), pady=5)
    
    
    def update_tree_columns_for_action(self, action: str) -> None:
        """Обновление колонок таблицы в зависимости от выбранного действия.

        Args:
            action: Название действия ('rename', 'convert')
        """
        if not hasattr(self.app, 'tree') or not self.app.tree:
            return
        
        try:
            current_columns = list(self.app.tree['columns'])
            
            # Всегда используем две колонки: "Добавленные файлы" и "Путь"
            required_columns = ("files", "path")
            if current_columns != list(required_columns):
                self.app.tree['columns'] = required_columns
                # Настраиваем заголовки
                self.app.tree.heading("files", text="Добавленные файлы", command=lambda: self.app.file_list_manager.sort_column("files"))
                self.app.tree.heading("path", text="Путь", command=lambda: self.app.file_list_manager.sort_column("path"))
                # Настраиваем колонки
                list_frame_width = self.app.list_frame.winfo_width() if hasattr(self.app, 'list_frame') else 900
                files_width = max(int(list_frame_width * 0.4), 200)
                path_width = max(int(list_frame_width * 0.5), 200)
                self.app.tree.column("files", width=files_width, anchor='w', minwidth=150, stretch=tk.YES)
                self.app.tree.column("path", width=path_width, anchor='w', minwidth=200, stretch=tk.YES)
            
            # Вызываем обновление размеров
            self.app.root.after(100, self.update_tree_columns)
        except (tk.TclError, AttributeError) as e:
            logger.debug(f"Ошибка обновления колонок для действия {action}: {e}")
    
    def update_tree_columns(self) -> None:
        """Обновление размеров колонок таблицы в соответствии с размером окна."""
        has_list_frame = hasattr(self.app, 'list_frame')
        has_tree = hasattr(self.app, 'tree')
        if has_list_frame and has_tree and self.app.list_frame and self.app.tree:
            try:
                list_frame_width = self.app.list_frame.winfo_width()
                if list_frame_width > 100:
                    # Распределяем ширину между двумя колонками
                    files_width = max(int(list_frame_width * 0.4), 150)
                    path_width = max(int(list_frame_width * 0.5), 200)
                    
                    self.app.tree.column(
                        "files",
                        width=files_width,
                        minwidth=150,
                        stretch=tk.YES
                    )
                    self.app.tree.column(
                        "path",
                        width=path_width,
                        minwidth=200,
                        stretch=tk.YES
                    )
                    
                    if hasattr(self.app, 'tree_scrollbar_x'):
                        self.app.root.after_idle(lambda: self.update_scrollbar_visibility(
                            self.app.tree, self.app.tree_scrollbar_x, 'horizontal'))
            except Exception as e:
                logger.debug(f"Ошибка обновления колонок таблицы: {e}")
    
    def _create_about_tab_content(self, parent):
        """Создание содержимого вкладки 'О программе'.
        
        Args:
            parent: Родительский контейнер (Frame)
        """
        from ui.about_tab import AboutTab
        
        # Создаем Canvas для прокрутки
        canvas = tk.Canvas(parent, bg=self.app.colors['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.app.colors['bg_main'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def on_canvas_configure(event):
            if event.widget == canvas:
                try:
                    canvas_width = event.width
                    canvas.itemconfig(canvas_window, width=canvas_width)
                    # Обновляем wraplength для текста в about_tab
                    scrollable_frame.update_idletasks()
                except (AttributeError, tk.TclError):
                    pass
        
        canvas.bind('<Configure>', on_canvas_configure)
        def on_window_configure(event):
            if event.widget == parent:
                try:
                    canvas_width = parent.winfo_width() - scrollbar.winfo_width() - 4
                    canvas.itemconfig(canvas_window, width=max(canvas_width, 100))
                    # Обновляем wraplength для текста в about_tab
                    scrollable_frame.update_idletasks()
                except (AttributeError, tk.TclError):
                    pass
        
        parent.bind('<Configure>', on_window_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Привязка прокрутки колесом мыши
        self.app.bind_mousewheel(canvas, canvas)
        self.app.bind_mousewheel(scrollable_frame, canvas)
        
        # Создаем AboutTab и используем его метод для создания содержимого
        about_tab_handler = AboutTab(
            None,  # notebook не нужен, так как мы используем Frame
            self.app.colors,
            self.app.bind_mousewheel,
            self.app._icon_photos
        )
        
        # Вызываем метод для создания содержимого на Frame
        about_tab_handler.create_content(scrollable_frame)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
    
    def update_scrollbar_visibility(
        self, widget, scrollbar, orientation: str = 'vertical'
    ) -> None:
        """Автоматическое управление видимостью скроллбара.
        
        Args:
            widget: Виджет (Treeview, Listbox, Text, Canvas)
            scrollbar: Скроллбар для управления
            orientation: Ориентация ('vertical' или 'horizontal')
        """
        try:
            if isinstance(widget, ttk.Treeview):
                items = widget.get_children()
                if not items:
                    scrollbar.grid_remove()
                    return
                
                widget.update_idletasks()
                if orientation == 'vertical':
                    widget_height = widget.winfo_height()
                    item_height = 20
                    visible_items = max(1, widget_height // item_height) if widget_height > 0 else 1
                    needs_scroll = len(items) > visible_items
                else:
                    widget_width = widget.winfo_width()
                    if widget_width > 0:
                        total_width = 0
                        for col in widget['columns']:
                            col_width = widget.column(col, 'width')
                            if col_width:
                                total_width += col_width
                        try:
                            tree_col_width = widget.column('#0', 'width')
                            if tree_col_width:
                                total_width += tree_col_width
                        except (tk.TclError, AttributeError):
                            pass
                        needs_scroll = total_width > widget_width
                    else:
                        needs_scroll = False
                
            elif isinstance(widget, tk.Listbox):
                count = widget.size()
                widget.update_idletasks()
                widget_height = widget.winfo_height()
                if widget_height > 0:
                    item_height = widget.bbox(0)[3] - widget.bbox(0)[1] if count > 0 and widget.bbox(0) else 20
                    visible_items = max(1, widget_height // item_height) if item_height > 0 else 1
                    needs_scroll = count > visible_items
                else:
                    needs_scroll = count > 0
            
            elif isinstance(widget, tk.Text):
                widget.update_idletasks()
                widget_height = widget.winfo_height()
                if widget_height > 0:
                    line_height = widget.dlineinfo('1.0')
                    if line_height:
                        line_height = line_height[3]
                        visible_lines = max(1, widget_height // line_height) if line_height > 0 else 1
                        total_lines = int(widget.index('end-1c').split('.')[0])
                        needs_scroll = total_lines > visible_lines
                    else:
                        needs_scroll = False
                else:
                    needs_scroll = False
            
            elif isinstance(widget, tk.Canvas):
                widget.update_idletasks()
                bbox = widget.bbox("all")
                if bbox:
                    if orientation == 'vertical':
                        canvas_height = widget.winfo_height()
                        content_height = bbox[3] - bbox[1]
                        needs_scroll = content_height > canvas_height and canvas_height > 1
                    else:
                        canvas_width = widget.winfo_width()
                        content_width = bbox[2] - bbox[0]
                        needs_scroll = content_width > canvas_width and canvas_width > 1
                else:
                    needs_scroll = False
            else:
                return
            
            # Показываем или скрываем скроллбар
            if needs_scroll:
                if scrollbar.winfo_manager() == '':
                    if hasattr(scrollbar, '_grid_info'):
                        scrollbar.grid(**scrollbar._grid_info)
                    elif hasattr(scrollbar, '_pack_info'):
                        scrollbar.pack(**scrollbar._pack_info)
                else:
                    try:
                        scrollbar.grid()
                    except tk.TclError:
                        try:
                            scrollbar.pack()
                        except tk.TclError as e:
                            logger.debug(f"Не удалось показать скроллбар: {e}")
            else:
                try:
                    grid_info = scrollbar.grid_info()
                    if grid_info:
                        scrollbar._grid_info = grid_info
                        scrollbar.grid_remove()
                except tk.TclError:
                    try:
                        pack_info = scrollbar.pack_info()
                        if pack_info:
                            scrollbar._pack_info = pack_info
                            scrollbar.pack_forget()
                    except tk.TclError as e:
                        logger.debug(f"Не удалось скрыть скроллбар: {e}")
        except (AttributeError, tk.TclError, ValueError):
            pass
    
    def on_window_resize(self, event=None) -> None:
        """Обработчик изменения размера окна для адаптивного масштабирования."""
        if event and event.widget == self.app.root:
            if hasattr(self.app, 'list_frame') and self.app.list_frame:
                try:
                    self.app.root.after(50, self.update_tree_columns)
                    self.app.root.after(200, self.update_tree_columns)
                except (AttributeError, tk.TclError):
                    pass


# ============================================================================
# ОБРАБОТЧИКИ ПОЛЬЗОВАТЕЛЬСКОГО ВВОДА
# ============================================================================

class HotkeysHandler:
    """Класс для управления горячими клавишами приложения."""
    
    def __init__(self, root, app) -> None:
        self.root = root
        self.app = app
        self.setup_hotkeys()
    
    def setup_hotkeys(self) -> None:
        """Настройка горячих клавиш."""
        self.root.bind('<Control-Shift-A>', lambda e: self.app.add_files())
        self.root.bind('<Control-z>', lambda e: self.app.undo_re_file())
        self.root.bind('<Control-y>', lambda e: self.app.redo_re_file())
        self.root.bind('<Control-Shift-Z>', lambda e: self.app.redo_re_file())
        self.root.bind('<Delete>', lambda e: self.app.delete_selected())
        self.root.bind('<Control-o>', lambda e: self.app.add_folder())
        self.root.bind('<Control-s>', lambda e: self.app.save_template_quick())
        self.root.bind('<Control-f>', lambda e: self.app.focus_search())
        self.root.bind('<F5>', lambda e: self.app.refresh_treeview())
        self.root.bind('<Control-r>', lambda e: self.app.apply_methods())


class SearchHandler:
    """Класс для управления поиском файлов в списке."""
    
    def __init__(self, app) -> None:
        self.app = app
    
    def focus_search(self) -> None:
        """Фокус на поле поиска (Ctrl+F)."""
        if hasattr(self.app, 'search_entry'):
            self.app.search_entry.focus()
            self.app.search_entry.select_range(0, tk.END)
    
    def on_search_change(self, event=None) -> None:
        """Обработка изменения текста поиска."""
        self.app.refresh_treeview()
    
    def clear_search(self) -> None:
        """Очистка поля поиска."""
        if hasattr(self.app, 'search_entry'):
            self.app.search_entry.delete(0, tk.END)
            self.app.refresh_treeview()
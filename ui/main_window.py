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
                                 fieldbackground=self.app.colors['bg_input'],
                                 foreground=self.app.colors['text_primary'],
                                 borderwidth=1,
                                 relief='solid',
                                 padding=(2, 2),
                                 font=('Robot', 9))
        # Сохраняем настройки bordercolor для правильного отображения рамок
        self.app.style.map('TCombobox',
                          bordercolor=[('focus', self.app.colors['border_focus']),
                                     ('!focus', self.app.colors['border'])],
                          selectbackground=[('focus', self.app.colors['bg_input'])],
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
        
        # Верхние вкладки (Файлы - первая, затем Сортировка, Настройки)
        top_tabs_list = [
            ("files", "📄 Файлы"),
            ("sort", "📂 Сортировка"),
            ("settings", "⚙️ Настройки"),
        ]
        
        # Создаем кнопки для верхних вкладок
        top_buttons_frame = tk.Frame(top_tabs_panel, bg=self.app.colors['bg_main'])
        top_buttons_frame.pack(fill=tk.X, padx=0, pady=0)
        
        for tab_id, tab_text in top_tabs_list:
            btn = tk.Button(
                top_buttons_frame,
                text=tab_text,
                font=('Robot', 9, 'bold'),
                bg=self.app.colors['bg_secondary'],
                fg=self.app.colors['text_primary'],
                relief=tk.FLAT,
                padx=20,
                pady=10,
                cursor='hand2',
                command=lambda t=tab_id: self.switch_tab(t)
            )
            btn.pack(side=tk.LEFT, fill=tk.Y)
            self.app.top_tab_buttons[tab_id] = btn
            self.app.tab_buttons[tab_id] = btn
        
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
        actions_panel.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 5))
        actions_panel.columnconfigure(2, weight=1)  # Контейнер для содержимого действий растягивается
        
        # Кнопка "Добавить" (квадратная, со значком "+")
        btn_add = self.app.create_square_icon_button(
            actions_panel,
            "+",
            self.app.add_files,
            bg_color=self.app.colors['success'],
            size=28,
            active_bg=self.app.colors['success_hover']
        )
        btn_add.grid(row=0, column=0, padx=(0, 5), pady=5)
        
        # Кнопка "Очистить" (квадратная, со значком "-")
        btn_clear = self.app.create_square_icon_button(
            actions_panel,
            "-",
            self.app.clear_files,
            bg_color=self.app.colors['danger'],
            size=28,
            active_bg=self.app.colors['danger_hover']
        )
        btn_clear.grid(row=0, column=1, padx=(0, 5), pady=5)
        
        # Контейнер для динамического содержимого действий (выбор действия + поля ввода и кнопки)
        action_content_frame = tk.Frame(actions_panel, bg=self.app.colors['bg_main'])
        action_content_frame.grid(row=0, column=2, sticky="ew", padx=(5, 0), pady=5)
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
            values=["Переименовать", "Конвертировать", "Сжать"],
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
        self.app.tab_contents["compress"] = None
        
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
            tab_id: Идентификатор вкладки ('files', 'sort', 'settings')
        """
        # Обновляем стиль кнопок верхних вкладок
        for tid, btn in self.app.top_tab_buttons.items():
            if tid == tab_id:
                btn.config(bg=self.app.colors['primary'], fg='white')
            else:
                btn.config(bg=self.app.colors['bg_secondary'], fg=self.app.colors['text_primary'])
        
        # Скрываем все контейнеры вкладок
        if hasattr(self.app, 'files_tab_container'):
            self.app.files_tab_container.grid_remove()
        if hasattr(self.app, 'sort_tab_container'):
            self.app.sort_tab_container.grid_remove()
        if hasattr(self.app, 'settings_tab_container'):
            self.app.settings_tab_container.grid_remove()
        
        # Показываем содержимое для выбранной вкладки
        if tab_id == "files":
            # Показываем вкладку "Файлы" (панель действий + список файлов)
            if hasattr(self.app, 'files_tab_container'):
                self.app.files_tab_container.grid(row=0, column=0, sticky="nsew")
            # Всегда показываем action_content_frame при переключении на вкладку "Файлы"
            if hasattr(self.app, 'action_content_frame'):
                self.app.action_content_frame.grid(row=0, column=2, sticky="ew", padx=(5, 0), pady=5)
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
        
        # Обновляем текущую вкладку
        self.app.current_tab = tab_id
    
    def _create_files_list_in_container(self, parent):
        """Создание панели со списком файлов в контейнере.
        
        Этот список файлов является ОБЩИМ для всех действий:
        переименования, конвертации и сжатия. Он создается один раз
        и используется всеми действиями.
        
        Args:
            parent: Родительский контейнер (files_container)
        """
        # Список файлов - общий для всех действий (переименование, конвертация, сжатие)
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
        
        columns = ("old_name", "new_name", "status")
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
        self.app.tree.heading("old_name", text="Исходное имя")
        self.app.tree.heading("new_name", text="Новое имя")
        self.app.tree.heading("status", text="Статус")
        
        # Тег для строки с путем (занимает обе колонки)
        self.app.tree.tag_configure('path_row', 
                                    background=self.app.colors.get('bg_secondary', '#F3F4F6'),
                                    foreground=self.app.colors.get('text_secondary', '#6B7280'),
                                    font=('Robot', 8))
        
        # Настройка тегов для цветового выделения
        self.app.tree.tag_configure('ready', background='#D1FAE5', foreground='#065F46')
        self.app.tree.tag_configure('error', background='#FEE2E2', foreground='#991B1B')
        self.app.tree.tag_configure('conflict', background='#FEF3C7', foreground='#92400E')
        self.app.tree.tag_configure('changed', foreground='#1E40AF')
        
        # Восстановление состояния сортировки
        if hasattr(self.app, 'settings_manager'):
            saved_sort = self.app.settings_manager.get('sort_column')
            saved_reverse = self.app.settings_manager.get('sort_reverse', False)
            if saved_sort:
                self.app.sort_column_name = saved_sort
                self.app.sort_reverse = saved_reverse
        
        # Настройка колонок с равными размерами
        column_width = 300
        self.app.tree.column("old_name", width=column_width, anchor='w', minwidth=100, stretch=tk.YES)
        self.app.tree.column("new_name", width=column_width, anchor='w', minwidth=100, stretch=tk.YES)
        self.app.tree.column("status", width=column_width, anchor='w', minwidth=100, stretch=tk.YES)
        
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
        for col in ("old_name", "new_name", "status"):
            self.app.tree.heading(col, command=lambda c=col: self.app.sort_column(c))
        
        # Функция для обновления путей в таблице (для обратной совместимости)
        # Удалена как неиспользуемая
        
        # Прогресс-бар (под списком файлов слева)
        progress_container = tk.Frame(left_panel, bg=self.app.colors['bg_card'])
        progress_container.pack(fill=tk.X, pady=(6, 0))
        progress_container.columnconfigure(0, weight=0)
        progress_container.columnconfigure(1, weight=1)
        
        progress_label = tk.Label(progress_container, text="Прогресс:",
                                 font=('Robot', 9, 'bold'),
                                 bg=self.app.colors['bg_card'],
                                 fg=self.app.colors['text_primary'],
                                 anchor='w')
        progress_label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        self.app.progress = ttk.Progressbar(progress_container, mode='determinate')
        self.app.progress.grid(row=0, column=1, sticky="ew")
        self.app.progress['value'] = 0
        
        self.app.progress_label = tk.Label(progress_container, text="",
                                          font=('Robot', 8),
                                          bg=self.app.colors['bg_card'],
                                          fg=self.app.colors['text_secondary'],
                                          anchor='w')
        self.app.progress_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
    
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
        methods_frame = tk.Frame(right_panel, bg=self.app.colors['bg_card'])
        self.app.methods_frame = methods_frame
        methods_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        methods_frame.columnconfigure(0, weight=1)
        methods_frame.rowconfigure(1, weight=1)
        
        # Устанавливаем метод "Новое имя" по умолчанию
        self.app.method_var = tk.StringVar()
        self.app.method_var.set("Новое имя")
        
        # Область настроек метода с прокруткой
        settings_container = tk.Frame(methods_frame, bg=self.app.colors['bg_card'])
        settings_container.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        settings_container.columnconfigure(0, weight=1)
        settings_container.rowconfigure(0, weight=1)
        
        # Canvas для прокрутки настроек
        settings_canvas = tk.Canvas(settings_container, bg=self.app.colors['bg_card'], 
                                    highlightthickness=0)
        settings_scrollbar = ttk.Scrollbar(settings_container, orient="vertical", 
                                           command=settings_canvas.yview)
        scrollable_frame = tk.Frame(settings_canvas, bg=self.app.colors['bg_card'])
        
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
        self.app.method_buttons_frame = tk.Frame(methods_frame, bg=self.app.colors['bg_card'])
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
            action: Название действия ("Переименовать", "Конвертировать", "Сжать")
        """
        # Скрываем текущее содержимое действий (только для действий переименования/конвертации/сжатия)
        for key in ["rename", "convert", "compress"]:
            if key in self.app.tab_contents and self.app.tab_contents[key]:
                self.app.tab_contents[key].grid_remove()
        
        # Убеждаемся, что мы находимся во вкладке "Файлы"
        # Если мы не во вкладке "Файлы", ничего не делаем
        if not hasattr(self.app, 'current_tab') or self.app.current_tab != "files":
            return
        
        # Убеждаемся, что мы находимся во вкладке "Файлы"
        # Список файлов уже находится в правильном месте (внутри files_tab_container)
        
        # Используем action_content_frame для размещения содержимого действий
        parent = self.app.action_content_frame if hasattr(self.app, 'action_content_frame') else None
        if not parent:
            return
        
        if action == "Переименовать":
            if "re_file" not in self.app.tab_contents or self.app.tab_contents["re_file"] is None:
                self.create_re_file_action_content(parent)
            if self.app.tab_contents["re_file"]:
                self.app.tab_contents["re_file"].grid(row=0, column=1, sticky="ew")
            # Обновляем колонки для переименования
            self.app.root.after(100, lambda act="re_file": self.update_tree_columns_for_action(act))
        elif action == "Конвертировать":
            if "convert" not in self.app.tab_contents or self.app.tab_contents["convert"] is None:
                self.create_convert_action_content(parent)
            if self.app.tab_contents.get("convert"):
                self.app.tab_contents["convert"].grid(row=0, column=1, sticky="ew")
            # Обновляем колонки для конвертации
            self.app.root.after(100, lambda act="convert": self.update_tree_columns_for_action(act))
        elif action == "Сжать":
            if "compress" not in self.app.tab_contents or self.app.tab_contents["compress"] is None:
                self.create_compress_action_content(parent)
            if self.app.tab_contents.get("compress"):
                self.app.tab_contents["compress"].grid(row=0, column=1, sticky="ew")
            # Обновляем колонки для сжатия
            self.app.root.after(100, lambda act="compress": self.update_tree_columns_for_action(act))
    
    def create_re_file_action_content(self, parent) -> None:
        """Создание содержимого для действия 'Переименовать' в одну линию.
        
        Args:
            parent: Родительский контейнер (action_content_frame)
        """
        # Создаем Frame для содержимого действия переименования
        re_file_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        re_file_frame.grid(row=0, column=1, sticky="ew")
        # Настраиваем веса колонок для правильного растяжения
        re_file_frame.columnconfigure(0, weight=1)  # Поле шаблона растягивается
        
        # Сохраняем ссылку
        self.app.tab_contents["re_file"] = re_file_frame
        
        # Контейнер для поля шаблона
        template_container = tk.Frame(re_file_frame, bg=self.app.colors['bg_main'])
        template_container.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=5)
        template_container.columnconfigure(1, weight=1)
        
        # Метка "Шаблон:" слева от поля
        template_label = tk.Label(
            template_container,
            text="Шаблон:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        template_label.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        # Комбинированное поле: поле ввода + выпадающее меню шаблонов (единое поле)
        if not hasattr(self.app, 'new_name_template'):
            self.app.new_name_template = tk.StringVar()
        
        # Frame для Combobox с фиксированной высотой 28px (как у кнопок)
        template_combo_frame = tk.Frame(template_container, bg=self.app.colors['bg_main'], height=28)
        template_combo_frame.grid(row=0, column=1, sticky="ew")
        template_combo_frame.grid_propagate(False)
        template_combo_frame.pack_propagate(False)
        
        # Используем Combobox с возможностью ввода и выбора из списка
        templates_combo = ttk.Combobox(
            template_combo_frame,
            textvariable=self.app.new_name_template,
            state='normal',  # normal вместо readonly, чтобы можно было вводить текст
            width=20,
            font=('Robot', 9)
        )
        # Заполняем весь Frame без отступов для правильной высоты 28px
        templates_combo.pack(fill=tk.BOTH, expand=True)
        self.app.rename_templates_combo = templates_combo
        
        # Контейнер для полей нумерации (скрыт по умолчанию, показывается когда есть {n} в шаблоне)
        # Размещаем справа от шаблона на той же строке
        numbering_container = tk.Frame(re_file_frame, bg=self.app.colors['bg_main'])
        self.app.rename_numbering_container = numbering_container
        # Размещаем контейнер в grid, но сразу скрываем
        numbering_container.grid(row=0, column=1, sticky="w", padx=(5, 5), pady=5)
        numbering_container.grid_remove()  # Скрываем по умолчанию
        
        # Метка и поле для начального номера
        start_number_label = tk.Label(
            numbering_container,
            text="С номера:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        start_number_label.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        # Контейнер для Spinbox с фиксированной высотой 28px (как у кнопок)
        start_number_frame = tk.Frame(numbering_container, bg=self.app.colors['bg_main'], height=28, width=60)
        start_number_frame.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        start_number_frame.grid_propagate(False)  # Запрещаем изменение размера фрейма
        
        # Сохраняем старое значение, если виджет существует
        old_start_value = "1"
        if hasattr(self.app, 'new_name_start_number'):
            try:
                old_start_value = self.app.new_name_start_number.get()
                # Уничтожаем старый виджет, если он существует
                try:
                    self.app.new_name_start_number.destroy()
                except (tk.TclError, AttributeError):
                    pass
            except (AttributeError, tk.TclError):
                pass
        
        # Создаем StringVar для Spinbox с начальным значением
        if not hasattr(self.app, 'start_number_var'):
            self.app.start_number_var = tk.StringVar(value=old_start_value)
        else:
            self.app.start_number_var.set(old_start_value)
        
        # Создаем новый Spinbox с начальным значением через textvariable
        self.app.new_name_start_number = tk.Spinbox(
            start_number_frame,
            from_=1,
            to=999999,
            width=6,
            font=('Robot', 9),
            bg='white',
            fg=self.app.colors['text_primary'],
            relief=tk.SOLID,
            borderwidth=1,
            justify=tk.CENTER,
            textvariable=self.app.start_number_var
        )
        # Размещаем виджет с помощью grid внутри Frame для правильного отображения
        self.app.new_name_start_number.grid(row=0, column=0, sticky="nsew")
        start_number_frame.rowconfigure(0, weight=1)
        start_number_frame.columnconfigure(0, weight=1)
        
        # Метка и поле для количества нулей
        zeros_label = tk.Label(
            numbering_container,
            text="Кол-во нулей:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        zeros_label.grid(row=0, column=2, sticky="w", padx=(0, 5))
        
        # Контейнер для Spinbox с фиксированной высотой 28px (как у кнопок)
        zeros_frame = tk.Frame(numbering_container, bg=self.app.colors['bg_main'], height=28, width=60)
        zeros_frame.grid(row=0, column=3, sticky="ew")
        zeros_frame.grid_propagate(False)  # Запрещаем изменение размера фрейма
        
        # Сохраняем старое значение, если виджет существует
        old_zeros_value = "0"
        if hasattr(self.app, 'new_name_zeros_count'):
            try:
                old_zeros_value = self.app.new_name_zeros_count.get()
                # Уничтожаем старый виджет, если он существует
                try:
                    self.app.new_name_zeros_count.destroy()
                except (tk.TclError, AttributeError):
                    pass
            except (AttributeError, tk.TclError):
                pass
        
        # Создаем StringVar для Spinbox с начальным значением
        if not hasattr(self.app, 'zeros_count_var'):
            self.app.zeros_count_var = tk.StringVar(value=old_zeros_value)
        else:
            self.app.zeros_count_var.set(old_zeros_value)
        
        # Создаем новый Spinbox с начальным значением через textvariable
        self.app.new_name_zeros_count = tk.Spinbox(
            zeros_frame,
            from_=0,
            to=20,
            width=6,  # Изменено с 4 на 6 для одинаковой ширины
            font=('Robot', 9),
            bg='white',
            fg=self.app.colors['text_primary'],
            relief=tk.SOLID,
            borderwidth=1,
            justify=tk.CENTER,
            textvariable=self.app.zeros_count_var
        )
        # Размещаем виджет с помощью grid внутри Frame для правильного отображения
        self.app.new_name_zeros_count.grid(row=0, column=0, sticky="nsew")
        zeros_frame.rowconfigure(0, weight=1)
        zeros_frame.columnconfigure(0, weight=1)
        
        # Контейнер для кнопок (в той же строке, что и поле шаблона)
        buttons_container = tk.Frame(re_file_frame, bg=self.app.colors['bg_main'])
        buttons_container.grid(row=0, column=2, sticky="n", padx=(5, 0), pady=5)
        
        # Функция для обновления списка шаблонов
        def refresh_templates_combo():
            try:
                # Всегда перезагружаем шаблоны из файла, чтобы получить актуальные данные
                if hasattr(self.app, 'templates_manager'):
                    try:
                        # Перезагружаем шаблоны из файла напрямую
                        reloaded_templates = self.app.templates_manager.load_templates()
                        if reloaded_templates:
                            self.app.saved_templates = reloaded_templates
                            self.app.templates_manager.templates = reloaded_templates
                    except Exception as e:
                        logger.debug(f"Ошибка перезагрузки шаблонов: {e}")
                
                # Если saved_templates все еще пустой, пытаемся загрузить из templates_manager
                if not hasattr(self.app, 'saved_templates') or not self.app.saved_templates:
                    if hasattr(self.app, 'templates_manager') and hasattr(self.app.templates_manager, 'templates'):
                        self.app.saved_templates = self.app.templates_manager.templates
                
                # Собираем все имена шаблонов
                template_names = []
                if hasattr(self.app, 'saved_templates') and self.app.saved_templates:
                    template_names.extend(self.app.saved_templates.keys())
                
                # Убираем дубликаты и сортируем
                if template_names:
                    template_names = sorted(set(template_names))
                    templates_combo['values'] = template_names
                    logger.debug(f"Загружено {len(template_names)} шаблонов в выпадающий список: {template_names}")
                else:
                    templates_combo['values'] = []
                    logger.debug("Шаблоны не найдены")
            except Exception as e:
                logger.error(f"Ошибка обновления списка шаблонов: {e}", exc_info=True)
                templates_combo['values'] = []
        
        # Функция для применения выбранного шаблона из выпадающего списка (определена ниже после создания полей номера и нулей)
        # Обновляем список шаблонов после создания
        refresh_templates_combo()
        # Сохраняем функцию обновления для использования извне
        self.app.refresh_rename_templates = refresh_templates_combo
        # Обновляем список шаблонов также после небольшой задержки, чтобы убедиться, что saved_templates загружены
        self.app.root.after(200, refresh_templates_combo)
        self.app.root.after(500, refresh_templates_combo)  # Еще одна попытка через полсекунды
        
        # Функция для показа/скрытия полей нумерации
        def update_numbering_fields_visibility():
            """Показывает/скрывает поля нумерации в зависимости от наличия {n} в шаблоне"""
            template = self.app.new_name_template.get().strip() if hasattr(self.app, 'new_name_template') else ""
            has_n = '{n}' in template
            
            if has_n:
                # Показываем контейнер с полями нумерации
                if hasattr(self.app, 'rename_numbering_container'):
                    self.app.rename_numbering_container.grid(row=0, column=1, sticky="w", padx=(5, 5), pady=5)
                    # Обновляем отображение контейнера
                    self.app.rename_numbering_container.update_idletasks()
            else:
                # Скрываем контейнер с полями нумерации
                if hasattr(self.app, 'rename_numbering_container'):
                    self.app.rename_numbering_container.grid_remove()
        
        # Привязка обработчика изменения шаблона в поле ввода
        def on_template_entry_change(event=None):
            update_numbering_fields_visibility()
            if hasattr(self.app, '_apply_template_delayed'):
                self.app._apply_template_delayed()
        templates_combo.bind('<KeyRelease>', on_template_entry_change)
        
        # Проверяем начальное состояние шаблона
        update_numbering_fields_visibility()
        
        # Обработчики для полей начального номера и нулей
        def on_number_change(event=None):
            if hasattr(self.app, '_apply_template_delayed'):
                self.app._apply_template_delayed()
        
        def on_zeros_change(event=None):
            if hasattr(self.app, '_apply_template_delayed'):
                self.app._apply_template_delayed()
        
        # Привязываем обработчики к полям номера и нулей
        self.app.new_name_start_number.config(command=on_number_change)
        self.app.new_name_start_number.bind('<KeyRelease>', lambda e: on_number_change())
        self.app.new_name_start_number.bind('<FocusOut>', lambda e: on_number_change())
        self.app.new_name_start_number.bind('<ButtonRelease-1>', lambda e: on_number_change())
        
        self.app.new_name_zeros_count.config(command=on_zeros_change)
        self.app.new_name_zeros_count.bind('<KeyRelease>', lambda e: on_zeros_change())
        self.app.new_name_zeros_count.bind('<FocusOut>', lambda e: on_zeros_change())
        self.app.new_name_zeros_count.bind('<ButtonRelease-1>', lambda e: on_zeros_change())
        
        # Обработка применения шаблона из выпадающего списка с восстановлением значений start_number и zeros_count
        def on_template_selected(event=None):
            selected_name = templates_combo.get()
            # Проверяем, есть ли это имя в сохраненных шаблонах
            if selected_name and hasattr(self.app, 'saved_templates') and selected_name in self.app.saved_templates:
                template_data = self.app.saved_templates.get(selected_name)
                if template_data:  # Если это сохраненный шаблон
                    if isinstance(template_data, dict):
                        template = template_data.get('template', '')
                        start_number = template_data.get('start_number', '1')
                        zeros_count = template_data.get('zeros_count', '0')
                    else:
                        template = str(template_data)
                        start_number = '1'
                        zeros_count = '0'
                    if template:
                        self.app.new_name_template.set(template)
                        # Восстанавливаем значения начального номера и нулей
                        if hasattr(self.app, 'start_number_var'):
                            self.app.start_number_var.set(str(start_number))
                        elif hasattr(self.app, 'new_name_start_number'):
                            self.app.new_name_start_number.delete(0, tk.END)
                            self.app.new_name_start_number.insert(0, str(start_number))
                        if hasattr(self.app, 'zeros_count_var'):
                            self.app.zeros_count_var.set(str(zeros_count))
                        elif hasattr(self.app, 'new_name_zeros_count'):
                            self.app.new_name_zeros_count.delete(0, tk.END)
                            self.app.new_name_zeros_count.insert(0, str(zeros_count))
                        # Обновляем видимость полей нумерации
                        update_numbering_fields_visibility()
                        # Применяем шаблон
                        if hasattr(self.app, '_apply_template_delayed'):
                            self.app._apply_template_delayed()
        
        # Переопределяем привязку для обработчика выбора шаблона
        templates_combo.bind('<<ComboboxSelected>>', on_template_selected)
        
        # Кнопка руководства "?" (квадратная)
        btn_guide = self.app.create_square_icon_button(
            buttons_container,
            "?",
            self.show_rename_guide,
            bg_color=self.app.colors['info'],
            size=28,
            active_bg=self.app.colors['info_hover']
        )
        btn_guide.grid(row=0, column=0, padx=(0, 5))
        self.app.rename_btn_guide = btn_guide
        
        # Кнопка "Начать переименовку" (квадратная, со значком галочки)
        btn_start = self.app.create_square_icon_button(
            buttons_container,
            "✓",
            self.app.start_re_file,
            bg_color=self.app.colors['success'],
            size=28,
            active_bg=self.app.colors['success_hover']
        )
        btn_start.grid(row=0, column=1)
        self.app.rename_btn_start = btn_start
    
    def show_rename_guide(self):
        """Показ окна руководства по шаблонам переименования"""
        guide_window = tk.Toplevel(self.app.root)
        guide_window.title("Руководство по шаблонам")
        guide_window.geometry("700x600")
        guide_window.configure(bg=self.app.colors['bg_main'])
        guide_window.transient(self.app.root)
        # Обработчик закрытия по Escape
        def on_close(event=None):
            guide_window.destroy()
        guide_window.bind('<Escape>', on_close)
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
        
        # Содержимое руководства
        guide_text = """Доступные переменные в шаблонах:

Основные:
{name} - исходное имя файла (без расширения)
{ext} - расширение файла
{n} - порядковый номер файла (начинается с 1)
{filename} - полное имя файла (с расширением)
{dirname} - имя папки, содержащей файл
{format} - формат файла (расширение без точки, заглавными)

Даты и время:
{date_created} - дата создания (YYYY-MM-DD)
{date_modified} - дата изменения (YYYY-MM-DD)
{date_created_time} - дата и время создания (YYYY-MM-DD_HH-MM-SS)
{date_modified_time} - дата и время изменения (YYYY-MM-DD_HH-MM-SS)
{year} - год создания
{month} - месяц создания (01-12)
{day} - день создания (01-31)
{hour} - час создания (00-23)
{minute} - минута создания (00-59)
{second} - секунда создания (00-59)

Метаданные изображений:
{width} - ширина изображения
{height} - высота изображения
{width}x{height} - размеры изображения (например, 1920x1080)
{camera} - модель камеры (из EXIF)
{iso} - ISO (из EXIF)
{focal_length} - фокусное расстояние (из EXIF)
{aperture} - диафрагма (из EXIF)
{exposure_time} - выдержка (из EXIF)

Метаданные аудио:
{artist} - исполнитель
{title} - название трека
{album} - альбом
{audio_year} - год выпуска
{track} - номер трека
{genre} - жанр
{duration} - длительность (MM:SS или HH:MM:SS)
{bitrate} - битрейт (kbps)

Общие:
{file_size} - размер файла (B, KB, MB, GB)

Примеры шаблонов:

IMG_{n} - создаст имена: IMG_1, IMG_2, IMG_3...
Фото_{date_created}_{n} - создаст: Фото_2024-01-15_1, Фото_2024-01-15_2...
{artist} - {title} - для аудио: Исполнитель - Название трека
{width}x{height}_{n} - для изображений: 1920x1080_1, 1920x1080_2...
{year}-{month}-{day}_{n} - дата в формате: 2024-01-15_1
{camera}_{iso}_{n} - для фото: Canon EOS 5D_ISO400_1
{date_created_time}_{name} - полная дата и время: 2024-01-15_14-30-45_файл

Условная логика:
{if:{ext}==jpg:IMG_{n}:FILE_{n}} - если расширение jpg, то IMG_номер, иначе FILE_номер"""
        
        guide_label = tk.Label(
            scrollable_frame,
            text=guide_text,
            font=('Robot', 10),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            justify=tk.LEFT,
            anchor=tk.NW,
            wraplength=650
        )
        guide_label.pack(padx=20, pady=20, anchor=tk.NW)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопка закрытия убрана - окно закрывается кликом вне его или по Escape
    
    def create_convert_action_content(self, parent) -> None:
        """Создание содержимого для действия 'Конвертировать'.
        
        Args:
            parent: Родительский контейнер (action_content_frame)
        """
        # Создаем Frame для содержимого действия конвертации
        convert_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        convert_frame.grid(row=0, column=1, sticky="ew")
        convert_frame.columnconfigure(3, weight=1)  # Чекбокс растягивается
        
        # Сохраняем ссылку
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
                                 fieldbackground=self.app.colors['bg_input'],
                                 foreground=self.app.colors['text_primary'],
                                 borderwidth=1,
                                 relief='solid',
                                 padding=(5, 5),
                                 font=('Robot', 9))
        self.app.style.map('Tall.TCombobox',
                          bordercolor=[('focus', self.app.colors['border_focus']),
                                     ('!focus', self.app.colors['border'])],
                          selectbackground=[('focus', self.app.colors['bg_input'])],
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
        compress_pdf_var = tk.BooleanVar(value=False)
        compress_pdf_check = tk.Checkbutton(
            convert_frame,
            text="Сжимать PDF",
            variable=compress_pdf_var,
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            font=('Robot', 9),
            anchor='w'
        )
        compress_pdf_check.grid(row=0, column=4, sticky="w", padx=(0, 5), pady=5)
        self.app.compress_pdf_var = compress_pdf_var
        self.app.compress_pdf_check = compress_pdf_check
        
        # Функция для обновления видимости чекбокса сжатия
        def update_compress_checkbox(*args):
            target_format = format_var.get()
            if target_format == '.pdf':
                compress_pdf_check.grid(row=0, column=4, sticky="w", padx=(0, 5), pady=5)
            else:
                compress_pdf_check.grid_remove()
        
        format_var.trace('w', update_compress_checkbox)
        update_compress_checkbox()
        
        # Кнопка руководства "?" (квадратная)
        btn_guide = self.app.create_square_icon_button(
            convert_frame,
            "?",
            self.show_convert_guide,
            bg_color=self.app.colors['info'],
            size=28,
            active_bg=self.app.colors['info_hover']
        )
        btn_guide.grid(row=0, column=5, padx=(0, 5), pady=5)
        
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
        btn_start.grid(row=0, column=6, padx=(0, 0), pady=5)
    
    def show_convert_guide(self):
        """Показ окна руководства по конвертации"""
        guide_window = tk.Toplevel(self.app.root)
        guide_window.title("Руководство по конвертации")
        guide_window.geometry("700x500")
        guide_window.configure(bg=self.app.colors['bg_main'])
        guide_window.transient(self.app.root)
        # Обработчик закрытия по Escape
        def on_close(event=None):
            guide_window.destroy()
        guide_window.bind('<Escape>', on_close)
        guide_window.focus_set()
        
        try:
            from ui.ui_components import set_window_icon
            set_window_icon(guide_window, self.app._icon_photos)
        except Exception:
            pass
        
        # Заголовок
        header = tk.Label(
            guide_window,
            text="Руководство по конвертации файлов",
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
        
        # Содержимое руководства
        guide_text = """Поддерживаемые форматы конвертации:

Изображения:
• PNG ↔ JPG, JPEG, WEBP, BMP, ICO
• JPG/JPEG ↔ PNG, WEBP, BMP
• WEBP ↔ PNG, JPG
• BMP ↔ PNG, JPG
• ICO ↔ PNG, JPG

Документы:
• PDF ↔ PNG, JPG (каждая страница как изображение)
• DOC, DOCX → PDF
• ODT → PDF

Презентации:
• PPTX, PPT → PDF (каждый слайд как страница)
• ODP → PDF

Аудио:
• MP3 ↔ WAV, OGG
• WAV ↔ MP3, OGG

Видео:
• MP4 ↔ GIF (первый кадр или анимация)

Как использовать:
1. Выберите целевой формат из выпадающего списка
2. Добавьте файлы в список (кнопка "+")
3. Нажмите кнопку "✓" для начала конвертации
4. Результаты появятся в той же папке, что и исходные файлы

Особенности:
• Для PDF доступна опция сжатия после конвертации
• Конвертация изображений сохраняет качество
• Многостраничные документы конвертируются постранично"""
        
        guide_label = tk.Label(
            scrollable_frame,
            text=guide_text,
            font=('Robot', 10),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            justify=tk.LEFT,
            anchor=tk.NW,
            wraplength=650
        )
        guide_label.pack(padx=20, pady=20, anchor=tk.NW)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопка закрытия убрана - окно закрывается кликом вне его или по Escape
    
    def create_compress_action_content(self, parent) -> None:
        """Создание содержимого для действия 'Сжать'.
        
        Args:
            parent: Родительский контейнер (action_content_frame)
        """
        # Создаем Frame для содержимого действия сжатия
        compress_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        compress_frame.grid(row=0, column=1, sticky="ew")
        compress_frame.columnconfigure(1, weight=1)  # Поле качества растягивается
        
        # Сохраняем ссылку
        self.app.tab_contents["compress"] = compress_frame
        
        # Метка "Качество:"
        quality_label = tk.Label(
            compress_frame,
            text="Качество:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        quality_label.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=5)
        
        # Frame для Combobox с фиксированной высотой 40px (как у кнопок)
        quality_combo_frame = tk.Frame(compress_frame, bg=self.app.colors['bg_main'], height=40)
        quality_combo_frame.grid(row=0, column=1, sticky="ew", padx=(0, 5), pady=5)
        quality_combo_frame.grid_propagate(False)
        
        # Выпадающее меню с уровнями качества
        quality_var = tk.StringVar(value="Среднее")
        quality_combo = ttk.Combobox(
            quality_combo_frame,
            textvariable=quality_var,
            values=["Высокое", "Среднее", "Низкое", "Минимальное"],
            state='readonly',
            width=15,
            font=('Robot', 9)
        )
        # Используем тот же стиль для поля "Качество" с увеличенным padding
        quality_combo.configure(style='Tall.TCombobox')
        # Заполняем весь Frame без отступов для правильной высоты 40px
        quality_combo.pack(expand=True, fill=tk.BOTH)
        self.app.compress_quality_var = quality_var
        
        # Кнопка руководства "?" (квадратная)
        btn_guide = self.app.create_square_icon_button(
            compress_frame,
            "?",
            self.show_compress_guide,
            bg_color=self.app.colors['info'],
            size=28,
            active_bg=self.app.colors['info_hover']
        )
        btn_guide.grid(row=0, column=2, padx=(0, 5), pady=5)
        
        # Кнопка "Начать сжатие" (квадратная, со значком галочки)
        btn_start = self.app.create_square_icon_button(
            compress_frame,
            "✓",
            lambda: self.start_compression(quality_var.get()),
            bg_color=self.app.colors['success'],
            size=28,
            active_bg=self.app.colors['success_hover']
        )
        btn_start.grid(row=0, column=3, padx=(0, 0), pady=5)
    
    def show_compress_guide(self):
        """Показ окна руководства по сжатию"""
        guide_window = tk.Toplevel(self.app.root)
        guide_window.title("Руководство по сжатию файлов")
        guide_window.geometry("700x500")
        guide_window.configure(bg=self.app.colors['bg_main'])
        guide_window.transient(self.app.root)
        # Обработчик закрытия по Escape
        def on_close(event=None):
            guide_window.destroy()
        guide_window.bind('<Escape>', on_close)
        guide_window.focus_set()
        
        try:
            from ui.ui_components import set_window_icon
            set_window_icon(guide_window, self.app._icon_photos)
        except Exception:
            pass
        
        # Заголовок
        header = tk.Label(
            guide_window,
            text="Руководство по сжатию файлов",
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
        
        # Содержимое руководства
        guide_text = """Уровни качества сжатия:

Высокое качество:
• Минимальное сжатие
• Наилучшее качество
• Больший размер файла
• Рекомендуется для важных изображений

Среднее качество:
• Баланс между качеством и размером
• Хорошее качество при заметном уменьшении размера
• Рекомендуется для большинства случаев

Низкое качество:
• Значительное сжатие
• Заметное снижение качества
• Малый размер файла
• Для экономии места

Минимальное качество:
• Максимальное сжатие
• Низкое качество
• Минимальный размер файла
• Только при острой необходимости экономии места

Поддерживаемые форматы:
• Изображения: JPG, JPEG, PNG (только JPG будет сжат)
• PDF документы: сжатие текста и изображений
• Архивы: ZIP, RAR, 7Z

Как использовать:
1. Выберите уровень качества из списка
2. Добавьте файлы в список (кнопка "+")
3. Нажмите кнопку "✓" для начала сжатия
4. Сжатые файлы сохранятся в той же папке"""
        
        guide_label = tk.Label(
            scrollable_frame,
            text=guide_text,
            font=('Robot', 10),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            justify=tk.LEFT,
            anchor=tk.NW,
            wraplength=650
        )
        guide_label.pack(padx=20, pady=20, anchor=tk.NW)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопка закрытия убрана - окно закрывается кликом вне его или по Escape
    
    def start_compression(self, quality: str):
        """Запуск сжатия файлов (заглушка для будущей реализации)
        
        Args:
            quality: Уровень качества сжатия
        """
        from tkinter import messagebox
        messagebox.showinfo(
            "Информация",
            f"Функция сжатия файлов будет реализована в будущем.\nВыбранный уровень качества: {quality}"
        )
    
    def update_tree_columns_for_action(self, action: str) -> None:
        """Обновление колонок таблицы в зависимости от выбранного действия.
        
        Args:
            action: Название действия ('rename', 'convert', 'compress')
        """
        if not hasattr(self.app, 'tree') or not self.app.tree:
            return
        
        try:
            current_columns = list(self.app.tree['columns'])
            
            if action == "rename":
                # Для переименования: Исходное имя, Новое имя, Статус
                required_columns = ("old_name", "new_name", "status")
                if current_columns != list(required_columns):
                    self.app.tree['columns'] = required_columns
                    # Настраиваем заголовки
                    self.app.tree.heading("old_name", text="Исходное имя")
                    self.app.tree.heading("new_name", text="Новое имя")
                    self.app.tree.heading("status", text="Статус")
                    # Настраиваем колонки (равная ширина)
                    column_width = 300
                    self.app.tree.column("old_name", width=column_width, anchor='w', minwidth=100, stretch=tk.YES)
                    self.app.tree.column("new_name", width=column_width, anchor='w', minwidth=100, stretch=tk.YES)
                    self.app.tree.column("status", width=column_width, anchor='w', minwidth=100, stretch=tk.YES)
            elif action == "convert":
                # Для конвертации: Имя файла, Тип, Статус
                required_columns = ("file_name", "file_type", "status")
                if current_columns != list(required_columns):
                    self.app.tree['columns'] = required_columns
                    # Настраиваем заголовки
                    self.app.tree.heading("file_name", text="Имя файла")
                    self.app.tree.heading("file_type", text="Тип")
                    self.app.tree.heading("status", text="Статус")
                    # Настраиваем колонки (равная ширина)
                    column_width = 300
                    self.app.tree.column("file_name", width=column_width, anchor='w', minwidth=100, stretch=tk.YES)
                    self.app.tree.column("file_type", width=column_width, anchor='w', minwidth=100, stretch=tk.YES)
                    self.app.tree.column("status", width=column_width, anchor='w', minwidth=100, stretch=tk.YES)
            elif action == "compress":
                # Для сжатия: Имя файла, Размер, Статус
                required_columns = ("file_name", "file_size", "status")
                if current_columns != list(required_columns):
                    self.app.tree['columns'] = required_columns
                    # Настраиваем заголовки
                    self.app.tree.heading("file_name", text="Имя файла")
                    self.app.tree.heading("file_size", text="Размер")
                    self.app.tree.heading("status", text="Статус")
                    # Настраиваем колонки (равная ширина)
                    column_width = 300
                    self.app.tree.column("file_name", width=column_width, anchor='w', minwidth=100, stretch=tk.YES)
                    self.app.tree.column("file_size", width=column_width, anchor='w', minwidth=100, stretch=tk.YES)
                    self.app.tree.column("status", width=column_width, anchor='w', minwidth=100, stretch=tk.YES)
            
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
                    available_width = max(list_frame_width - 30, 200)
                    # Равная ширина для всех колонок
                    column_width = int(available_width / 3)
                    min_width = max(80, int(column_width * 0.50))
                    
                    self.app.tree.column(
                        "old_name",
                        width=column_width,
                        minwidth=min_width,
                        stretch=tk.YES
                    )
                    self.app.tree.column(
                        "new_name",
                        width=column_width,
                        minwidth=min_width,
                        stretch=tk.YES
                    )
                    self.app.tree.column(
                        "status",
                        width=column_width,
                        minwidth=min_width,
                        stretch=tk.YES
                    )
                    
                    if hasattr(self.app, 'tree_scrollbar_x'):
                        self.app.root.after_idle(lambda: self.update_scrollbar_visibility(
                            self.app.tree, self.app.tree_scrollbar_x, 'horizontal'))
            except Exception as e:
                logger.debug(f"Ошибка обновления колонок таблицы: {e}")
    
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
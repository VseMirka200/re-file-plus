"""Модуль для создания главного окна и базовых виджетов.

Содержит обработчики пользовательского ввода: горячие клавиши и поиск.
"""

# Стандартная библиотека
import logging
import os
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
        
        Создает главное окно с вкладками, панели файлов и методов,
        а также все необходимые элементы управления.
        """
        
        # Основной контейнер с вкладками
        # Создаем Notebook для вкладок
        main_notebook = ttk.Notebook(self.app.root)
        main_notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Обработчик изменения размера главного окна (только для активной вкладки)
        def on_root_resize(event=None):
            # Проверяем, какая вкладка активна
            if hasattr(self.app, 'main_notebook') and self.app.main_notebook:
                try:
                    selected_tab = self.app.main_notebook.index(self.app.main_notebook.select())
                    # Обновляем только если активна вкладка "Файлы" (индекс 0)
                    if selected_tab == 0:
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
                            except (AttributeError, tk.TclError):
                                pass
                except (tk.TclError, AttributeError):
                    pass
        
        self.app.root.bind('<Configure>', on_root_resize)
        
        # Сохраняем ссылку на notebook
        self.app.main_notebook = main_notebook
        
        # Вкладка 1: Основное содержимое (файлы и методы)
        main_tab = tk.Frame(main_notebook, bg=self.app.colors['bg_main'])
        main_notebook.add(main_tab, text="Файлы")
        main_tab.columnconfigure(0, weight=1)
        main_tab.rowconfigure(0, weight=1)
        
        # Используем обычный Frame для распределения пространства (50/50)
        main_container = tk.Frame(main_tab, bg=self.app.colors['bg_main'])
        main_container.grid(row=0, column=0, sticky="nsew")
        # Левая панель занимает 60%, правая - 40%
        main_container.columnconfigure(0, weight=6, uniform="panels")
        main_container.columnconfigure(1, weight=4, uniform="panels")
        main_container.rowconfigure(0, weight=1)
        
        # Сохраняем ссылку на main_container для обновления размеров
        self.app.main_container = main_container
        
        # Принудительно обновляем конфигурацию колонок после создания
        def update_column_config():
            main_container.columnconfigure(0, weight=6, uniform="panels")
            main_container.columnconfigure(1, weight=4, uniform="panels")
            main_container.update_idletasks()
            # Дополнительное обновление после создания всех виджетов
            def configure_columns():
                main_container.columnconfigure(0, weight=6, uniform="panels")
                main_container.columnconfigure(1, weight=4, uniform="panels")
            
            self.app.root.after(500, configure_columns)
        
        # Оптимизация: один вызов вместо трех
        self.app.root.after(300, update_column_config)
        
        # Обработчик изменения размера для обновления колонок таблицы (только для этой вкладки)
        def on_resize(event=None):
            # Проверяем, что событие относится к этой вкладке и она активна
            if event and event.widget == main_container:
                # Проверяем, активна ли вкладка "Файлы"
                if hasattr(self.app, 'main_notebook') and self.app.main_notebook:
                    try:
                        selected_tab = self.app.main_notebook.index(
                            self.app.main_notebook.select()
                        )
                        # Если не активна вкладка "Файлы", не обновляем
                        if selected_tab != 0:
                            return
                    except (tk.TclError, AttributeError):
                        pass
                
                # Принудительно обновляем веса колонок при изменении размера
                main_container.columnconfigure(0, weight=6, uniform="panels")
                main_container.columnconfigure(1, weight=4, uniform="panels")
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
        def on_main_tab_configure(e):
            if e.widget == main_tab:
                on_resize(e)
        
        main_tab.bind('<Configure>', on_main_tab_configure)
        
        # Левая часть - список файлов
        files_count = len(self.app.files)
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
        self.app.left_panel = left_panel
        
        # Панель управления файлами
        control_panel = tk.Frame(left_panel, bg=self.app.colors['bg_card'])
        control_panel.pack(fill=tk.X, pady=(0, 12))
        control_panel.columnconfigure(0, weight=1)
        control_panel.columnconfigure(1, weight=1)
        control_panel.columnconfigure(2, weight=1)
        
        # Кнопки управления - компактное расположение
        btn_add_files = self.app.create_rounded_button(
            control_panel, "➕ Добавить файлы", self.app.add_files,
            self.app.colors['primary'], 'white', 
            font=('Robot', 9, 'bold'), padx=10, pady=6,
            active_bg=self.app.colors['primary_hover'])
        btn_add_files.grid(row=0, column=0, padx=(0, 4), sticky="ew")
        
        btn_add_folder = self.app.create_rounded_button(
            control_panel, "📁 Добавить папку", self.app.add_folder,
            self.app.colors['primary'], 'white',
            font=('Robot', 9, 'bold'), padx=10, pady=6,
            active_bg=self.app.colors['primary_hover'])
        btn_add_folder.grid(row=0, column=1, padx=(0, 4), sticky="ew")
        
        btn_clear = self.app.create_rounded_button(
            control_panel, "🗑️ Очистить", self.app.clear_files,
            self.app.colors['danger'], 'white',
            font=('Robot', 9, 'bold'), padx=10, pady=6,
            active_bg=self.app.colors['danger_hover'])
        btn_clear.grid(row=0, column=2, padx=(0, 4), sticky="ew")
        
        # Таблица файлов
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создание таблицы с прокруткой
        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL)
        
        columns = ("old_name", "new_name")
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
        
        # Тег для строки с путем (занимает обе колонки)
        self.app.tree.tag_configure('path_row', 
                                    background=self.app.colors.get('bg_secondary', '#F3F4F6'),
                                    foreground=self.app.colors.get('text_secondary', '#6B7280'),
                                    font=('Robot', 8))
        
        # Настройка тегов для цветового выделения
        # Светло-зеленый для готовых
        self.app.tree.tag_configure('ready', background='#D1FAE5', foreground='#065F46')
        # Светло-красный для ошибок
        self.app.tree.tag_configure('error', background='#FEE2E2', foreground='#991B1B')
        # Светло-желтый для конфликтов
        self.app.tree.tag_configure('conflict', background='#FEF3C7', foreground='#92400E')
        # Подсветка измененных имен
        self.app.tree.tag_configure('changed', foreground='#1E40AF')
        
        # Восстановление состояния сортировки
        if hasattr(self.app, 'settings_manager'):
            saved_sort = self.app.settings_manager.get('sort_column')
            saved_reverse = self.app.settings_manager.get('sort_reverse', False)
            if saved_sort:
                self.app.sort_column_name = saved_sort
                self.app.sort_reverse = saved_reverse
        
        # Настройка колонок с адаптивными размерами (процент от ширины)
        # Используем минимальные ширины, которые будут обновлены при изменении размера
        # Для заголовков папок первая колонка будет растягиваться на всю ширину
        self.app.tree.column("old_name", width=300, anchor='w', minwidth=100, stretch=tk.YES)
        self.app.tree.column("new_name", width=300, anchor='w', minwidth=100, stretch=tk.YES)
        
        # Обновляем колонки после инициализации
        self.app.root.after(200, self.update_tree_columns)
        
        # Сохраняем ссылку на list_frame для обновления размеров
        self.app.list_frame = list_frame
        
        # Настройка тегов для цветового выделения (отключено по запросу пользователя)
        # self.app.tree.tag_configure('ready', background='#D1FAE5')  # Светло-зеленый для готовых
        # self.app.tree.tag_configure('error', background='#FEE2E2')  # Светло-красный для ошибок
        # self.app.tree.tag_configure('conflict', background='#FEF3C7')  # Светло-желтый для конфликтов
        
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
        
        # Обработчики событий только для этой вкладки
        def on_tree_event(event=None):
            # Проверяем, активна ли вкладка "Файлы"
            if hasattr(self.app, 'main_notebook') and self.app.main_notebook:
                try:
                    selected_tab = self.app.main_notebook.index(self.app.main_notebook.select())
                    if selected_tab == 0:  # Только если активна вкладка "Файлы"
                        self.app.root.after_idle(update_tree_scrollbars)
                except (tk.TclError, AttributeError):
                    pass
        
        self.app.tree.bind('<<TreeviewSelect>>', on_tree_event)
        self.app.tree.bind('<Configure>', on_tree_event)
        
        # Обновляем видимость скроллбаров после создания виджетов
        self.app.root.after(200, update_tree_scrollbars)
        
        # Контекстное меню для таблицы файлов
        self.app.tree.bind('<Button-3>', self.app.show_file_context_menu)
        
        # Привязка сортировки
        self.app.sort_column_name = None
        self.app.sort_reverse = False
        for col in ("old_name", "new_name"):
            self.app.tree.heading(col, command=lambda c=col: self.app.sort_column(c))
        
        # Функция для обновления путей в таблице (теперь пути вставляются в refresh_treeview)
        # Эта функция больше не нужна, так как пути вставляются автоматически в refresh_treeview
        def update_files_path():
            # Пустая функция для обратной совместимости, если где-то еще вызывается
            pass
        
        # Сохраняем функцию для обратной совместимости
        self.app.update_files_path = update_files_path
        
        # Прогресс-бар (под списком файлов слева)
        progress_container = tk.Frame(left_panel, bg=self.app.colors['bg_card'])
        progress_container.pack(fill=tk.X, pady=(6, 0))
        # Настраиваем колонки для растягивания прогресс-бара на всю ширину
        progress_container.columnconfigure(0, weight=0)  # Метка "Прогресс:" не растягивается
        progress_container.columnconfigure(1, weight=1)  # Прогресс-бар растягивается на всю доступную ширину
        
        progress_label = tk.Label(progress_container, text="Прогресс:",
                                 font=('Robot', 9, 'bold'),
                                 bg=self.app.colors['bg_card'],
                                 fg=self.app.colors['text_primary'],
                                 anchor='w')
        progress_label.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        self.app.progress = ttk.Progressbar(progress_container, mode='determinate')
        # Прогресс-бар растягивается на всю доступную ширину контейнера (без правого отступа)
        self.app.progress.grid(row=0, column=1, sticky="ew")
        self.app.progress['value'] = 0
        
        self.app.progress_label = tk.Label(progress_container, text="",
                                          font=('Robot', 8),
                                          bg=self.app.colors['bg_card'],
                                          fg=self.app.colors['text_secondary'],
                                          anchor='w')
        self.app.progress_label.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        
        # Правая панель (только методы)
        # Правая панель занимает 70% пространства
        right_panel = ttk.LabelFrame(
            main_container,
            text="Методы переименования",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)
        )
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(2, 0), pady=(20, 20))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        # Внутренний Frame для содержимого с минимальными отступами
        methods_frame = tk.Frame(right_panel, bg=self.app.colors['bg_card'])
        self.app.methods_frame = methods_frame  # Сохраняем ссылку для использования в других модулях
        methods_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        methods_frame.columnconfigure(0, weight=1)
        methods_frame.rowconfigure(1, weight=1)  # Строка с настройками метода
        
        # Сохраняем ссылку на панель
        self.app.right_panel = right_panel
        
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
        # Флаг для отслеживания, нужна ли прокрутка
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
                        # Высота содержимого
                        content_height = bbox[3] - bbox[1]
                        # Если содержимое помещается (с небольшим запасом), скрываем скроллбар
                        if content_height <= canvas_height + 2:  # Небольшой запас для погрешности
                            # Устанавливаем scrollregion равным видимой области, чтобы запретить прокрутку
                            settings_canvas.configure(scrollregion=(0, 0, bbox[2], canvas_height))
                            # Сбрасываем позицию прокрутки в начало
                            settings_canvas.yview_moveto(0)
                            _needs_scrolling_settings = False
                            # Скрываем скроллбар
                            try:
                                if settings_scrollbar.winfo_viewable():
                                    settings_scrollbar.grid_remove()
                            except (tk.TclError, AttributeError):
                                pass
                        else:
                            # Обновляем scrollregion для прокрутки
                            settings_canvas.configure(scrollregion=bbox)
                            _needs_scrolling_settings = True
                            # Показываем скроллбар, если он был скрыт
                            try:
                                if not settings_scrollbar.winfo_viewable():
                                    settings_scrollbar.grid(row=0, column=1, sticky="ns")
                            except (tk.TclError, AttributeError):
                                pass
                            # Используем универсальную функцию для управления скроллбаром
                            self.update_scrollbar_visibility(settings_canvas, settings_scrollbar, 'vertical')
                else:
                    settings_scrollbar.grid_remove()
            except (AttributeError, tk.TclError):
                pass
            finally:
                _updating_scroll = False
        
        def on_frame_configure(event):
            # Обновляем scrollregion и видимость скроллбара с задержкой
            self.app.root.after_idle(update_scroll_region)
        
        scrollable_frame.bind("<Configure>", on_frame_configure)
        
        settings_canvas_window = settings_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def on_canvas_configure(event):
            if event.widget == settings_canvas:
                try:
                    canvas_width = event.width
                    if canvas_width > 1:
                        settings_canvas.itemconfig(settings_canvas_window, width=canvas_width)
                    # Обновляем видимость скроллбара при изменении размера canvas с задержкой
                    self.app.root.after_idle(update_scroll_region)
                except (AttributeError, tk.TclError):
                    pass
        
        settings_canvas.bind('<Configure>', on_canvas_configure)
        
        def on_scroll(*args):
            """Обработчик прокрутки"""
            settings_scrollbar.set(*args)
            # Не вызываем update_scroll_region здесь, чтобы избежать циклов
        
        settings_canvas.configure(yscrollcommand=on_scroll)
        
        # Сохраняем функцию обновления для использования извне
        self.app.update_scroll_region = update_scroll_region
        
        # Сохраняем ссылки для обновления размеров
        self.app.settings_canvas = settings_canvas
        self.app.settings_canvas_window = settings_canvas_window
        
        # Кастомная функция прокрутки с проверкой необходимости
        def on_mousewheel_settings(event):
            """Обработчик прокрутки с проверкой необходимости"""
            if not _needs_scrolling_settings:
                return  # Не прокручиваем, если содержимое помещается
            scroll_amount = int(-1 * (event.delta / 120))
            settings_canvas.yview_scroll(scroll_amount, "units")
        
        def on_mousewheel_linux_settings(event):
            """Обработчик прокрутки для Linux"""
            if not _needs_scrolling_settings:
                return  # Не прокручиваем, если содержимое помещается
            if event.num == 4:
                settings_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                settings_canvas.yview_scroll(1, "units")
        
        # Привязка прокрутки колесом мыши с проверкой
        settings_canvas.bind("<MouseWheel>", on_mousewheel_settings)
        settings_canvas.bind("<Button-4>", on_mousewheel_linux_settings)
        settings_canvas.bind("<Button-5>", on_mousewheel_linux_settings)
        
        # Привязка к дочерним виджетам
        def bind_to_children_settings(parent):
            """Рекурсивная привязка прокрутки к дочерним виджетам."""
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
        
        font = ('Robot', 9, 'bold')
        padx = 6  # Компактные отступы
        
        # Кнопки шаблонов будут созданы в create_new_name_settings под полем ввода
        
        # Кнопка "Начать переименование" внизу на всю ширину
        btn_start_rename = self.app.create_rounded_button(
            self.app.method_buttons_frame, "▶️ Начать переименование", self.app.start_rename,
            self.app.colors['success'], 'white',
            font=font, padx=6, pady=8,
            active_bg=self.app.colors['success_hover'], expand=True)
        btn_start_rename.pack(fill=tk.X, pady=(6, 0))
        
        # Скрытый listbox для внутреннего использования методов (для функции удаления)
        self.app.methods_listbox = tk.Listbox(methods_frame, height=0)
        self.app.methods_listbox.pack_forget()  # Скрываем его
        
        # Создаем log_text для логирования (будет использоваться в окне лога)
        self.app.logger.set_log_widget(None)
        
        # Инициализация первого метода (Новое имя)
        self.app.on_method_selected()
        
        
        
        # Создание вкладок на главном экране
        # Создаем вкладки для конвертации, сортировки и настроек
        self.app.converter_tab_handler.create_tab()
        self.app.sorter_tab_handler.create_tab()
        self.app.settings_tab_handler.create_tab()
        
        # Обработка файлов из аргументов командной строки
        if self.app.files_from_args:
            # Увеличиваем задержку, чтобы все вкладки успели инициализироваться
            self.app.root.after(1000, self.app._process_files_from_args)
            # Логируем для отладки
            self.app.log(f"Получено файлов из аргументов: {len(self.app.files_from_args)}")
            for f in self.app.files_from_args[:5]:  # Показываем первые 5 файлов
                self.app.log(f"  - {f}")
    
    def update_tree_columns(self) -> None:
        """Обновление размеров колонок таблицы в соответствии с размером окна."""
        has_list_frame = hasattr(self.app, 'list_frame')
        has_tree = hasattr(self.app, 'tree')
        if has_list_frame and has_tree and self.app.list_frame and self.app.tree:
            try:
                list_frame_width = self.app.list_frame.winfo_width()
                if list_frame_width > 100:  # Минимальная ширина для расчетов
                    # Вычитаем ширину скроллбара (примерно 20px) и отступы
                    # Минимальная ширина уменьшена
                    available_width = max(list_frame_width - 30, 200)
                    
                    # Убеждаемся, что минимальные ширины не слишком большие
                    min_width_old = max(50, int(available_width * 0.20))
                    min_width_new = max(50, int(available_width * 0.20))
                    
                    # Равная ширина для обеих колонок (50% каждая)
                    # Для заголовков папок первая колонка будет растягиваться
                    self.app.tree.column(
                        "old_name",
                        width=int(available_width * 0.50),
                        minwidth=min_width_old,
                        stretch=tk.YES
                    )
                    self.app.tree.column(
                        "new_name",
                        width=int(available_width * 0.50),
                        minwidth=min_width_new,
                        stretch=tk.YES
                    )
                    
                    # Обновляем горизонтальный скроллбар после изменения колонок
                    if hasattr(self.app, 'tree_scrollbar_x'):
                        self.app.root.after_idle(lambda: self.update_scrollbar_visibility(
                            self.app.tree, self.app.tree_scrollbar_x, 'horizontal'))
            except Exception as e:
                # Логируем ошибку, но не прерываем работу приложения
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
                # Для Treeview проверяем количество элементов
                items = widget.get_children()
                if not items:
                    if orientation == 'vertical':
                        scrollbar.grid_remove()
                    else:
                        scrollbar.grid_remove()
                    return
                
                # Проверяем, нужен ли скроллбар
                widget.update_idletasks()
                if orientation == 'vertical':
                    widget_height = widget.winfo_height()
                    # Приблизительная высота одного элемента
                    item_height = 20
                    visible_items = max(1, widget_height // item_height) if widget_height > 0 else 1
                    needs_scroll = len(items) > visible_items
                else:
                    # Для горизонтального скроллбара проверяем общую ширину всех колонок
                    widget_width = widget.winfo_width()
                    if widget_width > 0:
                        total_width = 0
                        for col in widget['columns']:
                            col_width = widget.column(col, 'width')
                            if col_width:
                                total_width += col_width
                        # Добавляем ширину колонки #0 (tree column), если она есть
                        try:
                            tree_col_width = widget.column('#0', 'width')
                            if tree_col_width:
                                total_width += tree_col_width
                        except (tk.TclError, AttributeError):
                            pass
                        # Проверяем, превышает ли общая ширина видимую ширину виджета
                        needs_scroll = total_width > widget_width
                    else:
                        needs_scroll = False
                
            elif isinstance(widget, tk.Listbox):
                # Для Listbox проверяем количество элементов
                count = widget.size()
                widget.update_idletasks()
                widget_height = widget.winfo_height()
                if widget_height > 0:
                    # Приблизительная высота одного элемента
                    item_height = widget.bbox(0)[3] - widget.bbox(0)[1] if count > 0 and widget.bbox(0) else 20
                    visible_items = max(1, widget_height // item_height) if item_height > 0 else 1
                    needs_scroll = count > visible_items
                else:
                    needs_scroll = count > 0
            
            elif isinstance(widget, tk.Text):
                # Для Text проверяем количество строк
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
                # Для Canvas проверяем размер контента
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
                    # Скроллбар не размещен, размещаем его
                    if hasattr(scrollbar, '_grid_info'):
                        scrollbar.grid(**scrollbar._grid_info)
                    elif hasattr(scrollbar, '_pack_info'):
                        scrollbar.pack(**scrollbar._pack_info)
                else:
                    # Скроллбар уже размещен, просто показываем
                    try:
                        scrollbar.grid()
                    except tk.TclError:
                        try:
                            scrollbar.pack()
                        except tk.TclError as e:
                            logger.debug(f"Не удалось показать скроллбар: {e}")
            else:
                # Сохраняем информацию о размещении перед скрытием
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
            # Игнорируем ошибки при обновлении
            pass
    
    def on_window_resize(self, event=None) -> None:
        """Обработчик изменения размера окна для адаптивного масштабирования."""
        if event and event.widget == self.app.root:
            # Обновляем размеры колонок таблицы при изменении размера окна
            if hasattr(self.app, 'list_frame') and self.app.list_frame:
                try:
                    # Используем небольшую задержку для получения актуального размера
                    self.app.root.after(50, self.update_tree_columns)
                    # Также обновляем при следующем событии для более плавной работы
                    self.app.root.after(200, self.update_tree_columns)
                except (AttributeError, tk.TclError):
                    # Некоторые виджеты не поддерживают операции с canvas
                    pass


# ============================================================================
# ОБРАБОТЧИКИ ПОЛЬЗОВАТЕЛЬСКОГО ВВОДА (объединены из ui/input_handlers.py)
# ============================================================================

class HotkeysHandler:
    """Класс для управления горячими клавишами приложения."""
    
    def __init__(self, root, app) -> None:
        """Инициализация обработчика горячих клавиш.
        
        Args:
            root: Корневое окно Tkinter
            app: Экземпляр главного приложения (для доступа к методам)
        """
        self.root = root
        self.app = app
        self.setup_hotkeys()
    
    def setup_hotkeys(self) -> None:
        """Настройка горячих клавиш."""
        self.root.bind('<Control-Shift-A>', lambda e: self.app.add_files())
        self.root.bind('<Control-z>', lambda e: self.app.undo_rename())
        self.root.bind('<Control-y>', lambda e: self.app.redo_rename())
        self.root.bind('<Control-Shift-Z>', lambda e: self.app.redo_rename())
        self.root.bind('<Delete>', lambda e: self.app.delete_selected())
        self.root.bind('<Control-o>', lambda e: self.app.add_folder())
        self.root.bind('<Control-s>', lambda e: self.app.save_template_quick())
        self.root.bind('<Control-f>', lambda e: self.app.focus_search())
        self.root.bind('<F5>', lambda e: self.app.refresh_treeview())
        self.root.bind('<Control-r>', lambda e: self.app.apply_methods())


class SearchHandler:
    """Класс для управления поиском файлов в списке."""
    
    def __init__(self, app) -> None:
        """Инициализация обработчика поиска.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам)
        """
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

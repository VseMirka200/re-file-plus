"""Модуль для создания UI вкладки сортировки."""

import logging
import os
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)


class SorterUI:
    """Класс для создания UI вкладки сортировки."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def create_tab(self):
        """Создание вкладки сортировки файлов на главном экране"""
        if not hasattr(self.app, 'main_notebook') or not self.app.main_notebook:
            return
        
        sorter_tab = tk.Frame(self.app.main_notebook, bg=self.app.colors['bg_main'])
        sorter_tab.columnconfigure(0, weight=1)
        sorter_tab.rowconfigure(0, weight=1)
        self.app.main_notebook.add(sorter_tab, text="Сортировка файлов")
        
        # Основной контейнер
        main_container = tk.Frame(sorter_tab, bg=self.app.colors['bg_main'])
        main_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        main_container.columnconfigure(0, weight=1)
        main_container.columnconfigure(1, weight=1)
        main_container.rowconfigure(0, weight=1)
        
        # Левая панель - настройки
        left_panel = ttk.LabelFrame(
            main_container,
            text="Настройки сортировки",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)
        )
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=(20, 20))
        left_panel.columnconfigure(0, weight=1)
        
        # Выбор папки для сортировки
        folder_frame = tk.Frame(left_panel, bg=self.app.colors['bg_main'])
        folder_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(folder_frame, text="Папка для сортировки:",
                font=('Robot', 9, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 5))
        
        folder_path_frame = tk.Frame(folder_frame, bg=self.app.colors['bg_main'])
        folder_path_frame.pack(fill=tk.X)
        
        self.app.sorter_folder_path = tk.StringVar()
        # По умолчанию - рабочий стол
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.exists(desktop_path):
            self.app.sorter_folder_path.set(desktop_path)
        else:
            # Альтернативный путь для рабочего стола
            desktop_path = os.path.join(os.path.expanduser("~"), "Рабочий стол")
            if os.path.exists(desktop_path):
                self.app.sorter_folder_path.set(desktop_path)
            else:
                self.app.sorter_folder_path.set(os.path.expanduser("~"))
        
        folder_entry = tk.Entry(folder_path_frame,
                               textvariable=self.app.sorter_folder_path,
                               font=('Robot', 9),
                               bg='white',
                               fg=self.app.colors['text_primary'],
                               relief=tk.SOLID,
                               borderwidth=1)
        folder_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        btn_browse = self.app.create_square_icon_button(
            folder_path_frame,
            "🔍",
            self.app.sorter_tab_handler.browse_sorter_folder,
            bg_color=self.app.colors['primary'],
            size=28,
            active_bg=self.app.colors['primary_hover'],
            tooltip="Обзор..."
        )
        btn_browse.pack(side=tk.LEFT, fill=tk.NONE)
        
        # Правая панель - результаты (пока пустая)
        right_panel = ttk.LabelFrame(
            main_container,
            text="Результаты сортировки",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)
        )
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(2, 0), pady=(20, 20))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
    
    def create_tab_content(self, parent):
        """Создание содержимого вкладки сортировки (для новой структуры с общим списком файлов)
        
        Args:
            parent: Родительский контейнер для размещения содержимого
        """
        # Создаем Frame для содержимого вкладки сортировки
        sort_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        sort_frame.grid(row=0, column=0, sticky="nsew", pady=(5, 0))
        sort_frame.columnconfigure(0, weight=1)
        sort_frame.rowconfigure(1, weight=1)  # settings_panel растягивается
        sort_frame.rowconfigure(0, weight=0)  # actions_panel не растягивается
        
        # Сохраняем ссылку
        self.app.tab_contents["sort"] = sort_frame
        
        # Панель действий для вкладки "Сортировка" (как во вкладке "Файлы")
        actions_panel = tk.Frame(sort_frame, bg=self.app.colors['bg_main'])
        actions_panel.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 5))
        
        # Контейнер для кнопок (чтобы они были "за границей" основного контейнера)
        buttons_container = tk.Frame(actions_panel, bg=self.app.colors['bg_main'])
        buttons_container.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Кнопки управления сортировкой (квадратные, только иконки)
        # Добавить правило
        btn_add_filter = self.app.create_square_icon_button(
            buttons_container,
            "+",
            self.app.sorter_tab_handler.add_sorter_filter,
            bg_color=self.app.colors['success'],
            size=28,
            active_bg=self.app.colors['success_hover'],
            tooltip="Добавить правило"
        )
        btn_add_filter.grid(row=0, column=0, padx=(0, 5), pady=0)
        
        # Сохранить
        btn_save = self.app.create_square_icon_button(
            buttons_container,
            "💾",
            self.app.sorter_tab_handler.save_sorter_filters,
            bg_color=self.app.colors['info'],
            size=28,
            active_bg=self.app.colors['info_hover'],
            tooltip="Сохранить правила"
        )
        btn_save.grid(row=0, column=1, padx=(0, 5), pady=0)
        
        # Предпросмотр
        btn_preview = self.app.create_square_icon_button(
            buttons_container,
            "🔍",
            self.app.sorter_tab_handler.preview_file_sorting,
            bg_color=self.app.colors['info'],
            size=28,
            active_bg=self.app.colors['info_hover'],
            tooltip="Предпросмотр сортировки"
        )
        btn_preview.grid(row=0, column=2, padx=(0, 5), pady=0)
        
        # Начать сортировку
        btn_start_sort = self.app.create_square_icon_button(
            buttons_container,
            "✓",
            self.app.sorter_tab_handler.start_file_sorting,
            bg_color=self.app.colors['success'],
            size=28,
            active_bg=self.app.colors['success_hover'],
            tooltip="Начать сортировку"
        )
        btn_start_sort.grid(row=0, column=3, padx=(0, 5), pady=0)
        
        # Контейнер для панели настроек (как files_container во вкладке "Файлы")
        settings_container = tk.Frame(sort_frame, bg=self.app.colors['bg_main'])
        settings_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        settings_container.columnconfigure(0, weight=1)
        settings_container.rowconfigure(0, weight=1)
        
        # Панель с настройками и действиями
        settings_panel = ttk.LabelFrame(
            settings_container,
            text="Настройки сортировки",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)
        )
        settings_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 1))
        settings_panel.columnconfigure(0, weight=1)
        
        # Выбор папки для сортировки
        folder_frame = tk.Frame(settings_panel, bg=self.app.colors['bg_main'])
        folder_frame.pack(fill=tk.X, pady=(0, 15))
        folder_frame.columnconfigure(1, weight=1)
        
        # Метка "Папка для сортировки:" в одной строке с полем и кнопкой
        tk.Label(folder_frame, text="Папка для сортировки:",
                font=('Robot', 9, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary']).grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        if not hasattr(self.app, 'sorter_folder_path'):
            self.app.sorter_folder_path = tk.StringVar()
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            if os.path.exists(desktop_path):
                self.app.sorter_folder_path.set(desktop_path)
            else:
                desktop_path = os.path.join(os.path.expanduser("~"), "Рабочий стол")
                if os.path.exists(desktop_path):
                    self.app.sorter_folder_path.set(desktop_path)
                else:
                    self.app.sorter_folder_path.set(os.path.expanduser("~"))
        
        # Frame для Entry с фиксированной высотой 28px (как у кнопки "Обзор")
        folder_entry_frame = tk.Frame(folder_frame, bg=self.app.colors['bg_main'], height=28)
        folder_entry_frame.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        folder_entry_frame.grid_propagate(False)
        folder_entry_frame.pack_propagate(False)
        
        folder_entry = tk.Entry(folder_entry_frame,
                               textvariable=self.app.sorter_folder_path,
                               font=('Robot', 9),
                               bg='white',
                               fg=self.app.colors['text_primary'],
                               relief=tk.SOLID,
                               borderwidth=1)
        folder_entry.pack(fill=tk.BOTH, expand=True)
        
        btn_browse = self.app.create_square_icon_button(
            folder_frame,
            "🔍",
            self.app.sorter_tab_handler.browse_sorter_folder,
            bg_color=self.app.colors['primary'],
            size=28,
            active_bg=self.app.colors['primary_hover'],
            tooltip="Обзор..."
        )
        btn_browse.grid(row=0, column=2, sticky="")
        
        # Фильтры
        filters_frame = tk.Frame(settings_panel, bg=self.app.colors['bg_main'])
        filters_frame.pack(fill=tk.BOTH, expand=True)
        filters_frame.columnconfigure(0, weight=1)
        
        tk.Label(filters_frame, text="Правила распределения:",
                font=('Robot', 9, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 10))
        
        # Canvas для прокрутки фильтров
        filters_canvas = tk.Canvas(filters_frame, bg=self.app.colors['bg_main'],
                                   highlightthickness=0)
        filters_scrollbar = ttk.Scrollbar(filters_frame, orient="vertical",
                                          command=filters_canvas.yview)
        filters_scrollable = tk.Frame(filters_canvas, bg=self.app.colors['bg_main'])
        
        filters_canvas_window = filters_canvas.create_window((0, 0),
                                                             window=filters_scrollable,
                                                             anchor="nw")
        
        # Функция для автоматического показа/скрытия скроллбара
        def update_scrollbar_visibility(*args):
            try:
                canvas_height = filters_canvas.winfo_height()
                scrollable_height = filters_scrollable.winfo_reqheight()
                
                if scrollable_height > canvas_height:
                    filters_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                else:
                    filters_scrollbar.pack_forget()
            except (tk.TclError, AttributeError):
                pass
        
        def on_filters_canvas_configure(event):
            if event.widget == filters_canvas:
                canvas_width = event.width
                filters_canvas.itemconfig(filters_canvas_window, width=canvas_width)
                # Обновляем видимость скроллбара при изменении размера canvas
                filters_canvas.after(10, update_scrollbar_visibility)
        
        filters_canvas.bind('<Configure>', on_filters_canvas_configure)
        
        def on_scroll(*args):
            filters_scrollbar.set(*args)
        
        filters_canvas.configure(yscrollcommand=on_scroll)
        
        def on_mousewheel_filters(event):
            scroll_amount = int(-1 * (event.delta / 120))
            filters_canvas.yview_scroll(scroll_amount, "units")
        
        filters_canvas.bind("<MouseWheel>", on_mousewheel_filters)
        
        # Обновляем видимость скроллбара при изменении содержимого
        def on_scrollable_configure(event):
            filters_canvas.configure(scrollregion=filters_canvas.bbox("all"))
            filters_canvas.after(10, update_scrollbar_visibility)
        
        filters_scrollable.bind("<Configure>", on_scrollable_configure)
        
        filters_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        filters_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Сохраняем ссылку на функцию обновления для вызова из refresh_filters_display
        self.app.update_filters_scrollbar = update_scrollbar_visibility
        
        # Контейнер для списка фильтров
        self.app.sorter_filters_frame = filters_scrollable
        if not hasattr(self.app, 'sorter_filters'):
            self.app.sorter_filters = []
        
        # Загружаем сохраненные фильтры
        self.app.sorter_tab_handler.load_sorter_filters()
        
        # Инициализация списка фильтров
        if not self.app.sorter_filters:
            self.app.sorter_tab_handler.add_default_filters()


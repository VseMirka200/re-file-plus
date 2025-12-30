"""Модуль для вкладки сортировки файлов.

Обеспечивает интерфейс для сортировки файлов по различным критериям:
дата создания, размер, расширение и другие параметры.
"""

import logging
import os
from datetime import datetime

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ui.ui_components import set_window_icon

logger = logging.getLogger(__name__)


class SorterTab:
    """Класс для управления вкладкой сортировки файлов."""
    
    def __init__(self, app):
        """Инициализация вкладки сортировки.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
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
            self.browse_sorter_folder,
            bg_color=self.app.colors['primary'],
            size=28,
            active_bg=self.app.colors['primary_hover'],
            tooltip="Обзор..."
        )
        btn_browse.pack(side=tk.LEFT, fill=tk.NONE)
        
        # Фильтры
        filters_frame = tk.Frame(left_panel, bg=self.app.colors['bg_main'])
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
        
        def on_filters_canvas_configure(event):
            if event.widget == filters_canvas:
                canvas_width = event.width
                filters_canvas.itemconfig(filters_canvas_window, width=canvas_width)
        
        filters_canvas.bind('<Configure>', on_filters_canvas_configure)
        filters_canvas.configure(yscrollcommand=filters_scrollbar.set)
        
        # Привязка прокрутки колесом мыши
        def on_mousewheel_filters(event):
            scroll_amount = int(-1 * (event.delta / 120))
            filters_canvas.yview_scroll(scroll_amount, "units")
        
        filters_canvas.bind("<MouseWheel>", on_mousewheel_filters)
        
        filters_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        filters_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Контейнер для списка фильтров
        self.app.sorter_filters_frame = filters_scrollable
        if not hasattr(self.app, 'sorter_filters'):
            self.app.sorter_filters = []  # Список фильтров
        
        # Кнопки управления фильтрами удалены - перенесены под вкладки
        
        # Правая панель - действия и результаты (такого же размера как настройка конвертации)
        right_panel = ttk.LabelFrame(
            main_container,
            text="Действия",
            style='Card.TLabelframe',
            padding=10
        )
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)
        # Устанавливаем одинаковую ширину с левой панелью (как в конвертации)
        main_container.columnconfigure(0, weight=6, uniform="panels")
        main_container.columnconfigure(1, weight=4, uniform="panels")
        
        # Внутренний Frame для содержимого (для работы с bg)
        right_panel_inner = tk.Frame(right_panel, bg=self.app.colors['bg_main'])
        right_panel_inner.pack(fill=tk.BOTH, expand=True)
        right_panel_inner.columnconfigure(0, weight=1)
        right_panel_inner.rowconfigure(2, weight=1)
        
        # Кнопки управления удалены - перенесены под вкладки
        
        # Результаты убраны
        
        # Загружаем сохраненные фильтры
        self.load_sorter_filters()
        
        # Инициализация списка фильтров
        if not self.app.sorter_filters:
            # Добавляем несколько примеров фильтров по умолчанию
            self.add_default_filters()
    
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
            self.add_sorter_filter,
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
            self.save_sorter_filters,
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
            self.preview_file_sorting,
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
            self.start_file_sorting,
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
            self.browse_sorter_folder,
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
        
        # Кнопки управления фильтрами удалены - перенесены под вкладки
        
        # Кнопки управления удалены - перенесены под вкладки
        
        # Результаты убраны
        
        # Загружаем сохраненные фильтры
        self.load_sorter_filters()
        
        # Инициализация списка фильтров
        if not self.app.sorter_filters:
            self.add_default_filters()
    
    def browse_sorter_folder(self):
        """Выбор папки для сортировки"""
        folder = filedialog.askdirectory(title="Выберите папку для сортировки")
        if folder:
            self.app.sorter_folder_path.set(folder)
    
    def add_sorter_filter(self):
        """Добавление нового правила фильтрации"""
        filter_window = tk.Toplevel(self.app.root)
        filter_window.title("Добавить правило")
        filter_window.geometry("500x400")
        filter_window.configure(bg=self.app.colors['bg_main'])
        
        try:
            set_window_icon(filter_window, self.app._icon_photos)
        except (AttributeError, tk.TclError, OSError) as e:
            logger.debug(f"Не удалось установить иконку окна: {e}")
        except Exception as e:
            logger.warning(f"Неожиданная ошибка при установке иконки: {e}")
        
        main_frame = tk.Frame(filter_window, bg=self.app.colors['bg_main'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Название папки назначения
        tk.Label(main_frame, text="Название папки назначения:",
                font=('Robot', 9, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 5))
        
        folder_name_var = tk.StringVar()
        folder_entry = tk.Entry(main_frame, textvariable=folder_name_var,
                               font=('Robot', 9), bg='white',
                               fg=self.app.colors['text_primary'],
                               relief=tk.SOLID, borderwidth=1)
        folder_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Тип фильтра
        tk.Label(main_frame, text="Тип фильтра:",
                font=('Robot', 9, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 5))
        
        filter_type_var = tk.StringVar(value="extension")
        filter_types = [
            ("По расширению", "extension"),
            ("По имени файла", "filename"),
            ("По размеру", "size"),
            ("По дате создания", "date"),
            ("По типу MIME", "mime")
        ]
        
        for text, value in filter_types:
            tk.Radiobutton(main_frame, text=text, variable=filter_type_var,
                          value=value, bg=self.app.colors['bg_main'],
                          fg=self.app.colors['text_primary'],
                          font=('Robot', 9)).pack(anchor=tk.W, padx=20)
        
        # Значение фильтра
        tk.Label(main_frame, text="Значение фильтра:",
                font=('Robot', 9, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(15, 5))
        
        filter_value_var = tk.StringVar()
        filter_value_entry = tk.Entry(main_frame, textvariable=filter_value_var,
                                      font=('Robot', 9), bg='white',
                                      fg=self.app.colors['text_primary'],
                                      relief=tk.SOLID, borderwidth=1)
        filter_value_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Подсказка
        hint_text = "Примеры:\n- Расширение: .jpg, .png, .pdf\n- Имя: содержит 'фото', начинается с 'IMG'\n- Размер: >10MB, <1MB\n- Дата: >2024-01-01, <2023-12-31"
        tk.Label(main_frame, text=hint_text,
                font=('Robot', 8),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_secondary'],
                justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 15))
        
        # Кнопки
        buttons_frame = tk.Frame(main_frame, bg=self.app.colors['bg_main'])
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        def save_filter():
            folder_name = folder_name_var.get().strip()
            filter_type = filter_type_var.get()
            filter_value = filter_value_var.get().strip()
            
            if not folder_name or not filter_value:
                messagebox.showwarning("Предупреждение",
                                      "Заполните все поля")
                return
            
            filter_data = {
                'folder_name': folder_name,
                'type': filter_type,
                'value': filter_value,
                'enabled': True
            }
            
            self.app.sorter_filters.append(filter_data)
            self.refresh_filters_display()
            filter_window.destroy()
            messagebox.showinfo("Успешно", "Правило добавлено")
        
        btn_save = self.app.create_rounded_button(
            buttons_frame, "💾 Сохранить", save_filter,
            self.app.colors['success'], 'white',
            font=('Robot', 9, 'bold'), padx=15, pady=8,
            active_bg=self.app.colors['success_hover'], expand=True)
        btn_save.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        btn_cancel = self.app.create_rounded_button(
            buttons_frame, "❌ Отмена", filter_window.destroy,
            self.app.colors['danger'], 'white',
            font=('Robot', 9, 'bold'), padx=15, pady=8,
            active_bg=self.app.colors['danger_hover'], expand=True)
        btn_cancel.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def refresh_filters_display(self):
        """Обновление отображения фильтров"""
        # Очищаем текущие виджеты
        for widget in self.app.sorter_filters_frame.winfo_children():
            widget.destroy()
        
        # Отображаем все фильтры
        for i, filter_data in enumerate(self.app.sorter_filters):
            filter_frame = tk.Frame(self.app.sorter_filters_frame, bg=self.app.colors['bg_main'],
                                   relief=tk.SOLID, borderwidth=1)
            filter_frame.pack(fill=tk.X, pady=2, padx=5)
            filter_frame.columnconfigure(1, weight=1)
            
            # Чекбокс включения
            enabled_var = tk.BooleanVar(value=filter_data.get('enabled', True))
            enabled_var.trace('w', lambda *args, idx=i: self.toggle_filter(idx))
            tk.Checkbutton(filter_frame, variable=enabled_var,
                          bg=self.app.colors['bg_main']).grid(row=0, column=0, padx=(5, 2))
            
            # Информация о фильтре
            info_text = f"{filter_data['folder_name']} | {filter_data['type']}: {filter_data['value']}"
            tk.Label(filter_frame, text=info_text,
                    font=('Robot', 9),
                    bg=self.app.colors['bg_main'],
                    fg=self.app.colors['text_primary']).grid(row=0, column=1, sticky="w", padx=(2, 2))
            
            # Кнопка удаления (квадратная, как кнопка "Добавить")
            btn_delete = self.app.create_square_icon_button(
                filter_frame,
                "🗑️",
                lambda idx=i: self.delete_filter(idx),
                bg_color=self.app.colors['danger'],
                size=28,
                active_bg=self.app.colors['danger_hover'],
                tooltip="Удалить правило"
            )
            btn_delete.grid(row=0, column=2, padx=(2, 5), sticky="nse")
        
        # Обновляем видимость скроллбара после обновления списка фильтров
        if hasattr(self.app, 'update_filters_scrollbar'):
            self.app.root.after(10, self.app.update_filters_scrollbar)
    
    def toggle_filter(self, index):
        """Включение/выключение фильтра"""
        if 0 <= index < len(self.app.sorter_filters):
            # Обновляем состояние через чекбокс
            pass
    
    def delete_filter(self, index):
        """Удаление фильтра"""
        if 0 <= index < len(self.app.sorter_filters):
            if messagebox.askyesno("Подтверждение", "Удалить это правило?"):
                del self.app.sorter_filters[index]
                self.refresh_filters_display()
    
    def add_default_filters(self):
        """Добавление фильтров по умолчанию"""
        default_filters = [
            {'folder_name': 'Изображения', 'type': 'extension', 'value': '.jpg,.jpeg,.png,.gif,.bmp,.webp', 'enabled': True},
            {'folder_name': 'Документы', 'type': 'extension', 'value': '.pdf,.doc,.docx,.xls,.xlsx,.txt', 'enabled': True},
            {'folder_name': 'Видео', 'type': 'extension', 'value': '.mp4,.avi,.mkv,.mov,.wmv', 'enabled': True},
            {'folder_name': 'Аудио', 'type': 'extension', 'value': '.mp3,.wav,.flac,.ogg,.m4a', 'enabled': True},
            {'folder_name': 'Архивы', 'type': 'extension', 'value': '.zip,.rar,.7z,.tar,.gz', 'enabled': True}
        ]
        
        self.app.sorter_filters.extend(default_filters)
        self.refresh_filters_display()
    
    def save_sorter_filters(self):
        """Сохранение фильтров в настройки"""
        try:
            filters_data = {
                'folder_path': self.app.sorter_folder_path.get(),
                'filters': self.app.sorter_filters
            }
            self.app.settings_manager.set('file_sorter_filters', filters_data)
            self.app.settings_manager.save_settings(self.app.settings_manager.settings)
            messagebox.showinfo("Успешно", "Фильтры сохранены")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить фильтры: {e}")
    
    def load_sorter_filters(self):
        """Загрузка фильтров из настроек"""
        try:
            filters_data = self.app.settings_manager.get('file_sorter_filters', {})
            if filters_data:
                if 'folder_path' in filters_data:
                    self.app.sorter_folder_path.set(filters_data['folder_path'])
                if 'filters' in filters_data:
                    self.app.sorter_filters = filters_data['filters']
                    self.refresh_filters_display()
        except Exception as e:
            logger.debug(f"Не удалось загрузить фильтры: {e}")
            # Если не удалось загрузить, добавляем фильтры по умолчанию
            if not self.app.sorter_filters:
                self.add_default_filters()
    
    def preview_file_sorting(self):
        """Предпросмотр сортировки файлов"""
        folder_path = self.app.sorter_folder_path.get()
        
        if not folder_path or not os.path.exists(folder_path):
            messagebox.showerror("Ошибка", "Укажите существующую папку для сортировки")
            return
        
        enabled_filters = [f for f in self.app.sorter_filters if f.get('enabled', True)]
        if not enabled_filters:
            messagebox.showwarning("Предупреждение", "Нет активных правил для сортировки")
            return
        
        # Собираем все файлы из папки
        files_to_sort = []
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                files_to_sort.append(item_path)
        
        if not files_to_sort:
            messagebox.showinfo("Информация", "В выбранной папке нет файлов для сортировки")
            return
        
        # Создаем окно предпросмотра
        preview_window = tk.Toplevel(self.app.root)
        preview_window.title("Предпросмотр сортировки")
        preview_window.geometry("900x600")
        preview_window.configure(bg=self.app.colors['bg_main'])
        
        try:
            set_window_icon(preview_window, self.app._icon_photos)
        except (AttributeError, tk.TclError, OSError) as e:
            logger.debug(f"Не удалось установить иконку окна: {e}")
        except Exception as e:
            logger.warning(f"Неожиданная ошибка при установке иконки: {e}")
        
        main_frame = tk.Frame(preview_window, bg=self.app.colors['bg_main'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Заголовок
        header_frame = tk.Frame(main_frame, bg=self.app.colors['bg_main'])
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        tk.Label(header_frame, text="Предпросмотр сортировки файлов",
                font=('Robot', 12, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary']).pack(anchor=tk.W)
        
        tk.Label(header_frame, text=f"Папка: {folder_path}",
                font=('Robot', 9),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_secondary']).pack(anchor=tk.W, pady=(5, 0))
        
        # Таблица предпросмотра
        table_frame = tk.Frame(main_frame, bg=self.app.colors['bg_main'])
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Создаем Treeview для отображения предпросмотра
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        
        columns = ("file", "destination", "status")
        preview_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            style='Custom.Treeview'
        )
        
        scrollbar_y.config(command=preview_tree.yview)
        scrollbar_x.config(command=preview_tree.xview)
        
        # Настройка колонок
        preview_tree.heading("file", text="Файл")
        preview_tree.heading("destination", text="Папка назначения")
        preview_tree.heading("status", text="Статус")
        
        preview_tree.column("file", width=200, anchor='w', minwidth=100)
        preview_tree.column("destination", width=200, anchor='w', minwidth=100)
        preview_tree.column("status", width=200, anchor='center', minwidth=100)
        
        # Теги для цветового выделения
        preview_tree.tag_configure('sorted', background='#D1FAE5', foreground='#065F46')
        preview_tree.tag_configure('unsorted', background='#FEF3C7', foreground='#92400E')
        preview_tree.tag_configure('error', background='#FEE2E2', foreground='#991B1B')
        
        # Размещение таблицы
        preview_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Статистика
        stats_frame = tk.Frame(main_frame, bg=self.app.colors['bg_main'])
        stats_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        stats_label = tk.Label(stats_frame, text="",
                               font=('Robot', 9, 'bold'),
                               bg=self.app.colors['bg_main'],
                               fg=self.app.colors['text_primary'],
                               anchor=tk.W)
        stats_label.pack(anchor=tk.W)
        
        # Обрабатываем файлы для предпросмотра
        sorted_count = 0
        unsorted_count = 0
        error_count = 0
        
        for file_path in files_to_sort:
            try:
                file_name = os.path.basename(file_path)
                matched = False
                destination = ""
                
                # Проверяем каждый фильтр
                for filter_data in enabled_filters:
                    if self.file_matches_filter(file_path, filter_data):
                        destination = filter_data['folder_name']
                        matched = True
                        sorted_count += 1
                        break
                
                if matched:
                    preview_tree.insert("", tk.END, values=(file_name, destination, "Будет отсортирован"),
                                      tags=('sorted',))
                else:
                    unsorted_count += 1
                    preview_tree.insert("", tk.END, values=(file_name, "-", "Не отсортирован"),
                                      tags=('unsorted',))
            
            except Exception as e:
                error_count += 1
                preview_tree.insert("", tk.END, values=(os.path.basename(file_path), "-", f"Ошибка: {e}"),
                                  tags=('error',))
        
        # Обновляем статистику
        total = len(files_to_sort)
        stats_text = f"Всего файлов: {total} | Будет отсортировано: {sorted_count} | Не отсортировано: {unsorted_count}"
        if error_count > 0:
            stats_text += f" | Ошибок: {error_count}"
        stats_label.config(text=stats_text)
        
        # Кнопка закрытия
        btn_close = self.app.create_rounded_button(
            main_frame, "❌ Закрыть", preview_window.destroy,
            self.app.colors['primary'], 'white',
            font=('Robot', 9, 'bold'), padx=15, pady=8,
            active_bg=self.app.colors['primary_hover'], expand=False)
        btn_close.grid(row=3, column=0, pady=(15, 0))
    
    def start_file_sorting(self):
        """Запуск сортировки файлов"""
        folder_path = self.app.sorter_folder_path.get()
        
        if not folder_path or not os.path.exists(folder_path):
            messagebox.showerror("Ошибка", "Укажите существующую папку для сортировки")
            return
        
        enabled_filters = [f for f in self.app.sorter_filters if f.get('enabled', True)]
        if not enabled_filters:
            messagebox.showwarning("Предупреждение", "Нет активных правил для сортировки")
            return
        
        if not messagebox.askyesno("Подтверждение",
                                   f"Начать сортировку файлов в папке:\n{folder_path}\n\n"
                                   f"Будет обработано {len(enabled_filters)} правил(а)?"):
            return
        
        # Запускаем сортировку в отдельном потоке через concurrent.futures
        # Запускаем в отдельном потоке через threading (безопаснее для GUI)
        import threading
        thread = threading.Thread(
            target=self.sort_files_thread, 
            args=(folder_path, enabled_filters),
            daemon=True, 
            name="sort_files"
        )
        thread.start()
    
    def sort_files_thread(self, folder_path, filters):
        """Поток для сортировки файлов"""
        try:
            total_files = 0
            moved_files = 0
            errors = []
            
            # Собираем все файлы из папки
            files_to_sort = []
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    files_to_sort.append(item_path)
                    total_files += 1
            
            # Результаты убраны
            # self.app.root.after(0, lambda: self.app.sorter_results_text.delete(1.0, tk.END))
            
            # Обрабатываем каждый файл
            for i, file_path in enumerate(files_to_sort):
                try:
                    file_name = os.path.basename(file_path)
                    file_ext = os.path.splitext(file_name)[1].lower()
                    
                    # Проверяем каждый фильтр
                    matched = False
                    for filter_data in filters:
                        if self.file_matches_filter(file_path, filter_data):
                            target_folder_name = filter_data['folder_name']
                            target_folder = os.path.join(folder_path, target_folder_name)
                            
                            # Создаем папку, если её нет
                            if not os.path.exists(target_folder):
                                os.makedirs(target_folder)
                            
                            # Перемещаем файл
                            target_path = os.path.join(target_folder, file_name)
                            
                            # Если файл с таким именем уже существует, добавляем номер
                            counter = 1
                            base_name, ext = os.path.splitext(file_name)
                            while os.path.exists(target_path):
                                new_name = f"{base_name}_{counter}{ext}"
                                target_path = os.path.join(target_folder, new_name)
                                counter += 1
                            
                            os.rename(file_path, target_path)
                            moved_files += 1
                            matched = True
                            
                            result_text = f"✓ {file_name} -> {target_folder_name}\n"
                            # Результаты убраны
                            # self.app.root.after(0, lambda t=result_text: self.app.sorter_results_text.insert(tk.END, t))
                            break
                    
                    if not matched:
                        # Результаты убраны
                        # result_text = f"○ {file_name} (не подошел ни под одно правило)\n"
                        # self.app.root.after(0, lambda t=result_text: self.app.sorter_results_text.insert(tk.END, t))
                        pass
                
                except Exception as e:
                    error_msg = f"Ошибка при обработке {os.path.basename(file_path)}: {e}\n"
                    errors.append(error_msg)
                    # Результаты убраны
                    # self.app.root.after(0, lambda t=error_msg: self.app.sorter_results_text.insert(tk.END, t))
                
            
            # Показываем итоги
            # Результаты убраны
            # summary = f"\n{'='*50}\n"
            # summary += f"Итого обработано: {total_files} файлов\n"
            # summary += f"Перемещено: {moved_files} файлов\n"
            # summary += f"Ошибок: {len(errors)}\n"
            # self.app.root.after(0, lambda t=summary: self.app.sorter_results_text.insert(tk.END, t))
            
            
            if moved_files > 0:
                self.app.root.after(0, lambda: messagebox.showinfo(
                    "Сортировка завершена",
                    f"Обработано файлов: {total_files}\n"
                    f"Перемещено: {moved_files}\n"
                    f"Ошибок: {len(errors)}"))
        
        except Exception as e:
            error_msg = f"Критическая ошибка: {e}"
            self.app.root.after(0, lambda: messagebox.showerror("Ошибка", error_msg))
            logger.error(f"Ошибка сортировки файлов: {e}", exc_info=True)
    
    def file_matches_filter(self, file_path, filter_data):
        """Проверка, соответствует ли файл фильтру"""
        filter_type = filter_data['type']
        filter_value = filter_data['value']
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        if filter_type == 'extension':
            # Поддерживаем несколько расширений через запятую
            extensions = [ext.strip().lower() for ext in filter_value.split(',')]
            return file_ext in extensions or f".{file_ext}" in extensions
        
        elif filter_type == 'filename':
            # Проверка по имени файла
            file_name_lower = file_name.lower()
            filter_value_lower = filter_value.lower()
            
            if filter_value_lower.startswith('начинается с '):
                prefix = filter_value_lower.replace('начинается с ', '').strip()
                return file_name_lower.startswith(prefix)
            elif filter_value_lower.startswith('содержит '):
                substring = filter_value_lower.replace('содержит ', '').strip()
                return substring in file_name_lower
            else:
                # Простое совпадение
                return filter_value_lower in file_name_lower
        
        elif filter_type == 'size':
            # Проверка по размеру (требует парсинга строки типа ">10MB")
            try:
                file_size = os.path.getsize(file_path)
                # Упрощенная проверка (можно расширить)
                if '>' in filter_value or '<' in filter_value:
                    # Парсим размер
                    size_str = filter_value.replace('>', '').replace('<', '').strip().upper()
                    if 'MB' in size_str:
                        size_bytes = float(size_str.replace('MB', '')) * 1024 * 1024
                    elif 'KB' in size_str:
                        size_bytes = float(size_str.replace('KB', '')) * 1024
                    elif 'GB' in size_str:
                        size_bytes = float(size_str.replace('GB', '')) * 1024 * 1024 * 1024
                    else:
                        size_bytes = float(size_str)
                    
                    if '>' in filter_value:
                        return file_size > size_bytes
                    else:
                        return file_size < size_bytes
            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Ошибка при парсинге размера файла: {e}")
                return False
            except Exception as e:
                logger.warning(f"Неожиданная ошибка при проверке размера файла: {e}")
                return False
        
        elif filter_type == 'date':
            # Проверка по дате (упрощенная)
            try:
                file_mtime = os.path.getmtime(file_path)
                file_date = datetime.fromtimestamp(file_mtime).date()
                # Упрощенная проверка (можно расширить)
                return True  # Заглушка
            except (OSError, ValueError, TypeError) as e:
                logger.debug(f"Ошибка при получении даты файла: {e}")
                return False
            except Exception as e:
                logger.warning(f"Неожиданная ошибка при проверке даты файла: {e}")
                return False
        
        elif filter_type == 'mime':
            # Проверка по типу MIME (упрощенная, по расширению)
            return self.file_matches_filter(file_path, {
                'type': 'extension',
                'value': filter_value
            })
        
        return False

"""Модуль для окна управления методами переименования.

Обеспечивает расширенный интерфейс для настройки методов переименования
с предпросмотром и примерами использования.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from core.re_file_methods import (
    AddRemoveMethod,
    CaseMethod,
    MetadataMethod,
    NewNameMethod,
    NumberingMethod,
    RegexMethod,
    ReplaceMethod,
)
from ui.ui_components import set_window_icon


class MethodsWindow:
    """Класс для управления окном методов переименования."""
    
    def __init__(self, app):
        """Инициализация окна методов.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
    
    def open_methods_window(self):
        """Открытие окна методов переименования"""
        if self.app.windows['methods'] is not None and self.app.windows['methods'].winfo_exists():
            try:
                if self.app.windows['methods'].state() == 'iconic':
                    self.app.windows['methods'].deiconify()
            except (AttributeError, tk.TclError):
                pass
            self.app.windows['methods'].lift()
            self.app.windows['methods'].focus_force()
            if hasattr(self.app, 'methods_window_listbox'):
                self.update_methods_window_list()
            return
        
        window = tk.Toplevel(self.app.root)
        window.title("Методы переименования")
        window.geometry("500x650")
        window.minsize(450, 550)
        window.configure(bg=self.app.colors['bg_main'])
        try:
            set_window_icon(window, self.app._icon_photos)
        except (AttributeError, tk.TclError, OSError, RuntimeError, TypeError):
            pass
        except (MemoryError, RecursionError):
            pass
        # Финальный catch для неожиданных исключений (критично для стабильности)
        except BaseException:
            pass
        
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)
        self.app.windows['methods'] = window
        
        # Основной контейнер
        main_frame = tk.Frame(window, bg=self.app.colors['bg_main'])
        main_frame.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Заголовок
        header_frame = tk.Frame(main_frame, bg=self.app.colors['bg_main'])
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        title_label = tk.Label(header_frame, text="Методы переименования", 
                              font=('Robot', 12, 'bold'),
                              bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'])
        title_label.pack(anchor=tk.W)
        
        # Кнопки управления (вертикально, с названиями)
        header_buttons = tk.Frame(header_frame, bg=self.app.colors['bg_main'])
        header_buttons.pack(fill=tk.X, pady=(10, 0))
        header_buttons.columnconfigure(0, weight=1)
        
        btn_add = self.app.create_rounded_button(
            header_buttons, "➕ Добавить", lambda: self.add_method_from_window(),
            self.app.colors['primary'], 'white',
            font=('Robot', 9, 'bold'), padx=10, pady=10,
            active_bg=self.app.colors['primary_hover'])
        btn_add.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        btn_remove = self.app.create_rounded_button(
            header_buttons, "➖ Удалить", lambda: self.remove_method_from_window(),
            self.app.colors['primary_light'], 'white',
            font=('Robot', 9, 'bold'), padx=10, pady=10,
            active_bg=self.app.colors['primary'])
        btn_remove.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        
        btn_clear = self.app.create_rounded_button(
            header_buttons, "🗑️ Очистить", lambda: self.clear_methods_from_window(),
            self.app.colors['danger'], 'white',
            font=('Robot', 9, 'bold'), padx=10, pady=10,
            active_bg=self.app.colors['danger_hover'])
        btn_clear.grid(row=2, column=0, sticky="ew")
        
        # Контент с двумя панелями
        content_frame = tk.Frame(main_frame, bg=self.app.colors['bg_main'])
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=2)
        content_frame.rowconfigure(0, weight=1)
        
        # Левая панель: список методов
        list_panel = ttk.LabelFrame(content_frame, text="Список", 
                                   style='Card.TLabelframe', padding=8)
        list_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        list_panel.columnconfigure(0, weight=1)
        list_panel.rowconfigure(0, weight=1)
        
        list_scroll = tk.Frame(list_panel, bg=self.app.colors['bg_main'])
        list_scroll.grid(row=0, column=0, sticky="nsew")
        list_scroll.columnconfigure(0, weight=1)
        list_scroll.rowconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(list_scroll)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.app.methods_window_listbox = tk.Listbox(list_scroll, font=('Robot', 9),
                                                bg='white', fg=self.app.colors['text_primary'],
                                                selectbackground=self.app.colors['primary'],
                                                selectforeground='white',
                                                yscrollcommand=scrollbar.set)
        self.app.methods_window_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar.config(command=self.app.methods_window_listbox.yview)
        self.app.methods_window_listbox.bind('<<ListboxSelect>>', 
                                       lambda e: self.on_method_selected_in_window())
        
        # Сохраняем ссылку на скроллбар
        self.app.methods_window_scrollbar = scrollbar
        
        # Автоматическое управление видимостью скроллбара для Listbox
        def update_methods_scrollbar(*args):
            self.app.update_scrollbar_visibility(self.app.methods_window_listbox, scrollbar, 'vertical')
        
        # Мгновенное обновление без задержки
        self.app.methods_window_listbox.bind('<Configure>', lambda e: update_methods_scrollbar())
        
        self.update_methods_window_list()
        
        # Обновляем скроллбар сразу после обновления списка
        update_methods_scrollbar()
        
        # Правая панель: настройки
        settings_panel = ttk.LabelFrame(content_frame, text="Настройки", 
                                       style='Card.TLabelframe', padding=8)
        settings_panel.grid(row=0, column=1, sticky="nsew")
        settings_panel.columnconfigure(0, weight=1)
        settings_panel.rowconfigure(1, weight=1)
        
        # Выбор типа метода
        self.app.methods_window_method_var = tk.StringVar()
        method_combo = ttk.Combobox(settings_panel,
                                   textvariable=self.app.methods_window_method_var,
                                   values=["Новое имя", "Добавить/Удалить", "Замена", 
                                          "Регистр", "Нумерация", "Метаданные", 
                                          "Регулярные выражения"],
                                   state="readonly", width=18, font=('Robot', 9))
        method_combo.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        method_combo.current(0)
        method_combo.bind("<<ComboboxSelected>>", 
                         lambda e: self.on_method_type_selected_in_window())
        
        # Область настроек
        settings_canvas = tk.Canvas(settings_panel, bg=self.app.colors['bg_main'], 
                                   highlightthickness=0)
        settings_scrollbar = ttk.Scrollbar(settings_panel, orient="vertical", 
                                          command=settings_canvas.yview)
        self.app.methods_window_settings_frame = tk.Frame(settings_canvas, 
                                                      bg=self.app.colors['bg_main'])
        
        # Флаг для отслеживания, нужна ли прокрутка
        _needs_scrolling_methods = True
        
        def update_methods_scroll_region():
            """Обновление области прокрутки и видимости скроллбара"""
            nonlocal _needs_scrolling_methods
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
                            _needs_scrolling_methods = False
                            # Скрываем скроллбар
                            try:
                                if settings_scrollbar.winfo_viewable():
                                    settings_scrollbar.grid_remove()
                            except (tk.TclError, AttributeError):
                                pass
                        else:
                            # Обновляем scrollregion для прокрутки
                            settings_canvas.configure(scrollregion=bbox)
                            _needs_scrolling_methods = True
                            # Показываем скроллбар, если он был скрыт
                            try:
                                if not settings_scrollbar.winfo_viewable():
                                    settings_scrollbar.grid(row=1, column=1, sticky="ns")
                            except (tk.TclError, AttributeError):
                                pass
                            # Используем универсальную функцию для управления скроллбаром
                            self.app.update_scrollbar_visibility(settings_canvas, settings_scrollbar, 'vertical')
            except (AttributeError, tk.TclError):
                pass
        
        self.app.methods_window_settings_frame.bind(
            "<Configure>",
            lambda e: update_methods_scroll_region())
        
        canvas_win = settings_canvas.create_window((0, 0), 
                                                   window=self.app.methods_window_settings_frame, 
                                                   anchor="nw")
        
        def on_canvas_configure(event):
            if event.widget == settings_canvas:
                try:
                    settings_canvas.itemconfig(canvas_win, width=event.width)
                    # Обновляем scrollregion и видимость скроллбара
                    window.after(10, update_methods_scroll_region)
                except (AttributeError, tk.TclError):
                    pass
        
        settings_canvas.bind('<Configure>', on_canvas_configure)
        
        def on_scroll_methods(*args):
            """Обработчик прокрутки"""
            settings_scrollbar.set(*args)
            # Обновляем видимость скроллбара после прокрутки
            window.after(10, update_methods_scroll_region)
        
        settings_canvas.configure(yscrollcommand=on_scroll_methods)
        
        # Кастомная функция прокрутки с проверкой необходимости
        def on_mousewheel_methods(event):
            """Обработчик прокрутки с проверкой необходимости"""
            if not _needs_scrolling_methods:
                return  # Не прокручиваем, если содержимое помещается
            scroll_amount = int(-1 * (event.delta / 120))
            settings_canvas.yview_scroll(scroll_amount, "units")
        
        def on_mousewheel_linux_methods(event):
            """Обработчик прокрутки для Linux"""
            if not _needs_scrolling_methods:
                return  # Не прокручиваем, если содержимое помещается
            if event.num == 4:
                settings_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                settings_canvas.yview_scroll(1, "units")
        
        # Привязка прокрутки колесом мыши с проверкой
        settings_canvas.bind("<MouseWheel>", on_mousewheel_methods)
        settings_canvas.bind("<Button-4>", on_mousewheel_linux_methods)
        settings_canvas.bind("<Button-5>", on_mousewheel_linux_methods)
        
        # Привязка к дочерним виджетам
        def bind_to_children_methods(parent):
            """Рекурсивная привязка прокрутки к дочерним виджетам."""
            for child in parent.winfo_children():
                try:
                    child.bind("<MouseWheel>", on_mousewheel_methods)
                    child.bind("<Button-4>", on_mousewheel_linux_methods)
                    child.bind("<Button-5>", on_mousewheel_linux_methods)
                    bind_to_children_methods(child)
                except (AttributeError, tk.TclError):
                    pass
        
        bind_to_children_methods(self.app.methods_window_settings_frame)
        
        settings_canvas.grid(row=1, column=0, sticky="nsew")
        settings_scrollbar.grid(row=1, column=1, sticky="ns")
        
        # Обновляем scrollregion после создания всех элементов
        def finalize_methods_scroll():
            update_methods_scroll_region()
        
        window.after(100, finalize_methods_scroll)
        
        self.on_method_type_selected_in_window()
        
        # Кнопка применения
        btn_apply = self.app.create_rounded_button(
            main_frame, "✅ Применить", lambda: self.apply_methods_from_window(),
            self.app.colors['success'], 'white',
            font=('Robot', 9, 'bold'), padx=12, pady=6,
            active_bg=self.app.colors['success_hover'])
        btn_apply.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        def on_close():
            try:
                if window.winfo_exists():
                    window.iconify()
            except (AttributeError, tk.TclError):
                pass
        
        window.protocol("WM_DELETE_WINDOW", on_close)
    
    def update_methods_window_list(self):
        """Обновление списка методов"""
        if not hasattr(self.app, 'methods_window_listbox'):
            return
        self.app.methods_window_listbox.delete(0, tk.END)
        for i, method in enumerate(self.app.methods_manager.get_methods()):
            name = self.get_method_display_name(method)
            self.app.methods_window_listbox.insert(tk.END, f"{i+1}. {name}")
    
    def get_method_display_name(self, method):
        """Получение имени метода для отображения"""
        return self.app.methods_manager.get_method_display_name(method)
    
    def on_method_selected_in_window(self):
        """Обработка выбора метода из списка"""
        selection = self.app.methods_window_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        methods = self.app.methods_manager.get_methods()
        if 0 <= index < len(methods):
            method = methods[index]
            self.load_method_settings(method)
    
    def load_method_settings(self, method):
        """Загрузка настроек метода"""
        method_map = {
            NewNameMethod: (0, "Новое имя"),
            AddRemoveMethod: (1, "Добавить/Удалить"),
            ReplaceMethod: (2, "Замена"),
            CaseMethod: (3, "Регистр"),
            NumberingMethod: (4, "Нумерация"),
            MetadataMethod: (5, "Метаданные"),
            RegexMethod: (6, "Регулярные выражения")
        }
        
        for cls, (idx, name) in method_map.items():
            if isinstance(method, cls):
                self.app.methods_window_method_var.set(name)
                break
        
        self.on_method_type_selected_in_window()
    
    def on_method_type_selected_in_window(self, event=None):
        """Обработка выбора типа метода"""
        for widget in self.app.methods_window_settings_frame.winfo_children():
            widget.destroy()
        
        method_name = self.app.methods_window_method_var.get()
        method_creators = {
            "Новое имя": self.create_new_name_settings,
            "Добавить/Удалить": self.create_add_remove_settings,
            "Замена": self.create_replace_settings,
            "Регистр": self.create_case_settings,
            "Нумерация": self.create_numbering_settings,
            "Метаданные": self.create_metadata_settings,
            "Регулярные выражения": self.create_regex_settings
        }
        
        creator = method_creators.get(method_name)
        if creator:
            creator()
    
    def create_new_name_settings(self):
        """Настройки для метода Новое имя"""
        tk.Label(self.app.methods_window_settings_frame, text="Шаблон:", 
                font=('Robot', 9), bg=self.app.colors['bg_main'], 
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 4))
        
        self.app.methods_window_new_name_template = tk.StringVar()
        tk.Entry(self.app.methods_window_settings_frame,
                textvariable=self.app.methods_window_new_name_template,
                font=('Robot', 9), bg='white', fg=self.app.colors['text_primary'],
                relief=tk.SOLID, borderwidth=1).pack(fill=tk.X, pady=(0, 8))
        
        num_frame = tk.Frame(self.app.methods_window_settings_frame, bg=self.app.colors['bg_main'])
        num_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(num_frame, text="Начальный номер:", font=('Robot', 8),
                bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary']).pack(side=tk.LEFT)
        
        self.app.methods_window_new_name_start_number = tk.StringVar(value="1")
        tk.Entry(num_frame, textvariable=self.app.methods_window_new_name_start_number,
                font=('Robot', 8), bg='white', fg=self.app.colors['text_primary'],
                relief=tk.SOLID, borderwidth=1, width=8).pack(side=tk.LEFT, padx=(5, 0))
    
    def create_add_remove_settings(self):
        """Настройки для метода Добавить/Удалить"""
        self.app.methods_window_add_remove_op = tk.StringVar(value="add")
        op_frame = tk.Frame(self.app.methods_window_settings_frame, bg=self.app.colors['bg_main'])
        op_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Radiobutton(op_frame, text="Добавить", variable=self.app.methods_window_add_remove_op,
                      value="add", bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'],
                      font=('Robot', 8)).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(op_frame, text="Удалить", variable=self.app.methods_window_add_remove_op,
                      value="remove", bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'],
                      font=('Robot', 8)).pack(side=tk.LEFT)
        
        tk.Label(self.app.methods_window_settings_frame, text="Текст:", 
                font=('Robot', 9), bg=self.app.colors['bg_main'], 
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 4))
        
        self.app.methods_window_add_remove_text = tk.StringVar()
        tk.Entry(self.app.methods_window_settings_frame,
                textvariable=self.app.methods_window_add_remove_text,
                font=('Robot', 9), bg='white', fg=self.app.colors['text_primary'],
                relief=tk.SOLID, borderwidth=1).pack(fill=tk.X, pady=(0, 8))
        
        self.app.methods_window_add_remove_pos = tk.StringVar(value="before")
        pos_frame = tk.Frame(self.app.methods_window_settings_frame, bg=self.app.colors['bg_main'])
        pos_frame.pack(fill=tk.X)
        
        tk.Radiobutton(pos_frame, text="Перед", variable=self.app.methods_window_add_remove_pos,
                      value="before", bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'],
                      font=('Robot', 8)).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(pos_frame, text="После", variable=self.app.methods_window_add_remove_pos,
                      value="after", bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'],
                      font=('Robot', 8)).pack(side=tk.LEFT)
    
    def create_replace_settings(self):
        """Настройки для метода Замена"""
        tk.Label(self.app.methods_window_settings_frame, text="Найти:", 
                font=('Robot', 9), bg=self.app.colors['bg_main'], 
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 4))
        
        self.app.methods_window_replace_find = tk.StringVar()
        tk.Entry(self.app.methods_window_settings_frame,
                textvariable=self.app.methods_window_replace_find,
                font=('Robot', 9), bg='white', fg=self.app.colors['text_primary'],
                relief=tk.SOLID, borderwidth=1).pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(self.app.methods_window_settings_frame, text="Заменить на:", 
                font=('Robot', 9), bg=self.app.colors['bg_main'], 
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 4))
        
        self.app.methods_window_replace_with = tk.StringVar()
        tk.Entry(self.app.methods_window_settings_frame,
                textvariable=self.app.methods_window_replace_with,
                font=('Robot', 9), bg='white', fg=self.app.colors['text_primary'],
                relief=tk.SOLID, borderwidth=1).pack(fill=tk.X, pady=(0, 8))
        
        self.app.methods_window_replace_case = tk.BooleanVar(value=False)
        tk.Checkbutton(self.app.methods_window_settings_frame, text="Учитывать регистр",
                      variable=self.app.methods_window_replace_case,
                      bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'],
                      font=('Robot', 8)).pack(anchor=tk.W)
    
    def create_case_settings(self):
        """Настройки для метода Регистр"""
        self.app.methods_window_case_type = tk.StringVar(value="lower")
        case_frame = tk.Frame(self.app.methods_window_settings_frame, bg=self.app.colors['bg_main'])
        case_frame.pack(fill=tk.X)
        
        types = [("lower", "Строчные"), ("upper", "Заглавные"),
                ("capitalize", "Первая заглавная"), ("title", "Заглавные слова")]
        
        for value, text in types:
            tk.Radiobutton(case_frame, text=text, variable=self.app.methods_window_case_type,
                          value=value, bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'],
                          font=('Robot', 8)).pack(anchor=tk.W)
    
    def create_numbering_settings(self):
        """Настройки для метода Нумерация"""
        params_frame = tk.Frame(self.app.methods_window_settings_frame, bg=self.app.colors['bg_main'])
        params_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(params_frame, text="С:", font=('Robot', 8),
                bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary']).pack(side=tk.LEFT)
        self.app.methods_window_numbering_start = tk.StringVar(value="1")
        tk.Entry(params_frame, textvariable=self.app.methods_window_numbering_start,
                font=('Robot', 8), bg='white', fg=self.app.colors['text_primary'],
                relief=tk.SOLID, borderwidth=1, width=6).pack(side=tk.LEFT, padx=5)
        
        tk.Label(params_frame, text="Шаг:", font=('Robot', 8),
                bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary']).pack(side=tk.LEFT)
        self.app.methods_window_numbering_step = tk.StringVar(value="1")
        tk.Entry(params_frame, textvariable=self.app.methods_window_numbering_step,
                font=('Robot', 8), bg='white', fg=self.app.colors['text_primary'],
                relief=tk.SOLID, borderwidth=1, width=6).pack(side=tk.LEFT, padx=5)
        
        tk.Label(params_frame, text="Цифр:", font=('Robot', 8),
                bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary']).pack(side=tk.LEFT)
        self.app.methods_window_numbering_digits = tk.StringVar(value="3")
        tk.Entry(params_frame, textvariable=self.app.methods_window_numbering_digits,
                font=('Robot', 8), bg='white', fg=self.app.colors['text_primary'],
                relief=tk.SOLID, borderwidth=1, width=6).pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.app.methods_window_settings_frame, text="Формат ({n} для номера):", 
                font=('Robot', 8), bg=self.app.colors['bg_main'], 
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 4))
        
        self.app.methods_window_numbering_format = tk.StringVar(value="({n})")
        tk.Entry(self.app.methods_window_settings_frame,
                textvariable=self.app.methods_window_numbering_format,
                font=('Robot', 8), bg='white', fg=self.app.colors['text_primary'],
                relief=tk.SOLID, borderwidth=1).pack(fill=tk.X, pady=(0, 8))
        
        self.app.methods_window_numbering_pos = tk.StringVar(value="end")
        pos_frame = tk.Frame(self.app.methods_window_settings_frame, bg=self.app.colors['bg_main'])
        pos_frame.pack(fill=tk.X)
        
        tk.Radiobutton(pos_frame, text="В начале", variable=self.app.methods_window_numbering_pos,
                      value="start", bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'],
                      font=('Robot', 8)).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(pos_frame, text="В конце", variable=self.app.methods_window_numbering_pos,
                      value="end", bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'],
                      font=('Robot', 8)).pack(side=tk.LEFT)
    
    def create_metadata_settings(self):
        """Настройки для метода Метаданные"""
        tk.Label(self.app.methods_window_settings_frame, text="Тег:", 
                font=('Robot', 9), bg=self.app.colors['bg_main'], 
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 4))
        
        self.app.methods_window_metadata_tag = tk.StringVar()
        tk.Entry(self.app.methods_window_settings_frame,
                textvariable=self.app.methods_window_metadata_tag,
                font=('Robot', 9), bg='white', fg=self.app.colors['text_primary'],
                relief=tk.SOLID, borderwidth=1).pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(self.app.methods_window_settings_frame, 
                text="Примеры: {width}x{height}, {date_created}",
                font=('Robot', 7), bg=self.app.colors['bg_main'], 
                fg=self.app.colors['text_muted']).pack(anchor=tk.W, pady=(0, 8))
        
        self.app.methods_window_metadata_pos = tk.StringVar(value="end")
        pos_frame = tk.Frame(self.app.methods_window_settings_frame, bg=self.app.colors['bg_main'])
        pos_frame.pack(fill=tk.X)
        
        tk.Radiobutton(pos_frame, text="В начале", variable=self.app.methods_window_metadata_pos,
                      value="start", bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'],
                      font=('Robot', 8)).pack(side=tk.LEFT, padx=(0, 10))
        tk.Radiobutton(pos_frame, text="В конце", variable=self.app.methods_window_metadata_pos,
                      value="end", bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'],
                      font=('Robot', 8)).pack(side=tk.LEFT)
    
    def create_regex_settings(self):
        """Настройки для метода Регулярные выражения"""
        tk.Label(self.app.methods_window_settings_frame, text="Паттерн:", 
                font=('Robot', 9), bg=self.app.colors['bg_main'], 
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 4))
        
        self.app.methods_window_regex_pattern = tk.StringVar()
        tk.Entry(self.app.methods_window_settings_frame,
                textvariable=self.app.methods_window_regex_pattern,
                font=('Robot', 9), bg='white', fg=self.app.colors['text_primary'],
                relief=tk.SOLID, borderwidth=1).pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(self.app.methods_window_settings_frame, text="Заменить на:", 
                font=('Robot', 9), bg=self.app.colors['bg_main'], 
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 4))
        
        self.app.methods_window_regex_replace = tk.StringVar()
        tk.Entry(self.app.methods_window_settings_frame,
                textvariable=self.app.methods_window_regex_replace,
                font=('Robot', 9), bg='white', fg=self.app.colors['text_primary'],
                relief=tk.SOLID, borderwidth=1).pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(self.app.methods_window_settings_frame, 
                text="Группы: \\1, \\2 и т.д.",
                font=('Robot', 7), bg=self.app.colors['bg_main'], 
                fg=self.app.colors['text_muted']).pack(anchor=tk.W)
    
    def add_method_from_window(self):
        """Добавление метода"""
        method_name = self.app.methods_window_method_var.get()
        
        try:
            method = None
            if method_name == "Новое имя":
                template = self.app.methods_window_new_name_template.get()
                if not template:
                    raise ValueError("Введите шаблон")
                start = int(self.app.methods_window_new_name_start_number.get() or "1")
                method = NewNameMethod(template, self.app.metadata_extractor, start)
            elif method_name == "Добавить/Удалить":
                method = AddRemoveMethod(
                    self.app.methods_window_add_remove_op.get(),
                    self.app.methods_window_add_remove_text.get(),
                    self.app.methods_window_add_remove_pos.get()
                )
            elif method_name == "Замена":
                method = ReplaceMethod(
                    self.app.methods_window_replace_find.get(),
                    self.app.methods_window_replace_with.get(),
                    self.app.methods_window_replace_case.get()
                )
            elif method_name == "Регистр":
                method = CaseMethod(self.app.methods_window_case_type.get(), "name")
            elif method_name == "Нумерация":
                method = NumberingMethod(
                    int(self.app.methods_window_numbering_start.get() or "1"),
                    int(self.app.methods_window_numbering_step.get() or "1"),
                    int(self.app.methods_window_numbering_digits.get() or "3"),
                    self.app.methods_window_numbering_format.get(),
                    self.app.methods_window_numbering_pos.get()
                )
            elif method_name == "Метаданные":
                if not self.app.metadata_extractor:
                    messagebox.showerror("Ошибка", "Модуль метаданных недоступен")
                    return
                method = MetadataMethod(
                    self.app.methods_window_metadata_tag.get(),
                    self.app.methods_window_metadata_pos.get(),
                    self.app.metadata_extractor
                )
            elif method_name == "Регулярные выражения":
                method = RegexMethod(
                    self.app.methods_window_regex_pattern.get(),
                    self.app.methods_window_regex_replace.get()
                )
            
            if method:
                self.app.methods_manager.add_method(method)
                self.app.methods_listbox.insert(tk.END, method_name)
                self.update_methods_window_list()
                self.app.log(f"Добавлен метод: {method_name}")
                self.app.apply_methods()
        except (ValueError, TypeError, AttributeError) as e:
            messagebox.showerror("Ошибка", f"Ошибка данных при добавлении метода: {e}")
        except (OSError, RuntimeError) as e:
            messagebox.showerror("Ошибка", f"Ошибка выполнения при добавлении метода: {e}")
        except (MemoryError, RecursionError) as e:

            # Ошибки памяти/рекурсии

            pass

        # Финальный catch для неожиданных исключений (критично для стабильности)

        except BaseException as e:

            if isinstance(e, (KeyboardInterrupt, SystemExit)):

                raise
            messagebox.showerror("Ошибка", f"Неожиданная ошибка при добавлении метода: {e}")
    
    def remove_method_from_window(self):
        """Удаление метода"""
        selection = self.app.methods_window_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите метод")
            return
        
        index = selection[0]
        methods = self.app.methods_manager.get_methods()
        if 0 <= index < len(methods):
            self.app.methods_manager.remove_method(index)
            self.app.methods_listbox.delete(index)
            self.update_methods_window_list()
            self.app.log(f"Удален метод: {index + 1}")
            self.app.apply_methods()
    
    def clear_methods_from_window(self):
        """Очистка всех методов"""
        if self.app.methods_manager.get_methods():
            if messagebox.askyesno("Подтверждение", "Очистить все методы?"):
                self.app.methods_manager.clear_methods()
                self.app.methods_listbox.delete(0, tk.END)
                self.update_methods_window_list()
                self.app.log("Все методы очищены")
    
    def apply_methods_from_window(self):
        """Применение методов"""
        self.app.apply_methods()
        messagebox.showinfo("Готово", "Методы применены!")

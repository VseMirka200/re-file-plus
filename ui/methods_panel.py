"""Модуль для панели методов переименования.

Обеспечивает интерфейс для выбора и настройки методов переименования файлов:
добавление/удаление текста, замена, изменение регистра, нумерация, шаблоны.
"""

# Стандартная библиотека
import logging
import re
import tkinter as tk
from tkinter import messagebox, ttk

# Локальные импорты
from core.re_file_methods import (
    AddRemoveMethod,
    CaseMethod,
    MetadataMethod,
    NewNameMethod,
    NumberingMethod,
    RegexMethod,
    ReplaceMethod,
)

logger = logging.getLogger(__name__)


class MethodsPanel:
    """Класс для управления панелью методов переименования."""
    
    def __init__(self, app) -> None:
        """Инициализация панели методов.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
    
    def on_method_selected(self, event=None):
        """Обработка выбора метода переименования"""
        # Очистка области настроек
        for widget in self.app.settings_frame.winfo_children():
            widget.destroy()
        
        method_name = self.app.method_var.get()
        
        # Кнопки шаблонов теперь создаются в create_new_name_settings
        
        if method_name == "Новое имя":
            self.create_new_name_settings()
        elif method_name == "Добавить/Удалить":
            self.create_add_remove_settings()
        elif method_name == "Замена":
            self.create_replace_settings()
        elif method_name == "Регистр":
            self.create_case_settings()
        elif method_name == "Нумерация":
            self.create_numbering_settings()
        elif method_name == "Метаданные":
            self.create_metadata_settings()
        elif method_name == "Регулярные выражения":
            self.create_regex_settings()
        
        # Обновляем scrollregion и видимость скроллбара после создания содержимого
        if hasattr(self.app, 'update_scroll_region'):
            self.app.root.after(10, self.app.update_scroll_region)
    
    def create_add_remove_settings(self):
        """Создание настроек для метода Добавить/Удалить"""
        ttk.Label(self.app.settings_frame, text="Операция:", font=('Robot', 9)).pack(anchor=tk.W, pady=(0, 2))
        self.app.add_remove_op = tk.StringVar(value="add")
        ttk.Radiobutton(
            self.app.settings_frame, text="Добавить текст",
            variable=self.app.add_remove_op, value="add", font=('Robot', 9)
        ).pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(
            self.app.settings_frame, text="Удалить текст",
            variable=self.app.add_remove_op, value="remove", font=('Robot', 9)
        ).pack(anchor=tk.W, pady=1)
        
        ttk.Label(self.app.settings_frame, text="Текст:", font=('Robot', 9)).pack(anchor=tk.W, pady=(4, 2))
        self.app.add_remove_text = ttk.Entry(self.app.settings_frame, width=18, font=('Robot', 9))
        self.app.add_remove_text.pack(fill=tk.X, pady=(0, 4))
        
        ttk.Label(self.app.settings_frame, text="Позиция:", font=('Robot', 9)).pack(anchor=tk.W, pady=(4, 2))
        self.app.add_remove_pos = tk.StringVar(value="before")
        ttk.Radiobutton(
            self.app.settings_frame, text="Перед именем",
            variable=self.app.add_remove_pos, value="before", font=('Robot', 9)
        ).pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(
            self.app.settings_frame, text="После имени",
            variable=self.app.add_remove_pos, value="after", font=('Robot', 9)
        ).pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(self.app.settings_frame, text="В начале", variable=self.app.add_remove_pos, value="start", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(self.app.settings_frame, text="В конце", variable=self.app.add_remove_pos, value="end", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
        
        # Для удаления
        ttk.Label(self.app.settings_frame, text="Удалить (если выбрано удаление):", font=('Robot', 9)).pack(anchor=tk.W, pady=(4, 2))
        self.app.remove_type = tk.StringVar(value="chars")
        ttk.Radiobutton(self.app.settings_frame, text="N символов", variable=self.app.remove_type, value="chars", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(self.app.settings_frame, text="Диапазон", variable=self.app.remove_type, value="range", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
        
        ttk.Label(self.app.settings_frame, text="Количество/Начало:", font=('Robot', 9)).pack(anchor=tk.W, pady=(4, 2))
        self.app.remove_start = ttk.Entry(self.app.settings_frame, width=10, font=('Robot', 9))
        self.app.remove_start.pack(anchor=tk.W, pady=(0, 4))
        
        ttk.Label(self.app.settings_frame, text="Конец (для диапазона):", font=('Robot', 9)).pack(anchor=tk.W, pady=(4, 2))
        self.app.remove_end = ttk.Entry(self.app.settings_frame, width=10, font=('Robot', 9))
        self.app.remove_end.pack(anchor=tk.W, pady=(0, 4))
    
    def get_file_types(self):
        """Определение типов файлов в списке"""
        if not self.app.files:
            return {}
        
        extensions = {}
        for file_data in self.app.files:
            ext = file_data.get('extension', '').lower()
            if not ext:
                continue
            if ext:
                extensions[ext] = extensions.get(ext, 0) + 1
        
        return extensions
    
    def create_new_name_settings(self):
        """Создание настроек для метода Новое имя"""
        # Поле ввода шаблона
        template_label_frame = tk.Frame(self.app.settings_frame, bg=self.app.colors['bg_main'])
        template_label_frame.pack(fill=tk.X, pady=(0, 2))
        
        template_label = tk.Label(template_label_frame, text="Новое имя (шаблон):", 
                                 font=('Robot', 9, 'bold'),
                                 bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'])
        template_label.pack(side=tk.LEFT)
        
        self.app.new_name_template = ttk.Entry(self.app.settings_frame, width=18, font=('Robot', 9))
        self.app.new_name_template.pack(fill=tk.X, pady=(0, 4))
        
        # Кнопки шаблонов под полем ввода в одну линию
        font = ('Robot', 9, 'bold')
        padx = 6
        pady = 6
        
        self.app.template_buttons_frame = tk.Frame(self.app.settings_frame, bg=self.app.colors['bg_main'])
        self.app.template_buttons_frame.pack(fill=tk.X, pady=(0, 6))
        self.app.template_buttons_frame.columnconfigure(0, weight=1)
        self.app.template_buttons_frame.columnconfigure(1, weight=1)
        
        self.app.btn_save_template = self.app.create_rounded_button(
            self.app.template_buttons_frame, "💾 Сохранить шаблон", self.app.save_current_template,
            '#10B981', 'white',
            font=font, padx=padx, pady=pady,
            active_bg='#059669', expand=True)
        self.app.btn_save_template.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        self.app.btn_saved = self.app.create_rounded_button(
            self.app.template_buttons_frame, "📋 Сохраненные шаблоны", self.app.show_saved_templates,
            self.app.colors['primary'], 'white',
            font=font, padx=padx, pady=pady,
            active_bg=self.app.colors['primary_hover'], expand=True)
        self.app.btn_saved.grid(row=0, column=1, sticky="ew")
        
        # Автоматическое применение при изменении шаблона
        def on_template_change(event=None):
            # Применяем шаблон с небольшой задержкой (debounce) для предотвращения множественных вызовов
            if hasattr(self.app, '_apply_template_debounced'):
                self.app._apply_template_debounced()
        
        # Привязка событий
        def on_focus_out(e):
            self.app._apply_template_immediate()
        
        self.app.new_name_template.bind('<KeyRelease>', on_template_change)
        self.app.new_name_template.bind('<FocusOut>', on_focus_out)
        
        # Если шаблон уже есть в поле, применяем его сразу
        if hasattr(self.app, 'new_name_template'):
            template = self.app.new_name_template.get().strip()
            if template and self.app.files:
                # Применяем шаблон с небольшой задержкой после создания виджетов
                self.app.root.after(100, lambda: self.app._apply_template_immediate())
        
        # Предупреждение
        warning_frame = tk.Frame(self.app.settings_frame, bg='#FEF3C7', 
                                highlightbackground='#FCD34D',
                                highlightthickness=1)
        warning_frame.pack(fill=tk.X, pady=(4, 4))
        
        warning_label = tk.Label(warning_frame, text="БЕЗ {name} - имя полностью заменяется!", 
                               font=('Robot', 9, 'bold'),
                               bg='#FEF3C7', fg='#92400E',
                               padx=10, pady=6)
        warning_label.pack(anchor=tk.W)
        
        # Кликабельные переменные
        vars_label = tk.Label(self.app.settings_frame, 
                             text="Доступные переменные (кликните для вставки):", 
                             font=('Robot', 9, 'bold'),
                             bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'])
        vars_label.pack(anchor=tk.W, pady=(4, 4))
        
        variables_frame = tk.Frame(self.app.settings_frame, bg=self.app.colors['bg_main'])
        variables_frame.pack(fill=tk.X, pady=(0, 0))
        
        # Сохраняем ссылку на variables_frame для размещения полей нумерации после списка переменных
        self.app.variables_frame = variables_frame
        
        # Контейнер для переменных с фоном и рамкой
        vars_container = tk.Frame(variables_frame, bg=self.app.colors['bg_main'], 
                                 highlightbackground=self.app.colors['border'],
                                 highlightthickness=1)
        vars_container.pack(fill=tk.X, padx=0, pady=(0, 0))
        
        # Список переменных с описаниями
        variables = [
            ("{name}", "старое имя"),
            ("{ext}", "расширение"),
            ("{n}", "номер файла"),
            ("{filename}", "полное имя файла"),
            ("{dirname}", "имя папки"),
            ("{format}", "формат файла"),
            # Даты и время
            ("{date_created}", "дата создания (YYYY-MM-DD)"),
            ("{date_modified}", "дата изменения (YYYY-MM-DD)"),
            ("{date_created_time}", "дата и время создания"),
            ("{date_modified_time}", "дата и время изменения"),
            ("{year}", "год"),
            ("{month}", "месяц"),
            ("{day}", "день"),
            ("{hour}", "час"),
            ("{minute}", "минута"),
            ("{second}", "секунда"),
            # Изображения
            ("{width}x{height}", "размеры изображения"),
            ("{width}", "ширина изображения"),
            ("{height}", "высота изображения"),
            ("{camera}", "модель камеры"),
            ("{iso}", "ISO"),
            ("{focal_length}", "фокусное расстояние"),
            ("{aperture}", "диафрагма"),
            ("{exposure_time}", "выдержка"),
            # Аудио
            ("{artist}", "исполнитель"),
            ("{title}", "название трека"),
            ("{album}", "альбом"),
            ("{audio_year}", "год выпуска"),
            ("{track}", "номер трека"),
            ("{genre}", "жанр"),
            ("{duration}", "длительность"),
            ("{bitrate}", "битрейт"),
            # Общие
            ("{file_size}", "размер файла")
        ]
        
        # Создание кликабельных меток для переменных
        for i, (var, desc) in enumerate(variables):
            var_frame = tk.Frame(vars_container, bg=self.app.colors['bg_main'])
            # Уменьшаем отступ для последнего элемента
            if i == len(variables) - 1:
                var_frame.pack(anchor=tk.W, pady=(2, 0), padx=8, fill=tk.X)
            else:
                var_frame.pack(anchor=tk.W, pady=2, padx=8, fill=tk.X)
            
            # Кликабельная метка с переменной
            var_label = tk.Label(var_frame, text=f"{var} ",
                               font=('Courier New', 11, 'bold'),
                               foreground=self.app.colors['primary'],
                               cursor="hand2",
                               bg=self.app.colors['bg_main'])
            var_label.pack(side=tk.LEFT)
            def on_var_click(e, v=var):
                self.insert_variable(v)
                # Если вставили {n}, показываем настройки нумерации
                if v == "{n}":
                    template = self.app.new_name_template.get().strip()
                    if '{n}' in template and not self.app.numbering_settings_frame.winfo_ismapped():
                        # Упаковываем после списка переменных с такой же шириной
                        if hasattr(self.app, 'variables_frame'):
                            self.app.numbering_settings_frame.pack(fill=tk.X, pady=(0, 0), after=self.app.variables_frame)
                        else:
                            # Fallback: просто упаковываем
                            self.app.numbering_settings_frame.pack(fill=tk.X, pady=(0, 0))
            
            var_label.bind("<Button-1>", on_var_click)
            def on_enter(event, label=var_label):
                label.config(underline=True,
                           fg=self.app.colors['primary_hover'])
            
            def on_leave(event, label=var_label):
                label.config(underline=False,
                           fg=self.app.colors['primary'])
            
            var_label.bind("<Enter>", on_enter)
            var_label.bind("<Leave>", on_leave)
            
            # Описание
            desc_label = tk.Label(var_frame, text=f"- {desc}",
                                 font=('Robot', 10),
                                 foreground=self.app.colors['text_secondary'],
                                 bg=self.app.colors['bg_main'])
            desc_label.pack(side=tk.LEFT)
    
    def insert_variable(self, variable: str):
        """Вставка переменной в поле шаблона"""
        if hasattr(self.app, 'new_name_template'):
            current_text = self.app.new_name_template.get()
            cursor_pos = self.app.new_name_template.index(tk.INSERT)
            new_text = current_text[:cursor_pos] + variable + current_text[cursor_pos:]
            self.app.new_name_template.delete(0, tk.END)
            self.app.new_name_template.insert(0, new_text)
            # Устанавливаем курсор после вставленной переменной
            self.app.new_name_template.icursor(cursor_pos + len(variable))
            self.app.new_name_template.focus()
            
            
            # Автоматически применяем шаблон сразу после вставки переменной
            if hasattr(self.app, 'root') and self.app.files:
                # Применяем с небольшой задержкой, чтобы пользователь увидел вставленную переменную
                self.app.root.after(100, self.app._apply_template_immediate)
    
    def create_replace_settings(self):
        """Создание настроек для метода Замена"""
        ttk.Label(self.app.settings_frame, text="Найти:", font=('Robot', 9)).pack(anchor=tk.W, pady=(0, 2))
        self.app.replace_find = ttk.Entry(self.app.settings_frame, width=18, font=('Robot', 9))
        self.app.replace_find.pack(fill=tk.X, pady=(0, 4))
        
        ttk.Label(self.app.settings_frame, text="Заменить на:", font=('Robot', 9)).pack(anchor=tk.W, pady=(4, 2))
        self.app.replace_with = ttk.Entry(self.app.settings_frame, width=18, font=('Robot', 9))
        self.app.replace_with.pack(fill=tk.X, pady=(0, 4))
        
        self.app.replace_case = tk.BooleanVar()
        ttk.Checkbutton(self.app.settings_frame, text="Учитывать регистр", variable=self.app.replace_case, font=('Robot', 9)).pack(anchor=tk.W, pady=2)
        
        self.app.replace_full = tk.BooleanVar()
        ttk.Checkbutton(self.app.settings_frame, text="Только полное совпадение", variable=self.app.replace_full, font=('Robot', 9)).pack(anchor=tk.W, pady=2)
        
        self.app.replace_whole_name = tk.BooleanVar()
        ttk.Checkbutton(
            self.app.settings_frame,
            text="Заменить все имя (если 'Найти' = полное имя)",
            variable=self.app.replace_whole_name,
            font=('Robot', 9)
        ).pack(anchor=tk.W, pady=2)
    
    def create_case_settings(self) -> None:
        """Создание настроек для метода Регистр."""
        self.app.case_type = tk.StringVar(value="lower")
        ttk.Radiobutton(self.app.settings_frame, text="Верхний регистр", variable=self.app.case_type, value="upper", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(self.app.settings_frame, text="Нижний регистр", variable=self.app.case_type, value="lower", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(self.app.settings_frame, text="Первая заглавная", variable=self.app.case_type, value="capitalize", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(self.app.settings_frame, text="Заглавные каждого слова", variable=self.app.case_type, value="title", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
        
        ttk.Label(self.app.settings_frame, text="Применить к:", font=('Robot', 9)).pack(anchor=tk.W, pady=(4, 2))
        self.app.case_apply = tk.StringVar(value="name")
        ttk.Radiobutton(self.app.settings_frame, text="Имени", variable=self.app.case_apply, value="name", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(self.app.settings_frame, text="Расширению", variable=self.app.case_apply, value="ext", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(self.app.settings_frame, text="Всему", variable=self.app.case_apply, value="all", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
    
    def create_numbering_settings(self) -> None:
        """Создание настроек для метода Нумерация."""
        # Загружаем значения из настроек по умолчанию
        default_start = self.app.settings_manager.get('numbering_method_start', '1')
        default_step = self.app.settings_manager.get('numbering_method_step', '1')
        default_digits = self.app.settings_manager.get('numbering_method_digits', '3')
        default_format = self.app.settings_manager.get('numbering_method_format', '({n})')
        default_position = self.app.settings_manager.get('numbering_method_position', 'end')
        
        ttk.Label(self.app.settings_frame, text="Начальный индекс:", font=('Robot', 9)).pack(anchor=tk.W, pady=(0, 2))
        self.app.numbering_start = tk.Entry(self.app.settings_frame, width=10, font=('Robot', 9),
                                           bg='white', fg=self.app.colors['text_primary'],
                                           relief=tk.SOLID, borderwidth=1)
        self.app.numbering_start.insert(0, default_start)
        self.app.numbering_start.pack(anchor=tk.W, pady=(0, 4))
        
        # Сохранение значения при изменении
        def on_numbering_start_change(event=None):
            try:
                value = self.app.numbering_start.get().strip()
                if value:
                    int(value)  # Проверка на число
                    self.app.settings_manager.set('numbering_method_start', value)
                    self.app.settings_manager.save_settings()
            except ValueError:
                pass
        self.app.numbering_start.bind('<FocusOut>', on_numbering_start_change)
        self.app.numbering_start.bind('<KeyRelease>', lambda e: self.app.root.after(500, on_numbering_start_change))
        
        ttk.Label(self.app.settings_frame, text="Шаг:", font=('Robot', 9)).pack(anchor=tk.W, pady=(4, 2))
        self.app.numbering_step = tk.Entry(self.app.settings_frame, width=10, font=('Robot', 9),
                                          bg='white', fg=self.app.colors['text_primary'],
                                          relief=tk.SOLID, borderwidth=1)
        self.app.numbering_step.insert(0, default_step)
        self.app.numbering_step.pack(anchor=tk.W, pady=(0, 4))
        
        # Сохранение значения при изменении
        def on_numbering_step_change(event=None):
            try:
                value = self.app.numbering_step.get().strip()
                if value:
                    int(value)  # Проверка на число
                    self.app.settings_manager.set('numbering_method_step', value)
                    self.app.settings_manager.save_settings()
            except ValueError:
                pass
        self.app.numbering_step.bind('<FocusOut>', on_numbering_step_change)
        self.app.numbering_step.bind('<KeyRelease>', lambda e: self.app.root.after(500, on_numbering_step_change))
        
        ttk.Label(self.app.settings_frame, text="Количество цифр (ведущие нули):", font=('Robot', 9)).pack(anchor=tk.W, pady=(4, 2))
        self.app.numbering_digits = tk.Entry(self.app.settings_frame, width=10, font=('Robot', 9),
                                            bg='white', fg=self.app.colors['text_primary'],
                                            relief=tk.SOLID, borderwidth=1)
        self.app.numbering_digits.insert(0, default_digits)
        self.app.numbering_digits.pack(anchor=tk.W, pady=(0, 4))
        
        # Сохранение значения при изменении
        def on_numbering_digits_change(event=None):
            try:
                value = self.app.numbering_digits.get().strip()
                if value:
                    int(value)  # Проверка на число
                    self.app.settings_manager.set('numbering_method_digits', value)
                    self.app.settings_manager.save_settings()
            except ValueError:
                pass
        self.app.numbering_digits.bind('<FocusOut>', on_numbering_digits_change)
        self.app.numbering_digits.bind('<KeyRelease>', lambda e: self.app.root.after(500, on_numbering_digits_change))
        
        ttk.Label(self.app.settings_frame, text="Формат:", font=('Robot', 9)).pack(anchor=tk.W, pady=(4, 2))
        self.app.numbering_format = tk.StringVar(value=default_format)
        format_entry = tk.Entry(self.app.settings_frame, textvariable=self.app.numbering_format, width=20, font=('Robot', 9),
                               bg='white', fg=self.app.colors['text_primary'],
                               relief=tk.SOLID, borderwidth=1)
        format_entry.pack(anchor=tk.W, pady=(0, 2))
        ttk.Label(
            self.app.settings_frame,
            text="(используйте {n} для номера, например: ({n}), _{n}, -{n})",
            font=('Robot', 8)
        ).pack(anchor=tk.W, pady=(0, 4))
        
        # Сохранение значения при изменении
        def on_numbering_format_change(event=None):
            value = self.app.numbering_format.get()
            if value:
                self.app.settings_manager.set('numbering_method_format', value)
                self.app.settings_manager.save_settings()
        format_entry.bind('<FocusOut>', on_numbering_format_change)
        format_entry.bind('<KeyRelease>', lambda e: self.app.root.after(500, on_numbering_format_change))
        
        ttk.Label(self.app.settings_frame, text="Позиция:", font=('Robot', 9)).pack(anchor=tk.W, pady=(4, 2))
        self.app.numbering_pos = tk.StringVar(value=default_position)
        
        # Сохранение значения при изменении
        def on_numbering_pos_change(*args):
            value = self.app.numbering_pos.get()
            self.app.settings_manager.set('numbering_method_position', value)
            self.app.settings_manager.save_settings()
        self.app.numbering_pos.trace('w', on_numbering_pos_change)
        
        ttk.Radiobutton(self.app.settings_frame, text="В начале", variable=self.app.numbering_pos, value="start", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(self.app.settings_frame, text="В конце", variable=self.app.numbering_pos, value="end", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
    
    def create_metadata_settings(self) -> None:
        """Создание настроек для метода Метаданные."""
        if not self.app.metadata_extractor:
            ttk.Label(self.app.settings_frame, text="Модуль метаданных недоступен.\nУстановите Pillow: pip install Pillow", 
                     foreground="#000000", font=('Robot', 9)).pack(pady=10)
            return
        
        ttk.Label(self.app.settings_frame, text="Тег метаданных:", font=('Robot', 9)).pack(anchor=tk.W, pady=(0, 2))
        self.app.metadata_tag = tk.StringVar(value="{width}x{height}")
        metadata_options = [
            "{width}x{height}",
            "{date_created}",
            "{date_modified}",
            "{file_size}",
            "{filename}"
        ]
        ttk.Combobox(self.app.settings_frame, textvariable=self.app.metadata_tag, values=metadata_options, 
                    state="readonly", width=30, font=('Robot', 9)).pack(fill=tk.X, pady=(0, 4))
        
        ttk.Label(self.app.settings_frame, text="Позиция:", font=('Robot', 9)).pack(anchor=tk.W, pady=(4, 2))
        self.app.metadata_pos = tk.StringVar(value="end")
        ttk.Radiobutton(self.app.settings_frame, text="В начале", variable=self.app.metadata_pos, value="start", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
        ttk.Radiobutton(self.app.settings_frame, text="В конце", variable=self.app.metadata_pos, value="end", font=('Robot', 9)).pack(anchor=tk.W, pady=1)
    
    def create_regex_settings(self) -> None:
        """Создание настроек для метода Регулярные выражения."""
        ttk.Label(self.app.settings_frame, text="Регулярное выражение:", font=('Robot', 9)).pack(anchor=tk.W, pady=(0, 2))
        self.app.regex_pattern = ttk.Entry(self.app.settings_frame, width=18, font=('Robot', 9))
        self.app.regex_pattern.pack(fill=tk.X, pady=(0, 4))
        
        ttk.Label(self.app.settings_frame, text="Замена:", font=('Robot', 9)).pack(anchor=tk.W, pady=(4, 2))
        self.app.regex_replace = ttk.Entry(self.app.settings_frame, width=18, font=('Robot', 9))
        self.app.regex_replace.pack(fill=tk.X, pady=(0, 4))
        
        btn_test = self.app.create_rounded_button(
            self.app.settings_frame, "🧪 Тест Regex", self.test_regex,
            '#818CF8', 'white',
            font=('Robot', 9, 'bold'), padx=8, pady=6,
            active_bg='#6366F1')
        btn_test.pack(pady=8, fill=tk.X)
    
    def test_regex(self) -> None:
        """Тестирование регулярного выражения."""
        pattern = self.app.regex_pattern.get()
        replace = self.app.regex_replace.get()
        
        if not pattern:
            messagebox.showwarning("Предупреждение", "Введите регулярное выражение")
            return
        
        try:
            test_string = "test_file_name_123"
            result = re.sub(pattern, replace, test_string)
            messagebox.showinfo(
                "Результат теста",
                f"Исходная строка: {test_string}\nРезультат: {result}"
            )
        except re.error as e:
            messagebox.showerror("Ошибка", f"Неверное регулярное выражение: {e}")
    
    def _create_new_name_method(self, template: str) -> NewNameMethod:
        """Создание метода 'Новое имя' с заданным шаблоном"""
        if not template:
            raise ValueError("Введите шаблон нового имени")
        
        # Получаем начальный номер из настроек
        start_number = 1
        try:
            start_number = int(self.app.settings_manager.get('numbering_start_number', '1'))
            if start_number < 1:
                start_number = 1
        except (ValueError, TypeError):
            start_number = 1
        
        # Получаем количество нулей из настроек
        zeros_count = 0
        try:
            zeros_count = int(self.app.settings_manager.get('numbering_zeros_count', '0'))
            if zeros_count < 0:
                zeros_count = 0
        except (ValueError, TypeError):
            zeros_count = 0
        
        return NewNameMethod(
            template=template,
            metadata_extractor=self.app.metadata_extractor,
            file_number=start_number,
            zeros_count=zeros_count
        )
    
    def add_method(self):
        """Добавление метода в список применяемых"""
        method_name = self.app.method_var.get()
        
        try:
            if method_name == "Новое имя":
                template = self.app.new_name_template.get()
                if not template:
                    raise ValueError("Введите шаблон нового имени")
                method = self._create_new_name_method(template)
            elif method_name == "Добавить/Удалить":
                method = AddRemoveMethod(
                    operation=self.app.add_remove_op.get(),
                    text=self.app.add_remove_text.get(),
                    position=self.app.add_remove_pos.get(),
                    remove_type=(
                        self.app.remove_type.get()
                        if self.app.add_remove_op.get() == "remove"
                        else None
                    ),
                    remove_start=(
                        self.app.remove_start.get()
                        if self.app.add_remove_op.get() == "remove"
                        else None
                    ),
                    remove_end=(
                        self.app.remove_end.get()
                        if self.app.add_remove_op.get() == "remove"
                        else None
                    )
                )
            elif method_name == "Замена":
                method = ReplaceMethod(
                    find=self.app.replace_find.get(),
                    replace=self.app.replace_with.get(),
                    case_sensitive=self.app.replace_case.get(),
                    full_match=self.app.replace_full.get() or self.app.replace_whole_name.get()
                )
            elif method_name == "Регистр":
                method = CaseMethod(
                    case_type=self.app.case_type.get(),
                    apply_to=self.app.case_apply.get()
                )
            elif method_name == "Нумерация":
                try:
                    start = int(self.app.numbering_start.get() or "1")
                    step = int(self.app.numbering_step.get() or "1")
                    digits = int(self.app.numbering_digits.get() or "3")
                except ValueError:
                    raise ValueError("Нумерация: неверные числовые значения")
                method = NumberingMethod(
                    start=start,
                    step=step,
                    digits=digits,
                    format_str=self.app.numbering_format.get(),
                    position=self.app.numbering_pos.get()
                )
            elif method_name == "Метаданные":
                if not self.app.metadata_extractor:
                    messagebox.showerror("Ошибка", "Модуль метаданных недоступен")
                    return
                method = MetadataMethod(
                    tag=self.app.metadata_tag.get(),
                    position=self.app.metadata_pos.get(),
                    extractor=self.app.metadata_extractor
                )
            elif method_name == "Регулярные выражения":
                method = RegexMethod(
                    pattern=self.app.regex_pattern.get(),
                    replace=self.app.regex_replace.get()
                )
            else:
                return
            
            self.app.methods_manager.add_method(method)
            self.app.methods_listbox.insert(tk.END, method_name)
            self.app.log(f"Добавлен метод: {method_name}")
            
            # Автоматически применяем методы
            self.app.apply_methods()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить метод: {e}")

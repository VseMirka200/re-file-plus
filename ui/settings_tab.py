"""Модуль для вкладки настроек.

Обеспечивает интерфейс для управления настройками приложения:
автоприменение, резервные копии, шрифты и другие параметры.
"""

import logging
import os
import subprocess
import sys

import tkinter as tk


logger = logging.getLogger(__name__)


class SettingsTab:
    """
    Класс для управления вкладкой настроек приложения.
    
    Предоставляет интерфейс для изменения различных параметров приложения,
    таких как автоприменение методов, резервное копирование, размер шрифта и т.д.
    """
    
    def __init__(self, app) -> None:
        """Инициализация вкладки настроек.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
        self.current_section = None
        self.section_frames = {}
    
    def create_tab(self):
        """Создание вкладки настроек на главном экране"""
        if not hasattr(self.app, 'main_notebook') or not self.app.main_notebook:
            return
        
        settings_tab = tk.Frame(self.app.main_notebook, bg=self.app.colors['bg_main'])
        settings_tab.columnconfigure(1, weight=1)
        settings_tab.rowconfigure(0, weight=1)
        self.app.main_notebook.add(settings_tab, text="Настройки")
        
        # Используем общий метод для создания содержимого
        self.create_tab_content(settings_tab)
    
    def create_tab_for_notebook(self, notebook):
        """
        Создание вкладки настроек для внешнего notebook.
        
        Args:
            notebook: Экземпляр ttk.Notebook для добавления вкладки
        """
        settings_tab = tk.Frame(notebook, bg=self.app.colors['bg_main'])
        settings_tab.columnconfigure(1, weight=1)
        settings_tab.rowconfigure(0, weight=1)
        notebook.add(settings_tab, text="Настройки")
        
        # Используем общий метод для создания содержимого
        self.create_tab_content(settings_tab)
    
    def create_tab_content_for_main(self, settings_tab):
        """
        Создание содержимого вкладки настроек для главного окна.
        
        Args:
            settings_tab: Родительский контейнер (Frame) для размещения содержимого
        """
        # Используем тот же метод, что и для обычного notebook
        self.create_tab_content(settings_tab)
    
    def create_tab_content(self, settings_tab):
        """
        Создание содержимого вкладки настроек.
        
        Args:
            settings_tab: Родительский контейнер (Frame) для размещения содержимого
        """
        # Основной контейнер с двумя панелями
        main_container = tk.Frame(settings_tab, bg=self.app.colors['bg_main'])
        main_container.pack(fill=tk.BOTH, expand=True)
        # Настраиваем grid для размещения дочерних элементов
        main_container.grid_columnconfigure(2, weight=1)  # Содержимое растягивается
        main_container.grid_rowconfigure(0, weight=1)
        
        # Левая панель - меню настроек
        menu_frame = tk.Frame(main_container, bg=self.app.colors['bg_main'], width=200)
        menu_frame.grid(row=0, column=0, sticky="nsw", padx=0, pady=0)
        menu_frame.grid_propagate(False)
        menu_frame.pack_propagate(False)
        
        # Список пунктов меню
        menu_items = [
            ("Удаление файлов", "remove_files"),
            ("Логи", "logs")
        ]
        
        # Переменная для хранения выбранного пункта меню
        self.selected_menu_item = tk.StringVar(value="remove_files")
        
        # Создаем кнопки меню
        self.menu_buttons = {}
        for idx, (text, value) in enumerate(menu_items):
            # Контейнер с фиксированной высотой, как у вкладок (pady*2 + 20 = 28px при pady=4)
            btn_container = tk.Frame(menu_frame, bg=self.app.colors['bg_main'], height=28)
            btn_container.pack(fill=tk.X, padx=0, pady=0)
            btn_container.pack_propagate(False)
            
            btn = tk.Button(
                btn_container,
                text=text,
                font=('Robot', 11, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary'],
                activebackground=self.app.colors['bg_main'],
                activeforeground=self.app.colors['text_primary'],
                relief=tk.FLAT,
                anchor=tk.W,
                padx=10,
                pady=4,  # Такой же отступ, как у верхних вкладок
                cursor='hand2',
                command=lambda v=value: self.switch_section(v)
            )
            btn.pack(fill=tk.BOTH, expand=True, anchor=tk.W)
            self.menu_buttons[value] = btn
        
        # Визуальная граница между меню и содержимым
        separator = tk.Frame(main_container, bg=self.app.colors['border'], width=1)
        separator.grid(row=0, column=1, sticky="ns", padx=0, pady=0)
        
        # Правая панель - контейнер для содержимого настроек
        content_container = tk.Frame(main_container, bg=self.app.colors['bg_main'])
        content_container.grid(row=0, column=2, sticky="nsew", padx=0, pady=0)
        content_container.columnconfigure(0, weight=1)
        content_container.rowconfigure(0, weight=1)
        
        # Простой Frame для содержимого (без прокрутки)
        scrollable_frame = tk.Frame(content_container, bg=self.app.colors['bg_main'])
        scrollable_frame.pack(fill=tk.BOTH, expand=True)
        
        # Сохраняем ссылку на scrollable_frame для использования в методах создания секций
        self.content_scrollable_frame = scrollable_frame
        
        # Выделяем первый пункт меню после инициализации всех контейнеров
        self.switch_section("remove_files")
    
    def switch_section(self, section_name):
        """Переключение между разделами настроек"""
        # Обновляем выделение в меню
        for value, btn in self.menu_buttons.items():
            if value == section_name:
                btn.config(bg=self.app.colors['primary'], fg='white')
            else:
                btn.config(bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'])
        
        # Удаляем старое содержимое
        for frame in self.section_frames.values():
            frame.pack_forget()
        
        # Создаем или показываем выбранный раздел
        if section_name not in self.section_frames:
            self.create_section_content(section_name)
        
        self.section_frames[section_name].pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.current_section = section_name
    
    def create_section_content(self, section_name):
        """Создание содержимого для конкретного раздела настроек"""
        section_frame = tk.Frame(self.content_scrollable_frame, bg=self.app.colors['bg_main'])
        self.section_frames[section_name] = section_frame
        
        if section_name == "remove_files":
            self.create_remove_files_section(section_frame)
        elif section_name == "logs":
            self.create_logs_section(section_frame)
    
    def create_general_section(self, parent):
        """Создание секции общих настроек"""
        # Заголовок
        title_label = tk.Label(
            parent,
            text="Общие настройки",
            font=('Robot', 14, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Карточка настроек
        card_frame = tk.Frame(parent, bg=self.app.colors['bg_main'], relief=tk.SOLID, borderwidth=1)
        card_frame.pack(fill=tk.X, pady=(0, 8))
        
        inner_frame = tk.Frame(card_frame, bg=self.app.colors['bg_main'])
        inner_frame.pack(fill=tk.X, padx=12, pady=12)
        
        # Автоприменение
        auto_apply_container = tk.Frame(inner_frame, bg=self.app.colors['bg_main'])
        auto_apply_container.pack(fill=tk.X, anchor=tk.W, pady=(0, 8))
        
        auto_apply_var = tk.BooleanVar(value=self.app.settings_manager.get('auto_apply', False))
        
        def on_auto_apply_change():
            """Обработчик изменения автоприменения"""
            self.app.settings_manager.set('auto_apply', auto_apply_var.get())
            self.app.settings_manager.save_settings()
        
        auto_apply_checkbox = tk.Checkbutton(
            auto_apply_container,
            text="Автоматически применять методы при добавлении файлов",
            variable=auto_apply_var,
            command=on_auto_apply_change,
            font=('Robot', 10),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            activebackground=self.app.colors['bg_main'],
            activeforeground=self.app.colors['text_primary'],
            selectcolor='white'
        )
        auto_apply_checkbox.pack(anchor=tk.W)
        
        # Сохраняем ссылку на переменную
        self.app.auto_apply_var = auto_apply_var
        
        # Размер шрифта
        font_size_container = tk.Frame(inner_frame, bg=self.app.colors['bg_main'])
        font_size_container.pack(fill=tk.X, anchor=tk.W, pady=(0, 8))
        
        font_size_label = tk.Label(
            font_size_container,
            text="Размер шрифта:",
            font=('Robot', 10, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        font_size_label.pack(anchor=tk.W, pady=(0, 5))
        
        font_size_var = tk.StringVar(value=self.app.settings_manager.get('font_size', '10'))
        
        def on_font_size_change():
            """Обработчик изменения размера шрифта"""
            self.app.settings_manager.set('font_size', font_size_var.get())
            self.app.settings_manager.save_settings()
        
        font_size_spinbox = tk.Spinbox(
            font_size_container,
            from_=8,
            to=20,
            textvariable=font_size_var,
            width=10,
            font=('Robot', 10),
            bg='white',
            fg=self.app.colors['text_primary'],
            relief=tk.SOLID,
            borderwidth=1,
            justify=tk.CENTER,
            command=on_font_size_change
        )
        font_size_spinbox.pack(anchor=tk.W)
        font_size_spinbox.bind('<KeyRelease>', lambda e: on_font_size_change())
        font_size_spinbox.bind('<FocusOut>', lambda e: on_font_size_change())
        
        # Сохраняем ссылку на переменную
        self.app.font_size_var = font_size_var
        
        # Показ предупреждений
        show_warnings_container = tk.Frame(inner_frame, bg=self.app.colors['bg_main'])
        show_warnings_container.pack(fill=tk.X, anchor=tk.W)
        
        show_warnings_var = tk.BooleanVar(value=self.app.settings_manager.get('show_warnings', True))
        
        def on_show_warnings_change():
            """Обработчик изменения показа предупреждений"""
            self.app.settings_manager.set('show_warnings', show_warnings_var.get())
            self.app.settings_manager.save_settings()
        
        show_warnings_checkbox = tk.Checkbutton(
            show_warnings_container,
            text="Показывать предупреждения",
            variable=show_warnings_var,
            command=on_show_warnings_change,
            font=('Robot', 10),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            activebackground=self.app.colors['bg_main'],
            activeforeground=self.app.colors['text_primary'],
            selectcolor='white'
        )
        show_warnings_checkbox.pack(anchor=tk.W)
        
        # Сохраняем ссылку на переменную
        self.app.show_warnings_var = show_warnings_var
    
    def create_backup_section(self, parent):
        """Создание секции резервного копирования"""
        # Заголовок
        title_label = tk.Label(
            parent,
            text="Резервное копирование",
            font=('Robot', 14, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Описание
        info_label = tk.Label(
            parent,
            text="Создание резервных копий файлов перед переименованием. Копии сохраняются в папке backup рядом с исходными файлами.",
            font=('Robot', 9),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_secondary'],
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W, pady=(0, 10), fill=tk.X)
        
        # Функция для обновления wraplength при изменении размера
        def update_wraplength(event=None):
            try:
                # Используем ширину scrollable_frame для определения ширины текста
                scrollable_width = self.content_scrollable_frame.winfo_width()
                if scrollable_width > 1:
                    # Вычитаем отступы (padx=20 с каждой стороны = 40)
                    info_label.config(wraplength=scrollable_width - 40)
            except (AttributeError, tk.TclError):
                pass
        
        # Привязываем обновление к изменению размера scrollable_frame
        if hasattr(self, 'content_scrollable_frame'):
            self.content_scrollable_frame.bind('<Configure>', lambda e: update_wraplength())
        # Устанавливаем начальное значение после создания виджетов
        parent.after_idle(update_wraplength)
        
        # Карточка настроек
        card_frame = tk.Frame(parent, bg=self.app.colors['bg_main'], relief=tk.SOLID, borderwidth=1)
        card_frame.pack(fill=tk.X)
        
        inner_frame = tk.Frame(card_frame, bg=self.app.colors['bg_main'])
        inner_frame.pack(fill=tk.X, padx=12, pady=12)
        
        backup_var = tk.BooleanVar(value=self.app.settings_manager.get('backup', False))
        
        def on_backup_change():
            """Обработчик изменения резервного копирования"""
            self.app.settings_manager.set('backup', backup_var.get())
            self.app.settings_manager.save_settings()
        
        backup_checkbox = tk.Checkbutton(
            inner_frame,
            text="Создавать резервные копии перед переименованием",
            variable=backup_var,
            command=on_backup_change,
            font=('Robot', 10),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            activebackground=self.app.colors['bg_main'],
            activeforeground=self.app.colors['text_primary'],
            selectcolor='white'
        )
        backup_checkbox.pack(anchor=tk.W)
        
        # Сохраняем ссылку на переменную
        self.app.backup_var = backup_var
    
    def create_remove_files_section(self, parent):
        """Создание секции удаления файлов из списка"""
        # Заголовок
        title_label = tk.Label(
            parent,
            text="Удаление файлов из списка",
            font=('Robot', 14, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Описание
        info_label = tk.Label(
            parent,
            text="Автоматически удалять файлы из списка после успешного переименования или конвертации.",
            font=('Robot', 9),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_secondary'],
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W, pady=(0, 10), fill=tk.X)
        
        # Функция для обновления wraplength при изменении размера
        def update_wraplength(event=None):
            try:
                # Используем ширину scrollable_frame для определения ширины текста
                scrollable_width = self.content_scrollable_frame.winfo_width()
                if scrollable_width > 1:
                    # Вычитаем отступы (padx=20 с каждой стороны = 40)
                    info_label.config(wraplength=scrollable_width - 40)
            except (AttributeError, tk.TclError):
                pass
        
        # Привязываем обновление к изменению размера scrollable_frame
        if hasattr(self, 'content_scrollable_frame'):
            self.content_scrollable_frame.bind('<Configure>', lambda e: update_wraplength())
        # Устанавливаем начальное значение после создания виджетов
        parent.after_idle(update_wraplength)
        
        # Карточка настроек
        card_frame = tk.Frame(parent, bg=self.app.colors['bg_main'], relief=tk.SOLID, borderwidth=1)
        card_frame.pack(fill=tk.X)
        
        inner_frame = tk.Frame(card_frame, bg=self.app.colors['bg_main'])
        inner_frame.pack(fill=tk.X, padx=12, pady=12)
        
        remove_files_var = tk.BooleanVar(value=self.app.settings_manager.get('remove_files_after_operation', False))
        
        def on_remove_files_change():
            """Обработчик изменения удаления файлов из списка"""
            self.app.settings_manager.set('remove_files_after_operation', remove_files_var.get())
            self.app.settings_manager.save_settings()
        
        remove_files_checkbox = tk.Checkbutton(
            inner_frame,
            text="Удалять файлы из списка после операции",
            variable=remove_files_var,
            command=on_remove_files_change,
            font=('Robot', 10),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            activebackground=self.app.colors['bg_main'],
            activeforeground=self.app.colors['text_primary'],
            selectcolor='white'
        )
        remove_files_checkbox.pack(anchor=tk.W)
        
        # Сохраняем ссылку на переменную для использования в других модулях
        self.app.remove_files_after_operation_var = remove_files_var
    
    def create_logs_section(self, parent):
        """Создание секции логов"""
        # Заголовок
        title_label = tk.Label(
            parent,
            text="Логи",
            font=('Robot', 14, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            anchor=tk.W
        )
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Описание
        info_label = tk.Label(
            parent,
            text="Просмотр и управление логами программы. Все действия записываются в файл лога.",
            font=('Robot', 9),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_secondary'],
            justify=tk.LEFT,
            anchor=tk.W
        )
        info_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Функция для обновления wraplength при изменении размера
        def update_wraplength(event=None):
            try:
                # Используем ширину scrollable_frame для определения ширины текста
                scrollable_width = self.content_scrollable_frame.winfo_width()
                if scrollable_width > 1:
                    # Вычитаем отступы (padx=20 с каждой стороны = 40)
                    info_label.config(wraplength=scrollable_width - 40)
            except (AttributeError, tk.TclError):
                pass
        
        # Привязываем обновление к изменению размера scrollable_frame
        if hasattr(self, 'content_scrollable_frame'):
            self.content_scrollable_frame.bind('<Configure>', lambda e: update_wraplength())
        # Устанавливаем начальное значение после создания виджетов
        parent.after_idle(update_wraplength)
        
        # Карточка настроек
        card_frame = tk.Frame(parent, bg=self.app.colors['bg_main'], relief=tk.SOLID, borderwidth=1)
        card_frame.pack(fill=tk.X, anchor=tk.W)
        
        inner_frame = tk.Frame(card_frame, bg=self.app.colors['bg_main'])
        inner_frame.pack(padx=12, pady=12, anchor=tk.W)
        
        def open_logs():
            """Открытие файла логов"""
            try:
                # Импорт функции работы с путями
                try:
                    from config.paths import get_logs_dir
                    logs_dir = get_logs_dir()
                except ImportError:
                    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
                
                if not os.path.exists(logs_dir):
                    os.makedirs(logs_dir)
                
                # Находим последний файл лога
                log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
                if not log_files:
                    self.app.log("Файлы логов не найдены")
                    return
                
                latest_log = max(log_files, key=lambda f: os.path.getmtime(os.path.join(logs_dir, f)))
                log_path = os.path.join(logs_dir, latest_log)
                
                # Открываем файл в системном редакторе
                if sys.platform == 'win32':
                    os.startfile(log_path)
                elif sys.platform == 'darwin':
                    subprocess.run(['open', log_path])
                else:
                    subprocess.run(['xdg-open', log_path])
            except Exception as e:
                logger.error(f"Ошибка открытия логов: {e}", exc_info=True)
                self.app.log(f"Ошибка открытия логов: {e}")
        
        open_logs_button = tk.Button(
            inner_frame,
            text="Открыть файл логов",
            command=open_logs,
            font=('Robot', 8),
            bg=self.app.colors['primary'],
            fg='white',
            activebackground=self.app.colors['primary_hover'],
            activeforeground='white',
            relief=tk.FLAT,
            cursor='hand2',
            padx=6,
            pady=3,
            anchor=tk.W
        )
        open_logs_button.pack(anchor=tk.W)

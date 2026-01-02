"""Модуль для вкладки настроек.

Обеспечивает интерфейс для управления настройками приложения:
автоприменение, шрифты и другие параметры.
"""

import logging
import os
import subprocess
import sys

import tkinter as tk
import tkinter.messagebox as messagebox
from tkinter import ttk


logger = logging.getLogger(__name__)


class SettingsTab:
    """
    Класс для управления вкладкой настроек приложения.
    
    Предоставляет интерфейс для изменения различных параметров приложения,
    таких как автоприменение методов, размер шрифта и т.д.
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
        self.selected_menu_item = tk.StringVar(value=menu_items[0][1])
        
        # Создаем кнопки меню
        self.menu_buttons = {}
        for text, value in menu_items:
            btn = tk.Button(
                menu_frame,
                text=text,
                font=('Robot', 10),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary'],
                activebackground=self.app.colors['primary'],
                activeforeground='white',
                relief=tk.FLAT,
                anchor='w',
                padx=15,
                pady=10,
                command=lambda v=value: self.switch_section(v)
            )
            btn.pack(fill=tk.X, padx=0, pady=0)
            self.menu_buttons[value] = btn
        
        # Добавляем "О программе" внизу меню
        about_label = tk.Label(
            menu_frame,
            text="О программе",
            font=('Robot', 10),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors.get('text_muted', self.app.colors.get('secondary', '#718096')),  # Голубовато-серый цвет
            cursor='hand2',
            anchor='w',
            padx=15,
            pady=10
        )
        about_label.pack(side=tk.BOTTOM, fill=tk.X, padx=0, pady=0)
        about_label.bind("<Button-1>", lambda e: self.open_about_window())
        self.menu_buttons["about"] = about_label
        
        # Правая панель - содержимое настроек
        content_container = tk.Frame(main_container, bg=self.app.colors['bg_main'])
        content_container.grid(row=0, column=1, columnspan=2, sticky="nsew", padx=0, pady=0)
        content_container.columnconfigure(0, weight=1)
        content_container.rowconfigure(0, weight=1)
        
        # Простой Frame для содержимого (без прокрутки для упрощения)
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
                if value == "about":
                    # Для "О программе" не меняем стиль, оставляем как есть
                    pass
                else:
                    btn.config(bg=self.app.colors['primary'], fg='white')
            else:
                if value == "about":
                    # Для "О программе" не меняем стиль
                    pass
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
        elif section_name == "about":
            self.create_about_section(section_frame)
    
    def create_general_section(self, parent):
        """Создание секции общих настроек.
        
        Args:
            parent: Родительский виджет для размещения секции
        """
        self._create_section_header(parent, "Общие настройки")
        # Здесь можно добавить общие настройки
    
    def create_remove_files_section(self, parent):
        """Создание секции настроек удаления файлов.
        
        Args:
            parent: Родительский виджет для размещения секции
        """
        self._create_section_header(parent, "Удаление файлов", "Настройки поведения при удалении файлов")
        
        # Чекбоксы для настроек удаления файлов
        settings_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Настройка удаления файлов из списка после операции
        self._create_remove_files_checkbox(settings_frame)
    
    def create_logs_section(self, parent):
        """Создание секции настроек логов.
        
        Args:
            parent: Родительский виджет для размещения секции
        """
        self._create_section_header(parent, "Логи", "Настройки логирования приложения")
        
        # Получаем путь к логам
        logs_path = self._get_logs_path()
        
        # Отображаем путь к логам
        self._create_logs_path_display(parent, logs_path)
        
        # Кнопки открытия папки и файла логов
        logs_buttons_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        logs_buttons_frame.pack(fill=tk.X, pady=(0, 10))
        
        self._create_open_logs_folder_button(logs_buttons_frame, logs_path)
        self._create_open_log_file_button(logs_buttons_frame)
    
    def open_about_window(self):
        """Открытие отдельного окна 'О программе'."""
        # Проверяем, не открыто ли уже окно
        if hasattr(self.app, '_about_window') and self.app._about_window is not None:
            try:
                if self.app._about_window.winfo_exists():
                    # Окно уже открыто, поднимаем его на передний план
                    self.app._about_window.lift()
                    self.app._about_window.focus_force()
                    return
            except (tk.TclError, AttributeError):
                # Окно было закрыто, но ссылка осталась
                pass
        
        # Создаем новое окно
        about_window = tk.Toplevel(self.app.root)
        about_window.title("О программе")
        about_window.geometry("800x600")
        about_window.minsize(600, 400)
        about_window.configure(bg=self.app.colors['bg_main'])
        
        # Установка иконки
        try:
            from ui.ui_components import set_window_icon
            set_window_icon(about_window, self.app._icon_photos)
        except (ImportError, AttributeError, tk.TclError, OSError):
            pass
        
        about_window.columnconfigure(0, weight=1)
        about_window.rowconfigure(0, weight=1)
        
        # Сохраняем ссылку на окно
        self.app._about_window = about_window
        
        # Создаем содержимое окна
        if hasattr(self.app, 'main_window_handler') and hasattr(self.app.main_window_handler, 'about'):
            self.app.main_window_handler.about.create_about_tab_content(about_window)
        else:
            # Если нет доступа к main_window_handler, создаем напрямую
            from ui.window.about import MainWindowAbout
            about_handler = MainWindowAbout(self.app)
            about_handler.create_about_tab_content(about_window)
        
        # Обработчик закрытия окна
        def on_close():
            self.app._about_window = None
            about_window.destroy()
        
        about_window.protocol("WM_DELETE_WINDOW", on_close)
    
    def create_about_section(self, parent):
        """Создание секции 'О программе'.
        
        Args:
            parent: Родительский виджет для размещения секции (section_frame)
        """
        from ui.about_tab import AboutTab
        
        # Создаем экземпляр AboutTab для использования его метода создания содержимого
        about_tab_handler = AboutTab(
            None,  # notebook не нужен
            self.app.colors,
            self.app.bind_mousewheel,
            self.app._icon_photos
        )
        
        # Используем метод создания содержимого напрямую в parent
        # (как и другие секции, просто добавляем контент в section_frame)
        about_tab_handler._create_content(parent)
    
    def _create_section_header(self, parent, title, description=None):
        """Создание заголовка и описания для секции настроек.
        
        Args:
            parent: Родительский виджет
            title: Заголовок секции
            description: Описание секции (опционально)
        """
        title_label = tk.Label(
            parent,
            text=title,
            font=('Robot', 14, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        if description:
            description_label = tk.Label(
                parent,
                text=description,
                font=('Robot', 10),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_secondary']
            )
            description_label.pack(anchor=tk.W, pady=(0, 15))
    
    def _create_remove_files_checkbox(self, parent):
        """Создание чекбокса для настройки удаления файлов из списка после операции.
        
        Args:
            parent: Родительский виджет для размещения чекбокса
        """
        # Инициализируем переменную, если её еще нет
        if not hasattr(self.app, 'remove_files_after_operation_var'):
            default_value = False
            if hasattr(self.app, 'settings_manager'):
                default_value = self.app.settings_manager.get('remove_files_after_operation', False)
            self.app.remove_files_after_operation_var = tk.BooleanVar(value=default_value)
        
        def on_remove_files_change(*args):
            """Обработчик изменения настройки удаления файлов"""
            if hasattr(self.app, 'settings_manager'):
                value = self.app.remove_files_after_operation_var.get()
                self.app.settings_manager.set('remove_files_after_operation', value)
                self.app.settings_manager.save_settings()
        
        self.app.remove_files_after_operation_var.trace('w', on_remove_files_change)
        
        checkbox = tk.Checkbutton(
            parent,
            text="Удалять файлы из списка после операции",
            font=('Robot', 10),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            activebackground=self.app.colors['bg_main'],
            activeforeground=self.app.colors['text_primary'],
            selectcolor=self.app.colors['bg_main'],
            variable=self.app.remove_files_after_operation_var,
            anchor='w'
        )
        checkbox.pack(anchor=tk.W, pady=(0, 10))
    
    def _get_logs_path(self):
        """Получение пути к директории с логами.
        
        Returns:
            str: Путь к директории с логами
        """
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "logs"
        )
    
    def _create_logs_path_display(self, parent, logs_path):
        """Создание отображения пути к логам.
        
        Args:
            parent: Родительский виджет
            logs_path: Путь к директории с логами
        """
        logs_path_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        logs_path_frame.pack(fill=tk.X, pady=(0, 10))
        
        logs_path_label = tk.Label(
            logs_path_frame,
            text="Путь к логам:",
            font=('Robot', 10),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        logs_path_label.pack(side=tk.LEFT, padx=(0, 10))
        
        logs_path_text = tk.Label(
            logs_path_frame,
            text=logs_path,
            font=('Robot', 9),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_secondary']
        )
        logs_path_text.pack(side=tk.LEFT)
    
    def _open_path_in_system(self, path):
        """Открытие пути в системе по умолчанию.
        
        Args:
            path: Путь к файлу или директории
            
        Raises:
            Exception: Если не удалось открыть путь
        """
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            logger.error(f"Ошибка при открытии пути {path}: {e}")
            raise
    
    def _create_open_logs_folder_button(self, parent, logs_path):
        """Создание кнопки для открытия папки с логами.
        
        Args:
            parent: Родительский виджет
            logs_path: Путь к директории с логами
        """
        def open_logs_folder():
            """Открытие папки с логами"""
            try:
                self._open_path_in_system(logs_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть папку с логами:\n{e}")
        
        open_logs_btn = tk.Button(
            parent,
            text="Открыть папку",
            font=('Robot', 9),
            bg=self.app.colors['primary'],
            fg='white',
            activebackground=self.app.colors['primary_hover'],
            activeforeground='white',
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=open_logs_folder
        )
        open_logs_btn.pack(side=tk.LEFT)
    
    def _create_open_log_file_button(self, parent):
        """Создание кнопки для открытия файла логов.
        
        Args:
            parent: Родительский виджет
        """
        open_log_file_btn = tk.Button(
            parent,
            text="Открыть файл логов",
            font=('Robot', 9),
            bg=self.app.colors['info'],
            fg='white',
            activebackground=self.app.colors['info_hover'],
            activeforeground='white',
            relief=tk.FLAT,
            padx=15,
            pady=5,
            command=self._open_log_file
        )
        open_log_file_btn.pack(side=tk.LEFT, padx=(10, 0))
    
    def _open_log_file(self):
        """Открытие файла логов в редакторе по умолчанию"""
        logs_path = self._get_logs_path()
        log_file_path = os.path.join(logs_path, "re-file-plus.log")
        
        try:
            if os.path.exists(log_file_path):
                self._open_path_in_system(log_file_path)
            else:
                messagebox.showinfo("Информация", "Файл логов не найден")
        except Exception as e:
            logger.error(f"Ошибка при открытии файла логов: {e}")
            messagebox.showerror("Ошибка", f"Не удалось открыть файл логов:\n{e}")

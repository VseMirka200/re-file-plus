"""Модуль для создания диалоговых окон и управления окнами.

Обеспечивает создание и управление диалоговыми окнами приложения.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from ui.ui_components import set_window_icon

if TYPE_CHECKING:
    from app.app_core import ReFilePlusApp

logger = logging.getLogger(__name__)


class Dialogs:
    """Класс для управления диалоговыми окнами приложения."""
    
    def __init__(self, app):
        """Инициализация диалогов.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
    
    def open_actions_window(self):
        """Открытие окна действий"""
        if self.app.windows['actions'] is not None and self.app.windows['actions'].winfo_exists():
            # Если окно свернуто, разворачиваем его
            try:
                if self.app.windows['actions'].state() == 'iconic':
                    self.app.windows['actions'].deiconify()
            except (AttributeError, tk.TclError):
                pass
            self.app.windows['actions'].lift()
            self.app.windows['actions'].focus_force()
            return
        
        window = tk.Toplevel(self.app.root)
        window.title("🚀 Действия")
        window.geometry("600x180")
        window.minsize(500, 150)
        window.configure(bg=self.app.colors['bg_main'])
        
        # Установка иконки
        try:
            set_window_icon(window, self.app._icon_photos)
        except (AttributeError, tk.TclError, OSError) as e:
            logger.debug(f"Не удалось установить иконку окна: {e}")
        except Exception as e:
            logger.warning(f"Неожиданная ошибка при установке иконки: {e}")
        
        # Настройка адаптивности окна
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)
        
        # Обработчик изменения размера окна
        def on_actions_window_resize(event):
            if event.widget == window:
                try:
                    window.update_idletasks()
                except (AttributeError, tk.TclError):
                    pass
        
        window.bind('<Configure>', on_actions_window_resize)
        
        self.app.windows['actions'] = window
        
        # Основной контейнер для масштабирования
        main_frame = tk.Frame(window, bg=self.app.colors['bg_main'])
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Кнопки действий
        buttons_frame = tk.Frame(main_frame, bg=self.app.colors['bg_main'])
        buttons_frame.grid(row=0, column=0, sticky="ew")
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        
        btn_start = self.app.create_rounded_button(
            buttons_frame, "✓ Применить", self.app.start_re_file,
            self.app.colors['success'], 'white',
            font=('Robot', 9, 'bold'), padx=10, pady=6,
            active_bg=self.app.colors['success_hover'])
        btn_start.grid(row=0, column=1, sticky="ew", padx=4)
        
        # Кнопка отмены
        self.app.cancel_rename_var = tk.BooleanVar(value=False)
        btn_cancel = self.app.create_rounded_button(
            buttons_frame, "❌ Отменить", lambda: self.app.cancel_rename_var.set(True),
            self.app.colors['danger'], 'white',
            font=('Robot', 8, 'bold'), padx=8, pady=4,
            active_bg=self.app.colors['danger_hover'])
        btn_cancel.grid(row=0, column=0, sticky="ew", padx=4)
        
        # Обработчик закрытия окна - делаем окно статичным (сворачиваем вместо закрытия)
        def on_close_actions_window():
            try:
                if window.winfo_exists():
                    window.iconify()
            except (AttributeError, tk.TclError):
                pass
        
        window.protocol("WM_DELETE_WINDOW", on_close_actions_window)
    
    def open_log_window(self) -> None:
        """Переключение на вкладку настроек (логи теперь в настройках)."""
        if hasattr(self.app, 'main_notebook') and self.app.main_notebook:
            # Находим индекс вкладки "Настройки"
            for i in range(self.app.main_notebook.index('end')):
                if self.app.main_notebook.tab(i, 'text') == 'Настройки':
                    self.app.main_notebook.select(i)
                    break
    
    def open_settings_window(self) -> None:
        """Переключение на вкладку настроек в главном окне."""
        if hasattr(self.app, 'main_notebook') and self.app.main_notebook:
            # Находим индекс вкладки "Настройки"
            for i in range(self.app.main_notebook.index('end')):
                if self.app.main_notebook.tab(i, 'text') == 'Настройки':
                    self.app.main_notebook.select(i)
                    break
    
    def open_tabs_window(self, tab_name: str = 'about') -> None:
        """Открытие окна с вкладками (настройки, о программе, поддержка)"""
        if self.app.windows['tabs'] is not None and self.app.windows['tabs'].winfo_exists():
            try:
                if self.app.windows['tabs'].state() == 'iconic':
                    self.app.windows['tabs'].deiconify()
            except (AttributeError, tk.TclError):
                pass
            self.app.windows['tabs'].lift()
            self.app.windows['tabs'].focus_force()
            
            # Переключаемся на нужную вкладку
            if self.app.tabs_window_notebook:
                tab_index_map = {'settings': 0, 'about': 1, 'support': 2}
                if tab_name in tab_index_map:
                    self.app.tabs_window_notebook.select(tab_index_map[tab_name])
            return
        
        window = tk.Toplevel(self.app.root)
        window.title("Вкладки")
        window.geometry("800x600")
        window.minsize(600, 400)
        window.configure(bg=self.app.colors['bg_main'])
        
        # Установка иконки
        try:
            set_window_icon(window, self.app._icon_photos)
        except (AttributeError, tk.TclError, OSError) as e:
            logger.debug(f"Не удалось установить иконку окна: {e}")
        except Exception as e:
            logger.warning(f"Неожиданная ошибка при установке иконки: {e}")
        
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)
        self.app.windows['tabs'] = window
        
        notebook = ttk.Notebook(window)
        notebook.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.app.tabs_window_notebook = notebook
        
        # Создаем вкладки
        self.app._create_settings_tab(notebook)
        self.app._create_about_tab(notebook)
        self.app._create_support_tab(notebook)
        
        # Переключаемся на нужную вкладку
        tab_index_map = {'settings': 0, 'about': 1, 'support': 2}
        if tab_name in tab_index_map:
            notebook.select(tab_index_map[tab_name])
        
        # Обработчик закрытия окна
        def on_close():
            self.app.logger.set_log_widget(None)
            self.app.close_window('tabs')
        
        window.protocol("WM_DELETE_WINDOW", on_close)


class WindowManagement:
    """Класс для управления дополнительными окнами приложения.
    
    Упрощенная обертка над Dialogs для обратной совместимости.
    Все методы делегируют вызовы к Dialogs.
    """
    
    def __init__(self, app: 'ReFilePlusApp') -> None:
        """Инициализация управления окнами.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def open_actions_window(self) -> None:
        """Открытие окна действий."""
        self.app.dialogs.open_actions_window()
    
    def open_tabs_window(self, tab_name: str = 'about') -> None:
        """Открытие окна с вкладками.
        
        Args:
            tab_name: Имя вкладки для открытия
        """
        self.app.dialogs.open_tabs_window(tab_name)
    
    def open_log_window(self) -> None:
        """Открытие окна лога."""
        self.app.dialogs.open_log_window()
    
    def open_settings_window(self) -> None:
        """Переключение на вкладку настроек."""
        self.app.dialogs.open_settings_window()
    
    def open_about_window(self) -> None:
        """Открытие окна с вкладкой 'О программе'."""
        self.open_tabs_window('about')
    
    def open_support_window(self) -> None:
        """Открытие окна с вкладкой 'Поддержка'."""
        self.open_tabs_window('support')
    
    def close_window(self, window_name: str):
        """Закрытие окна по имени
        
        Args:
            window_name: Имя окна в словаре self.windows
        """
        if hasattr(self.app, 'windows') and window_name in self.app.windows:
            window = self.app.windows[window_name]
            try:
                if window and window.winfo_exists():
                    window.destroy()
                    del self.app.windows[window_name]
            except (tk.TclError, AttributeError):
                if window_name in self.app.windows:
                    del self.app.windows[window_name]

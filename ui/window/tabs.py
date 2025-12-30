"""Модуль для управления вкладками главного окна."""

import logging
import tkinter as tk

logger = logging.getLogger(__name__)


class MainWindowTabs:
    """Класс для управления вкладками главного окна."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
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
                self.app.main_window_handler.on_action_changed(self.app.action_var.get())
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
                self.app.main_window_handler._create_about_tab_content(about_container)
            else:
                self.app.about_tab_container.grid(row=0, column=0, sticky="nsew")
        
        # Обновляем текущую вкладку
        self.app.current_tab = tab_id


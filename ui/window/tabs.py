"""Модуль для управления вкладками главного окна."""

import logging
import tkinter as tk

logger = logging.getLogger(__name__)


class MainWindowTabs:
    """Класс для управления переключением между вкладками главного окна.
    
    Отвечает за:
    - Переключение между основными вкладками (Переименовщик, Конвертация, Сортировка, Настройки)
    - Управление видимостью контейнеров вкладок
    - Координация отображения общих элементов (список файлов) между вкладками
    - Создание содержимого вкладок при первом обращении
    
    Обеспечивает правильное отображение контента при переключении между вкладками.
    """
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
            tab_id: Идентификатор вкладки ('files', 'convert', 'sort', 'settings')
        """
        # Обновляем текущую вкладку (в начале, чтобы была доступна для всех проверок)
        self.app.current_tab = tab_id
        
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
        if hasattr(self.app, 'convert_tab_container'):
            self.app.convert_tab_container.grid_remove()
        if hasattr(self.app, 'sort_tab_container'):
            self.app.sort_tab_container.grid_remove()
        if hasattr(self.app, 'settings_tab_container'):
            self.app.settings_tab_container.grid_remove()
        
        # Показываем содержимое для выбранной вкладки
        if tab_id == "files":
            # Показываем вкладку "Переименовщик" (панель действий + список файлов)
            if hasattr(self.app, 'files_tab_container'):
                self.app.files_tab_container.grid(row=0, column=0, sticky="nsew")
            # Скрываем converter_top_panel при переключении на переименовщик
            if hasattr(self.app, 'converter_top_panel'):
                try:
                    self.app.converter_top_panel.grid_remove()
                except (tk.TclError, AttributeError):
                    pass
            # Показываем actions_panel в переименовщике
            if hasattr(self.app, 'actions_panel'):
                self.app.actions_panel.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 1))
            # Перемещаем list_frame обратно в files_container при переключении на переименовщик
            if hasattr(self.app, 'files_container') and hasattr(self.app, 'list_frame'):
                if self.app.list_frame.master != self.app.files_container:
                    if self.app.list_frame.winfo_manager() == 'pack':
                        self.app.list_frame.pack_forget()
                    elif self.app.list_frame.winfo_manager() == 'grid':
                        self.app.list_frame.grid_forget()
                    self.app.list_frame.master = self.app.files_container
                    self.app.list_frame.pack(fill=tk.BOTH, expand=True)
            # Всегда показываем action_content_frame при переключении на вкладку "Переименовщик"
            if hasattr(self.app, 'action_content_frame'):
                self.app.action_content_frame.grid(row=0, column=1, sticky="ew", padx=(5, 10), pady=5)
            # Создаем содержимое переименования, если его еще нет
            if hasattr(self.app, 'main_window_handler') and hasattr(self.app, 'action_content_frame'):
                if "re_file" not in self.app.tab_contents or self.app.tab_contents["re_file"] is None:
                    self.app.main_window_handler.actions.create_re_file_action_content(self.app.action_content_frame)
                else:
                    re_file_frame = self.app.tab_contents.get("re_file")
                    if re_file_frame:
                        try:
                            if re_file_frame.winfo_exists():
                                re_file_frame.grid(row=0, column=0, sticky="ew")
                            else:
                                self.app.main_window_handler.actions.create_re_file_action_content(self.app.action_content_frame)
                        except (tk.TclError, AttributeError):
                            self.app.main_window_handler.actions.create_re_file_action_content(self.app.action_content_frame)
            # Обновляем колонки для переименовщика
            if hasattr(self.app, 'main_window_handler'):
                self.app.root.after(100, self.app.main_window_handler.update_tree_columns)
        elif tab_id == "convert":
            # Показываем files_tab_container для доступа к files_container
            if hasattr(self.app, 'files_tab_container'):
                self.app.files_tab_container.grid(row=0, column=0, sticky="nsew")
            # Инициализируем верхнюю панель конвертера при первом переключении
            if not hasattr(self.app, 'converter_top_panel'):
                # Создаем верхнюю панель конвертера в files_tab_container
                if hasattr(self.app, 'files_tab_container') and hasattr(self.app, 'converter_tab_handler'):
                    if hasattr(self.app.converter_tab_handler, 'tab_builder'):
                        self.app.converter_tab_handler.tab_builder._create_top_panel(self.app.files_tab_container)
            # Скрываем actions_panel в files_tab_container для конвертера
            if hasattr(self.app, 'actions_panel'):
                self.app.actions_panel.grid_remove()
            # Показываем верхнюю панель конвертера в files_tab_container (вместо actions_panel)
            if hasattr(self.app, 'converter_top_panel'):
                try:
                    self.app.converter_top_panel.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 1))
                except tk.TclError:
                    # Если виджет был уничтожен, создаем заново
                    if hasattr(self.app, 'files_tab_container') and hasattr(self.app, 'converter_tab_handler'):
                        if hasattr(self.app.converter_tab_handler, 'tab_builder'):
                            self.app.converter_tab_handler.tab_builder._create_top_panel(self.app.files_tab_container)
                            self.app.converter_top_panel.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 1))
            # Скрываем action_content_frame в конвертере
            if hasattr(self.app, 'action_content_frame'):
                self.app.action_content_frame.grid_remove()
            # Обновляем колонки для конвертера
            if hasattr(self.app, 'main_window_handler'):
                self.app.root.after(100, self.app.main_window_handler.update_tree_columns)
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


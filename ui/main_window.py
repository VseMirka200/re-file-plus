"""Модуль для создания главного окна и базовых виджетов.

Содержит обработчики пользовательского ввода: горячие клавиши и поиск.

ВНИМАНИЕ: Этот модуль теперь является координатором.
Основная логика перенесена в ui/window/.
"""

# Стандартная библиотека
import logging
import tkinter as tk
from tkinter import ttk

# Локальные импорты
from ui.window.widgets import MainWindowWidgets
from ui.window.tabs import MainWindowTabs
from ui.window.actions import MainWindowActions
from ui.window.templates_guide import TemplatesGuide
from ui.window.resize import MainWindowResize
from ui.window.about import MainWindowAbout

logger = logging.getLogger(__name__)


class MainWindow:
    """Класс для управления главным окном и базовыми виджетами.
    
    Теперь является координатором, делегирующим работу подмодулям.
    """
    
    def __init__(self, app) -> None:
        """Инициализация главного окна.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
        # Инициализируем подмодули
        self.widgets = MainWindowWidgets(app)
        self.tabs = MainWindowTabs(app)
        self.actions = MainWindowActions(app)
        self.templates_guide = TemplatesGuide(app)
        self.resize = MainWindowResize(app)
        self.about = MainWindowAbout(app)
    
    def create_widgets(self) -> None:
        """Создание всех виджетов интерфейса.
        
        Создает главное окно с вкладками вверху, общим списком файлов слева
        и содержимым вкладок справа.
        """
        # Делегируем создание виджетов подмодулю
        self.widgets.create_widgets()
    
    def switch_tab(self, tab_id: str) -> None:
        """Переключение между вкладками.
        
        Args:
            tab_id: Идентификатор вкладки ('files', 'sort', 'settings', 'about')
        """
        # Делегируем переключение вкладок подмодулю
        self.tabs.switch_tab(tab_id)
    
    def _create_files_list_in_container(self, parent):
        """Создание списка файлов в контейнере (делегируется widgets)."""
        return self.widgets._create_files_list_in_container(parent)
    
    def create_rename_tab_content(self, parent) -> None:
        """Создание содержимого вкладки переименования (делегируется actions).
        
        Args:
            parent: Родительский контейнер (action_content_frame)
        """
        return self.actions.create_rename_tab_content(parent)
    
    def on_action_changed(self, action: str) -> None:
        """Обработка изменения выбранного действия (делегируется actions).
        
        Args:
            action: Название действия ("Переименовать", "Конвертировать")
        """
        return self.actions.on_action_changed(action)
    
    def create_re_file_action_content(self, parent) -> None:
        """Создание содержимого для действия 'Переименовать' (делегируется actions).
        
        Args:
            parent: Родительский контейнер (action_content_frame)
        """
        return self.actions.create_re_file_action_content(parent)
    
    def show_templates_guide(self):
        """Показ окна руководства по шаблонам (делегируется templates_guide)."""
        return self.templates_guide.show_templates_guide()
    
    def create_convert_action_content(self, parent) -> None:
        """Создание содержимого для действия 'Конвертировать' (делегируется actions).
        
        Args:
            parent: Родительский контейнер (action_content_frame)
        """
        return self.actions.create_convert_action_content(parent)
    
    def update_tree_columns_for_action(self, action: str) -> None:
        """Обновление колонок таблицы (делегируется resize).

        Args:
            action: Название действия ('rename', 'convert')
        """
        return self.resize.update_tree_columns_for_action(action)
    
    def update_tree_columns(self) -> None:
        """Обновление размеров колонок таблицы (делегируется resize)."""
        return self.resize.update_tree_columns()
    
    def _create_about_tab_content(self, parent):
        """Создание содержимого вкладки 'О программе' (делегируется about).
        
        Args:
            parent: Родительский контейнер (Frame)
        """
        return self.about.create_about_tab_content(parent)
    
    def update_scrollbar_visibility(
        self, widget, scrollbar, orientation: str = 'vertical'
    ) -> None:
        """Автоматическое управление видимостью скроллбара (делегируется resize).
        
        Args:
            widget: Виджет (Treeview, Listbox, Text, Canvas)
            scrollbar: Скроллбар для управления
            orientation: Ориентация ('vertical' или 'horizontal')
        """
        return self.resize.update_scrollbar_visibility(widget, scrollbar, orientation)
    
    def on_window_resize(self, event=None) -> None:
        """Обработчик изменения размера окна (делегируется resize)."""
        return self.resize.on_window_resize(event)


# ============================================================================
# ОБРАБОТЧИКИ ПОЛЬЗОВАТЕЛЬСКОГО ВВОДА
# ============================================================================

# Импортируем обработчики из отдельных модулей
from ui.window.hotkeys import HotkeysHandler
from ui.window.search import SearchHandler

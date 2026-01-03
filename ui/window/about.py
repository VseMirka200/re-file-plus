"""Модуль для создания вкладки 'О программе'.

Использует переиспользуемые компоненты для создания прокручиваемого контента.
"""

import tkinter as tk
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.app_core import ReFilePlusApp

# Локальные импорты
from ui.components import create_scrollable_frame


class MainWindowAbout:
    """Класс для создания вкладки 'О программе'.
    
    Использует переиспользуемый компонент ScrollableFrame для создания
    прокручиваемого контента с автоматической настройкой scrollbar.
    """
    
    def __init__(self, app: 'ReFilePlusApp') -> None:
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app: 'ReFilePlusApp' = app
    
    def create_about_tab_content(self, parent: tk.Widget) -> None:
        """Создание содержимого вкладки 'О программе'.
        
        Создает прокручиваемый контейнер с содержимым о программе,
        используя переиспользуемый компонент ScrollableFrame.
        
        Args:
            parent: Родительский контейнер (Frame или Toplevel)
        """
        from ui.tabs.about_tab import AboutTab
        
        # Создаем прокручиваемый фрейм используя переиспользуемый компонент
        scrollable_frame, scrollable = create_scrollable_frame(
            parent,
            bg_color=self.app.colors['bg_main'],
            bind_mousewheel_func=self.app.bind_mousewheel
        )
        
        # Размещаем scrollable компонент
        scrollable.grid(row=0, column=0, sticky="nsew")
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)
        
        # Создаем AboutTab и используем его метод для создания содержимого
        about_tab_handler = AboutTab(
            None,  # notebook не нужен, так как мы используем Frame
            self.app.colors,
            self.app.bind_mousewheel,
            self.app._icon_photos
        )
        
        # Вызываем метод для создания содержимого на Frame
        about_tab_handler.create_content(scrollable_frame)


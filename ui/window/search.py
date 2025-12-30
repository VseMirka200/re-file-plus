"""Обработчики поиска файлов в списке."""

import logging
import tkinter as tk

logger = logging.getLogger(__name__)


class SearchHandler:
    """Класс для управления поиском файлов в списке."""
    
    def __init__(self, app) -> None:
        self.app = app
    
    def focus_search(self) -> None:
        """Фокус на поле поиска (Ctrl+F)."""
        if hasattr(self.app, 'search_entry'):
            self.app.search_entry.focus()
            self.app.search_entry.select_range(0, tk.END)
    
    def on_search_change(self, event=None) -> None:
        """Обработка изменения текста поиска."""
        self.app.refresh_treeview()
    
    def clear_search(self) -> None:
        """Очистка поля поиска."""
        if hasattr(self.app, 'search_entry'):
            self.app.search_entry.delete(0, tk.END)
            self.app.refresh_treeview()


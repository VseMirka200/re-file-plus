"""Модуль для выбора папки сортировки."""

import logging
from tkinter import filedialog

logger = logging.getLogger(__name__)


class SorterFolder:
    """Класс для управления выбором папки сортировки."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def browse_sorter_folder(self):
        """Выбор папки для сортировки"""
        folder = filedialog.askdirectory(title="Выберите папку для сортировки")
        if folder:
            self.app.sorter_folder_path.set(folder)


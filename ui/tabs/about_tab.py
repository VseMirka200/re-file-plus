"""Модуль для создания вкладки 'О программе'."""

import logging
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class AboutTab:
    """Класс для создания и управления вкладкой 'О программе'."""
    
    def __init__(self, notebook, colors, bind_mousewheel_func, icon_photos_list):
        """Инициализация вкладки 'О программе'.
        
        Args:
            notebook: Notebook виджет (не используется в PyQt6)
            colors: Словарь с цветами интерфейса
            bind_mousewheel_func: Функция для привязки прокрутки (не используется)
            icon_photos_list: Список для хранения ссылок на изображения (не используется)
        """
        self.colors = colors
    
    def _create_content(self, parent):
        """Создание содержимого вкладки 'О программе'.
        
        Args:
            parent: Родительский виджет
        """
        # Если parent - QWidget, создаем layout
        if isinstance(parent, QWidget):
            layout = QVBoxLayout(parent)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
        else:
            # Если это layout, используем его напрямую
            layout = parent
        
        # Заголовок
        try:
            from config.constants import APP_VERSION
            title = QLabel(f"Ре-Файл+ v{APP_VERSION}")
        except ImportError:
            title = QLabel("Ре-Файл+")
        
        title.setFont(QFont("Robot", 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Описание
        description = QLabel(
            "Приложение для переименования, конвертации и сортировки файлов.\n\n"
            "Разработано с использованием PyQt6."
        )
        description.setFont(QFont("Robot", 10))
        description.setWordWrap(True)
        description.setStyleSheet(f"color: {self.colors.get('text_secondary', '#666666')};")
        layout.addWidget(description)
        
        layout.addStretch()


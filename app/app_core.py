"""Основной класс приложения Ре-Файл+.

Содержит главный класс приложения, который инициализирует все компоненты.
"""

import logging
from typing import List, Optional, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)


class ReFilePlusApp:
    """Главный класс приложения Ре-Файл+.
    
    Управляет жизненным циклом приложения и координирует работу всех модулей.
    """
    
    def __init__(self, files_from_args: Optional[List[str]] = None):
        """Инициализация приложения.
        
        Args:
            files_from_args: Список файлов из аргументов командной строки
        """
        logger.info("Инициализация ReFilePlusApp...")
        
        self.files_from_args = files_from_args or []
        
        # Базовые атрибуты
        self.cancel_rename_var = None
        
        # Управление окнами
        self.windows: Dict[str, Optional] = {
            'actions': None,
            'tabs': None,
            'methods': None
        }
        
        # Цветовая схема (будет загружена из настроек)
        self.colors = {
            'bg_main': '#FFFFFF',
            'bg_secondary': '#F5F5F5',
            'text_primary': '#000000',
            'text_secondary': '#666666',
            'accent': '#0078D4',
            'primary': '#0078D4',
            'primary_hover': '#0063B1',
            'success': '#107C10',
            'success_hover': '#0E6B0E',
            'warning': '#FFB900',
            'error': '#D13438',
            'danger': '#D13438',
            'danger_hover': '#B02A2E',
            'info': '#17A2B8',
            'info_hover': '#138496'
        }
        
        # Инициализация приложения через AppInitializer
        from app.app_initializer import AppInitializer
        initializer = AppInitializer(self)
        initializer.initialize(files_from_args)
        
        logger.info("ReFilePlusApp инициализирован успешно")
    
    def log(self, message: str):
        """Логирование сообщений (для совместимости)."""
        logger.info(message)


"""Модуль вкладок приложения.

Содержит классы для создания и управления вкладками:
- about_tab: Вкладка "О программе"
- converter_tab: Вкладка конвертации файлов
- settings_tab: Вкладка настроек
- sorter_tab: Вкладка сортировки файлов
"""

from .about_tab import AboutTab
from .converter_tab import ConverterTab
from .settings_tab import SettingsTab
from .sorter_tab import SorterTab

__all__ = [
    'AboutTab',
    'ConverterTab',
    'SettingsTab',
    'SorterTab',
]


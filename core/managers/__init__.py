"""Модуль менеджеров ядра приложения.

Содержит классы для управления различными аспектами приложения:
- history_manager: Управление историей операций
- methods_manager: Управление методами переименования
- plugins: Управление плагинами
- settings_manager: Управление настройками
"""

from .history_manager import HistoryManager
from .methods_manager import MethodsManager
from .plugins import PluginManager
from .settings_manager import SettingsManager

__all__ = [
    'HistoryManager',
    'MethodsManager',
    'PluginManager',
    'SettingsManager',
]


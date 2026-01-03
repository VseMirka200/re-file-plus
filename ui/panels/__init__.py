"""Модуль панелей UI.

Содержит классы для создания панелей интерфейса:
- methods_panel: Панель методов переименования
- methods_window: Окно управления методами
"""

from .methods_panel import MethodsPanel
from .methods_window import MethodsWindow

__all__ = [
    'MethodsPanel',
    'MethodsWindow',
]


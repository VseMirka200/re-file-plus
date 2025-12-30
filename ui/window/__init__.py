"""Модуль главного окна приложения.

Разбит на подмодули для лучшей организации кода:
- widgets: Основные виджеты главного окна
- tabs: Управление вкладками
- actions: Действия (переименование, конвертация)
- hotkeys: Обработчики горячих клавиш
- search: Обработчики поиска
- resize: Обработка изменения размера окна
- about: Вкладка "О программе"
- templates_guide: Руководство по шаблонам

Примечание: MainWindow находится в ui/main_window.py и импортируется напрямую оттуда.
"""

from .hotkeys import HotkeysHandler
from .search import SearchHandler

__all__ = [
    'HotkeysHandler',
    'SearchHandler',
]


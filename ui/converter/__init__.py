"""Модуль вкладки конвертации файлов.

Разбит на подмодули для лучшей организации кода:
- file_handler: Обработка файлов (добавление, удаление, фильтрация)
- ui_components: UI компоненты (таблицы, кнопки, меню)
- tab_builder: Построение UI вкладки
- args_processor: Обработка аргументов командной строки
- drag_drop: Drag and drop функциональность
- context_menu: Контекстное меню
- converter: Процессор конвертации
- progress: Управление прогрессом
"""

# Основной класс ConverterTab находится в ui/converter_tab.py
# Импортируем из основного модуля для обратной совместимости
try:
    from ui.converter_tab import ConverterTab
    __all__ = ['ConverterTab']
except ImportError:
    __all__ = []


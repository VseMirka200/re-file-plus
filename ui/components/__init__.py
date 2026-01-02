"""Модуль UI компонентов.

Разбит на подмодули для лучшей организации кода:
- tooltip: Подсказки при наведении
- buttons: Создание кнопок
- styles: Управление стилями
- themes: Управление темами
- window_utils: Утилиты для работы с окнами
- scrollable: Прокручиваемые компоненты
- cards: Карточки (cards)
"""

# Импортируем для обратной совместимости
from .tooltip import ToolTip
from .buttons import UIComponents
from .styles import StyleManager
from .themes import ThemeManager
from .window_utils import (
    load_image_icon,
    set_window_icon,
    bind_mousewheel,
    setup_window_resize_handler,
)
from .scrollable import ScrollableFrame, create_scrollable_frame
from .cards import create_card, create_card_with_content

__all__ = [
    'ToolTip',
    'UIComponents',
    'StyleManager',
    'ThemeManager',
    'load_image_icon',
    'set_window_icon',
    'bind_mousewheel',
    'setup_window_resize_handler',
    'ScrollableFrame',
    'create_scrollable_frame',
    'create_card',
    'create_card_with_content',
]


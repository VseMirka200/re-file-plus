"""Модуль для UI компонентов, стилей и утилит работы с окнами.

Объединяет:
- UI компоненты и стили (UIComponents, StyleManager)
- Утилиты для работы с окнами (set_window_icon, bind_mousewheel, setup_window_resize_handler)
- Менеджер тем (ThemeManager)

ВНИМАНИЕ: Этот модуль теперь является оберткой для обратной совместимости.
Все классы и функции перенесены в ui/components/.
"""

# Импортируем все из новых модулей для обратной совместимости
from ui.components import (
    ToolTip,
    UIComponents,
    StyleManager,
    ThemeManager,
    load_image_icon,
    set_window_icon,
    bind_mousewheel,
    setup_window_resize_handler,
)

# Экспортируем для обратной совместимости
__all__ = [
    'ToolTip',
    'UIComponents',
    'StyleManager',
    'ThemeManager',
    'load_image_icon',
    'set_window_icon',
    'bind_mousewheel',
    'setup_window_resize_handler',
]

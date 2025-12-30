"""Модуль re-file операций.

Разбит на подмодули для лучшей организации кода:
- method_applier: Применение методов к файлам
- validator: Валидация файлов
- ui_updater: Обновление UI (теги, прогресс)
- undo_redo: Отмена и повтор операций
- re_file_starter: Запуск re-file операций
- re_file_completer: Завершение re-file операций

Примечание: Основной класс ReFileOperations находится в ui/re_file_operations.py
и импортируется напрямую оттуда.
"""

# Экспортируем только подмодули, основной класс ReFileOperations в ui/re_file_operations.py
from .method_applier import MethodApplier
from .ui_updater import UIUpdater
from .validator import FileValidator
from .undo_redo import UndoRedoManager
from .re_file_starter import ReFileStarter
from .re_file_completer import ReFileCompleter

__all__ = [
    'MethodApplier',
    'UIUpdater',
    'FileValidator',
    'UndoRedoManager',
    'ReFileStarter',
    'ReFileCompleter',
]


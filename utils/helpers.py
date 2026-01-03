"""Вспомогательные утилиты приложения.

Для обратной совместимости - импортирует классы из infrastructure/ и core/.
Все классы перенесены в соответствующие модули:
- NotificationManager -> infrastructure/system/notifications.py
- ErrorHandler -> core/error_handling/error_handler.py
- I18nManager -> infrastructure/system/i18n.py
- UpdateChecker -> infrastructure/system/updates.py
- Logger -> infrastructure/logging/logger.py
- StatisticsManager -> infrastructure/system/statistics.py
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Импорт из новых модулей для обратной совместимости
try:
    from infrastructure.system.notifications import NotificationManager
except ImportError:
    # Fallback если infrastructure еще не создан
    NotificationManager = None

try:
    # Используем основной ErrorHandler из core
    from core.error_handling import ErrorHandler
except ImportError:
    ErrorHandler = None

try:
    from infrastructure.system.i18n import I18nManager
except ImportError:
    I18nManager = None

try:
    from infrastructure.system.updates import UpdateChecker
except ImportError:
    UpdateChecker = None

try:
    from infrastructure.logging.logger import Logger
except ImportError:
    Logger = None

try:
    from infrastructure.system.statistics import StatisticsManager
except ImportError:
    StatisticsManager = None  # type: ignore

# Импорт функций валидации путей
try:
    from infrastructure.system.paths import (
        is_safe_path as is_safe_file_path,
        check_windows_path_length
    )
except ImportError:
    # Fallback
    import os
    import sys
    
    def is_safe_file_path(path: str, allowed_dirs: Optional[List[str]] = None) -> bool:  # type: ignore[misc]
        """Проверка безопасности пути к файлу (fallback)."""
        try:
            if not path or not isinstance(path, str) or not path.strip():
                return False
            if '..' in path or path.startswith('~'):
                return False
            abs_path = os.path.abspath(path)
            if not os.path.isfile(abs_path):
                return False
            if allowed_dirs:
                for allowed_dir in allowed_dirs:
                    if abs_path.startswith(os.path.abspath(allowed_dir)):
                        return True
                return False
            return True
        except (OSError, ValueError, TypeError, AttributeError):
            return False
        except (PermissionError, FileNotFoundError) as e:
            logger.debug(f"Ошибка доступа при проверке пути: {e}")
            return False
        except (MemoryError, RecursionError) as e:
            # Ошибки памяти/рекурсии
            pass
        # Финальный catch для неожиданных исключений (критично для стабильности)
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            logger.debug(f"Неожиданная ошибка при проверке пути: {e}")
            return False
    
    def check_windows_path_length(full_path: str) -> bool:  # type: ignore[misc]
        """Проверка длины пути для Windows (fallback)."""
        if sys.platform == 'win32':
            return len(full_path) <= 260 or full_path.startswith('\\\\?\\')
        return True


def validate_file_paths(paths: List[str], allowed_dirs: Optional[List[str]] = None) -> List[str]:
    """Валидация списка путей к файлам.
    
    Args:
        paths: Список путей к файлам
        allowed_dirs: Список разрешенных директорий (опционально)
        
    Returns:
        Список валидных и безопасных путей
    """
    valid_paths = []
    for path in paths:
        if is_safe_file_path(path, allowed_dirs):
            valid_paths.append(path)
        else:
            logger.warning(f"Небезопасный путь отклонен: {path}")
    return valid_paths

"""Утилиты приложения.

Содержит вспомогательные функции и утилиты для работы приложения.
"""

# Импорты из helpers
from utils.helpers import (
    NotificationManager,
    ErrorHandler,
    I18nManager,
    UpdateChecker,
    Logger,
    StatisticsManager,
    validate_file_paths,
    is_safe_file_path,
    check_windows_path_length
)

# Импорты из path_processing
from utils.path_processing import (
    process_file_argument,
    filter_cli_args
)

# Импорты из structured_logging
from utils.structured_logging import (
    StructuredFormatter,
    log_action,
    log_file_action,
    log_batch_action
)

__all__ = [
    # Из helpers
    'NotificationManager',
    'ErrorHandler',
    'I18nManager',
    'UpdateChecker',
    'Logger',
    'StatisticsManager',
    'validate_file_paths',
    'is_safe_file_path',
    'check_windows_path_length',
    # Из path_processing
    'process_file_argument',
    'filter_cli_args',
    'normalize_path',
    # Из structured_logging
    'StructuredFormatter',
    'log_action',
    'log_file_action',
    'log_batch_action',
]

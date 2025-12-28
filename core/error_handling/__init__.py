"""Централизованная система обработки ошибок."""

from core.error_handling.error_handler import ErrorHandler
from core.error_handling.error_types import ErrorType, AppError

__all__ = ['ErrorHandler', 'ErrorType', 'AppError']


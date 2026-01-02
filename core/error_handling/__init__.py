"""Централизованная система обработки ошибок."""

from .errors import ErrorHandler, ErrorType, AppError

__all__ = ['ErrorHandler', 'ErrorType', 'AppError']


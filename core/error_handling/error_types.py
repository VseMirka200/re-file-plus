"""Типы ошибок приложения."""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorType(Enum):
    """Типы ошибок приложения."""
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    INVALID_PATH = "invalid_path"
    INVALID_FILENAME = "invalid_filename"
    FILE_EXISTS = "file_exists"
    RACE_CONDITION = "race_condition"
    VALIDATION_ERROR = "validation_error"
    CONVERSION_ERROR = "conversion_error"
    NETWORK_ERROR = "network_error"
    UNKNOWN_ERROR = "unknown_error"


class AppError(Exception):
    """Базовый класс для ошибок приложения."""
    
    def __init__(
        self,
        error_type: ErrorType,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """Инициализация ошибки.
        
        Args:
            error_type: Тип ошибки
            message: Сообщение об ошибке
            details: Дополнительные детали
            original_error: Исходное исключение (если есть)
        """
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.details = details or {}
        self.original_error = original_error
    
    def __str__(self) -> str:
        return f"[{self.error_type.value}] {self.message}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование ошибки в словарь."""
        return {
            'type': self.error_type.value,
            'message': self.message,
            'details': self.details,
            'original_error': str(self.original_error) if self.original_error else None
        }


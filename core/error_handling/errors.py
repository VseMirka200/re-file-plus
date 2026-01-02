"""Обработка ошибок приложения.

Объединяет типы ошибок и обработчик ошибок.
"""

import logging
import traceback
from enum import Enum
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger(__name__)


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


class ErrorHandler:
    """Централизованный обработчик ошибок приложения."""
    
    def __init__(self):
        """Инициализация обработчика ошибок."""
        self._error_callbacks: Dict[ErrorType, list[Callable]] = {}
        self._default_callback: Optional[Callable] = None
    
    def register_callback(
        self,
        error_type: ErrorType,
        callback: Callable[[AppError], None]
    ) -> None:
        """Регистрация callback для определенного типа ошибки.
        
        Args:
            error_type: Тип ошибки
            callback: Функция обратного вызова
        """
        if error_type not in self._error_callbacks:
            self._error_callbacks[error_type] = []
        self._error_callbacks[error_type].append(callback)
    
    def register_default_callback(self, callback: Callable[[AppError], None]) -> None:
        """Регистрация callback по умолчанию для всех ошибок.
        
        Args:
            callback: Функция обратного вызова
        """
        self._default_callback = callback
    
    def handle_error(
        self,
        error: Exception,
        error_type: Optional[ErrorType] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AppError:
        """Обработка ошибки.
        
        Args:
            error: Исключение для обработки
            error_type: Тип ошибки (если None, определяется автоматически)
            context: Дополнительный контекст
            
        Returns:
            AppError: Обернутая ошибка приложения
        """
        # Определяем тип ошибки, если не указан
        if error_type is None:
            error_type = self._determine_error_type(error)
        
        # Создаем AppError
        app_error = AppError(
            error_type=error_type,
            message=str(error),
            details=context or {},
            original_error=error if not isinstance(error, AppError) else error.original_error
        )
        
        # Логируем ошибку
        logger.error(f"Ошибка [{error_type.value}]: {app_error.message}", exc_info=True)
        
        # Вызываем зарегистрированные callbacks
        if error_type in self._error_callbacks:
            for callback in self._error_callbacks[error_type]:
                try:
                    callback(app_error)
                except Exception as e:
                    logger.error(f"Ошибка в callback обработки ошибок: {e}", exc_info=True)
        
        # Вызываем callback по умолчанию, если есть
        if self._default_callback:
            try:
                self._default_callback(app_error)
            except Exception as e:
                logger.error(f"Ошибка в default callback: {e}", exc_info=True)
        
        return app_error
    
    def _determine_error_type(self, error: Exception) -> ErrorType:
        """Определение типа ошибки по исключению.
        
        Args:
            error: Исключение
            
        Returns:
            ErrorType: Тип ошибки
        """
        if isinstance(error, AppError):
            return error.error_type
        
        error_str = str(error).lower()
        error_type_str = type(error).__name__.lower()
        
        # Проверяем по типу исключения
        if isinstance(error, FileNotFoundError):
            return ErrorType.FILE_NOT_FOUND
        elif isinstance(error, PermissionError):
            return ErrorType.PERMISSION_DENIED
        elif isinstance(error, ValueError):
            if 'path' in error_str or 'путь' in error_str:
                return ErrorType.INVALID_PATH
            elif 'filename' in error_str or 'имя' in error_str or 'название' in error_str:
                return ErrorType.INVALID_FILENAME
            else:
                return ErrorType.VALIDATION_ERROR
        elif isinstance(error, FileExistsError):
            return ErrorType.FILE_EXISTS
        elif 'network' in error_type_str or 'connection' in error_type_str:
            return ErrorType.NETWORK_ERROR
        
        # Проверяем по сообщению об ошибке
        if 'not found' in error_str or 'не найден' in error_str:
            return ErrorType.FILE_NOT_FOUND
        elif 'permission' in error_str or 'доступ' in error_str:
            return ErrorType.PERMISSION_DENIED
        elif 'path' in error_str or 'путь' in error_str:
            return ErrorType.INVALID_PATH
        elif 'filename' in error_str or 'имя' in error_str:
            return ErrorType.INVALID_FILENAME
        elif 'exists' in error_str or 'существует' in error_str:
            return ErrorType.FILE_EXISTS
        
        return ErrorType.UNKNOWN_ERROR
    
    def get_error_summary(self, error: AppError) -> str:
        """Получение краткого описания ошибки.
        
        Args:
            error: Ошибка приложения
            
        Returns:
            Строка с кратким описанием
        """
        summary = f"{error.error_type.value}: {error.message}"
        if error.details:
            detail_str = ", ".join(f"{k}={v}" for k, v in error.details.items())
            summary += f" ({detail_str})"
        return summary


"""Централизованный обработчик ошибок."""

import logging
import traceback
from typing import Optional, Dict, Any, Callable

from core.error_handling.error_types import ErrorType, AppError

logger = logging.getLogger(__name__)


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
            error: Исключение
            error_type: Тип ошибки (определяется автоматически если не указан)
            context: Дополнительный контекст
            
        Returns:
            AppError объект
        """
        # Определяем тип ошибки если не указан
        if error_type is None:
            error_type = self._detect_error_type(error)
        
        # Создаем AppError
        app_error = AppError(
            error_type=error_type,
            message=str(error),
            details=context or {},
            original_error=error
        )
        
        # Логируем ошибку
        logger.error(
            f"Ошибка [{error_type.value}]: {app_error.message}",
            exc_info=error,
            extra={'error_details': app_error.to_dict()}
        )
        
        # Вызываем зарегистрированные callbacks
        if error_type in self._error_callbacks:
            for callback in self._error_callbacks[error_type]:
                try:
                    callback(app_error)
                except Exception as e:
                    logger.error(f"Ошибка в callback обработки ошибок: {e}", exc_info=True)
        
        # Вызываем callback по умолчанию
        if self._default_callback:
            try:
                self._default_callback(app_error)
            except Exception as e:
                logger.error(f"Ошибка в default callback: {e}", exc_info=True)
        
        return app_error
    
    def _detect_error_type(self, error: Exception) -> ErrorType:
        """Автоматическое определение типа ошибки.
        
        Args:
            error: Исключение
            
        Returns:
            Тип ошибки
        """
        error_name = type(error).__name__
        error_message = str(error).lower()
        
        if 'FileNotFoundError' in error_name or 'not found' in error_message:
            return ErrorType.FILE_NOT_FOUND
        elif 'PermissionError' in error_name or 'permission' in error_message:
            return ErrorType.PERMISSION_DENIED
        elif 'FileExistsError' in error_name or 'already exists' in error_message:
            return ErrorType.FILE_EXISTS
        elif 'race' in error_message or 'concurrent' in error_message:
            return ErrorType.RACE_CONDITION
        elif 'ValueError' in error_name or 'invalid' in error_message:
            return ErrorType.VALIDATION_ERROR
        else:
            return ErrorType.UNKNOWN_ERROR
    
    @staticmethod
    def get_error_suggestions(error_type: ErrorType) -> list[str]:
        """Получение предложений по исправлению ошибки.
        
        Args:
            error_type: Тип ошибки
            
        Returns:
            Список предложений
        """
        suggestions = {
            ErrorType.FILE_NOT_FOUND: [
                "Проверьте, что файл существует",
                "Убедитесь, что путь указан правильно"
            ],
            ErrorType.PERMISSION_DENIED: [
                "Проверьте права доступа к файлу",
                "Убедитесь, что файл не открыт в другой программе",
                "Попробуйте запустить программу от имени администратора"
            ],
            ErrorType.INVALID_PATH: [
                "Проверьте корректность пути",
                "Убедитесь, что путь не содержит недопустимых символов"
            ],
            ErrorType.INVALID_FILENAME: [
                "Проверьте, что имя файла не содержит недопустимых символов",
                "Убедитесь, что имя файла не зарезервировано в Windows"
            ],
            ErrorType.FILE_EXISTS: [
                "Файл с таким именем уже существует",
                "Выберите другое имя или удалите существующий файл"
            ],
            ErrorType.RACE_CONDITION: [
                "Файл был изменен другим процессом",
                "Попробуйте повторить операцию"
            ]
        }
        
        return suggestions.get(error_type, ["Попробуйте повторить операцию"])


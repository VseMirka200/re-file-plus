"""Сервис re-file операций."""

import logging
from pathlib import Path
from typing import List, Optional, Any

from core.domain.file_info import FileInfo, FileStatus
from core.domain.re_file_result import ReFileResult, ReFiledFile
from core.re_file_methods import ReFileMethod
from core.re_file_methods import validate_filename
from core.error_handling.error_handler import ErrorHandler
from core.error_handling.error_types import ErrorType, AppError

logger = logging.getLogger(__name__)


class ReFileService:
    """Сервис re-file операций.
    
    Унифицированная логика для CLI и GUI.
    """
    
    def __init__(
        self,
        metadata_extractor: Optional[Any] = None,
        backup_manager: Optional[Any] = None,
        error_handler: Optional[ErrorHandler] = None
    ) -> None:
        """Инициализация сервиса.
        
        Args:
            metadata_extractor: Экстрактор метаданных (опционально)
            backup_manager: Менеджер резервных копий (опционально)
            error_handler: Обработчик ошибок (опционально)
        """
        self.metadata_extractor = metadata_extractor
        self.backup_manager = backup_manager
        self.error_handler = error_handler or ErrorHandler()
    
    def re_file_files(
        self,
        files: List[FileInfo],
        methods: List[ReFileMethod],
        dry_run: bool = False
    ) -> ReFileResult:
        """Re-file операции с файлами.
        
        Args:
            files: Список файлов для re-file операций
            methods: Список методов re-file
            dry_run: Только предпросмотр без выполнения операций
            
        Returns:
            Результат re-file операций
        """
        result = ReFileResult()
        
        # Проверка конфликтов имен в рамках одной re-file операции
        # Собираем все новые имена для проверки конфликтов
        new_names_map = {}  # new_full_name -> list of files
        for file in files:
            try:
                # Начинаем с исходного имени
                new_name = file.old_name
                new_ext = file.extension
                
                # Применяем методы re-file
                for method in methods:
                    new_name, new_ext = method.apply(
                        new_name, new_ext, str(file.path)
                    )
                
                # Обновляем файл
                file.new_name = new_name
                file.extension = new_ext
                
                # Валидация
                validation_status = validate_filename(
                    new_name, new_ext, str(file.path), 0
                )
                
                if validation_status != 'Готов':
                    file.set_error(validation_status)
                    result.add_error(file, validation_status)
                    continue
                
                # Проверяем, изменилось ли имя
                if not file.is_renamed():
                    # Имя не изменилось, пропускаем
                    continue
                
                # Добавляем в карту для проверки конфликтов
                new_full_name = file.new_full_name
                if new_full_name not in new_names_map:
                    new_names_map[new_full_name] = []
                new_names_map[new_full_name].append(file)
                
            except (ValueError, TypeError, AttributeError) as e:
                # Ошибки данных или доступа к атрибутам
                error_msg = f"Ошибка обработки файла: {str(e)}"
                file.set_error(error_msg)
                result.add_error(file, error_msg)
                logger.error(f"Ошибка обработки файла {file.path}: {e}", exc_info=True)
            except (OSError, PermissionError) as e:
                # Ошибки файловой системы
                error_msg = f"Ошибка доступа к файлу: {str(e)}"
                file.set_error(error_msg)
                result.add_error(file, error_msg)
                logger.error(f"Ошибка доступа к файлу {file.path}: {e}", exc_info=True)
            except Exception as e:
                # Неожиданные ошибки
                error_msg = f"Неожиданная ошибка обработки файла: {str(e)}"
                file.set_error(error_msg)
                result.add_error(file, error_msg)
                logger.error(f"Неожиданная ошибка обработки файла {file.path}: {e}", exc_info=True)
        
        # Проверяем конфликты имен
        for new_full_name, conflicting_files in new_names_map.items():
            if len(conflicting_files) > 1:
                # Найдены конфликты - несколько файлов переименовываются в одно имя
                error_msg = f"Конфликт: {len(conflicting_files)} файла переименовываются в '{new_full_name}'"
                for file in conflicting_files:
                    file.set_error(error_msg)
                    result.add_error(file, error_msg)
                logger.warning(error_msg)
                continue
        
        # Выполняем re-file операции
        if not dry_run:
            for file in files:
                # Пропускаем файлы с ошибками
                if file.status != FileStatus.READY and file.status != FileStatus.PENDING:
                    continue
                
                if not file.is_renamed():
                    continue
                
                try:
                    new_path = file.new_path
                    
                    # Атомарная проверка и re-file операция
                    # Используем try-except для обработки race condition
                    try:
                        # Проверяем существование исходного файла
                        if not file.path.exists():
                            app_error = AppError(
                                ErrorType.FILE_NOT_FOUND,
                                f"Исходный файл не найден: {file.path}",
                                {'file_path': str(file.path)}
                            )
                            self.error_handler.handle_error(app_error)
                            file.set_error(app_error.message)
                            result.add_error(file, app_error.message)
                            continue
                        
                        # Создаем резервную копию, если нужно
                        if self.backup_manager:
                            try:
                                self.backup_manager.create_backup(str(file.path))
                            except Exception as e:
                                app_error = AppError(
                                    ErrorType.PERMISSION_DENIED,
                                    f"Не удалось создать резервную копию: {e}",
                                    {'file_path': str(file.path)},
                                    original_error=e
                                )
                                self.error_handler.handle_error(app_error)
                        
                        # Выполняем re-file операции (атомарная операция)
                        # os.rename/path.rename атомарны и сами проверят существование
                        # Это уменьшает вероятность race condition
                        # Если файл уже существует, это вызовет FileExistsError
                        try:
                            file.path.rename(new_path)
                        except FileExistsError:
                            # Файл уже существует (возможна race condition)
                            app_error = AppError(
                                ErrorType.FILE_EXISTS,
                                f"Файл '{file.new_full_name}' уже существует",
                                {'new_path': str(new_path)}
                            )
                            self.error_handler.handle_error(app_error)
                            file.set_error(app_error.message)
                            result.add_error(file, app_error.message)
                            continue
                        file.path = new_path
                        file.set_ready()
                        
                        result.add_success(file, str(new_path))
                        
                    except FileExistsError as e:
                        # Race condition: файл был создан между проверкой и re-file операцией
                        app_error = AppError(
                            ErrorType.RACE_CONDITION,
                            f"Файл '{file.new_full_name}' уже существует (race condition)",
                            {'old_path': str(file.path), 'new_path': str(new_path)},
                            original_error=e
                        )
                        self.error_handler.handle_error(app_error)
                        file.set_error(app_error.message)
                        result.add_error(file, app_error.message)
                    except (OSError, PermissionError) as e:
                        # Другие ошибки файловой системы
                        error_type = ErrorType.PERMISSION_DENIED if isinstance(e, PermissionError) else ErrorType.UNKNOWN_ERROR
                        app_error = AppError(
                            error_type,
                            f"Ошибка переименования: {str(e)}",
                            {'old_path': str(file.path), 'new_path': str(new_path)},
                            original_error=e
                        )
                        self.error_handler.handle_error(app_error)
                        file.set_error(app_error.message)
                        result.add_error(file, app_error.message)
                        
                except Exception as e:
                    app_error = AppError(
                        ErrorType.UNKNOWN_ERROR,
                        f"Неожиданная ошибка: {str(e)}",
                        {'file_path': str(file.path)},
                        original_error=e
                    )
                    self.error_handler.handle_error(app_error)
                    file.set_error(app_error.message)
                    result.add_error(file, app_error.message)
        else:
            # Только предпросмотр
            for file in files:
                if file.is_renamed():
                    result.add_success(file, str(file.new_path), preview=True)
                    file.set_ready()
        
        return result


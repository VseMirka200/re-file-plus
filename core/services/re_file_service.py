"""Сервис re-file операций."""

import logging
from pathlib import Path
from typing import List, Optional, Any, TYPE_CHECKING

from core.domain.file_info import FileInfo, FileStatus
from core.domain.re_file_result import ReFileResult, ReFiledFile
from core.re_file_methods import ReFileMethod
from core.re_file_methods import validate_filename
from core.error_handling.errors import ErrorHandler, ErrorType, AppError

if TYPE_CHECKING:
    from core.metadata.extractor import MetadataExtractor

logger = logging.getLogger(__name__)


class ReFileService:
    """Сервис re-file операций.
    
    Унифицированная логика для CLI и GUI.
    """
    
    def __init__(
        self,
        metadata_extractor: Optional['MetadataExtractor'] = None,
        error_handler: Optional[ErrorHandler] = None
    ) -> None:
        """Инициализация сервиса.
        
        Args:
            metadata_extractor: Экстрактор метаданных (опционально)
            error_handler: Обработчик ошибок (опционально)
        """
        self.metadata_extractor = metadata_extractor
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
        if logger.isEnabledFor(logging.INFO):
            logger.info(
                f"Начало re-file операций: файлов={len(files)}, методов={len(methods)}, dry_run={dry_run}",
                extra={'action': 'RE_FILE_STARTED', 'file_count': len(files), 'method_count': len(methods), 'dry_run': dry_run}
            )
        result = ReFileResult()
        
        # Проверка конфликтов имен в рамках одной re-file операции
        # Собираем все новые имена для проверки конфликтов перед выполнением операций
        # Это позволяет обнаружить проблемы заранее и не выполнять частичные переименования
        new_names_map = {}  # new_full_name -> list of files (для обнаружения конфликтов)
        for file in files:
            try:
                # Начинаем с исходного имени файла
                new_name = file.old_name
                new_ext = file.extension
                
                # Применяем методы re-file последовательно
                # Каждый метод получает результат предыдущего и возвращает новое имя
                for method in methods:
                    new_name, new_ext = method.apply(
                        new_name, new_ext, str(file.path)
                    )
                
                # Обновляем файл с новым именем и расширением
                file.new_name = new_name
                file.extension = new_ext
                
                # Валидация нового имени: проверяем на недопустимые символы,
                # длину пути, зарезервированные имена Windows и т.д.
                validation_status = validate_filename(
                    new_name, new_ext, str(file.path), 0
                )
                
                if validation_status != 'Готов':
                    # Имя не прошло валидацию - помечаем ошибку и пропускаем файл
                    file.set_error(validation_status)
                    result.add_error(file, validation_status)
                    continue
                
                # Проверяем, изменилось ли имя вообще
                # Если имя не изменилось, нет смысла выполнять переименование
                if not file.is_renamed():
                    # Имя не изменилось, пропускаем (не добавляем в карту конфликтов)
                    continue
                
                # Добавляем в карту для проверки конфликтов
                # Если несколько файлов получают одно и то же имя, это конфликт
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
            except (KeyError, IndexError) as e:
                # Ошибки доступа к данным
                error_msg = f"Ошибка доступа к данным файла: {str(e)}"
                file.set_error(error_msg)
                result.add_error(file, error_msg)
                logger.error(f"Ошибка доступа к данным файла {file.path}: {e}", exc_info=True)
            except (MemoryError, RecursionError) as e:
                # Ошибки памяти/рекурсии
                error_msg = f"Ошибка памяти/рекурсии при обработке файла: {str(e)}"
                file.set_error(error_msg)
                result.add_error(file, error_msg)
                logger.error(f"Ошибка памяти/рекурсии при обработке файла {file.path}: {e}", exc_info=True)
            except (MemoryError, RecursionError) as e:

                # Ошибки памяти/рекурсии

                pass

            # Финальный catch для неожиданных исключений (критично для стабильности)

            except BaseException as e:

                if isinstance(e, (KeyboardInterrupt, SystemExit)):

                    raise
                # Неожиданные ошибки
                error_msg = f"Неожиданная ошибка обработки файла: {str(e)}"
                file.set_error(error_msg)
                result.add_error(file, error_msg)
                logger.error(f"Неожиданная ошибка обработки файла {file.path}: {e}", exc_info=True)
        
        # Проверяем конфликты имен: если несколько файлов получают одно и то же имя,
        # это проблема, так как нельзя иметь два файла с одинаковым именем в одной папке
        for new_full_name, conflicting_files in new_names_map.items():
            if len(conflicting_files) > 1:
                # Найдены конфликты - несколько файлов переименовываются в одно имя
                # Помечаем все конфликтующие файлы ошибкой, чтобы пользователь мог исправить
                error_msg = f"Конфликт: {len(conflicting_files)} файла переименовываются в '{new_full_name}'"
                for file in conflicting_files:
                    file.set_error(error_msg)
                    result.add_error(file, error_msg)
                logger.warning(error_msg)
                continue  # Пропускаем конфликтующие файлы, не выполняем переименование
        
        # Выполняем re-file операции
        # Оптимизация: обрабатываем файлы батчами для лучшей производительности
        # Батчинг позволяет:
        # 1. Уменьшить количество операций ввода-вывода
        # 2. Лучше контролировать использование памяти
        # 3. Показывать прогресс пользователю более плавно
        if not dry_run:
            # Разбиваем на батчи для обработки (по 100 файлов за раз)
            # Размер батча выбран эмпирически как баланс между производительностью
            # и отзывчивостью UI
            BATCH_SIZE = 100
            files_to_process = [f for f in files if f.is_renamed() and (f.status == FileStatus.READY or f.status == FileStatus.PENDING)]
            total_files = len(files_to_process)
            
            if logger.isEnabledFor(logging.INFO) and total_files > BATCH_SIZE:
                logger.info(f"Обработка {total_files} файлов батчами по {BATCH_SIZE}")
            
            processed_count = 0
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
                        
                        # Выполняем re-file операции (атомарная операция)
                        # os.rename/path.rename атомарны и сами проверят существование
                        # Это уменьшает вероятность race condition
                        # Если файл уже существует, это вызовет FileExistsError
                        try:
                        # Выполняем атомарное переименование
                        # path.rename() - атомарная операция на уровне ОС, которая либо
                        # выполняется полностью, либо не выполняется вообще
                        # Это предотвращает ситуации, когда файл частично переименован
                        file.path.rename(new_path)
                        # Логируем успешное переименование для отладки и аудита
                        if logger.isEnabledFor(logging.INFO):
                            logger.info(
                                f"Файл успешно переименован: {file.old_full_name} -> {file.new_full_name}",
                                extra={'action': 'FILE_RENAMED'}
                            )
                        except FileExistsError:
                            # Файл уже существует (возможна race condition)
                            # Это может произойти, если другой процесс создал файл с таким же именем
                            # между проверкой и переименованием
                            app_error = AppError(
                                ErrorType.FILE_EXISTS,
                                f"Файл '{file.new_full_name}' уже существует",
                                {'new_path': str(new_path)}
                            )
                            self.error_handler.handle_error(app_error)
                            file.set_error(app_error.message)
                            result.add_error(file, app_error.message)
                            continue
                        # Обновляем путь файла на новый (после успешного переименования)
                        file.path = new_path
                        # Устанавливаем статус "готов" - файл успешно переименован
                        file.set_ready()
                        
                        # Добавляем в результат успешных операций
                        result.add_success(file, str(new_path))
                        processed_count += 1
                        
                        # Логируем прогресс для больших батчей
                        # Это помогает отслеживать прогресс при обработке тысяч файлов
                        if logger.isEnabledFor(logging.DEBUG) and total_files > BATCH_SIZE:
                            if processed_count % BATCH_SIZE == 0:
                                logger.debug(f"Обработано {processed_count}/{total_files} файлов")
                        
                    except FileExistsError as e:
                        # Race condition: файл был создан между проверкой и re-file операцией
                        # Это редкая ситуация, но возможная в многопоточной среде или
                        # при параллельной работе нескольких процессов
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
                        
                except (ValueError, TypeError, AttributeError) as e:
                    app_error = AppError(
                        ErrorType.VALIDATION_ERROR,
                        f"Ошибка валидации: {str(e)}",
                        {'file_path': str(file.path)},
                        original_error=e
                    )
                    self.error_handler.handle_error(app_error)
                    file.set_error(app_error.message)
                    result.add_error(file, app_error.message)
                except (KeyboardInterrupt, SystemExit):
                    # Не перехватываем системные исключения
                    raise
                except (RuntimeError, AttributeError) as e:
                    # Ошибки выполнения или доступа к атрибутам
                    logger.error(f"Ошибка выполнения при переименовании файла: {e}", exc_info=True)
                    app_error = AppError(
                        ErrorType.UNKNOWN_ERROR,
                        f"Ошибка выполнения: {str(e)}",
                        {'old_path': str(file.path), 'new_path': str(new_path)},
                        original_error=e
                    )
                    self.error_handler.handle_error(app_error)
                    file.set_error(app_error.message)
                    result.add_error(file, app_error.message)
                except (ValueError, TypeError, KeyError, IndexError) as e:
                    # Ошибки данных при обработке ошибки
                    logger.error(f"Ошибка данных при обработке ошибки переименования: {e}", exc_info=True)
                except (MemoryError, RecursionError) as e:
                    # Ошибки памяти/рекурсии
                    pass
                # Финальный catch для неожиданных исключений (критично для стабильности)

                except BaseException as e:

                    if isinstance(e, (KeyboardInterrupt, SystemExit)):

                        raise
                    # Логируем неожиданные исключения
                    logger.error(f"Неожиданная ошибка при переименовании файла: {e}", exc_info=True)
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
        
        if logger.isEnabledFor(logging.INFO):
            logger.info(
                f"Завершение re-file операций: успешно={len(result.success_files)}, ошибок={len(result.error_files)}",
                extra={'action': 'RE_FILE_COMPLETED', 'success_count': len(result.success_files), 'error_count': len(result.error_files)}
            )
        
        return result


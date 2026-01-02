"""Модуль для re-file операций.

Обеспечивает выполнение re-file операций с поддержкой:
- Применения методов re-file к файлам
- Валидации имен файлов
- Отмены/повтора операций
- Прогресса выполнения
- Обработки ошибок
- Структурированного логирования
"""

# Стандартная библиотека
import logging
import os
import threading
from typing import Dict, List, Optional

# Локальные импорты
from core.re_file_methods import (
    NewNameMethod,
    NumberingMethod,
    check_conflicts,
    validate_filename,
)

logger = logging.getLogger(__name__)

# Импорт структурированного логирования
try:
    from utils.logging_utils import log_action, log_file_action, log_batch_action
except ImportError:
    # Fallback если модуль недоступен
    def log_action(logger, level, action, message, **kwargs):
        logger.log(level, f"[{action}] {message}")
    def log_file_action(logger, action, message, **kwargs):
        logger.info(f"[{action}] {message}")
    def log_batch_action(logger, action, message, file_count, **kwargs):
        logger.info(f"[{action}] {message} (файлов: {file_count})")


class ReFileOperations:
    """Класс для управления re-file операциями.
    
    Координирует процесс re-file операций, включая валидацию,
    применение методов и обработку результатов.
    """
    
    def __init__(self, app) -> None:
        """Инициализация re-file операций.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
        
        # Инициализируем подмодули
        from ui.operations.method_applier import MethodApplier
        from ui.operations.ui_updater import UIUpdater
        from ui.operations.validator import FileValidator
        from ui.operations.undo_redo import UndoRedoManager
        from ui.operations.re_file_starter import ReFileStarter
        from ui.operations.re_file_completer import ReFileCompleter
        
        self.method_applier = MethodApplier(app)
        self.ui_updater = UIUpdater(app)
        self.validator = FileValidator(app)
        self.undo_redo = UndoRedoManager(app)
        self.re_file_starter = ReFileStarter(app, self)
        self.re_file_completer = ReFileCompleter(app)
    
    def apply_to_selected(self):
        """Применение методов только к выбранным файлам"""
        self.method_applier.apply_to_selected()
    
    def apply_methods(self):
        """Применение всех методов к файлам (асинхронно, не блокирует UI)"""
        logger.info("Вызов apply_methods")
        
        # Убеждаемся, что флаг re-file операции сброшен перед применением методов
        # (на случай, если он остался установленным после предыдущей операции)
        if hasattr(self.app, '_re_file_in_progress') and self.app._re_file_in_progress:
            logger.info("Сбрасываем зависший флаг _re_file_in_progress перед применением методов")
            self.app._re_file_in_progress = False
            if hasattr(self.app, '_re_file_start_time'):
                delattr(self.app, '_re_file_start_time')
        
        if not self.app.files:
            logger.warning("Попытка применения методов при отсутствии файлов")
            return
        
        methods = self.app.methods_manager.get_methods()
        if not methods:
            logger.warning("Попытка применения методов при отсутствии методов")
            return
        
        # Защита от повторного вызова
        if hasattr(self.app, '_applying_methods') and self.app._applying_methods:
            logger.warning("Применение методов уже выполняется, пропускаем")
            return
        
        logger.info(f"Начинаем применение методов. Файлов: {len(self.app.files)}, методов: {len(methods)}")
        self.app._applying_methods = True
        
        # Определяем имена методов для логирования
        method_names = [type(m).__name__ for m in methods]
        
        # Запускаем в отдельном потоке
        def apply_methods_worker():
            try:
                self.method_applier.apply_methods_worker(methods, method_names)
            except (OSError, PermissionError, ValueError) as e:
                # Ошибки файловой системы
                error_msg = f"Ошибка файловой системы: {str(e)}"
                # Используем ErrorHandler если доступен
                if hasattr(self.app, 'error_handler') and self.app.error_handler:
                    try:
                        from core.error_handling.errors import ErrorType
                        self.app.error_handler.handle_error(
                            e,
                            error_type=ErrorType.PERMISSION_DENIED if isinstance(e, PermissionError) else ErrorType.INVALID_PATH,
                            context={'operation': 'apply_methods', 'methods': method_names}
                        )
                    except Exception:
                        pass  # Если ErrorHandler недоступен, продолжаем без него
                logger.error(f"Ошибка в потоке применения методов: {error_msg}", exc_info=True)
                self.app.root.after(0, lambda: self._apply_methods_error(error_msg))
            except (AttributeError, TypeError) as e:
                # Ошибки доступа к атрибутам
                error_msg = f"Ошибка доступа к данным: {str(e)}"
                # Используем ErrorHandler если доступен
                if hasattr(self.app, 'error_handler') and self.app.error_handler:
                    try:
                        from core.error_handling.errors import ErrorType
                        self.app.error_handler.handle_error(
                            e,
                            error_type=ErrorType.VALIDATION_ERROR,
                            context={'operation': 'apply_methods', 'methods': method_names}
                        )
                    except Exception:
                        pass  # Если ErrorHandler недоступен, продолжаем без него
                logger.error(f"Ошибка в потоке применения методов: {error_msg}", exc_info=True)
                self.app.root.after(0, lambda: self._apply_methods_error(error_msg))
            except Exception as e:
                # Неожиданные ошибки
                error_msg = f"Неожиданная ошибка: {str(e)}"
                # Используем ErrorHandler если доступен
                if hasattr(self.app, 'error_handler') and self.app.error_handler:
                    try:
                        from core.error_handling.errors import ErrorType
                        self.app.error_handler.handle_error(
                            e,
                            error_type=ErrorType.UNKNOWN_ERROR,
                            context={'operation': 'apply_methods', 'methods': method_names}
                        )
                    except Exception:
                        pass  # Если ErrorHandler недоступен, продолжаем без него
                logger.error(f"Неожиданная ошибка в потоке применения методов: {error_msg}", exc_info=True)
                self.app.root.after(0, lambda: self._apply_methods_error(error_msg))
            finally:
                self.app._applying_methods = False
        
        # Запускаем в отдельном потоке через threading (безопаснее для GUI)
        import threading
        thread = threading.Thread(target=apply_methods_worker, daemon=True, name="apply_methods")
        thread.start()
    
    def _set_file_in_progress(self, file_path: str):
        """Установка желтого тега 'в работе' для файла в treeview."""
        self.ui_updater.set_file_in_progress(file_path)
    
    def _set_file_ready(self, file_path: str):
        """Установка зеленого тега 'готово' для файла в treeview."""
        self.ui_updater.set_file_ready(file_path)
    
    def _set_file_error(self, file_path: str):
        """Установка красного тега 'ошибка' для файла в treeview."""
        self.ui_updater.set_file_error(file_path)
    
    def _update_progress_ui(self, current: int, total: int, applied: int, errors: int, filename: str = None):
        """Обновление UI прогресса."""
        self.ui_updater.update_progress_ui(current, total, applied, errors, filename)
    
    def _apply_methods_complete(self, applied_count: int, error_count: int, method_names: list):
        """Завершение применения методов (вызывается из главного потока)."""
        log_batch_action(
            logger=logger,
            action='METHODS_APPLY_COMPLETED',
            message=f"Применение методов завершено",
            file_count=len(self.app.files),
            success_count=applied_count,
            error_count=error_count,
            method_name='apply_methods',
            details={'methods': method_names}
        )
        
        # Принудительное обновление интерфейса
        # Обновляем таблицу несколько раз для надежности
        logger.debug(f"Обновление интерфейса после применения методов. Файлов: {len(self.app.files)}")
        # Проверяем, что new_name установлен для всех файлов
        for i, file_data in enumerate(self.app.files[:3]):  # Проверяем первые 3 файла
            logger.debug(
                f"Файл {i}: old_name={file_data.get('old_name')}, "
                f"new_name={file_data.get('new_name')}, "
                f"has_new_name={'new_name' in file_data}"
            )
        
        # Сбрасываем флаг применения методов
        self.app._applying_methods = False
        
        # Убеждаемся, что флаг re-file операции тоже сброшен
        # (на случай, если он был установлен ранее и не сбросился)
        if hasattr(self.app, '_re_file_in_progress') and self.app._re_file_in_progress:
            logger.warning("Флаг _re_file_in_progress был установлен после применения методов - сбрасываем")
            self.app._re_file_in_progress = False
            if hasattr(self.app, '_re_file_start_time'):
                delattr(self.app, '_re_file_start_time')
        
        self.app.refresh_treeview()
        # Дополнительное обновление через небольшую задержку
        self.app.root.after(50, self.app.refresh_treeview)
        self.app.root.after(100, self.app.refresh_treeview)
        
        self.app.log(
            f"Методы применены к {len(self.app.files)} файлам "
            f"(успешно: {applied_count}, ошибок: {error_count})"
        )
        
        # Сбрасываем прогресс
        if hasattr(self.app, 'progress'):
            self.app.progress['value'] = 0
    
    def _apply_methods_error(self, error_msg: str):
        """Обработка ошибки применения методов (вызывается из главного потока)."""
        # Сбрасываем флаг применения методов при ошибке
        self.app._applying_methods = False
        
        # Убеждаемся, что флаг re-file операции тоже сброшен
        if hasattr(self.app, '_re_file_in_progress') and self.app._re_file_in_progress:
            logger.warning("Флаг _re_file_in_progress был установлен при ошибке применения методов - сбрасываем")
            self.app._re_file_in_progress = False
            if hasattr(self.app, '_re_file_start_time'):
                delattr(self.app, '_re_file_start_time')
        
        logger.error(f"Ошибка применения методов: {error_msg}")
        self.app.log(f"Ошибка применения методов: {error_msg}")
        self.app.refresh_treeview()
    
    def validate_all_files(self):
        """Валидация всех готовых файлов перед переименованием.
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, errors) - валидны ли все файлы и список ошибок
        """
        # Используем валидатор, но добавляем проверку конфликтов
        is_valid, errors = self.validator.validate_all_files()
        
        # Дополнительная проверка на конфликты имен
        ready_files = [f for f in self.app.files if f.get('status') == 'Готов']
        name_counts = {}
        for file_data in ready_files:
            new_name = None
            extension = None
            if hasattr(file_data, 'new_name'):
                new_name = file_data.new_name
                extension = file_data.extension
            elif isinstance(file_data, dict):
                new_name = file_data.get('new_name', '')
                extension = file_data.get('extension', '')
            
            if new_name is not None and extension is not None:
                full_name = new_name + extension
                if full_name not in name_counts:
                    name_counts[full_name] = []
                name_counts[full_name].append(file_data)
        
        for full_name, file_list in name_counts.items():
            if len(file_list) > 1:
                file_paths = []
                for f in file_list:
                    if hasattr(f, 'full_path'):
                        file_paths.append(os.path.basename(f.full_path))
                    elif isinstance(f, dict):
                        file_paths.append(os.path.basename(f.get('path') or f.get('full_path', '')))
                errors.append(f"Конфликт имен: {full_name} ({len(file_list)} файлов: {', '.join(file_paths[:3])})")
                is_valid = False
        
        return is_valid, errors
    
    def start_re_file(self):
        """Начало процесса re-file операций"""
        self.re_file_starter.start_re_file()
    
    def re_file_complete(self, success: int, error: int, re_filed_files: list = None):
        """Обработка завершения re-file операций.
        
        Args:
            success: Количество успешных операций
            error: Количество ошибок
            re_filed_files: Список файлов после re-file операций
        """
        self.re_file_completer.re_file_complete(success, error, re_filed_files)
    
    def undo_re_file(self):
        """Отмена последней re-file операции."""
        self.undo_redo.undo_re_file()
    
    def redo_re_file(self):
        """Повтор последней отмененной операции переименования."""
        self.undo_redo.redo_re_file()

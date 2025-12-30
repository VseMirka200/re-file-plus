"""Модуль для запуска re-file операций.

Содержит логику начала процесса переименования файлов,
включая валидацию, подтверждение и запуск в отдельном потоке.
"""

# Стандартная библиотека
import logging
import threading
import time
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional

# Локальные импорты
from core.re_file_methods import re_file_files_thread

logger = logging.getLogger(__name__)

# Импорт структурированного логирования
try:
    from utils.structured_logging import log_action
except ImportError:
    # Fallback если модуль недоступен
    def log_action(logger, level, action, message, **kwargs):
        logger.log(level, f"[{action}] {message}")


class ReFileStarter:
    """Класс для запуска re-file операций.
    
    Управляет процессом начала переименования файлов, включая:
    - Проверку флагов и защиту от повторного вызова
    - Валидацию файлов
    - Подтверждение операции
    - Запуск переименования в отдельном потоке
    """
    
    def __init__(self, app, re_file_operations):
        """Инициализация запуска re-file операций.
        
        Args:
            app: Экземпляр главного приложения
            re_file_operations: Экземпляр ReFileOperations для доступа к методам
        """
        self.app = app
        self.re_file_operations = re_file_operations
    
    def start_re_file(self):
        """Начало процесса re-file операций"""
        # Инициализируем флаг, если он еще не установлен
        if not hasattr(self.app, '_re_file_in_progress'):
            self.app._re_file_in_progress = False
        
        # Защита от повторного вызова - если операция уже выполняется, блокируем новый запуск
        if self.app._re_file_in_progress:
            if hasattr(self.app, '_re_file_start_time'):
                elapsed = time.time() - self.app._re_file_start_time
                if elapsed > 10:
                    logger.error(f"Операция переименования зависла более чем на {elapsed:.1f} секунд")
            else:
                # Принудительно сбрасываем флаг, если нет времени начала
                self.app._re_file_in_progress = False
            return
        
        log_action(
            logger=logger,
            level=logging.INFO,
            action='RE_FILE_STARTED',
            message="Начало процесса re-file операций",
            method_name='start_re_file',
            file_count=len(self.app.files)
        )
        self.app._re_file_in_progress = True
        # Сохраняем время начала для защиты от зависших операций
        self.app._re_file_start_time = time.time()
        
        if not self.app.files:
            log_action(
                logger=logger,
                level=logging.WARNING,
                action='RE_FILE_FAILED',
                message="Попытка re-file операции при отсутствии файлов",
                method_name='start_re_file',
                details={'reason': 'no_files'}
            )
            messagebox.showwarning("Предупреждение", "Нет файлов для переименования")
            self.app._re_file_in_progress = False
            return
        
        # Подсчет готовых файлов
        # Функция для проверки, готов ли файл к переименованию
        def is_file_ready(file_data):
            """Проверка, готов ли файл к переименованию."""
            # Проверяем статус
            status_ready = False
            status_value = None
            if hasattr(file_data, 'status'):
                # Объект FileInfo
                from core.domain.file_info import FileStatus
                status_value = file_data.status
                if isinstance(file_data.status, FileStatus):
                    status_ready = file_data.status == FileStatus.READY
                elif isinstance(file_data.status, str):
                    status_ready = file_data.status == 'Готов' or file_data.status == FileStatus.READY.value
            elif isinstance(file_data, dict):
                # Словарь
                status = file_data.get('status', '')
                status_value = status
                if isinstance(status, str):
                    status_ready = status == 'Готов'
                # Может быть FileStatus enum
                from core.domain.file_info import FileStatus
                if isinstance(status, FileStatus):
                    status_ready = status == FileStatus.READY
            
            if not status_ready:
                logger.debug(f"Файл не готов: статус={status_value}, ожидается 'Готов' или FileStatus.READY")
                return False
            
            # Проверяем, что имя изменилось (есть new_name и оно отличается от old_name)
            if hasattr(file_data, 'new_name') and hasattr(file_data, 'old_name'):
                new_name = file_data.new_name or ''
                old_name = file_data.old_name or ''
                # Имя должно измениться (расширение обычно не меняется при переименовании)
                name_changed = new_name != old_name
                if not name_changed:
                    logger.debug(f"Файл не готов: имя не изменилось, old_name={old_name}, new_name={new_name}")
                return name_changed
            elif isinstance(file_data, dict):
                new_name = file_data.get('new_name', '') or ''
                old_name = file_data.get('old_name', '') or ''
                # Имя должно измениться
                name_changed = new_name != old_name
                if not name_changed:
                    logger.debug(f"Файл не готов (dict): имя не изменилось, old_name={old_name}, new_name={new_name}")
                return name_changed
            
            logger.debug(f"Файл не готов: нет атрибутов new_name или old_name")
            return False
        
        ready_files = [f for f in self.app.files if is_file_ready(f)]
        
        if not ready_files:
            # Проверяем, может быть нужно сначала применить методы
            has_methods = hasattr(self.app, 'methods_manager') and self.app.methods_manager.get_methods()
            if has_methods:
                message = "Нет файлов готовых к переименованию.\n\nВозможно, нужно сначала применить методы переименования (кнопка 'Применить')."
            else:
                message = "Нет файлов готовых к переименованию.\n\nДобавьте методы переименования и примените их к файлам."
            messagebox.showwarning("Предупреждение", message)
            self.app._re_file_in_progress = False
            if hasattr(self.app, '_re_file_start_time'):
                delattr(self.app, '_re_file_start_time')
            return
        
        # Валидация всех файлов перед переименованием
        is_valid, errors = self.re_file_operations.validate_all_files()
        
        # Формируем сообщение подтверждения
        confirm_msg = f"Вы собираетесь переименовать {len(ready_files)} файлов."
        
        if not is_valid:
            error_msg = "Обнаружены ошибки валидации:\n\n" + "\n".join(errors[:10])
            if len(errors) > 10:
                error_msg += f"\n... и еще {len(errors) - 10} ошибок"
            confirm_msg = f"{error_msg}\n\n{confirm_msg}\n\nПродолжить переименование несмотря на ошибки?"
            title = "Ошибки валидации"
        else:
            confirm_msg += "\n\nВыполнить?"
            title = "Подтверждение"
        
        # Единое подтверждение
        if not messagebox.askyesno(title, confirm_msg):
            self.app._re_file_in_progress = False
            return
        
        # Сохранение состояния для отмены
        undo_state = [f.copy() for f in self.app.files]
        self.app.undo_stack.append(undo_state)
        # Очищаем redo стек при новой операции
        self.app.redo_stack.clear()
        
        # Сброс флага отмены
        if not hasattr(self.app, 'cancel_re_file_var') or not self.app.cancel_re_file_var:
            self.app.cancel_re_file_var = tk.BooleanVar(value=False)
        else:
            self.app.cancel_re_file_var.set(False)
        
        # Запуск переименования в отдельном потоке
        # Создаем событие для отмены
        try:
            cancel_event = threading.Event()
        except Exception as e:
            logger.error(f"Ошибка при создании события отмены: {e}", exc_info=True)
            self.app._re_file_in_progress = False
            if hasattr(self.app, '_re_file_start_time'):
                delattr(self.app, '_re_file_start_time')
            return
        
        # Функция обновления прогресса
        def update_progress(current, total, filename):
            if hasattr(self.app, 'progress_window') and self.app.progress_window:
                try:
                    self.app.progress_window['value'] = current
                    self.app.progress_window['maximum'] = total
                except (AttributeError, tk.TclError):
                    pass
            if hasattr(self.app, 'current_file_label') and self.app.current_file_label:
                try:
                    self.app.current_file_label.config(
                        text=f"Обрабатывается: {filename} ({current}/{total})"
                    )
                except (AttributeError, tk.TclError):
                    pass
        
        # Периодическая проверка отмены
        def check_cancel():
            if hasattr(self.app, 'cancel_re_file_var') and self.app.cancel_re_file_var:
                if self.app.cancel_re_file_var.get():
                    cancel_event.set()
                    if hasattr(self.app, 'current_file_label') and self.app.current_file_label:
                        try:
                            self.app.current_file_label.config(text="Отмена...")
                        except (AttributeError, tk.TclError):
                            pass
                else:
                    self.app.root.after(100, check_cancel)
        
        check_cancel()
        
        try:
            if not ready_files:
                self.app._re_file_in_progress = False
                if hasattr(self.app, '_re_file_start_time'):
                    delattr(self.app, '_re_file_start_time')
                return
            
            # Создаем обертку для callback, чтобы вызывать его в главном потоке
            def safe_callback(success: int, error: int, re_filed_files: list = None):
                """Безопасный вызов callback в главном потоке Tkinter"""
                try:
                    # НЕ сбрасываем флаг здесь - он будет сброшен в re_file_complete после всех операций
                    # Это предотвращает двойной запуск операции, если пользователь нажмет кнопку
                    # между вызовом callback и выполнением re_file_complete в главном потоке
                    self.app.root.after(0, lambda: self.re_file_operations.re_file_complete(success, error, re_filed_files))
                except Exception as e:
                    logger.error(f"Ошибка при планировании callback: {e}", exc_info=True)
                    # Если не удалось запланировать, вызываем напрямую
                    try:
                        self.re_file_operations.re_file_complete(success, error, re_filed_files)
                    except Exception as e2:
                        logger.error(f"Ошибка при прямом вызове callback: {e2}", exc_info=True)
                        # В крайнем случае сбрасываем флаг вручную
                        if hasattr(self.app, '_re_file_in_progress'):
                            self.app._re_file_in_progress = False
            
            try:
                re_file_files_thread(
                    ready_files,
                    safe_callback,
                    self.app.log,
                    update_progress,
                    cancel_event
                )
            except Exception as call_error:
                logger.error(f"Ошибка при вызове re_file_files_thread: {call_error}", exc_info=True)
                raise
        except Exception as e:
            logger.error(f"Ошибка при запуске переименования: {e}", exc_info=True)
            # Сбрасываем флаг и вызываем callback вручную при ошибке запуска
            self.re_file_operations.re_file_complete(0, len(ready_files), [])


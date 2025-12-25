"""Модуль для операций переименования файлов.

Обеспечивает выполнение операций переименования с поддержкой:
- Применения методов переименования к файлам
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
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List, Optional

# Локальные импорты
from core.rename_methods import (
    NewNameMethod,
    NumberingMethod,
    check_conflicts,
    rename_files_thread,
    validate_filename,
)

logger = logging.getLogger(__name__)

# Импорт структурированного логирования
try:
    from utils.structured_logging import log_action, log_file_action, log_batch_action
except ImportError:
    # Fallback если модуль недоступен
    def log_action(logger, level, action, message, **kwargs):
        logger.log(level, f"[{action}] {message}")
    def log_file_action(logger, action, message, **kwargs):
        logger.info(f"[{action}] {message}")
    def log_batch_action(logger, action, message, file_count, **kwargs):
        logger.info(f"[{action}] {message} (файлов: {file_count})")


class RenameOperations:
    """Класс для управления операциями переименования файлов.
    
    Координирует процесс переименования, включая валидацию,
    применение методов и обработку результатов.
    """
    
    def __init__(self, app) -> None:
        """Инициализация операций переименования.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
    
    def apply_to_selected(self):
        """Применение методов только к выбранным файлам"""
        selected = self.app.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите файлы для применения методов")
            return
        
        # Получаем индексы выбранных файлов
        selected_indices = [self.app.tree.index(item) for item in selected]
        selected_files = [self.app.files[i] for i in selected_indices if i < len(self.app.files)]
        
        if not selected_files:
            return
        
        # Применяем методы только к выбранным файлам
        for file_data in selected_files:
            try:
                new_name, extension = self.app.methods_manager.apply_methods(
                    file_data.get('old_name', ''),
                    file_data.get('extension', ''),
                    file_data.get('full_path') or file_data.get('path', '')
                )
                file_data['new_name'] = new_name
                file_data['extension'] = extension
                
                # Проверка на валидность имени
                file_path = file_data.get('path') or file_data.get('full_path', '')
                index = self.app.files.index(file_data)
                status = validate_filename(new_name, extension, file_path, index)
                file_data['status'] = status
            except Exception as e:
                self.app.log(f"Ошибка при применении методов: {e}")
        
        # Обновление таблицы
        self.app.refresh_treeview()
        self.app.log(f"Методы применены к {len(selected_files)} выбранным файлам")
    
    def apply_methods(self):
        """Применение всех методов к файлам (асинхронно, не блокирует UI)"""
        if not self.app.files:
            logger.debug("Попытка применения методов при отсутствии файлов")
            return
        
        methods = self.app.methods_manager.get_methods()
        if not methods:
            logger.debug("Попытка применения методов при отсутствии методов")
            return
        
        # Защита от повторного вызова
        if hasattr(self.app, '_applying_methods') and self.app._applying_methods:
            logger.debug("Применение методов уже выполняется")
            return
        
        self.app._applying_methods = True
        
        # Запускаем в отдельном потоке
        def apply_methods_worker():
            try:
                method_names = [type(m).__name__ for m in methods]
                log_batch_action(
                    logger=logger,
                    action='METHODS_APPLY_STARTED',
                    message=f"Применение методов к файлам: {', '.join(method_names)}",
                    file_count=len(self.app.files),
                    method_name='apply_methods',
                    details={'methods': method_names}
                )
                
                # Сброс счетчиков нумерации перед применением
                for method in methods:
                    if isinstance(method, NumberingMethod):
                        method.reset()
                    elif isinstance(method, NewNameMethod):
                        method.reset()
                
                # Применение методов к каждому файлу
                applied_count = 0
                error_count = 0
                # Используем _get_files_list() для получения реального списка, который можно изменять
                files_list = self.app._get_files_list()
                total_files = len(files_list)
                
                for i, file_data in enumerate(files_list):
                    # Безопасный доступ к данным файла
                    # Поддержка как FileInfo, так и словарей
                    if hasattr(file_data, 'old_name'):
                        # FileInfo объект
                        old_name_before = file_data.old_name
                        new_name = file_data.old_name
                        extension = file_data.extension
                        file_path = str(file_data.path) if hasattr(file_data, 'path') else ''
                    else:
                        # Словарь
                        new_name = file_data.get('old_name', '')
                        extension = file_data.get('extension', '')
                        old_name_before = new_name
                        file_path = file_data.get('full_path') or file_data.get('path', '')
                    
                    if not new_name:
                        continue
                    
                    if not file_path:
                        continue
                    
                    # Применяем все методы последовательно
                    try:
                        for method in methods:
                            new_name, extension = method.apply(new_name, extension, file_path)
                        
                        # Сохраняем new_name в зависимости от типа данных
                        if hasattr(file_data, 'new_name'):
                            # FileInfo объект
                            file_data.new_name = new_name
                            file_data.extension = extension
                        else:
                            # Словарь
                            file_data['new_name'] = new_name
                            file_data['extension'] = extension
                        applied_count += 1
                        
                        # Логируем изменение имени, если оно произошло
                        if old_name_before != new_name:
                            log_file_action(
                                logger=logger,
                                action='METHOD_APPLIED',
                                message=f"Методы применены к файлу",
                                file_path=file_path,
                                old_name=old_name_before,
                                new_name=new_name,
                                method_name='apply_methods',
                                details={'methods': method_names}
                            )
                    except Exception as e:
                        error_count += 1
                        old_name = file_data.get('old_name', 'unknown')
                        # Устанавливаем new_name даже при ошибке (используем старое имя)
                        if 'new_name' not in file_data or not file_data.get('new_name'):
                            file_data['new_name'] = old_name_before
                        log_file_action(
                            logger=logger,
                            action='METHOD_APPLY_ERROR',
                            message=f"Ошибка при применении метода: {e}",
                            file_path=file_path,
                            method_name='apply_methods',
                            details={'error': str(e), 'methods': method_names}
                        )
                        # Логируем в главном потоке
                        self.app.root.after(0, lambda msg=f"Ошибка при применении метода к {old_name}: {e}": 
                            self.app.log(msg))
                    else:
                        # Успешное применение - new_name уже установлен выше
                        pass
                    
                    # Проверка на валидность имени
                    if not file_path:
                        file_path = file_data.get('path') or file_data.get('full_path', '') if isinstance(file_data, dict) else str(file_data.path) if hasattr(file_data, 'path') else ''
                    status = validate_filename(new_name, extension, file_path, i)
                    
                    # Сохраняем статус в зависимости от типа данных
                    if hasattr(file_data, 'status'):
                        # FileInfo объект - конвертируем строку в FileStatus
                        from core.domain.file_info import FileStatus
                        if isinstance(status, str):
                            file_data.status = FileStatus.from_string(status)
                        else:
                            file_data.status = status
                    else:
                        # Словарь - сохраняем как строку
                        file_data['status'] = status
                    
                    # Обновление прогресса каждые 10 файлов или для последнего файла
                    if (i + 1) % 10 == 0 or i == total_files - 1:
                        # Обновляем UI в главном потоке
                        self.app.root.after(0, lambda idx=i, cnt=applied_count, err=error_count: 
                            self._update_progress_ui(idx + 1, total_files, cnt, err))
                
                # Проверка на конфликты
                check_conflicts(self.app.files)
                
                # Завершение в главном потоке
                self.app.root.after(0, lambda: self._apply_methods_complete(
                    applied_count, error_count, method_names))
            except Exception as e:
                logger.error(f"Ошибка в потоке применения методов: {e}", exc_info=True)
                self.app.root.after(0, lambda: self._apply_methods_error(str(e)))
            finally:
                self.app._applying_methods = False
        
        # Запускаем в отдельном потоке
        thread = threading.Thread(target=apply_methods_worker, daemon=True)
        thread.start()
    
    def _update_progress_ui(self, current: int, total: int, applied: int, errors: int):
        """Обновление UI прогресса (вызывается из главного потока)."""
        try:
            # Обновляем прогресс-бар если он есть
            if hasattr(self.app, 'progress'):
                self.app.progress['value'] = (current / total) * 100
                self.app.progress['maximum'] = 100
            
            # Обновляем таблицу периодически (не каждый файл, чтобы не тормозить)
            if current % 10 == 0 or current == total:
                self.app.refresh_treeview()
        except Exception as e:
            logger.debug(f"Ошибка обновления UI прогресса: {e}")
    
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
        logger.error(f"Ошибка применения методов: {error_msg}")
        self.app.log(f"Ошибка применения методов: {error_msg}")
        self.app.refresh_treeview()
    
    def validate_all_files(self):
        """Валидация всех готовых файлов перед переименованием.
        
        Returns:
            Tuple[bool, List[str]]: (is_valid, errors) - валидны ли все файлы и список ошибок
        """
        errors = []
        ready_files = [f for f in self.app.files if f.get('status') == 'Готов']
        
        for i, file_data in enumerate(ready_files):
            new_name = file_data.get('new_name', '')
            extension = file_data.get('extension', '')
            file_path = file_data.get('path') or file_data.get('full_path', '')
            
            # Валидация имени файла
            status = validate_filename(new_name, extension, file_path, i)
            if status != 'Готов':
                errors.append(f"{os.path.basename(file_path)}: {status}")
        
        # Проверка на конфликты имен
        name_counts = {}
        for file_data in ready_files:
            full_name = file_data.get('new_name', '') + file_data.get('extension', '')
            if full_name not in name_counts:
                name_counts[full_name] = []
            name_counts[full_name].append(file_data)
        
        for full_name, file_list in name_counts.items():
            if len(file_list) > 1:
                file_paths = [os.path.basename(f.get('path') or f.get('full_path', '')) for f in file_list]
                errors.append(f"Конфликт: {len(file_list)} файла с именем '{full_name}': {', '.join(file_paths[:3])}")
        
        return len(errors) == 0, errors
    
    def start_rename(self):
        """Начало процесса переименования"""
        # Защита от повторного вызова (если метод уже выполняется, игнорируем новый вызов)
        if hasattr(self.app, '_renaming_in_progress') and self.app._renaming_in_progress:
            logger.warning("Попытка начать переименование во время выполнения другой операции")
            return
        
        log_action(
            logger=logger,
            level=logging.INFO,
            action='RENAME_STARTED',
            message="Начало процесса переименования файлов",
            method_name='start_rename',
            file_count=len(self.app.files)
        )
        self.app._renaming_in_progress = True
        
        if not self.app.files:
            log_action(
                logger=logger,
                level=logging.WARNING,
                action='RENAME_FAILED',
                message="Попытка переименования при отсутствии файлов",
                method_name='start_rename',
                details={'reason': 'no_files'}
            )
            messagebox.showwarning("Предупреждение", "Нет файлов для переименования")
            self.app._renaming_in_progress = False
            return
        
        # Подсчет готовых файлов
        ready_files = [f for f in self.app.files if f.get('status') == 'Готов']
        
        log_action(
            logger=logger,
            level=logging.INFO,
            action='RENAME_PREPARED',
            message=f"Файлов готовых к переименованию: {len(ready_files)} из {len(self.app.files)}",
            method_name='start_rename',
            file_count=len(ready_files),
            details={'total_files': len(self.app.files), 'ready_files': len(ready_files)}
        )
        
        if not ready_files:
            logger.warning("Нет файлов готовых к переименованию")
            messagebox.showwarning(
                "Предупреждение",
                "Нет файлов готовых к переименованию"
            )
            self.app._renaming_in_progress = False
            return
        
        # Валидация всех файлов перед переименованием
        is_valid, errors = self.validate_all_files()
        
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
            self.app._renaming_in_progress = False
            return
        
        # Сохранение состояния для отмены
        undo_state = [f.copy() for f in self.app.files]
        self.app.undo_stack.append(undo_state)
        # Очищаем redo стек при новой операции
        self.app.redo_stack.clear()
        
        # Сброс флага отмены
        if not hasattr(self.app, 'cancel_rename_var') or not self.app.cancel_rename_var:
            self.app.cancel_rename_var = tk.BooleanVar(value=False)
        else:
            self.app.cancel_rename_var.set(False)
        
        # Запуск переименования в отдельном потоке
        backup_mgr = None
        if hasattr(self.app, 'backup_manager') and self.app.backup_manager:
            backup_mgr = self.app.backup_manager
        
        # Создаем событие для отмены
        cancel_event = threading.Event()
        
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
            if hasattr(self.app, 'cancel_rename_var') and self.app.cancel_rename_var:
                if self.app.cancel_rename_var.get():
                    cancel_event.set()
                    if hasattr(self.app, 'current_file_label') and self.app.current_file_label:
                        try:
                            self.app.current_file_label.config(text="Отмена...")
                        except (AttributeError, tk.TclError):
                            pass
                else:
                    self.app.root.after(100, check_cancel)
        
        check_cancel()
        
        rename_files_thread(
            ready_files,
            self.rename_complete,
            self.app.log,
            backup_mgr,
            update_progress,
            cancel_event
        )
    
    def rename_complete(self, success: int, error: int, renamed_files: list = None):
        """Обработка завершения переименования.
        
        Args:
            success: Количество успешных операций
            error: Количество ошибок
            renamed_files: Список переименованных файлов
        """
        log_batch_action(
            logger=logger,
            action='RENAME_COMPLETED',
            message=f"Переименование завершено: успешно {success}, ошибок {error}",
            file_count=success + error,
            success_count=success,
            error_count=error,
            method_name='rename_complete',
            details={'renamed_files_count': len(renamed_files) if renamed_files else 0}
        )
        # Сбрасываем флаг выполнения переименования
        if hasattr(self.app, '_renaming_in_progress'):
            self.app._renaming_in_progress = False
        
        # Добавляем операцию в историю
        if hasattr(self.app, 'history_manager') and self.app.history_manager:
            try:
                files_for_history = renamed_files if renamed_files else self.app.files[:100]
                self.app.history_manager.add_operation(
                    'rename',
                    files_for_history,
                    success,
                    error
                )
            except Exception as e:
                logger.debug(f"Не удалось добавить операцию в историю: {e}")
        
        # Записываем в статистику
        if hasattr(self.app, 'statistics_manager') and self.app.statistics_manager:
            try:
                methods_used = [type(m).__name__ for m in self.app.methods_manager.get_methods()]
                self.app.statistics_manager.record_operation(
                    'rename',
                    success,
                    error,
                    methods_used,
                    renamed_files if renamed_files else []
                )
            except Exception as e:
                logger.debug(f"Не удалось записать статистику: {e}")
        
        # Показываем уведомление
        if hasattr(self.app, 'notification_manager') and self.app.notification_manager:
            try:
                if success > 0:
                    self.app.notification_manager.notify_success(
                        f"Переименовано файлов: {success}"
                    )
                if error > 0:
                    self.app.notification_manager.notify_error(
                        f"Ошибок при переименовании: {error}"
                    )
            except Exception as e:
                logger.debug(f"Не удалось показать уведомление: {e}")
        
        # Защита от дублирования сообщения
        if not hasattr(self.app, '_rename_complete_shown'):
            self.app._rename_complete_shown = True
            messagebox.showinfo("Завершено", f"Переименование завершено.\nУспешно: {success}\nОшибок: {error}")
            # Сбрасываем флаг после небольшой задержки
            self.app.root.after(100, lambda: setattr(self.app, '_rename_complete_shown', False))
        self.app.progress['value'] = 0
        # Синхронизация прогресс-бара в окне действий, если оно открыто
        if hasattr(self.app, 'progress_window') and self.app.progress_window is not None:
            try:
                self.app.progress_window['value'] = 0
            except (AttributeError, tk.TclError):
                # Прогресс-бар может быть уничтожен
                pass
        
        # Удаляем файлы из списка после переименования, если включена соответствующая настройка
        if success > 0 and hasattr(self.app, 'remove_files_after_operation_var'):
            if self.app.remove_files_after_operation_var.get():
                # Удаляем только успешно переименованные файлы
                if renamed_files:
                    for renamed_file in renamed_files:
                        if renamed_file in self.app.files:
                            self.app.files.remove(renamed_file)
                    # Обновляем интерфейс
                    self.app.refresh_treeview()
                    self.app.update_status()
        
        # Обновление списка файлов в таблице
        for item in self.app.tree.get_children():
            self.app.tree.delete(item)
        
        for file_data in self.app.files:
            self.app.tree.insert("", tk.END, values=(
                file_data.get('old_name', ''),
                file_data.get('new_name', ''),
                file_data.get('path', ''),
                file_data['status']
            ))
        
        # Обновляем статус
        if hasattr(self.app, 'update_status'):
            self.app.update_status()
    
    def undo_rename(self):
        """Отмена последнего переименования"""
        if not self.app.undo_stack:
            messagebox.showinfo("Информация", "Нет операций для отмены")
            return
        
        # Сохраняем текущее состояние для redo
        current_state = [f.copy() for f in self.app.files]
        self.app.redo_stack.append(current_state)
        
        undo_state = self.app.undo_stack.pop()
        
        # Восстановление файлов
        for i, old_file_data in enumerate(undo_state):
            if i < len(self.app.files):
                current_file = self.app.files[i]
                # Безопасный доступ к путям
                old_path = old_file_data.get('full_path') or old_file_data.get('path')
                new_path = current_file.get('full_path') or current_file.get('path')
                
                if not old_path or not new_path:
                    continue
                
                if old_path != new_path and os.path.exists(new_path):
                    try:
                        os.rename(new_path, old_path)
                        self.app.files[i] = old_file_data.copy()
                        new_basename = os.path.basename(new_path)
                        old_basename = os.path.basename(old_path)
                        self.app.log(
                            f"Отменено: {new_basename} -> {old_basename}"
                        )
                    except Exception as e:
                        self.app.log(f"Ошибка при отмене: {e}")
        
        # Обновление интерфейса
        self.app.refresh_treeview()
        messagebox.showinfo("Отменено", "Последняя операция переименования отменена")
    
    def redo_rename(self):
        """Повтор последней отмененной операции"""
        if not self.app.redo_stack:
            messagebox.showinfo("Информация", "Нет операций для повтора")
            return
        
        # Сохраняем текущее состояние для undo
        current_state = [f.copy() for f in self.app.files]
        self.app.undo_stack.append(current_state)
        
        redo_state = self.app.redo_stack.pop()
        
        # Восстановление файлов из redo
        for i, redo_file_data in enumerate(redo_state):
            if i < len(self.app.files):
                current_file = self.app.files[i]
                # Безопасный доступ к путям
                redo_path = redo_file_data.get('full_path') or redo_file_data.get('path')
                current_path = current_file.get('full_path') or current_file.get('path')
                
                if not redo_path or not current_path:
                    continue
                
                if redo_path != current_path and os.path.exists(current_path):
                    try:
                        os.rename(current_path, redo_path)
                        self.app.files[i] = redo_file_data.copy()
                        current_basename = os.path.basename(current_path)
                        redo_basename = os.path.basename(redo_path)
                        self.app.log(
                            f"Повторено: {current_basename} -> {redo_basename}"
                        )
                    except Exception as e:
                        self.app.log(f"Ошибка при повторе: {e}")
        
        # Обновление интерфейса
        self.app.refresh_treeview()
        messagebox.showinfo("Повторено", "Операция переименования повторена")

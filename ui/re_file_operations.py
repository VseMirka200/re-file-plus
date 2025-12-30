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
import tkinter as tk
from tkinter import messagebox
from typing import Dict, List, Optional

# Локальные импорты
from core.re_file_methods import (
    NewNameMethod,
    NumberingMethod,
    check_conflicts,
    re_file_files_thread,
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
                # Упрощенное логирование: убрано избыточные данные
                
                # Определяем имена методов для логирования
                method_names = [type(m).__name__ for m in methods]
                
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
                        old_name_before = file_data.old_name or ''  # Может быть пустым для файлов типа .gitignore
                        new_name = file_data.old_name or ''  # Используем пустую строку вместо None
                        extension = file_data.extension or ''
                        file_path = str(file_data.path) if hasattr(file_data, 'path') else (file_data.full_path if hasattr(file_data, 'full_path') else '')
                    elif isinstance(file_data, dict):
                        # Словарь
                        new_name = file_data.get('old_name', '') or ''  # Может быть пустым
                        extension = file_data.get('extension', '') or ''
                        old_name_before = new_name
                        file_path = file_data.get('full_path') or file_data.get('path', '')
                    else:
                        # Неизвестный тип, пропускаем
                        continue
                    
                    # Проверяем только путь - имя может быть пустым (файлы типа .gitignore)
                    if not file_path:
                        continue
                    
                    # Если имя пустое, но есть расширение, используем расширение как имя для обработки
                    # Это нужно для файлов типа .gitignore, где old_name будет пустым
                    if not new_name and extension:
                        # Для файлов только с расширением используем расширение как имя
                        # Методы должны обработать это корректно
                        pass  # Продолжаем обработку - методы должны справиться с пустым именем
                    
                    # Формируем имя файла для отображения
                    display_name = f"{old_name_before}{extension}" if extension else old_name_before
                    
                    # Обновляем прогресс с именем текущего файла
                    current_file_index = i + 1
                    self.app.root.after(0, lambda c=current_file_index, t=total_files, 
                                       fn=display_name, a=applied_count, e=error_count:
                                       self._update_progress_ui(c, t, a, e, fn))
                    
                    # Устанавливаем желтый тег "в работе" перед обработкой файла
                    self.app.root.after(0, lambda fp=file_path: self._set_file_in_progress(fp))
                    
                    # Применяем все методы последовательно
                    try:
                        for method in methods:
                            new_name, extension = method.apply(new_name, extension, file_path)
                        
                        # Сохраняем new_name в зависимости от типа данных
                        # Важно: всегда устанавливаем new_name, даже если он равен old_name
                        if hasattr(file_data, 'old_name'):
                            # FileInfo объект
                            file_data.new_name = new_name
                            file_data.extension = extension
                        elif isinstance(file_data, dict):
                            # Словарь
                            file_data['new_name'] = new_name
                            file_data['extension'] = extension
                        applied_count += 1
                        
                        # Устанавливаем зеленый тег "готово" после успешной обработки
                        if file_path:
                            self.app.root.after(0, lambda fp=file_path: self._set_file_ready(fp))
                        
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
                        # Устанавливаем красный тег "ошибка" при ошибке
                        if file_path:
                            self.app.root.after(0, lambda fp=file_path: self._set_file_error(fp))
                        # Получаем old_name в зависимости от типа данных
                        if hasattr(file_data, 'old_name'):
                            old_name = file_data.old_name or 'unknown'
                        elif isinstance(file_data, dict):
                            old_name = file_data.get('old_name', 'unknown')
                        else:
                            old_name = 'unknown'
                        
                        # Устанавливаем new_name даже при ошибке (используем старое имя)
                        if hasattr(file_data, 'new_name'):
                            if not file_data.new_name:
                                file_data.new_name = old_name_before or ''
                        elif isinstance(file_data, dict):
                            if 'new_name' not in file_data or not file_data.get('new_name'):
                                file_data['new_name'] = old_name_before or ''
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
                        if hasattr(file_data, 'path'):
                            file_path = str(file_data.path)
                        elif hasattr(file_data, 'full_path'):
                            file_path = file_data.full_path
                        elif isinstance(file_data, dict):
                            file_path = file_data.get('path') or file_data.get('full_path', '')
                        else:
                            file_path = ''
                    
                    # Валидация имени (new_name может быть пустым для файлов типа .gitignore)
                    # Для файлов только с расширением используем расширение как имя для валидации
                    validation_name = new_name if new_name else (extension.lstrip('.') if extension else 'file')
                    status = validate_filename(validation_name, extension, file_path, i)
                    
                    # Сохраняем статус в зависимости от типа данных
                    if hasattr(file_data, 'status'):
                        # FileInfo объект - конвертируем строку в FileStatus
                        from core.domain.file_info import FileStatus
                        if isinstance(status, str):
                            file_data.status = FileStatus.from_string(status)
                            if status != 'Готов' and hasattr(file_data, 'set_error'):
                                file_data.set_error(status)
                        else:
                            file_data.status = status
                    elif isinstance(file_data, dict):
                        # Словарь - сохраняем как строку
                        file_data['status'] = status
                    
                    # Обновление прогресса с заданным интервалом или для последнего файла
                    try:
                        from config.constants import PROGRESS_UPDATE_INTERVAL
                        update_interval = PROGRESS_UPDATE_INTERVAL
                    except ImportError:
                        update_interval = 10  # Fallback значение
                    
                    if (i + 1) % update_interval == 0 or i == total_files - 1:
                        # Обновляем UI в главном потоке с именем текущего файла
                        current_display_name = f"{old_name_before}{extension}" if extension else old_name_before
                        self.app.root.after(0, lambda idx=i, cnt=applied_count, err=error_count, fn=current_display_name: 
                            self._update_progress_ui(idx + 1, total_files, cnt, err, fn))
                
                # Проверка на конфликты
                check_conflicts(self.app.files)
                
                # Завершение в главном потоке
                self.app.root.after(0, lambda: self._apply_methods_complete(
                    applied_count, error_count, method_names))
            except (OSError, PermissionError, ValueError) as e:
                # Ошибки файловой системы
                error_msg = f"Ошибка файловой системы: {str(e)}"
                logger.error(f"Ошибка в потоке применения методов: {error_msg}", exc_info=True)
                self.app.root.after(0, lambda: self._apply_methods_error(error_msg))
            except (AttributeError, TypeError) as e:
                # Ошибки доступа к атрибутам
                error_msg = f"Ошибка доступа к данным: {str(e)}"
                logger.error(f"Ошибка в потоке применения методов: {error_msg}", exc_info=True)
                self.app.root.after(0, lambda: self._apply_methods_error(error_msg))
            except Exception as e:
                # Неожиданные ошибки
                error_msg = f"Неожиданная ошибка: {str(e)}"
                logger.error(f"Неожиданная ошибка в потоке применения методов: {error_msg}", exc_info=True)
                self.app.root.after(0, lambda: self._apply_methods_error(error_msg))
            finally:
                self.app._applying_methods = False
        
        # Запускаем в отдельном потоке через threading (безопаснее для GUI)
        import threading
        thread = threading.Thread(target=apply_methods_worker, daemon=True, name="apply_methods")
        thread.start()
    
    def _set_file_in_progress(self, file_path: str):
        """Установка желтого тега "в работе" для файла в treeview
        
        Args:
            file_path: Путь к файлу
        """
        if not hasattr(self.app, 'tree'):
            return
        
        # Нормализуем путь для сравнения
        file_path_normalized = os.path.normpath(os.path.abspath(file_path))
        
        # Находим файл в treeview и устанавливаем тег "in_progress"
        actual_file_index = 0
        for item in self.app.tree.get_children():
            tags = self.app.tree.item(item, 'tags')
            if tags and 'path_row' in tags:
                continue
            
            if actual_file_index < len(self.app.files):
                file_item = self.app.files[actual_file_index]
                item_file_path = None
                if hasattr(file_item, 'full_path'):
                    item_file_path = file_item.full_path
                elif hasattr(file_item, 'path'):
                    item_file_path = str(file_item.path) if hasattr(file_item.path, '__str__') else file_item.path
                elif isinstance(file_item, dict):
                    item_file_path = file_item.get('full_path') or file_item.get('path', '')
                
                if item_file_path:
                    item_file_path_normalized = os.path.normpath(os.path.abspath(item_file_path))
                    if item_file_path_normalized == file_path_normalized:
                        # Обновляем тег на "in_progress" (без изменения текста)
                        item_values = self.app.tree.item(item, 'values')
                        display_text = item_values[0] if item_values and len(item_values) > 0 else ''
                        path_text = item_values[1] if item_values and len(item_values) > 1 else ''
                        self.app.tree.item(item, values=(display_text, path_text), tags=('in_progress',))
                        break
            actual_file_index += 1
    
    def _set_file_ready(self, file_path: str):
        """Установка зеленого тега "готово" для файла в treeview
        
        Args:
            file_path: Путь к файлу
        """
        if not hasattr(self.app, 'tree'):
            return
        
        # Нормализуем путь для сравнения
        file_path_normalized = os.path.normpath(os.path.abspath(file_path))
        
        # Находим файл в treeview и устанавливаем тег "ready"
        actual_file_index = 0
        for item in self.app.tree.get_children():
            tags = self.app.tree.item(item, 'tags')
            if tags and 'path_row' in tags:
                continue
            
            if actual_file_index < len(self.app.files):
                file_item = self.app.files[actual_file_index]
                item_file_path = None
                if hasattr(file_item, 'full_path'):
                    item_file_path = file_item.full_path
                elif hasattr(file_item, 'path'):
                    item_file_path = str(file_item.path) if hasattr(file_item.path, '__str__') else file_item.path
                elif isinstance(file_item, dict):
                    item_file_path = file_item.get('full_path') or file_item.get('path', '')
                
                if item_file_path:
                    item_file_path_normalized = os.path.normpath(os.path.abspath(item_file_path))
                    if item_file_path_normalized == file_path_normalized:
                        # Обновляем тег на "ready" (без изменения текста)
                        item_values = self.app.tree.item(item, 'values')
                        display_text = item_values[0] if item_values and len(item_values) > 0 else ''
                        path_text = item_values[1] if item_values and len(item_values) > 1 else ''
                        self.app.tree.item(item, values=(display_text, path_text), tags=('ready',))
                        break
            actual_file_index += 1
    
    def _set_file_error(self, file_path: str):
        """Установка красного тега "ошибка" для файла в treeview
        
        Args:
            file_path: Путь к файлу
        """
        if not hasattr(self.app, 'tree'):
            return
        
        # Нормализуем путь для сравнения
        file_path_normalized = os.path.normpath(os.path.abspath(file_path))
        
        # Находим файл в treeview и устанавливаем тег "error"
        actual_file_index = 0
        for item in self.app.tree.get_children():
            tags = self.app.tree.item(item, 'tags')
            if tags and 'path_row' in tags:
                continue
            
            if actual_file_index < len(self.app.files):
                file_item = self.app.files[actual_file_index]
                item_file_path = None
                if hasattr(file_item, 'full_path'):
                    item_file_path = file_item.full_path
                elif hasattr(file_item, 'path'):
                    item_file_path = str(file_item.path) if hasattr(file_item.path, '__str__') else file_item.path
                elif isinstance(file_item, dict):
                    item_file_path = file_item.get('full_path') or file_item.get('path', '')
                
                if item_file_path:
                    item_file_path_normalized = os.path.normpath(os.path.abspath(item_file_path))
                    if item_file_path_normalized == file_path_normalized:
                        # Обновляем тег на "error" (без изменения текста)
                        item_values = self.app.tree.item(item, 'values')
                        display_text = item_values[0] if item_values and len(item_values) > 0 else ''
                        path_text = item_values[1] if item_values and len(item_values) > 1 else ''
                        self.app.tree.item(item, values=(display_text, path_text), tags=('error',))
                        break
            actual_file_index += 1
    
    def _update_progress_ui(self, current: int, total: int, applied: int, errors: int, filename: str = None):
        """Обновление UI прогресса (вызывается из главного потока)."""
        try:
            # Обновляем прогресс-бар если он есть
            if hasattr(self.app, 'progress'):
                self.app.progress['value'] = (current / total) * 100
                self.app.progress['maximum'] = 100
            
            # Обновляем метку прогресса с именем текущего файла
            if hasattr(self.app, 'progress_label'):
                if filename:
                    self.app.progress_label.config(
                        text=f"Обрабатывается: {filename} ({current}/{total})"
                    )
                else:
                    self.app.progress_label.config(
                        text=f"Обработано: {current}/{total}"
                    )
            
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
    
    def start_re_file(self):
        """Начало процесса re-file операций"""
        # Защита от повторного вызова (если метод уже выполняется, игнорируем новый вызов)
        if hasattr(self.app, '_re_file_in_progress') and self.app._re_file_in_progress:
            logger.warning("Попытка начать re-file операцию во время выполнения другой операции")
            # Принудительно сбрасываем флаг, если прошло слишком много времени
            # (защита от зависших операций)
            if hasattr(self.app, '_re_file_start_time'):
                import time
                elapsed = time.time() - self.app._re_file_start_time
                if elapsed > 300:  # 5 минут
                    logger.warning(f"Принудительный сброс флага re-file операции (таймаут 5 минут, прошло {elapsed:.1f} сек)")
                    self.app._re_file_in_progress = False
                    delattr(self.app, '_re_file_start_time')
                else:
                    logger.info(f"Операция еще выполняется (прошло {elapsed:.1f} сек из 300)")
                    return
            else:
                # Если нет времени начала, но флаг установлен - сбрасываем (защита от зависших флагов)
                logger.warning("Флаг установлен, но нет времени начала - принудительный сброс")
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
        import time
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
        ready_files = [f for f in self.app.files if f.get('status') == 'Готов']
        
        log_action(
            logger=logger,
            level=logging.INFO,
            action='RE_FILE_PREPARED',
            message=f"Файлов готовых к re-file операциям: {len(ready_files)} из {len(self.app.files)}",
            method_name='start_re_file',
            file_count=len(ready_files),
            details={'total_files': len(self.app.files), 'ready_files': len(ready_files)}
        )
        
        if not ready_files:
            logger.warning("Нет файлов готовых к переименованию")
            messagebox.showwarning(
                "Предупреждение",
                "Нет файлов готовых к переименованию"
            )
            self.app._re_file_in_progress = False
            if hasattr(self.app, '_re_file_start_time'):
                delattr(self.app, '_re_file_start_time')
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
            logger.info(f"Запуск re_file_files_thread для {len(ready_files)} файлов")
            re_file_files_thread(
                ready_files,
                self.re_file_complete,
                self.app.log,
                backup_mgr,
                update_progress,
                cancel_event
            )
            logger.debug("re_file_files_thread запущен успешно")
        except Exception as e:
            logger.error(f"Ошибка при запуске re_file_files_thread: {e}", exc_info=True)
            # Сбрасываем флаг и вызываем callback вручную при ошибке запуска
            self.re_file_complete(0, len(ready_files), [])
    
    def re_file_complete(self, success: int, error: int, re_filed_files: list = None):
        """Обработка завершения re-file операций.
        
        Args:
            success: Количество успешных операций
            error: Количество ошибок
            re_filed_files: Список файлов после re-file операций
        """
        try:
            log_batch_action(
                logger=logger,
                action='RE_FILE_COMPLETED',
                message=f"Переименование завершено: успешно {success}, ошибок {error}",
                file_count=success + error,
                success_count=success,
                error_count=error,
                method_name='re_file_complete',
                details={'re_filed_files_count': len(re_filed_files) if re_filed_files else 0}
            )
        except Exception as e:
            logger.error(f"Ошибка при логировании завершения операции: {e}", exc_info=True)
        
        # Сбрасываем флаг выполнения re-file операций (всегда, даже при ошибках)
        try:
            if hasattr(self.app, '_re_file_in_progress'):
                self.app._re_file_in_progress = False
            # Очищаем время начала
            if hasattr(self.app, '_re_file_start_time'):
                delattr(self.app, '_re_file_start_time')
        except Exception as e:
            logger.error(f"Ошибка при сбросе флага операции: {e}", exc_info=True)
        
        # Добавляем операцию в историю
        if hasattr(self.app, 'history_manager') and self.app.history_manager:
            try:
                files_for_history = re_filed_files if re_filed_files else self.app.files[:100]
                self.app.history_manager.add_operation(
                    're_file',
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
                    're_file',
                    success,
                    error,
                    methods_used,
                    re_filed_files if re_filed_files else []
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
        if not hasattr(self.app, '_re_file_complete_shown'):
            self.app._re_file_complete_shown = True
            messagebox.showinfo("Завершено", f"Переименование завершено.\nУспешно: {success}\nОшибок: {error}")
            # Сбрасываем флаг после небольшой задержки
            self.app.root.after(100, lambda: setattr(self.app, '_re_file_complete_shown', False))
        if hasattr(self.app, 'progress'):
            self.app.progress['value'] = 0
        # Синхронизация прогресс-бара в окне действий, если оно открыто
        if hasattr(self.app, 'progress_window') and self.app.progress_window is not None:
            try:
                self.app.progress_window['value'] = 0
            except (AttributeError, tk.TclError):
                # Прогресс-бар может быть уничтожен
                pass
        
        # Удаляем файлы из списка после переименования, если включена соответствующая настройка
        if success > 0:
            # Используем настройки напрямую из settings_manager для актуальности
            remove_files = False
            if hasattr(self.app, 'remove_files_after_operation_var'):
                remove_files = self.app.remove_files_after_operation_var.get()
            elif hasattr(self.app, 'settings_manager'):
                remove_files = self.app.settings_manager.get('remove_files_after_operation', False)
            
            if remove_files:
                # Удаляем только успешно обработанные файлы
                if re_filed_files:
                    for re_filed_file in re_filed_files:
                        if re_filed_file in self.app.files:
                            self.app.files.remove(re_filed_file)
                    # Обновляем интерфейс
                    self.app.refresh_treeview()
                    self.app.update_status()
        
        # Обновление списка файлов через refresh_treeview
        # Это более правильный способ, который правильно форматирует данные для одной колонки
        if hasattr(self.app, 'refresh_treeview'):
            self.app.refresh_treeview()
        
        # Обновляем статус
        if hasattr(self.app, 'update_status'):
            self.app.update_status()
    
    def undo_re_file(self):
        """Отмена последней re-file операции"""
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
    
    def redo_re_file(self):
        """Повтор последней отмененной операции переименования"""
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

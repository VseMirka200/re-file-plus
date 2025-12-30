"""Модуль применения методов переименования к файлам."""

import logging
import os
from typing import List

logger = logging.getLogger(__name__)


class MethodApplier:
    """Класс для применения методов переименования к файлам."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def apply_to_selected(self):
        """Применение методов только к выбранным файлам."""
        from tkinter import messagebox
        
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
        from core.re_file_methods import validate_filename
        
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
    
    def apply_methods_worker(self, methods, method_names):
        """Рабочая функция для применения методов в отдельном потоке.
        
        Args:
            methods: Список методов для применения
            method_names: Список имен методов для логирования
        """
        from core.re_file_methods import (
            NewNameMethod,
            NumberingMethod,
            check_conflicts,
            validate_filename,
        )
        from utils.structured_logging import log_file_action
        
        # Сброс счетчиков нумерации перед применением
        for method in methods:
            if isinstance(method, NumberingMethod):
                method.reset()
            elif isinstance(method, NewNameMethod):
                method.reset()
        
        # Применение методов к каждому файлу
        applied_count = 0
        error_count = 0
        files_list = self.app._get_files_list()
        total_files = len(files_list)
        
        for i, file_data in enumerate(files_list):
            # Безопасный доступ к данным файла
            if hasattr(file_data, 'old_name'):
                file_path = str(file_data.path) if hasattr(file_data, 'path') else (file_data.full_path if hasattr(file_data, 'full_path') else '')
            elif isinstance(file_data, dict):
                file_path = file_data.get('full_path') or file_data.get('path', '')
            else:
                continue
            
            # Проверяем только путь - имя может быть пустым (файлы типа .gitignore)
            if not file_path:
                continue
            
            # ВАЖНО: Обновляем old_name и путь из реального имени файла в файловой системе
            if os.path.exists(file_path):
                real_basename = os.path.basename(file_path)
                real_dir = os.path.dirname(file_path)
                if os.path.isfile(file_path):
                    real_name, real_ext = os.path.splitext(real_basename)
                else:
                    real_name = real_basename
                    real_ext = ''
                
                # Обновляем old_name, extension и путь из реального файла
                if hasattr(file_data, 'old_name'):
                    file_data.old_name = real_name
                    file_data.extension = real_ext
                    from pathlib import Path
                    file_data.path = Path(file_path)
                    file_data.full_path = file_path
                    old_name_before = real_name
                    new_name = real_name
                    extension = real_ext
                elif isinstance(file_data, dict):
                    file_data['old_name'] = real_name
                    file_data['extension'] = real_ext
                    file_data['path'] = real_dir
                    file_data['full_path'] = file_path
                    old_name_before = real_name
                    new_name = real_name
                    extension = real_ext
            else:
                # Файл не существует - используем сохраненные значения
                if hasattr(file_data, 'old_name'):
                    old_name_before = file_data.old_name or ''
                    new_name = file_data.old_name or ''
                    extension = file_data.extension or ''
                elif isinstance(file_data, dict):
                    new_name = file_data.get('old_name', '') or ''
                    extension = file_data.get('extension', '') or ''
                    old_name_before = new_name
                else:
                    continue
            
            # Формируем имя файла для отображения
            display_name = f"{old_name_before}{extension}" if extension else old_name_before
            
            # Обновляем прогресс с именем текущего файла
            current_file_index = i + 1
            self.app.root.after(0, lambda c=current_file_index, t=total_files, 
                               fn=display_name, a=applied_count, e=error_count:
                               self.app.re_file_operations_handler.ui_updater.update_progress_ui(c, t, a, e, fn))
            
            # Устанавливаем желтый тег "в работе" перед обработкой файла
            self.app.root.after(0, lambda fp=file_path: self.app.re_file_operations_handler.ui_updater.set_file_in_progress(fp))
            
            # Применяем все методы последовательно
            try:
                for method in methods:
                    new_name, extension = method.apply(new_name, extension, file_path)
                
                # Сохраняем new_name
                if hasattr(file_data, 'old_name'):
                    file_data.new_name = new_name
                    file_data.extension = extension
                    # Устанавливаем статус "готов" для объектов FileInfo
                    if hasattr(file_data, 'set_ready'):
                        file_data.set_ready()
                elif isinstance(file_data, dict):
                    file_data['new_name'] = new_name
                    file_data['extension'] = extension
                    # Устанавливаем статус "готов" для словарей
                    file_data['status'] = 'Готов'
                applied_count += 1
                
                # Устанавливаем зеленый тег "готово" после успешной обработки
                if file_path:
                    self.app.root.after(0, lambda fp=file_path: self.app.re_file_operations_handler.ui_updater.set_file_ready(fp))
                
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
                    self.app.root.after(0, lambda fp=file_path: self.app.re_file_operations_handler.ui_updater.set_file_error(fp))
                
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
            validation_name = new_name if new_name else (extension.lstrip('.') if extension else 'file')
            status = validate_filename(validation_name, extension, file_path, i)
            
            # Сохраняем статус в зависимости от типа данных
            if hasattr(file_data, 'status'):
                from core.domain.file_info import FileStatus
                if isinstance(status, str):
                    file_data.status = FileStatus.from_string(status)
                    if status != 'Готов' and hasattr(file_data, 'set_error'):
                        file_data.set_error(status)
                else:
                    file_data.status = status
            elif isinstance(file_data, dict):
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
                    self.app.re_file_operations_handler.ui_updater.update_progress_ui(idx + 1, total_files, cnt, err, fn))
        
        # Проверка на конфликты
        check_conflicts(self.app.files)
        
        # Завершение в главном потоке
        self.app.root.after(0, lambda: self.app.re_file_operations_handler._apply_methods_complete(
            applied_count, error_count, method_names))


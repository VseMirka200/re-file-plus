"""Модуль конвертации файлов."""

import logging
import os
import time
from typing import Optional
from tkinter import messagebox
import tkinter as tk

from utils.path_processing import normalize_path
from utils.logging_utils import log_action, log_batch_action, log_file_action

logger = logging.getLogger(__name__)


class ConverterProcessor:
    """Класс для обработки конвертации файлов."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def _find_file_index(self, file_path: str) -> Optional[int]:
        """Находит индекс файла в списке по пути.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Индекс файла в списке или None
        """
        files_list = getattr(self.app, 'converter_files', None) or getattr(self.app, 'files', [])
        file_path_normalized = normalize_path(file_path)
        for idx, f in enumerate(files_list):
            f_path = f.get('path', '') if isinstance(f, dict) else (f.full_path if hasattr(f, 'full_path') else '')
            if f_path:
                f_path_normalized = normalize_path(f_path)
                if f_path_normalized == file_path_normalized:
                    return idx
        return None
    
    def convert_files(self):
        """Конвертация выбранных файлов."""
        if hasattr(self.app, '_converting_files') and self.app._converting_files:
            return
        
        if not hasattr(self.app, 'files') or not self.app.files:
            messagebox.showwarning("Предупреждение", "Список файлов пуст")
            return
        
        target_format = self.app.converter_format_var.get()
        if not target_format:
            messagebox.showwarning("Предупреждение", "Выберите целевой формат")
            return
        
        tree = getattr(self.app, 'converter_tree', None) or getattr(self.app, 'tree', None)
        if not tree:
            return
        
        selected_items = tree.selection()
        files_list = getattr(self.app, 'converter_files', None) or getattr(self.app, 'files', [])
        all_files = []
        for file_item in files_list:
            if hasattr(file_item, 'full_path'):
                file_path = file_item.full_path
            elif hasattr(file_item, 'path'):
                file_path = str(file_item.path) if hasattr(file_item.path, '__str__') else file_item.path
            elif isinstance(file_item, dict):
                file_path = file_item.get('full_path') or file_item.get('path', '')
            else:
                continue
            
            if file_path and os.path.exists(file_path) and os.path.isfile(file_path):
                if hasattr(file_item, 'full_path'):
                    file_data = {'path': file_path}
                elif isinstance(file_item, dict):
                    file_data = file_item.copy()
                    file_data['path'] = file_path
                else:
                    file_data = {'path': file_path}
                all_files.append(file_data)
        
        files_to_convert = all_files.copy()
        
        if not selected_items:
            log_batch_action(
                logger=logger,
                action='CONVERT_STARTED',
                message=f"Начало конвертации всех файлов в формат {target_format}",
                file_count=len(files_to_convert),
                method_name='convert_files',
                details={'target_format': target_format, 'selection': 'all'}
            )
            if not messagebox.askyesno("Подтверждение", 
                                      f"Конвертировать все {len(files_to_convert)} файл(ов) в {target_format}?"):
                log_action(
                    logger=logger,
                    level=logging.INFO,
                    action='CONVERT_CANCELLED',
                    message="Конвертация отменена пользователем",
                    method_name='convert_files',
                    file_count=len(files_to_convert)
                )
                return
        else:
            log_batch_action(
                logger=logger,
                action='CONVERT_STARTED',
                message=f"Начало конвертации выбранных файлов в формат {target_format}",
                file_count=len(selected_items),
                method_name='convert_files',
                details={'target_format': target_format, 'selection': 'selected'}
            )
            confirm_msg = (
                f"Конвертировать {len(selected_items)} "
                f"файл(ов) в {target_format}?"
            )
            if not messagebox.askyesno("Подтверждение", confirm_msg):
                log_action(
                    logger=logger,
                    level=logging.INFO,
                    action='CONVERT_CANCELLED',
                    message="Конвертация отменена пользователем",
                    method_name='convert_files',
                    file_count=len(selected_items)
                )
                return
            
            selected_files = []
            for item in selected_items:
                tags = tree.item(item, 'tags')
                if tags and 'path_row' in tags:
                    continue
                
                try:
                    item_index = tree.index(item)
                    if item_index < len(all_files):
                        selected_files.append(all_files[item_index])
                except (ValueError, tk.TclError):
                    item_values = tree.item(item, 'values')
                    if item_values and len(item_values) > 0:
                        file_name = item_values[0] if item_values else ''
                        if file_name:
                            for file_data in all_files:
                                file_path = file_data.get('path', '')
                                if file_path and os.path.basename(file_path) == file_name:
                                    if file_data not in selected_files:
                                        selected_files.append(file_data)
                                    break
            
            files_to_convert = selected_files
        
        self.app._converting_files = True
        log_batch_action(
            logger=logger,
            action='CONVERT_PROCESSING',
            message=f"Начало конвертации файлов в формат {target_format}",
            file_count=len(files_to_convert),
            method_name='convert_files',
            details={'target_format': target_format}
        )
        
        total_files = len(files_to_convert)
        if hasattr(self.app, 'converter_progress_bar'):
            self.app.root.after(
                0,
                lambda: self.app.converter_progress_bar.config(
                    maximum=total_files,
                    value=0
                )
            )
        if hasattr(self.app, 'converter_progress_label'):
            self.app.root.after(
                0,
                lambda: self.app.converter_progress_label.config(
                    text=f"Обработка: 0 / {total_files}"
                )
            )
        if hasattr(self.app, 'converter_current_file_label'):
            self.app.root.after(
                0,
                lambda: self.app.converter_current_file_label.config(text="")
            )
        
        def process_files():
            start_time = time.time()
            log_batch_action(
                logger=logger,
                action='CONVERT_PROCESSING_STARTED',
                message=f"Начало обработки файлов для конвертации",
                file_count=len(files_to_convert),
                method_name='process_files',
                details={'target_format': target_format}
            )
            success_count = 0
            error_count = 0
            processed = 0
            files_to_remove = []
            
            for file_data in files_to_convert:
                file_path = file_data.get('path', '')
                if not file_path:
                    continue
                
                if not os.path.isfile(file_path):
                    logger.warning(f"Пропуск папки при конвертации: {file_path}")
                    error_count += 1
                    processed += 1
                    continue
                
                file_start_time = time.time()
                log_file_action(
                    logger=logger,
                    action='CONVERT_FILE_STARTED',
                    message=f"Конвертация файла {processed + 1}/{len(files_to_convert)}",
                    file_path=file_path,
                    method_name='process_files',
                    details={
                        'file_number': processed + 1,
                        'total_files': len(files_to_convert),
                        'target_format': target_format
                    }
                )
                
                self.app.root.after(0, lambda fp=file_path: self.app.converter_tab_handler._set_file_in_progress(fp))
                
                processed += 1
                file_name = os.path.basename(file_path)
                self.app.root.after(
                    0,
                    lambda fn=file_name, curr=processed, total=total_files:
                    self.app.converter_tab_handler.update_converter_progress(curr, total, fn)
                )
                
                try:
                    output_path = self.app.file_converter.convert_file(file_path, target_format)
                    
                    if output_path and os.path.exists(output_path):
                        file_end_time = time.time()
                        conversion_time = file_end_time - file_start_time
                        log_file_action(
                            logger=logger,
                            action='CONVERT_FILE_SUCCESS',
                            message=f"Файл успешно сконвертирован за {conversion_time:.2f}с",
                            file_path=file_path,
                            method_name='process_files',
                            details={
                                'output_path': output_path,
                                'conversion_time': conversion_time,
                                'target_format': target_format
                            }
                        )
                        
                        file_index = self._find_file_index(file_path)
                        
                        self.app.root.after(
                            0,
                            lambda idx=file_index, success=True, msg="Успешно", out=output_path, fp=file_path:
                            self.app.converter_tab_handler.update_converter_status(idx, success, msg, out, fp)
                        )
                        success_count += 1
                    else:
                        error_count += 1
                        log_file_action(
                            logger=logger,
                            action='CONVERT_FILE_ERROR',
                            message="Конвертация не вернула путь к выходному файлу",
                            file_path=file_path,
                            method_name='process_files',
                            details={'target_format': target_format}
                        )
                        file_index = self._find_file_index(file_path)
                        
                        self.app.root.after(
                            0,
                            lambda idx=file_index, success=False, msg="Ошибка конвертации", out=None, fp=file_path:
                            self.app.converter_tab_handler.update_converter_status(idx, success, msg, out, fp)
                        )
                except Exception as e:
                    error_count += 1
                    log_file_action(
                        logger=logger,
                        action='CONVERT_FILE_ERROR',
                        message=f"Ошибка при конвертации: {str(e)}",
                        file_path=file_path,
                        method_name='process_files',
                        details={'target_format': target_format, 'error': str(e)}
                    )
                    file_index = self._find_file_index(file_path)
                    
                    self.app.root.after(
                        0,
                        lambda idx=file_index, success=False, msg=f"Ошибка: {str(e)}", out=None, fp=file_path:
                        self.app.converter_tab_handler.update_converter_status(idx, success, msg, out, fp)
                    )
            
            end_time = time.time()
            total_time = end_time - start_time
            
            def remove_files():
                for file_data in files_to_remove:
                    file_path = file_data.get('path', '')
                    if file_path in self.app.files:
                        try:
                            self.app.files.remove(file_path)
                        except ValueError:
                            pass
            
            def show_converter_result():
                self.app._converting_files = False
                log_batch_action(
                    logger=logger,
                    action='CONVERT_COMPLETED',
                    message=f"Конвертация завершена: успешно {success_count}, ошибок {error_count}, время {total_time:.2f}с",
                    file_count=len(files_to_convert),
                    method_name='convert_files',
                    details={
                        'success_count': success_count,
                        'error_count': error_count,
                        'total_time': total_time,
                        'target_format': target_format
                    }
                )
                
                result_msg = (
                    f"Конвертация завершена!\n\n"
                    f"Успешно: {success_count}\n"
                    f"Ошибок: {error_count}\n"
                    f"Время: {total_time:.2f}с"
                )
                messagebox.showinfo("Результат", result_msg)
            
            self.app.root.after(0, remove_files)
            self.app.root.after(0, show_converter_result)
        
        import threading
        thread = threading.Thread(target=process_files, daemon=True)
        thread.start()


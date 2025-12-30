"""Модуль для завершения re-file операций.

Содержит логику обработки результатов переименования файлов,
включая обновление интерфейса, логирование и удаление файлов из списка.
"""

# Стандартная библиотека
import logging
import os
import tkinter as tk
from tkinter import messagebox
from typing import List, Optional

from utils.path_processing import normalize_path

logger = logging.getLogger(__name__)

# Импорт структурированного логирования
try:
    from utils.structured_logging import log_batch_action
except ImportError:
    # Fallback если модуль недоступен
    def log_batch_action(logger, action, message, file_count, **kwargs):
        logger.info(f"[{action}] {message} (файлов: {file_count})")


class ReFileCompleter:
    """Класс для завершения re-file операций.
    
    Управляет процессом завершения переименования файлов, включая:
    - Сброс флагов операции
    - Логирование результатов
    - Обновление интерфейса
    - Удаление файлов из списка (если включено)
    - Запись в историю и статистику
    """
    
    def __init__(self, app):
        """Инициализация завершения re-file операций.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def re_file_complete(self, success: int, error: int, re_filed_files: list = None):
        """Обработка завершения re-file операций.
        
        Args:
            success: Количество успешных операций
            error: Количество ошибок
            re_filed_files: Список файлов после re-file операций
        """
        # НЕ сбрасываем флаг здесь - он будет сброшен в конце функции после всех операций
        # Это предотвращает двойной запуск операции
        
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
        # ВАЖНО: Удаление выполняется ТОЛЬКО после успешного переименования и НЕ блокирует переименование
        if success > 0:
            # Используем настройки напрямую из settings_manager для актуальности
            remove_files = False
            if hasattr(self.app, 'remove_files_after_operation_var'):
                remove_files = self.app.remove_files_after_operation_var.get()
            elif hasattr(self.app, 'settings_manager'):
                remove_files = self.app.settings_manager.get('remove_files_after_operation', False)
            
            logger.info(f"Настройка удаления файлов после операции: {remove_files}, успешно переименовано: {success}")
            
            if remove_files:
                # Удаляем только успешно обработанные файлы
                if re_filed_files and len(re_filed_files) > 0:
                    logger.debug(f"Получено {len(re_filed_files)} переименованных файлов для удаления")
                    # Получаем реальный список файлов для модификации
                    files_list = self.app._get_files_list() if hasattr(self.app, '_get_files_list') else self.app.files
                    
                    # Удаляем файлы по исходным путям (до переименования)
                    # Это самый надежный способ, так как пути в списке могут еще не обновиться
                    files_to_remove = []
                    for re_filed_file in re_filed_files:
                        # Получаем исходный путь (до переименования)
                        original_path = None
                        if hasattr(re_filed_file, 'metadata') and isinstance(re_filed_file.metadata, dict):
                            original_path = re_filed_file.metadata.get('_original_path')
                        elif isinstance(re_filed_file, dict):
                            original_path = re_filed_file.get('_original_path')
                        
                        # Если исходный путь не сохранен, пробуем использовать текущий путь
                        if not original_path:
                            if hasattr(re_filed_file, 'full_path'):
                                original_path = re_filed_file.full_path or str(re_filed_file.path) if hasattr(re_filed_file, 'path') else ''
                            elif isinstance(re_filed_file, dict):
                                original_path = re_filed_file.get('full_path') or re_filed_file.get('path', '')
                        
                        if original_path:
                            normalized_original_path = normalize_path(original_path)
                            
                            # Ищем файл в списке по исходному пути
                            for file_item in files_list:
                                file_path = None
                                if hasattr(file_item, 'full_path'):
                                    file_path = file_item.full_path or str(file_item.path) if hasattr(file_item, 'path') else ''
                                elif isinstance(file_item, dict):
                                    file_path = file_item.get('full_path') or file_item.get('path', '')
                                
                                if file_path:
                                    normalized_file_path = normalize_path(file_path)
                                    # Сравниваем по исходному пути или по текущему пути (на случай, если список уже обновлен)
                                    if normalized_file_path == normalized_original_path:
                                        files_to_remove.append(file_item)
                                        break
                                    # Также пробуем сравнить по новому пути (если список уже обновлен)
                                    if hasattr(re_filed_file, 'full_path'):
                                        new_path = re_filed_file.full_path or str(re_filed_file.path) if hasattr(re_filed_file, 'path') else ''
                                    elif isinstance(re_filed_file, dict):
                                        new_path = re_filed_file.get('full_path') or re_filed_file.get('path', '')
                                    if new_path:
                                        normalized_new_path = normalize_path(new_path)
                                        if normalized_file_path == normalized_new_path:
                                            files_to_remove.append(file_item)
                                            break
                    
                    # Удаляем найденные файлы
                    removed_count = 0
                    for file_to_remove in files_to_remove:
                        try:
                            files_list.remove(file_to_remove)
                            removed_count += 1
                        except ValueError:
                            # Файл уже удален или не найден
                            pass
                    
                    # Обновляем интерфейс
                    if removed_count > 0:
                        self.app.refresh_treeview()
                        self.app.update_status()
                        logger.info(f"Удалено {removed_count} файлов из списка после переименования")
                        if hasattr(self.app, 'log'):
                            self.app.log(f"Удалено {removed_count} файлов из списка")
                    else:
                        # Детальное логирование для отладки
                        logger.warning(f"Не удалось удалить файлы из списка. Переименовано: {len(re_filed_files)}, найдено для удаления: {len(files_to_remove)}, файлов в списке: {len(files_list)}")
                        # Логируем пути для отладки
                        for i, re_filed_file in enumerate(re_filed_files[:3]):  # Первые 3 файла
                            original_path = None
                            if hasattr(re_filed_file, 'metadata') and isinstance(re_filed_file.metadata, dict):
                                original_path = re_filed_file.metadata.get('_original_path')
                            elif isinstance(re_filed_file, dict):
                                original_path = re_filed_file.get('_original_path')
                            current_path = None
                            if hasattr(re_filed_file, 'full_path'):
                                current_path = re_filed_file.full_path or str(re_filed_file.path) if hasattr(re_filed_file, 'path') else ''
                            elif isinstance(re_filed_file, dict):
                                current_path = re_filed_file.get('full_path') or re_filed_file.get('path', '')
                            logger.debug(f"Файл {i+1}: исходный путь={original_path}, текущий путь={current_path}")
                        # Логируем пути из списка
                        for i, file_item in enumerate(files_list[:3]):  # Первые 3 файла
                            file_path = None
                            if hasattr(file_item, 'full_path'):
                                file_path = file_item.full_path or str(file_item.path) if hasattr(file_item, 'path') else ''
                            elif isinstance(file_item, dict):
                                file_path = file_item.get('full_path') or file_item.get('path', '')
                            logger.debug(f"Файл в списке {i+1}: путь={file_path}")
                else:
                    logger.warning(f"Список переименованных файлов пуст или None. Успешно переименовано: {success}, но файлы не переданы для удаления")
        
        # Обновление списка файлов через refresh_treeview
        # Это более правильный способ, который правильно форматирует данные для одной колонки
        # ВАЖНО: Обновление интерфейса выполняется ПОСЛЕ удаления файлов (если они были удалены)
        # и НЕ блокирует переименование
        if hasattr(self.app, 'refresh_treeview'):
            self.app.refresh_treeview()
        
        # Обновляем статус
        if hasattr(self.app, 'update_status'):
            self.app.update_status()
        
        # Сбрасываем флаг ПОСЛЕ всех операций, чтобы предотвратить двойной запуск
        # Это должно быть последним действием в функции
        try:
            if hasattr(self.app, '_re_file_in_progress'):
                self.app._re_file_in_progress = False
            # Очищаем время начала
            if hasattr(self.app, '_re_file_start_time'):
                delattr(self.app, '_re_file_start_time')
        except Exception as e:
            logger.error(f"Ошибка при сбросе флага операции: {e}", exc_info=True)


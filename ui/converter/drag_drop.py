"""Модуль drag and drop для вкладки конвертации."""

import logging
import os
import re
import sys
from typing import List

from utils.path_processing import normalize_path

logger = logging.getLogger(__name__)

# Опциональные импорты
HAS_TKINTERDND2 = False
try:
    from tkinterdnd2 import DND_FILES
    HAS_TKINTERDND2 = True
except ImportError:
    pass


class ConverterDragDrop:
    """Класс для обработки drag and drop файлов в конвертацию."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def setup_drag_drop(self, list_frame, tree, tab_frame):
        """Настройка drag and drop для вкладки конвертации."""
        if not HAS_TKINTERDND2:
            return
        
        try:
            if hasattr(list_frame, 'drop_target_register'):
                list_frame.drop_target_register(DND_FILES)
                list_frame.dnd_bind('<<Drop>>', lambda e: self.on_drop_files(e))
            
            if hasattr(tree, 'drop_target_register'):
                tree.drop_target_register(DND_FILES)
                tree.dnd_bind('<<Drop>>', lambda e: self.on_drop_files(e))
            
            if hasattr(tab_frame, 'drop_target_register'):
                tab_frame.drop_target_register(DND_FILES)
                tab_frame.dnd_bind('<<Drop>>', lambda e: self.on_drop_files(e))
        except (AttributeError, TypeError, RuntimeError) as e:
            logger.debug(f"Ошибка настройки drag and drop для вкладки конвертации: {e}")
        except (MemoryError, RecursionError) as e:

            # Ошибки памяти/рекурсии

            pass

        # Финальный catch для неожиданных исключений (критично для стабильности)

        except BaseException as e:

            if isinstance(e, (KeyboardInterrupt, SystemExit)):

                raise
            logger.debug(f"Неожиданная ошибка настройки drag and drop для вкладки конвертации: {e}")
    
    def on_drop_files(self, event):
        """Обработка перетаскивания файлов на вкладку конвертации."""
        try:
            data = event.data
            if not data:
                return
            
            file_paths = []
            
            if sys.platform == 'win32':
                file_paths = re.findall(r'\{([^}]+)\}', data)
                if not file_paths:
                    file_paths = data.split()
            else:
                file_paths = data.split()
            
            file_paths = [f.strip().strip('"').strip("'") for f in file_paths if f.strip()]
            valid_file_paths = [f for f in file_paths if os.path.exists(f) and os.path.isfile(f)]
            
            added_count = 0
            for file_path in valid_file_paths:
                if not file_path:
                    continue
                
                try:
                    if not os.path.isabs(file_path):
                        file_path = os.path.abspath(file_path)
                    else:
                        file_path = os.path.normpath(file_path)
                except (OSError, ValueError, TypeError):
                    # Пропускаем файлы с некорректными путями
                    continue
                
                if not os.path.exists(file_path) or not os.path.isfile(file_path):
                    continue
                
                normalized_path = normalize_path(file_path)
                if any(normalize_path(f.get('path', '')) == normalized_path 
                       for f in self.app.converter_files if f.get('path')):
                    continue
                
                ext = os.path.splitext(file_path)[1].lower()
                
                available_formats = []
                all_formats = self.app.file_converter.get_supported_formats()
                for target_format in all_formats:
                    if self.app.file_converter.can_convert(file_path, target_format):
                        available_formats.append(target_format)
                
                file_category = self.app.file_converter.get_file_type_category(file_path)
                
                status = self.app.converter_tab_handler.file_handler.check_if_file_already_converted(file_path, available_formats)
                if not status:
                    if available_formats:
                        status = 'Готов'
                    else:
                        status = 'Не поддерживается'
                
                file_data = {
                    'path': file_path,
                    'format': ext,
                    'status': status,
                    'available_formats': available_formats,
                    'category': file_category
                }
                self.app.converter_files.append(file_data)
                added_count += 1
                
                # Автоматически устанавливаем тип файла при первом добавлении
                if added_count == 1 and file_category:
                    self._auto_set_file_type(file_category)
            
            if added_count > 0:
                if hasattr(self.app, 'converter_left_panel'):
                    count = len(self.app.converter_files)
                    self.app.converter_left_panel.config(text=f"Список файлов (Файлов: {count})")
                self.app.converter_tab_handler.filter_converter_files_by_type()
                # Обновляем отображение списка файлов
                if hasattr(self.app, 'file_list_manager') and hasattr(self.app.file_list_manager, 'refresh_treeview'):
                    self.app.file_list_manager.refresh_treeview()
                self.app.log(f"Добавлено файлов для конвертации перетаскиванием: {added_count}")
        except (OSError, PermissionError, ValueError, TypeError, AttributeError, FileNotFoundError) as e:
            # Используем ErrorHandler если доступен
            if hasattr(self.app, 'error_handler') and self.app.error_handler:
                try:
                    from core.error_handling.errors import ErrorType
                    error_type = ErrorType.UNKNOWN_ERROR
                    if isinstance(e, (OSError, PermissionError)):
                        error_type = ErrorType.PERMISSION_DENIED
                    elif isinstance(e, ValueError):
                        error_type = ErrorType.INVALID_PATH
                    self.app.error_handler.handle_error(
                        e,
                        error_type=error_type,
                        context={'operation': 'handle_drop_converter'}
                    )
                except (ImportError, AttributeError, TypeError, ValueError) as handler_error:
                    logger.debug(f"Ошибка в ErrorHandler при обработке drag&drop: {handler_error}")
                    pass
            logger.error(f"Ошибка при обработке перетаскивания файлов для конвертации: {e}", exc_info=True)
    
    def _auto_set_file_type(self, file_category: str):
        """Автоматическая установка типа файла в фильтре.
        
        Args:
            file_category: Категория файла (image, document, presentation, audio, video)
        """
        if not file_category:
            return
        
        if not hasattr(self.app, 'converter_filter_var'):
            import tkinter as tk
            self.app.converter_filter_var = tk.StringVar(value="Все")
        
        category_mapping = {
            'image': 'Изображения',
            'document': 'Документы',
            'presentation': 'Презентации',
            'audio': 'Аудио',
            'video': 'Видео'
        }
        
        filter_name = category_mapping.get(file_category)
        if filter_name:
            logger.info(f"Автоматическая установка типа файла (drag-drop): {file_category} -> {filter_name}")
            self.app.converter_filter_var.set(filter_name)
            
            def update_filter_ui():
                try:
                    if hasattr(self.app, 'converter_filter_combo') and self.app.converter_filter_combo:
                        self.app.converter_filter_combo.set(filter_name)
                        logger.debug(f"Combobox обновлен (drag-drop): {filter_name}")
                    # Обновляем список форматов для выбранного типа
                    if hasattr(self.app, 'converter_tab_handler'):
                        self.app.converter_tab_handler.filter_converter_files_by_type()
                except (AttributeError, TypeError, RuntimeError) as e:
                    logger.debug(f"Ошибка при обновлении combobox: {e}")
                except (MemoryError, RecursionError):
                    pass
            
            if hasattr(self.app, 'root'):
                self.app.root.after(10, update_filter_ui)


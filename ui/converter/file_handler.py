"""Модуль обработки файлов для конвертации.

Содержит функции для:
- Добавления файлов для конвертации
- Обработки файлов из аргументов командной строки
- Очистки списка файлов
- Проверки уже конвертированных файлов
"""

import logging
import os
from tkinter import filedialog
from typing import Optional

from utils.path_processing import normalize_path

logger = logging.getLogger(__name__)


class ConverterFileHandler:
    """Класс для обработки файлов конвертации."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def _validate_and_normalize_file(self, file_path: str) -> Optional[str]:
        """Валидация и нормализация пути к файлу.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Нормализованный путь или None, если файл невалиден
        """
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return None
        if os.path.isdir(file_path):
            return None
        return normalize_path(file_path)
    
    def _is_file_duplicate(self, file_path: str, normalized_path: str) -> bool:
        """Проверяет, является ли файл дубликатом.
        
        Args:
            file_path: Исходный путь к файлу
            normalized_path: Нормализованный путь к файлу
            
        Returns:
            True, если файл уже в списке
        """
        return any(normalize_path(f.get('path', '')) == normalized_path 
                   for f in self.app.converter_files if f.get('path'))
    
    def add_files_for_conversion(self):
        """Добавление файлов для конвертации."""
        files = filedialog.askopenfilenames(
            title="Выберите файлы для конвертации",
            filetypes=[
                ("Все файлы", "*.*"),
                ("Изображения", "*.png *.jpg *.jpeg *.ico *.webp *.gif *.pdf"),
                ("Документы", "*.pdf *.doc *.docx *.odt"),
                ("Презентации", "*.pptx *.ppt *.odp"),
            ]
        )
        
        if files:
            added_count = 0
            skipped_count = 0
            
            if not hasattr(self.app, 'converter_files'):
                self.app.converter_files = []
            
            for file_path in files:
                # Валидация и нормализация пути
                normalized_path = self._validate_and_normalize_file(file_path)
                if not normalized_path:
                    skipped_count += 1
                    continue
                
                # Проверка на дубликаты
                if self._is_file_duplicate(file_path, normalized_path):
                    skipped_count += 1
                    continue
                
                added_count += 1
                
                ext = os.path.splitext(file_path)[1].lower()
                
                # Получение информации о файле
                available_formats = []
                file_category = None
                if hasattr(self.app, 'file_converter'):
                    try:
                        available_formats = self.app.file_converter.get_target_formats_for_file(file_path)
                        file_category = self.app.file_converter.get_file_type_category(file_path)
                    except (MemoryError, RecursionError) as e:

                        # Ошибки памяти/рекурсии

                        pass

                    # Финальный catch для неожиданных исключений (критично для стабильности)

                    except BaseException as e:

                        if isinstance(e, (KeyboardInterrupt, SystemExit)):

                            raise
                        logger.error(f"Ошибка при получении информации о файле {os.path.basename(file_path)}: {e}")
                
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
                
                # Автоматически устанавливаем фильтр по типу файла при первом добавлении
                if added_count == 1 and file_category:
                    if not hasattr(self.app, 'converter_filter_var'):
                        import tkinter as tk
                        self.app.converter_filter_var = tk.StringVar(value="Все")
                    
                    if hasattr(self.app, 'converter_filter_var'):
                        current_filter = self.app.converter_filter_var.get()
                        if not current_filter or current_filter == "Все" or current_filter == "":
                            category_mapping = {
                                'image': 'Изображения',
                                'document': 'Документы',
                                'presentation': 'Презентации',
                                'audio': 'Аудио',
                                'video': 'Видео'
                            }
                            filter_name = category_mapping.get(file_category)
                            if filter_name:
                                self.app.converter_filter_var.set(filter_name)
                                
                                def update_filter_ui():
                                    try:
                                        if hasattr(self.app, 'converter_filter_combo') and self.app.converter_filter_combo:
                                            self.app.converter_filter_combo.set(filter_name)
                                    except (AttributeError, TypeError, RuntimeError):
                                        # Игнорируем ошибки UI операций (не критично)
                                        pass
                                if hasattr(self.app, 'root'):
                                    self.app.root.after(10, update_filter_ui)
            
            if hasattr(self.app, 'converter_left_panel'):
                count = len(self.app.converter_files)
                self.app.converter_left_panel.config(text=f"Список файлов (Файлов: {count})")
            
            if hasattr(self.app, 'converter_tab_handler'):
                self.app.converter_tab_handler.filter_converter_files_by_type()
                self.app.converter_tab_handler.update_available_formats()
            
            # Обновляем отображение списка файлов
            if hasattr(self.app, 'file_list_manager') and hasattr(self.app.file_list_manager, 'refresh_treeview'):
                self.app.file_list_manager.refresh_treeview()
            
            self.app.log(f"Добавлено файлов для конвертации: {added_count}")
    
    def clear_converter_files_list(self):
        """Очистка списка файлов конвертации."""
        from tkinter import messagebox
        
        if hasattr(self.app, 'converter_files') and self.app.converter_files:
            if messagebox.askyesno("Подтверждение", "Очистить список файлов для конвертации?"):
                count = len(self.app.converter_files)
                self.app.converter_files.clear()
                
                if hasattr(self.app, 'converter_left_panel'):
                    self.app.converter_left_panel.config(text="Список файлов (Файлов: 0)")
                
                if hasattr(self.app, 'converter_tab_handler'):
                    self.app.converter_tab_handler.filter_converter_files_by_type()
                
                self.app.log(f"Очищено файлов из списка конвертации: {count}")
    
    def check_if_file_already_converted(self, file_path: str, available_formats: list) -> Optional[str]:
        """Проверка, был ли файл уже конвертирован.
        
        Args:
            file_path: Путь к файлу
            available_formats: Список доступных форматов конвертации
            
        Returns:
            Сообщение о статусе или None
        """
        if not available_formats:
            return None
        
        file_dir = os.path.dirname(file_path)
        file_name_without_ext = os.path.splitext(os.path.basename(file_path))[0]
        source_ext = os.path.splitext(file_path)[1].lower()
        
        for target_format in available_formats:
            if target_format == source_ext:
                continue
            
            expected_output = os.path.join(file_dir, file_name_without_ext + target_format)
            if os.path.exists(expected_output):
                return f"Уже конвертирован в {target_format}"
        
        return None


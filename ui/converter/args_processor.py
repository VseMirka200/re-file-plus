"""Модуль для обработки аргументов командной строки для конвертации.

Содержит класс для обработки файлов, переданных через аргументы командной строки.
"""

import logging
import os

from utils.path_processing import normalize_path

logger = logging.getLogger(__name__)


class ConverterArgsProcessor:
    """Класс для обработки аргументов командной строки для конвертации."""
    
    def __init__(self, app, converter_tab):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
            converter_tab: Экземпляр ConverterTab для доступа к методам
        """
        self.app = app
        self.converter_tab = converter_tab
    
    def process_files_from_args(self):
        """Обработка файлов из аргументов командной строки"""
        if not self.app.files_from_args:
            self.app.log("Нет файлов для обработки из аргументов")
            return
        
        self.app.log(f"Начинаем обработку {len(self.app.files_from_args)} файлов из аргументов командной строки")
        
        # Переключаемся на вкладку конвертации
        self._switch_to_converter_tab()
        
        # Добавляем файлы
        added_count = 0
        for file_path in self.app.files_from_args:
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                continue
            
            if not hasattr(self.app, 'converter_files'):
                self.app.converter_files = []
            
            # Проверяем, что файл еще не добавлен
            normalized_path = normalize_path(file_path)
            if any(normalize_path(f.get('path', '')) == normalized_path 
                   for f in self.app.converter_files if f.get('path')):
                continue
            
            # Получаем информацию о файле
            file_data = self._create_file_data(file_path)
            if file_data:
                self.app.converter_files.append(file_data)
                added_count += 1
                
                # Автоматически устанавливаем фильтр по типу файла при первом добавлении
                if added_count == 1:
                    self._auto_set_filter(file_data.get('category'))
        
        # Обновляем UI
        self._update_ui_after_adding_files(added_count)
    
    def _switch_to_converter_tab(self):
        """Переключение на вкладку конвертации."""
        if hasattr(self.app, 'main_window_handler') and hasattr(self.app.main_window_handler, 'switch_tab'):
            self.app.main_window_handler.switch_tab('convert')
            self.app.log("Переключились на вкладку 'Конвертация'")
        else:
            self.app.log("Не удалось переключиться на вкладку конвертации")
    
    def _create_file_data(self, file_path):
        """Создание данных файла для добавления в список конвертации.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Словарь с данными файла или None
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        # Определяем доступные форматы конвертации
        available_formats = []
        if hasattr(self.app, 'file_converter'):
            available_formats = self.app.file_converter.get_target_formats_for_file(file_path)
        
        # Определяем категорию файла автоматически
        file_category = self.app.file_converter.get_file_type_category(file_path)
        
        # Определяем статус файла
        status = self.converter_tab._check_if_file_already_converted(file_path, available_formats)
        if not status:
            if available_formats:
                status = 'Готов'
            else:
                status = 'Не поддерживается'
        
        return {
            'path': file_path,
            'format': ext,
            'status': status,
            'available_formats': available_formats,
            'category': file_category
        }
    
    def _auto_set_filter(self, file_category):
        """Автоматическая установка фильтра по типу файла.
        
        Args:
            file_category: Категория файла
        """
        if not file_category or not hasattr(self.app, 'converter_filter_var'):
            return
        
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
                # Обновляем список форматов для этого типа
                self.converter_tab.update_available_formats()
    
    def _update_ui_after_adding_files(self, added_count):
        """Обновление UI после добавления файлов.
        
        Args:
            added_count: Количество добавленных файлов
        """
        # Обновляем заголовок панели
        if hasattr(self.app, 'converter_left_panel'):
            count = len(self.app.converter_files)
            self.app.converter_left_panel.config(text=f"Список файлов (Файлов: {count})")
        
        # Применяем фильтр и обновляем отображение
        if hasattr(self.app, 'converter_tab_handler'):
            self.app.converter_tab_handler.filter_converter_files_by_type()
        
        # Обновляем отображение списка файлов
        if hasattr(self.app, 'file_list_manager') and hasattr(self.app.file_list_manager, 'refresh_treeview'):
            self.app.file_list_manager.refresh_treeview()
        
        total_count = len(self.app.converter_files) if hasattr(self.app, 'converter_files') else 0
        self.app.log(f"Добавлено файлов из аргументов: {total_count} из {len(self.app.files_from_args)}")


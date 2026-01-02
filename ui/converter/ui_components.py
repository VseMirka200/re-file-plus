"""Модуль UI компонентов для вкладки конвертации.

Содержит функции для:
- Создания UI компонентов (фильтры, форматы, кнопки)
- Обновления доступных форматов
- Фильтрации файлов по типу
"""

import logging
import os
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)


class ConverterUIComponents:
    """Класс для управления UI компонентами конвертации."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def create_settings_panel(self, parent):
        """Создание панели настроек конвертации.
        
        Args:
            parent: Родительский виджет
        """
        settings_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        
        # Фильтр по типу файла
        filter_label = tk.Label(settings_frame, text="Фильтр по типу:",
                               font=('Robot', 9, 'bold'),
                               bg=self.app.colors['bg_main'],
                               fg=self.app.colors['text_primary'],
                               anchor='w')
        filter_label.pack(anchor=tk.W, pady=(0, 6))
        
        filter_var = tk.StringVar(value="Все")
        filter_combo = ttk.Combobox(
            settings_frame,
            textvariable=filter_var,
            values=[
                "Все",
                "Изображения",
                "Документы",
                "Презентации"
            ],
            state='readonly',
            width=15
        )
        filter_combo.pack(fill=tk.X, pady=(0, 10))
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.app.converter_tab_handler.filter_converter_files_by_type())
        self.app.converter_filter_var = filter_var
        self.app.converter_filter_combo = filter_combo
        
        self.app.root.after(100, lambda: self.app.converter_tab_handler.filter_converter_files_by_type())
        
        # Выбор формата
        format_label = tk.Label(settings_frame, text="Целевой формат:",
                               font=('Robot', 9, 'bold'),
                               bg=self.app.colors['bg_main'],
                               fg=self.app.colors['text_primary'],
                               anchor='w')
        format_label.pack(anchor=tk.W, pady=(0, 12))
        
        formats = self.app.file_converter.get_supported_formats()
        format_var = tk.StringVar(value=formats[0] if formats else '.png')
        format_combo = ttk.Combobox(settings_frame, textvariable=format_var,
                                   values=formats, state='readonly', width=15)
        format_combo.pack(fill=tk.X, pady=(0, 10))
        self.app.converter_format_var = format_var
        self.app.converter_format_combo = format_combo
        
        return settings_frame
    
    def update_available_formats(self):
        """Обновление списка доступных форматов в combobox на основе выбранных файлов."""
        if not hasattr(self.app, 'converter_format_combo') or not self.app.converter_format_combo:
            return
        
        selected_items = []
        if hasattr(self.app, 'tree') and self.app.tree:
            selected_items = self.app.tree.selection()
        
        files_to_check = []
        
        if selected_items:
            for item_id in selected_items:
                try:
                    item_index = self.app.tree.index(item_id)
                    if item_index >= 0 and item_index < len(self.app.files):
                        file_item = self.app.files[item_index]
                        if isinstance(file_item, dict):
                            file_path = file_item.get('path', '') or file_item.get('full_path', '')
                        elif hasattr(file_item, 'full_path'):
                            file_path = file_item.full_path
                        elif hasattr(file_item, 'path'):
                            file_path = str(file_item.path) if hasattr(file_item.path, '__str__') else file_item.path
                        else:
                            continue
                        
                        if file_path and os.path.exists(file_path) and os.path.isfile(file_path):
                            files_to_check.append(file_path)
                except (tk.TclError, ValueError, IndexError):
                    continue
        
        if not files_to_check:
            if not hasattr(self.app, 'converter_files') or not self.app.converter_files:
                all_supported_formats = self.app.file_converter.get_supported_formats()
                self.app.converter_format_combo['values'] = all_supported_formats
                return
            
            for file_item in self.app.converter_files:
                if isinstance(file_item, dict):
                    file_path = file_item.get('path', '')
                    if file_path and os.path.exists(file_path) and os.path.isfile(file_path):
                        files_to_check.append(file_path)
        
        if files_to_check:
            common_formats = set()
            for file_path in files_to_check:
                formats = self.app.file_converter.get_target_formats_for_file(file_path)
                if common_formats:
                    common_formats &= set(formats)
                else:
                    common_formats = set(formats)
            
            if common_formats:
                final_formats = sorted(list(common_formats))
                self.app.converter_format_combo['values'] = final_formats
                current_value = self.app.converter_format_var.get()
                if current_value not in final_formats and final_formats:
                    self.app.converter_format_var.set(final_formats[0])
            else:
                all_supported_formats = self.app.file_converter.get_supported_formats()
                self.app.converter_format_combo['values'] = all_supported_formats
        else:
            all_supported_formats = self.app.file_converter.get_supported_formats()
            self.app.converter_format_combo['values'] = all_supported_formats
    
    def filter_converter_files_by_type(self):
        """Фильтрация файлов в конвертере по типу."""
        if not hasattr(self.app, 'tree') or not hasattr(self.app, 'files'):
            return
        
        filter_type = self.app.converter_filter_var.get() if hasattr(self.app, 'converter_filter_var') else "Все"
        
        filter_mapping = {
            "Все": None,
            "Изображения": "image",
            "Документы": "document",
            "Презентации": "presentation",
            "Аудио": "audio",
            "Видео": "video"
        }
        
        target_category = filter_mapping.get(filter_type)
        
        if hasattr(self.app, 'converter_format_combo'):
            if target_category == "image":
                final_formats = list(self.app.file_converter.supported_image_formats.keys())
            elif target_category == "document":
                final_formats = list(self.app.file_converter.supported_document_formats.keys())
            elif target_category == "presentation":
                final_formats = list(self.app.file_converter.supported_presentation_formats.keys())
            elif target_category == "audio":
                final_formats = list(self.app.file_converter.supported_audio_formats.keys())
            elif target_category == "video":
                final_formats = list(self.app.file_converter.supported_video_formats.keys())
            else:
                final_formats = self.app.file_converter.get_supported_formats()
            
            self.app.converter_format_combo['values'] = final_formats
            
            current_value = self.app.converter_format_var.get()
            if current_value not in final_formats:
                self.app.converter_format_var.set('')
        
        if hasattr(self.app, 'left_panel'):
            total_count = len(self.app.files)
            self.app.left_panel.config(text=f"Список файлов (Файлов: {total_count})")


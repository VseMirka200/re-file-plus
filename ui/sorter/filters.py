"""Модуль для управления фильтрами сортировки."""

import logging
import tkinter as tk
from tkinter import messagebox

from ui.ui_components import set_window_icon

logger = logging.getLogger(__name__)


class SorterFilters:
    """Класс для управления фильтрами сортировки."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def add_sorter_filter(self):
        """Добавление нового правила фильтрации"""
        filter_window = tk.Toplevel(self.app.root)
        filter_window.title("Добавить правило")
        filter_window.geometry("500x400")
        filter_window.configure(bg=self.app.colors['bg_main'])
        
        try:
            set_window_icon(filter_window, self.app._icon_photos)
        except (AttributeError, tk.TclError, OSError) as e:
            logger.debug(f"Не удалось установить иконку окна: {e}")
        except Exception as e:
            logger.warning(f"Неожиданная ошибка при установке иконки: {e}")
        
        main_frame = tk.Frame(filter_window, bg=self.app.colors['bg_main'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Название папки назначения
        tk.Label(main_frame, text="Название папки назначения:",
                font=('Robot', 9, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 5))
        
        folder_name_var = tk.StringVar()
        folder_entry = tk.Entry(main_frame, textvariable=folder_name_var,
                               font=('Robot', 9), bg='white',
                               fg=self.app.colors['text_primary'],
                               relief=tk.SOLID, borderwidth=1)
        folder_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Тип фильтра
        tk.Label(main_frame, text="Тип фильтра:",
                font=('Robot', 9, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(0, 5))
        
        filter_type_var = tk.StringVar(value="extension")
        filter_types = [
            ("По расширению", "extension"),
            ("По имени файла", "filename"),
            ("По размеру", "size"),
            ("По дате создания", "date"),
            ("По типу MIME", "mime")
        ]
        
        for text, value in filter_types:
            tk.Radiobutton(main_frame, text=text, variable=filter_type_var,
                          value=value, bg=self.app.colors['bg_main'],
                          fg=self.app.colors['text_primary'],
                          font=('Robot', 9)).pack(anchor=tk.W, padx=20)
        
        # Значение фильтра
        tk.Label(main_frame, text="Значение фильтра:",
                font=('Robot', 9, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary']).pack(anchor=tk.W, pady=(15, 5))
        
        filter_value_var = tk.StringVar()
        filter_value_entry = tk.Entry(main_frame, textvariable=filter_value_var,
                                      font=('Robot', 9), bg='white',
                                      fg=self.app.colors['text_primary'],
                                      relief=tk.SOLID, borderwidth=1)
        filter_value_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Подсказка
        hint_text = "Примеры:\n- Расширение: .jpg, .png, .pdf\n- Имя: содержит 'фото', начинается с 'IMG'\n- Размер: >10MB, <1MB\n- Дата: >2024-01-01, <2023-12-31"
        tk.Label(main_frame, text=hint_text,
                font=('Robot', 8),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_secondary'],
                justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 15))
        
        # Кнопки
        buttons_frame = tk.Frame(main_frame, bg=self.app.colors['bg_main'])
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        def save_filter():
            folder_name = folder_name_var.get().strip()
            filter_type = filter_type_var.get()
            filter_value = filter_value_var.get().strip()
            
            if not folder_name or not filter_value:
                messagebox.showwarning("Предупреждение",
                                      "Заполните все поля")
                return
            
            filter_data = {
                'folder_name': folder_name,
                'type': filter_type,
                'value': filter_value,
                'enabled': True
            }
            
            self.app.sorter_filters.append(filter_data)
            self.app.sorter_tab_handler.refresh_filters_display()
            filter_window.destroy()
            messagebox.showinfo("Успешно", "Правило добавлено")
        
        btn_save = self.app.create_rounded_button(
            buttons_frame, "💾 Сохранить", save_filter,
            self.app.colors['success'], 'white',
            font=('Robot', 9, 'bold'), padx=15, pady=8,
            active_bg=self.app.colors['success_hover'], expand=True)
        btn_save.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        btn_cancel = self.app.create_rounded_button(
            buttons_frame, "❌ Отмена", filter_window.destroy,
            self.app.colors['danger'], 'white',
            font=('Robot', 9, 'bold'), padx=15, pady=8,
            active_bg=self.app.colors['danger_hover'], expand=True)
        btn_cancel.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def refresh_filters_display(self):
        """Обновление отображения фильтров"""
        # Очищаем текущие виджеты
        for widget in self.app.sorter_filters_frame.winfo_children():
            widget.destroy()
        
        # Отображаем все фильтры
        for i, filter_data in enumerate(self.app.sorter_filters):
            filter_frame = tk.Frame(self.app.sorter_filters_frame, bg=self.app.colors['bg_main'],
                                   relief=tk.SOLID, borderwidth=1)
            filter_frame.pack(fill=tk.X, pady=2, padx=5)
            filter_frame.columnconfigure(1, weight=1)
            
            # Чекбокс включения
            enabled_var = tk.BooleanVar(value=filter_data.get('enabled', True))
            enabled_var.trace('w', lambda *args, idx=i: self.app.sorter_tab_handler.toggle_filter(idx))
            tk.Checkbutton(filter_frame, variable=enabled_var,
                          bg=self.app.colors['bg_main']).grid(row=0, column=0, padx=(5, 2))
            
            # Информация о фильтре
            info_text = f"{filter_data['folder_name']} | {filter_data['type']}: {filter_data['value']}"
            tk.Label(filter_frame, text=info_text,
                    font=('Robot', 9),
                    bg=self.app.colors['bg_main'],
                    fg=self.app.colors['text_primary']).grid(row=0, column=1, sticky="w", padx=(2, 2))
            
            # Кнопка удаления (квадратная, как кнопка "Добавить")
            btn_delete = self.app.create_square_icon_button(
                filter_frame,
                "🗑️",
                lambda idx=i: self.app.sorter_tab_handler.delete_filter(idx),
                bg_color=self.app.colors['danger'],
                size=28,
                active_bg=self.app.colors['danger_hover'],
                tooltip="Удалить правило"
            )
            btn_delete.grid(row=0, column=2, padx=(2, 5), sticky="nse")
        
        # Обновляем видимость скроллбара после обновления списка фильтров
        if hasattr(self.app, 'update_filters_scrollbar'):
            self.app.root.after(10, self.app.update_filters_scrollbar)
    
    def toggle_filter(self, index):
        """Включение/выключение фильтра"""
        if 0 <= index < len(self.app.sorter_filters):
            # Обновляем состояние через чекбокс
            pass
    
    def delete_filter(self, index):
        """Удаление фильтра"""
        if 0 <= index < len(self.app.sorter_filters):
            if messagebox.askyesno("Подтверждение", "Удалить это правило?"):
                del self.app.sorter_filters[index]
                self.app.sorter_tab_handler.refresh_filters_display()
    
    def add_default_filters(self):
        """Добавление фильтров по умолчанию"""
        default_filters = [
            {'folder_name': 'Изображения', 'type': 'extension', 'value': '.jpg,.jpeg,.png,.gif,.bmp,.webp', 'enabled': True},
            {'folder_name': 'Документы', 'type': 'extension', 'value': '.pdf,.doc,.docx,.txt', 'enabled': True},
            {'folder_name': 'Архивы', 'type': 'extension', 'value': '.zip,.rar,.7z,.tar,.gz', 'enabled': True}
        ]
        
        self.app.sorter_filters.extend(default_filters)
        self.app.sorter_tab_handler.refresh_filters_display()
    
    def save_sorter_filters(self):
        """Сохранение фильтров в настройки"""
        try:
            filters_data = {
                'folder_path': self.app.sorter_folder_path.get(),
                'filters': self.app.sorter_filters
            }
            self.app.settings_manager.set('file_sorter_filters', filters_data)
            self.app.settings_manager.save_settings(self.app.settings_manager.settings)
            messagebox.showinfo("Успешно", "Фильтры сохранены")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить фильтры: {e}")
    
    def load_sorter_filters(self):
        """Загрузка фильтров из настроек"""
        try:
            filters_data = self.app.settings_manager.get('file_sorter_filters', {})
            if filters_data:
                if 'folder_path' in filters_data:
                    self.app.sorter_folder_path.set(filters_data['folder_path'])
                if 'filters' in filters_data:
                    self.app.sorter_filters = filters_data['filters']
                    self.app.sorter_tab_handler.refresh_filters_display()
        except Exception as e:
            logger.debug(f"Не удалось загрузить фильтры: {e}")
            # Если не удалось загрузить, добавляем фильтры по умолчанию
            if not self.app.sorter_filters:
                self.app.sorter_tab_handler.add_default_filters()


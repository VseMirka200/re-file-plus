"""Модуль для логики сортировки файлов."""

import logging
import os
import threading
from datetime import datetime

import tkinter as tk
from tkinter import messagebox, ttk

from ui.ui_components import set_window_icon

logger = logging.getLogger(__name__)


class SorterSorting:
    """Класс для логики сортировки файлов."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def preview_file_sorting(self):
        """Предпросмотр сортировки файлов"""
        folder_path = self.app.sorter_folder_path.get()
        
        if not folder_path or not os.path.exists(folder_path):
            messagebox.showerror("Ошибка", "Укажите существующую папку для сортировки")
            return
        
        enabled_filters = [f for f in self.app.sorter_filters if f.get('enabled', True)]
        if not enabled_filters:
            messagebox.showwarning("Предупреждение", "Нет активных правил для сортировки")
            return
        
        # Собираем все файлы из папки
        files_to_sort = []
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                files_to_sort.append(item_path)
        
        if not files_to_sort:
            messagebox.showinfo("Информация", "В выбранной папке нет файлов для сортировки")
            return
        
        # Создаем окно предпросмотра
        preview_window = tk.Toplevel(self.app.root)
        preview_window.title("Предпросмотр сортировки")
        preview_window.geometry("900x600")
        preview_window.configure(bg=self.app.colors['bg_main'])
        
        try:
            set_window_icon(preview_window, self.app._icon_photos)
        except (AttributeError, tk.TclError, OSError) as e:
            logger.debug(f"Не удалось установить иконку окна: {e}")
        except Exception as e:
            logger.warning(f"Неожиданная ошибка при установке иконки: {e}")
        
        main_frame = tk.Frame(preview_window, bg=self.app.colors['bg_main'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Заголовок
        header_frame = tk.Frame(main_frame, bg=self.app.colors['bg_main'])
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        tk.Label(header_frame, text="Предпросмотр сортировки файлов",
                font=('Robot', 12, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary']).pack(anchor=tk.W)
        
        tk.Label(header_frame, text=f"Папка: {folder_path}",
                font=('Robot', 9),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_secondary']).pack(anchor=tk.W, pady=(5, 0))
        
        # Таблица предпросмотра
        table_frame = tk.Frame(main_frame, bg=self.app.colors['bg_main'])
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Создаем Treeview для отображения предпросмотра
        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        
        columns = ("file", "destination", "status")
        preview_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            style='Custom.Treeview'
        )
        
        scrollbar_y.config(command=preview_tree.yview)
        scrollbar_x.config(command=preview_tree.xview)
        
        # Настройка колонок
        preview_tree.heading("file", text="Файл")
        preview_tree.heading("destination", text="Папка назначения")
        preview_tree.heading("status", text="Статус")
        
        preview_tree.column("file", width=200, anchor='w', minwidth=100)
        preview_tree.column("destination", width=200, anchor='w', minwidth=100)
        preview_tree.column("status", width=200, anchor='center', minwidth=100)
        
        # Теги для цветового выделения
        preview_tree.tag_configure('sorted', background='#D1FAE5', foreground='#065F46')
        preview_tree.tag_configure('unsorted', background='#FEF3C7', foreground='#92400E')
        preview_tree.tag_configure('error', background='#FEE2E2', foreground='#991B1B')
        
        # Размещение таблицы
        preview_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Статистика
        stats_frame = tk.Frame(main_frame, bg=self.app.colors['bg_main'])
        stats_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        stats_label = tk.Label(stats_frame, text="",
                               font=('Robot', 9, 'bold'),
                               bg=self.app.colors['bg_main'],
                               fg=self.app.colors['text_primary'],
                               anchor=tk.W)
        stats_label.pack(anchor=tk.W)
        
        # Обрабатываем файлы для предпросмотра
        sorted_count = 0
        unsorted_count = 0
        error_count = 0
        
        for file_path in files_to_sort:
            try:
                file_name = os.path.basename(file_path)
                matched = False
                destination = ""
                
                # Проверяем каждый фильтр
                for filter_data in enabled_filters:
                    if self.app.sorter_tab_handler.file_matches_filter(file_path, filter_data):
                        destination = filter_data['folder_name']
                        matched = True
                        sorted_count += 1
                        break
                
                if matched:
                    preview_tree.insert("", tk.END, values=(file_name, destination, "Будет отсортирован"),
                                      tags=('sorted',))
                else:
                    unsorted_count += 1
                    preview_tree.insert("", tk.END, values=(file_name, "-", "Не отсортирован"),
                                      tags=('unsorted',))
            
            except Exception as e:
                error_count += 1
                preview_tree.insert("", tk.END, values=(os.path.basename(file_path), "-", f"Ошибка: {e}"),
                                  tags=('error',))
        
        # Обновляем статистику
        total = len(files_to_sort)
        stats_text = f"Всего файлов: {total} | Будет отсортировано: {sorted_count} | Не отсортировано: {unsorted_count}"
        if error_count > 0:
            stats_text += f" | Ошибок: {error_count}"
        stats_label.config(text=stats_text)
        
        # Кнопка закрытия
        btn_close = self.app.create_rounded_button(
            main_frame, "❌ Закрыть", preview_window.destroy,
            self.app.colors['primary'], 'white',
            font=('Robot', 9, 'bold'), padx=15, pady=8,
            active_bg=self.app.colors['primary_hover'], expand=False)
        btn_close.grid(row=3, column=0, pady=(15, 0))
    
    def start_file_sorting(self):
        """Запуск сортировки файлов"""
        folder_path = self.app.sorter_folder_path.get()
        
        if not folder_path or not os.path.exists(folder_path):
            messagebox.showerror("Ошибка", "Укажите существующую папку для сортировки")
            return
        
        enabled_filters = [f for f in self.app.sorter_filters if f.get('enabled', True)]
        if not enabled_filters:
            messagebox.showwarning("Предупреждение", "Нет активных правил для сортировки")
            return
        
        if not messagebox.askyesno("Подтверждение",
                                   f"Начать сортировку файлов в папке:\n{folder_path}\n\n"
                                   f"Будет обработано {len(enabled_filters)} правил(а)?"):
            return
        
        # Запускаем сортировку в отдельном потоке
        thread = threading.Thread(
            target=self.sort_files_thread, 
            args=(folder_path, enabled_filters),
            daemon=True, 
            name="sort_files"
        )
        thread.start()
    
    def sort_files_thread(self, folder_path, filters):
        """Поток для сортировки файлов"""
        try:
            total_files = 0
            moved_files = 0
            errors = []
            
            # Собираем все файлы из папки
            files_to_sort = []
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    files_to_sort.append(item_path)
                    total_files += 1
            
            # Обрабатываем каждый файл
            for i, file_path in enumerate(files_to_sort):
                try:
                    file_name = os.path.basename(file_path)
                    file_ext = os.path.splitext(file_name)[1].lower()
                    
                    # Проверяем каждый фильтр
                    matched = False
                    for filter_data in filters:
                        if self.app.sorter_tab_handler.file_matches_filter(file_path, filter_data):
                            target_folder_name = filter_data['folder_name']
                            target_folder = os.path.join(folder_path, target_folder_name)
                            
                            # Создаем папку, если её нет
                            if not os.path.exists(target_folder):
                                os.makedirs(target_folder)
                            
                            # Перемещаем файл
                            target_path = os.path.join(target_folder, file_name)
                            
                            # Если файл с таким именем уже существует, добавляем номер
                            counter = 1
                            base_name, ext = os.path.splitext(file_name)
                            while os.path.exists(target_path):
                                new_name = f"{base_name}_{counter}{ext}"
                                target_path = os.path.join(target_folder, new_name)
                                counter += 1
                            
                            os.rename(file_path, target_path)
                            moved_files += 1
                            matched = True
                            break
                    
                except Exception as e:
                    error_msg = f"Ошибка при обработке {os.path.basename(file_path)}: {e}\n"
                    errors.append(error_msg)
            
            if moved_files > 0:
                self.app.root.after(0, lambda: messagebox.showinfo(
                    "Сортировка завершена",
                    f"Обработано файлов: {total_files}\n"
                    f"Перемещено: {moved_files}\n"
                    f"Ошибок: {len(errors)}"))
        
        except Exception as e:
            error_msg = f"Критическая ошибка: {e}"
            self.app.root.after(0, lambda: messagebox.showerror("Ошибка", error_msg))
            logger.error(f"Ошибка сортировки файлов: {e}", exc_info=True)
    
    def file_matches_filter(self, file_path, filter_data):
        """Проверка, соответствует ли файл фильтру"""
        filter_type = filter_data['type']
        filter_value = filter_data['value']
        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()
        
        if filter_type == 'extension':
            # Поддерживаем несколько расширений через запятую
            extensions = [ext.strip().lower() for ext in filter_value.split(',')]
            return file_ext in extensions or f".{file_ext}" in extensions
        
        elif filter_type == 'filename':
            # Проверка по имени файла
            file_name_lower = file_name.lower()
            filter_value_lower = filter_value.lower()
            
            if filter_value_lower.startswith('начинается с '):
                prefix = filter_value_lower.replace('начинается с ', '').strip()
                return file_name_lower.startswith(prefix)
            elif filter_value_lower.startswith('содержит '):
                substring = filter_value_lower.replace('содержит ', '').strip()
                return substring in file_name_lower
            else:
                # Простое совпадение
                return filter_value_lower in file_name_lower
        
        elif filter_type == 'size':
            # Проверка по размеру (требует парсинга строки типа ">10MB")
            try:
                file_size = os.path.getsize(file_path)
                # Упрощенная проверка (можно расширить)
                if '>' in filter_value or '<' in filter_value:
                    # Парсим размер
                    size_str = filter_value.replace('>', '').replace('<', '').strip().upper()
                    if 'MB' in size_str:
                        size_bytes = float(size_str.replace('MB', '')) * 1024 * 1024
                    elif 'KB' in size_str:
                        size_bytes = float(size_str.replace('KB', '')) * 1024
                    elif 'GB' in size_str:
                        size_bytes = float(size_str.replace('GB', '')) * 1024 * 1024 * 1024
                    else:
                        size_bytes = float(size_str)
                    
                    if '>' in filter_value:
                        return file_size > size_bytes
                    else:
                        return file_size < size_bytes
            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Ошибка при парсинге размера файла: {e}")
                return False
            except Exception as e:
                logger.warning(f"Неожиданная ошибка при проверке размера файла: {e}")
                return False
        
        elif filter_type == 'date':
            # Проверка по дате (упрощенная)
            try:
                file_mtime = os.path.getmtime(file_path)
                file_date = datetime.fromtimestamp(file_mtime).date()
                # Упрощенная проверка (можно расширить)
                return True  # Заглушка
            except (OSError, ValueError, TypeError) as e:
                logger.debug(f"Ошибка при получении даты файла: {e}")
                return False
            except Exception as e:
                logger.warning(f"Неожиданная ошибка при проверке даты файла: {e}")
                return False
        
        elif filter_type == 'mime':
            # Проверка по типу MIME (упрощенная, по расширению)
            return self.file_matches_filter(file_path, {
                'type': 'extension',
                'value': filter_value
            })
        
        return False


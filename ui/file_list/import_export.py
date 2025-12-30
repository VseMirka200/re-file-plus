"""Модуль импорта и экспорта списка файлов."""

import csv
import json
import logging
import os
from tkinter import filedialog, messagebox

from utils.path_processing import normalize_path

logger = logging.getLogger(__name__)


class ImportExportManager:
    """Класс для импорта и экспорта списка файлов."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def export_files_list(self) -> None:
        """Экспорт списка файлов в файл."""
        if not self.app.files:
            messagebox.showwarning("Предупреждение", "Список файлов пуст")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON файлы", "*.json"),
                ("CSV файлы", "*.csv"),
                ("Все файлы", "*.*")
            ],
            title="Экспорт списка файлов"
        )
        
        if not filename:
            return
        
        try:
            if filename.endswith('.csv'):
                # Экспорт в CSV
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'Старое имя',
                        'Новое имя',
                        'Расширение',
                        'Путь',
                        'Статус'
                    ])
                    for file_data in self.app.files:
                        writer.writerow([
                            file_data.get('old_name', ''),
                            file_data.get('new_name', ''),
                            file_data.get('path', ''),
                            file_data.get('status', 'Готов')
                        ])
            else:
                # Экспорт в JSON
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(
                        self.app.files,
                        f,
                        ensure_ascii=False,
                        indent=2
                    )
            
            messagebox.showinfo(
                "Успех",
                f"Список файлов экспортирован в:\n{filename}"
            )
            self.app.log(f"Список файлов экспортирован: {filename}")
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось экспортировать список файлов:\n{str(e)}"
            )
            logger.error(f"Ошибка экспорта списка файлов: {e}", exc_info=True)
    
    def import_files_list(self) -> None:
        """Импорт списка файлов из файла."""
        filename = filedialog.askopenfilename(
            filetypes=[
                ("JSON файлы", "*.json"),
                ("CSV файлы", "*.csv"),
                ("Все файлы", "*.*")
            ],
            title="Импорт списка файлов"
        )
        
        if not filename:
            return
        
        try:
            imported_files = []
            
            if filename.endswith('.csv'):
                # Импорт из CSV
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        file_path = row.get('Путь', '')
                        if file_path and os.path.exists(file_path) and os.path.isfile(file_path):
                            file_data = {
                                'path': file_path,
                                'full_path': file_path,
                                'old_name': row.get('Старое имя', ''),
                                'new_name': row.get('Новое имя', ''),
                                'extension': row.get('Расширение', ''),
                                'status': row.get('Статус', 'Готов')
                            }
                            imported_files.append(file_data)
            else:
                # Импорт из JSON
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for file_data in data:
                            file_path = (
                                file_data.get('path') or
                                file_data.get('full_path', '')
                            )
                            if (file_path and
                                    os.path.exists(file_path) and
                                    os.path.isfile(file_path)):
                                imported_files.append(file_data)
            
            if imported_files:
                # Добавляем файлы в список
                files_list = self.app._get_files_list()
                for file_data in imported_files:
                    # Проверяем на дубликаты
                    is_duplicate = False
                    file_path = file_data.get('full_path') or file_data.get('path', '')
                    if file_path:
                        file_path = normalize_path(file_path)
                        for existing_file in files_list:
                            existing_path = None
                            if hasattr(existing_file, 'full_path'):
                                existing_path = existing_file.full_path
                            elif isinstance(existing_file, dict):
                                existing_path = existing_file.get('full_path') or existing_file.get('path', '')
                            
                            if existing_path:
                                existing_path = normalize_path(existing_path)
                                if existing_path == file_path:
                                    is_duplicate = True
                                    break
                    
                    if not is_duplicate:
                        if self.app.state:
                            from core.domain.file_info import FileInfo
                            file_info = FileInfo.from_dict(file_data)
                            files_list.append(file_info)
                        else:
                            files_list.append(file_data)
                
                # Применяем методы, если они есть
                if self.app.methods_manager.get_methods():
                    self.app.apply_methods()
                else:
                    self.app.refresh_treeview()
                
                self.app.update_status()
                messagebox.showinfo(
                    "Успех",
                    f"Импортировано файлов: {len(imported_files)}"
                )
                self.app.log(f"Импортировано файлов: {len(imported_files)}")
            else:
                messagebox.showwarning(
                    "Предупреждение",
                    "Не найдено валидных файлов для импорта"
                )
        except Exception as e:
            messagebox.showerror(
                "Ошибка",
                f"Не удалось импортировать список файлов:\n{str(e)}"
            )
            logger.error(f"Ошибка импорта списка файлов: {e}", exc_info=True)


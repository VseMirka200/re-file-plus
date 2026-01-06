"""Обработчики операций сортировки файлов."""

import logging
import os
import shutil
from typing import List, Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class SorterWorker(QThread):
    """Поток для выполнения сортировки файлов."""
    
    progress = pyqtSignal(int, int)  # current, total
    file_processed = pyqtSignal(str, bool, str)  # file_path, success, message
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, app, files: List[str], target_folder: str, filters: List[Dict[str, Any]]):
        """Инициализация потока.
        
        Args:
            app: Экземпляр приложения
            files: Список путей к файлам для сортировки
            target_folder: Целевая папка для сортировки
            filters: Список фильтров
        """
        super().__init__()
        self.app = app
        self.files = files
        self.target_folder = target_folder
        self.filters = filters
        self.cancelled = False
    
    def cancel(self):
        """Отмена операции."""
        self.cancelled = True
    
    def _get_target_subfolder(self, file_path: str) -> str:
        """Определение подпапки для файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Имя подпапки или пустая строка
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        for filter_data in self.filters:
            if not filter_data.get('enabled', True):
                continue
            
            filter_type = filter_data.get('type', 'extension')
            filter_value = filter_data.get('value', '')
            
            if filter_type == 'extension':
                extensions = [ext.strip().lower() for ext in filter_value.split(',')]
                if file_ext in extensions:
                    return filter_data.get('folder_name', '')
        
        return ""
    
    def run(self):
        """Выполнение сортировки."""
        try:
            if not self.files:
                self.finished.emit(False, "Нет файлов для сортировки")
                return
            
            if not os.path.exists(self.target_folder):
                self.finished.emit(False, f"Папка назначения не существует: {self.target_folder}")
                return
            
            total = len(self.files)
            success_count = 0
            error_count = 0
            
            for i, file_path in enumerate(self.files):
                if self.cancelled:
                    self.finished.emit(False, "Операция отменена")
                    return
                
                try:
                    if not os.path.exists(file_path):
                        error_count += 1
                        self.file_processed.emit(
                            file_path,
                            False,
                            "Файл не найден"
                        )
                        continue
                    
                    # Определяем подпапку
                    subfolder_name = self._get_target_subfolder(file_path)
                    if not subfolder_name:
                        error_count += 1
                        self.file_processed.emit(
                            file_path,
                            False,
                            "Не определен фильтр"
                        )
                        continue
                    
                    # Создаем подпапку если нужно
                    target_subfolder = os.path.join(self.target_folder, subfolder_name)
                    os.makedirs(target_subfolder, exist_ok=True)
                    
                    # Определяем путь назначения
                    target_path = os.path.join(target_subfolder, os.path.basename(file_path))
                    
                    # Если файл уже существует, добавляем номер
                    counter = 1
                    base_target = target_path
                    while os.path.exists(target_path):
                        base_name, ext = os.path.splitext(base_target)
                        target_path = f"{base_name}_{counter}{ext}"
                        counter += 1
                    
                    # Перемещаем файл
                    shutil.move(file_path, target_path)
                    success_count += 1
                    self.file_processed.emit(
                        file_path,
                        True,
                        f"Перемещен в {subfolder_name}"
                    )
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Ошибка при сортировке {file_path}: {e}", exc_info=True)
                    self.file_processed.emit(
                        file_path,
                        False,
                        f"Ошибка: {str(e)}"
                    )
                
                self.progress.emit(i + 1, total)
            
            message = f"Отсортировано: {success_count}, ошибок: {error_count}"
            self.finished.emit(success_count > 0, message)
            
        except Exception as e:
            logger.error(f"Критическая ошибка при сортировке: {e}", exc_info=True)
            self.finished.emit(False, f"Критическая ошибка: {str(e)}")


"""Обработчики операций сжатия файлов."""

import logging
import os
import zipfile
from typing import List
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class ZipWorker(QThread):
    """Поток для выполнения сжатия файлов."""
    
    progress = pyqtSignal(int, int)  # current, total
    file_processed = pyqtSignal(str, bool, str)  # file_path, success, message
    finished = pyqtSignal(bool, str, str)  # success, message, zip_path
    
    def __init__(self, app, files: List[str], compression_level: int = 6, output_path: str = None):
        """Инициализация потока.
        
        Args:
            app: Экземпляр приложения
            files: Список путей к файлам для сжатия
            compression_level: Уровень сжатия (0-9)
            output_path: Путь для сохранения ZIP файла
        """
        super().__init__()
        self.app = app
        self.files = files
        self.compression_level = compression_level
        self.output_path = output_path
        self.cancelled = False
    
    def cancel(self):
        """Отмена операции."""
        self.cancelled = True
    
    def run(self):
        """Выполнение сжатия."""
        try:
            if not self.files:
                self.finished.emit(False, "Нет файлов для сжатия", "")
                return
            
            # Определяем путь для сохранения ZIP
            if not self.output_path:
                # Используем директорию первого файла
                first_file_dir = os.path.dirname(self.files[0])
                zip_name = "Архив.zip"
                self.output_path = os.path.join(first_file_dir, zip_name)
                
                # Если файл существует, добавляем номер
                counter = 1
                base_path = self.output_path
                while os.path.exists(self.output_path):
                    base_name = os.path.splitext(base_path)[0]
                    self.output_path = f"{base_name}_{counter}.zip"
                    counter += 1
            
            total = len(self.files)
            success_count = 0
            error_count = 0
            
            try:
                with zipfile.ZipFile(self.output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=self.compression_level) as zipf:
                    for i, file_path in enumerate(self.files):
                        if self.cancelled:
                            self.finished.emit(False, "Операция отменена", "")
                            return
                        
                        try:
                            if os.path.exists(file_path):
                                if os.path.isfile(file_path):
                                    # Добавляем файл в архив
                                    arcname = os.path.basename(file_path)
                                    zipf.write(file_path, arcname)
                                    success_count += 1
                                    self.file_processed.emit(
                                        file_path,
                                        True,
                                        "Добавлен в архив"
                                    )
                                elif os.path.isdir(file_path):
                                    # Добавляем директорию в архив
                                    for root, dirs, filenames in os.walk(file_path):
                                        for filename in filenames:
                                            file_full_path = os.path.join(root, filename)
                                            arcname = os.path.relpath(file_full_path, os.path.dirname(file_path))
                                            zipf.write(file_full_path, arcname)
                                    success_count += 1
                                    self.file_processed.emit(
                                        file_path,
                                        True,
                                        "Директория добавлена в архив"
                                    )
                                else:
                                    error_count += 1
                                    self.file_processed.emit(
                                        file_path,
                                        False,
                                        "Неизвестный тип"
                                    )
                            else:
                                error_count += 1
                                self.file_processed.emit(
                                    file_path,
                                    False,
                                    "Файл не найден"
                                )
                        except Exception as e:
                            error_count += 1
                            logger.error(f"Ошибка при добавлении {file_path} в архив: {e}", exc_info=True)
                            self.file_processed.emit(
                                file_path,
                                False,
                                f"Ошибка: {str(e)}"
                            )
                        
                        self.progress.emit(i + 1, total)
                
                message = f"Создан архив: {os.path.basename(self.output_path)}. Файлов: {success_count}, ошибок: {error_count}"
                self.finished.emit(success_count > 0, message, self.output_path)
                
            except Exception as e:
                logger.error(f"Ошибка при создании архива: {e}", exc_info=True)
                self.finished.emit(False, f"Ошибка создания архива: {str(e)}", "")
            
        except Exception as e:
            logger.error(f"Критическая ошибка при сжатии: {e}", exc_info=True)
            self.finished.emit(False, f"Критическая ошибка: {str(e)}", "")


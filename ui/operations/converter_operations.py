"""Обработчики операций конвертации файлов."""

import logging
import os
from typing import List, Dict, Optional
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class ConverterFile:
    """Класс для хранения информации о файле для конвертации."""
    
    def __init__(self, file_path: str, target_format: Optional[str] = None):
        """Инициализация.
        
        Args:
            file_path: Путь к файлу
            target_format: Целевой формат (расширение с точкой)
        """
        self.file_path = file_path
        self.source_format = os.path.splitext(file_path)[1].lower()
        self.target_format = target_format or self.source_format
        self.status = "Готов"
        self.output_path = None


class ConverterWorker(QThread):
    """Поток для выполнения конвертации файлов."""
    
    progress = pyqtSignal(int, int)  # current, total
    file_processed = pyqtSignal(str, bool, str)  # file_path, success, message
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, app, files: List[ConverterFile]):
        """Инициализация потока.
        
        Args:
            app: Экземпляр приложения
            files: Список файлов для конвертации
        """
        super().__init__()
        self.app = app
        self.files = files
        self.cancelled = False
    
    def cancel(self):
        """Отмена операции."""
        self.cancelled = True
    
    def run(self):
        """Выполнение конвертации."""
        try:
            if not hasattr(self.app, 'file_converter') or not self.app.file_converter:
                self.finished.emit(False, "Конвертер файлов не инициализирован")
                return
            
            total = len(self.files)
            success_count = 0
            error_count = 0
            
            for i, converter_file in enumerate(self.files):
                if self.cancelled:
                    self.finished.emit(False, "Операция отменена")
                    return
                
                try:
                    # Определяем путь для сохранения
                    output_path = None
                    if converter_file.target_format != converter_file.source_format:
                        base_name = os.path.splitext(converter_file.file_path)[0]
                        output_path = base_name + converter_file.target_format
                    
                    # Выполняем конвертацию
                    success, message, converted_path = self.app.file_converter.convert(
                        converter_file.file_path,
                        converter_file.target_format,
                        output_path
                    )
                    
                    if success:
                        success_count += 1
                        converter_file.status = "Успешно"
                        converter_file.output_path = converted_path
                        self.file_processed.emit(
                            converter_file.file_path,
                            True,
                            f"Конвертирован в {converter_file.target_format}"
                        )
                    else:
                        error_count += 1
                        converter_file.status = f"Ошибка: {message}"
                        self.file_processed.emit(
                            converter_file.file_path,
                            False,
                            message
                        )
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Ошибка при конвертации {converter_file.file_path}: {e}", exc_info=True)
                    converter_file.status = f"Ошибка: {str(e)}"
                    self.file_processed.emit(
                        converter_file.file_path,
                        False,
                        f"Ошибка: {str(e)}"
                    )
                
                self.progress.emit(i + 1, total)
            
            message = f"Конвертировано: {success_count}, ошибок: {error_count}"
            self.finished.emit(success_count > 0, message)
            
        except Exception as e:
            logger.error(f"Критическая ошибка при конвертации: {e}", exc_info=True)
            self.finished.emit(False, f"Критическая ошибка: {str(e)}")


"""Обработчики операций переименования файлов."""

import logging
from typing import List, Optional
from PyQt6.QtCore import QThread, pyqtSignal
from core.domain.file_info import FileInfo
from core.re_file_methods import ReFileMethod

logger = logging.getLogger(__name__)


class ReFileWorker(QThread):
    """Поток для выполнения переименования файлов."""
    
    progress = pyqtSignal(int, int)  # current, total
    file_processed = pyqtSignal(str, bool, str)  # file_path, success, message
    finished = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, app, files: List[FileInfo], methods: List[ReFileMethod]):
        """Инициализация потока.
        
        Args:
            app: Экземпляр приложения
            files: Список файлов для переименования
            methods: Список методов для применения
        """
        super().__init__()
        self.app = app
        self.files = files
        self.methods = methods
        self.cancelled = False
    
    def cancel(self):
        """Отмена операции."""
        self.cancelled = True
    
    def run(self):
        """Выполнение переименования."""
        try:
            if not hasattr(self.app, 're_file_service') or not self.app.re_file_service:
                self.finished.emit(False, "Сервис переименования не инициализирован")
                return
            
            total = len(self.files)
            success_count = 0
            error_count = 0
            
            # Применяем методы к файлам
            for i, file_info in enumerate(self.files):
                if self.cancelled:
                    self.finished.emit(False, "Операция отменена")
                    return
                
                try:
                    # Применяем методы
                    new_name = file_info.old_name
                    new_ext = file_info.extension
                    
                    for method in self.methods:
                        new_name, new_ext = method.apply(
                            new_name, new_ext, str(file_info.path)
                        )
                    
                    file_info.new_name = new_name
                    file_info.extension = new_ext
                    
                    # Проверяем, нужно ли переименование
                    if file_info.is_renamed():
                        # Выполняем переименование
                        result = self.app.re_file_service.re_file_files(
                            [file_info],
                            self.methods,
                            dry_run=False
                        )
                        
                        if result.success_count > 0:
                            success_count += 1
                            self.file_processed.emit(
                                str(file_info.path),
                                True,
                                "Файл успешно переименован"
                            )
                        else:
                            error_count += 1
                            error_msg = result.errors[0].error_message if result.errors else "Неизвестная ошибка"
                            self.file_processed.emit(
                                str(file_info.path),
                                False,
                                error_msg
                            )
                    else:
                        self.file_processed.emit(
                            str(file_info.path),
                            True,
                            "Имя не изменилось"
                        )
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Ошибка при переименовании {file_info.path}: {e}", exc_info=True)
                    self.file_processed.emit(
                        str(file_info.path),
                        False,
                        f"Ошибка: {str(e)}"
                    )
                
                self.progress.emit(i + 1, total)
            
            message = f"Переименовано: {success_count}, ошибок: {error_count}"
            self.finished.emit(success_count > 0, message)
            
        except Exception as e:
            logger.error(f"Критическая ошибка при переименовании: {e}", exc_info=True)
            self.finished.emit(False, f"Критическая ошибка: {str(e)}")


class ApplyMethodsWorker(QThread):
    """Поток для применения методов к файлам (предпросмотр)."""
    
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal()
    
    def __init__(self, app, files: List[FileInfo], methods: List[ReFileMethod]):
        """Инициализация потока.
        
        Args:
            app: Экземпляр приложения
            files: Список файлов
            methods: Список методов
        """
        super().__init__()
        self.app = app
        self.files = files
        self.methods = methods
    
    def run(self):
        """Применение методов."""
        try:
            total = len(self.files)
            
            for i, file_info in enumerate(self.files):
                try:
                    # Применяем методы
                    new_name = file_info.old_name
                    new_ext = file_info.extension
                    
                    for method in self.methods:
                        new_name, new_ext = method.apply(
                            new_name, new_ext, str(file_info.path)
                        )
                    
                    file_info.new_name = new_name
                    file_info.extension = new_ext
                    file_info.set_ready()
                    
                except Exception as e:
                    logger.error(f"Ошибка при применении методов к {file_info.path}: {e}", exc_info=True)
                    file_info.set_error(f"Ошибка: {str(e)}")
                
                self.progress.emit(i + 1, total)
            
            self.finished.emit()
            
        except Exception as e:
            logger.error(f"Критическая ошибка при применении методов: {e}", exc_info=True)
            self.finished.emit()


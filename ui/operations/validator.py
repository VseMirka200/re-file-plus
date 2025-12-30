"""Модуль валидации файлов для re-file операций."""

import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)


class FileValidator:
    """Класс для валидации файлов перед re-file операциями."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def validate_all_files(self) -> Tuple[bool, List[str]]:
        """Валидация всех файлов в списке.
        
        Returns:
            Кортеж (все файлы валидны, список ошибок)
        """
        from core.re_file_methods import validate_filename
        
        errors = []
        files_list = self.app._get_files_list() if hasattr(self.app, '_get_files_list') else self.app.files
        
        for i, file_data in enumerate(files_list):
            # Безопасный доступ к данным файла
            if hasattr(file_data, 'new_name'):
                new_name = file_data.new_name or ''
                extension = file_data.extension or ''
                file_path = str(file_data.path) if hasattr(file_data, 'path') else (file_data.full_path if hasattr(file_data, 'full_path') else '')
            elif isinstance(file_data, dict):
                new_name = file_data.get('new_name', '') or ''
                extension = file_data.get('extension', '') or ''
                file_path = file_data.get('path') or file_data.get('full_path', '')
            else:
                continue
            
            # Валидация имени
            validation_name = new_name if new_name else (extension.lstrip('.') if extension else 'file')
            status = validate_filename(validation_name, extension, file_path, i)
            
            if status != 'Готов':
                errors.append(f"Файл {i+1}: {status}")
        
        return len(errors) == 0, errors


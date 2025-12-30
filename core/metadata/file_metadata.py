"""Модуль извлечения общих метаданных файлов.

Содержит функции для извлечения общих метаданных файлов:
- Даты создания и изменения
- Размер файла
- Информация о пути (имя файла, папка, родительская папка)
- Компоненты даты (год, месяц, день, час, минута, секунда)
"""

import logging
import os
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class FileMetadataExtractor:
    """Класс для извлечения общих метаданных файлов."""
    
    def extract_date_created(self, file_path: str) -> Optional[str]:
        """Извлечение даты создания файла.
        
        Returns:
            Дата создания в формате YYYY-MM-DD или None
        """
        try:
            stat = os.stat(file_path)
            if hasattr(stat, 'st_birthtime'):
                timestamp = stat.st_birthtime
            else:
                timestamp = stat.st_ctime
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d")
        except Exception as e:
            logger.debug(f"Не удалось извлечь дату создания {file_path}: {e}")
            return None
    
    def extract_date_modified(self, file_path: str) -> Optional[str]:
        """Извлечение даты изменения файла.
        
        Returns:
            Дата изменения в формате YYYY-MM-DD или None
        """
        try:
            stat = os.stat(file_path)
            timestamp = stat.st_mtime
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d")
        except Exception as e:
            logger.debug(f"Не удалось извлечь дату изменения {file_path}: {e}")
            return None
    
    def extract_date_created_time(self, file_path: str) -> Optional[str]:
        """Извлечение даты и времени создания файла.
        
        Returns:
            Дата и время создания в формате YYYY-MM-DD_HH-MM-SS или None
        """
        try:
            stat = os.stat(file_path)
            if hasattr(stat, 'st_birthtime'):
                timestamp = stat.st_birthtime
            else:
                timestamp = stat.st_ctime
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d_%H-%M-%S")
        except Exception as e:
            logger.debug(f"Не удалось извлечь дату и время создания {file_path}: {e}")
            return None
    
    def extract_date_modified_time(self, file_path: str) -> Optional[str]:
        """Извлечение даты и времени изменения файла.
        
        Returns:
            Дата и время изменения в формате YYYY-MM-DD_HH-MM-SS или None
        """
        try:
            stat = os.stat(file_path)
            timestamp = stat.st_mtime
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d_%H-%M-%S")
        except Exception as e:
            logger.debug(f"Не удалось извлечь дату и время изменения {file_path}: {e}")
            return None
    
    def extract_file_size(self, file_path: str) -> Optional[str]:
        """Извлечение размера файла.
        
        Returns:
            Размер файла в отформатированном виде (B, KB, MB, GB) или None
        """
        try:
            size = os.path.getsize(file_path)
            
            if size < 1024:
                return f"{size}B"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f}KB"
            elif size < 1024 * 1024 * 1024:
                return f"{size / (1024 * 1024):.1f}MB"
            else:
                return f"{size / (1024 * 1024 * 1024):.1f}GB"
        except Exception as e:
            logger.debug(f"Не удалось извлечь размер файла {file_path}: {e}")
            return None
    
    def extract_format(self, file_path: str) -> Optional[str]:
        """Извлечение формата файла (расширение без точки)."""
        try:
            _, ext = os.path.splitext(file_path)
            return ext.lstrip('.').upper() if ext else None
        except Exception:
            return None
    
    def extract_filename(self, file_path: str) -> Optional[str]:
        """Извлечение имени файла."""
        return os.path.basename(file_path)
    
    def extract_dirname(self, file_path: str) -> Optional[str]:
        """Извлечение имени папки."""
        return os.path.basename(os.path.dirname(file_path))
    
    def extract_parent_dir(self, file_path: str) -> Optional[str]:
        """Извлечение родительской папки."""
        return os.path.dirname(file_path)
    
    def extract_year(self, file_path: str) -> Optional[str]:
        """Извлечение года создания файла."""
        try:
            stat = os.stat(file_path)
            if hasattr(stat, 'st_birthtime'):
                timestamp = stat.st_birthtime
            else:
                timestamp = stat.st_ctime
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y")
        except Exception:
            return None
    
    def extract_month(self, file_path: str) -> Optional[str]:
        """Извлечение месяца создания файла."""
        try:
            stat = os.stat(file_path)
            if hasattr(stat, 'st_birthtime'):
                timestamp = stat.st_birthtime
            else:
                timestamp = stat.st_ctime
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%m")
        except Exception:
            return None
    
    def extract_day(self, file_path: str) -> Optional[str]:
        """Извлечение дня создания файла."""
        try:
            stat = os.stat(file_path)
            if hasattr(stat, 'st_birthtime'):
                timestamp = stat.st_birthtime
            else:
                timestamp = stat.st_ctime
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%d")
        except Exception:
            return None
    
    def extract_hour(self, file_path: str) -> Optional[str]:
        """Извлечение часа создания файла."""
        try:
            stat = os.stat(file_path)
            if hasattr(stat, 'st_birthtime'):
                timestamp = stat.st_birthtime
            else:
                timestamp = stat.st_ctime
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%H")
        except Exception:
            return None
    
    def extract_minute(self, file_path: str) -> Optional[str]:
        """Извлечение минуты создания файла."""
        try:
            stat = os.stat(file_path)
            if hasattr(stat, 'st_birthtime'):
                timestamp = stat.st_birthtime
            else:
                timestamp = stat.st_ctime
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%M")
        except Exception:
            return None
    
    def extract_second(self, file_path: str) -> Optional[str]:
        """Извлечение секунды создания файла."""
        try:
            stat = os.stat(file_path)
            if hasattr(stat, 'st_birthtime'):
                timestamp = stat.st_birthtime
            else:
                timestamp = stat.st_ctime
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%S")
        except Exception:
            return None


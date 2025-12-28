"""Валидатор путей к файлам и директориям."""

import os
import logging
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


class PathValidator:
    """Класс для валидации путей к файлам и директориям."""
    
    @staticmethod
    def is_safe_path(
        path: str,
        allowed_dirs: Optional[List[str]] = None,
        must_exist: bool = True,
        must_be_file: bool = True
    ) -> bool:
        """Проверка безопасности пути.
        
        Args:
            path: Путь к файлу для проверки
            allowed_dirs: Список разрешенных директорий (опционально)
            must_exist: Должен ли путь существовать
            must_be_file: Должен ли путь указывать на файл (True) или директорию (False)
            
        Returns:
            True если путь безопасен, False в противном случае
        """
        try:
            # Проверка типа
            if not isinstance(path, str):
                return False
            if not path or not path.strip():
                return False
            
            # Проверка на NULL байты (могут использоваться для обхода проверок)
            if '\0' in path:
                return False
            
            # Улучшенная проверка на path traversal
            # Проверяем, что '..' не является частью пути (не в имени файла)
            path_parts = path.split(os.sep)
            if '..' in path_parts or path.startswith('~'):
                return False
            
            # Проверка на абсолютные пути с символами подстановки
            if os.path.isabs(path):
                # Проверяем на использование символов подстановки в пути
                if '*' in path or '?' in path:
                    return False
            
            # Нормализуем путь
            abs_path = os.path.abspath(path)
            
            # Проверка существования
            if must_exist:
                if not os.path.exists(abs_path):
                    return False
                
                # Проверяем тип (файл или директория)
                if must_be_file:
                    if not os.path.isfile(abs_path):
                        return False
                else:
                    if not os.path.isdir(abs_path):
                        return False
            
            # Если указаны разрешенные директории, проверяем
            if allowed_dirs:
                for allowed_dir in allowed_dirs:
                    allowed_abs = os.path.abspath(allowed_dir)
                    if abs_path.startswith(allowed_abs):
                        return True
                return False
            
            return True
        except (OSError, ValueError, TypeError) as e:
            logger.debug(f"Ошибка валидации пути {path}: {e}")
            return False
    
    @staticmethod
    def validate_paths(
        paths: List[str],
        allowed_dirs: Optional[List[str]] = None,
        must_exist: bool = True,
        must_be_file: bool = True
    ) -> List[str]:
        """Валидация списка путей.
        
        Args:
            paths: Список путей для валидации
            allowed_dirs: Список разрешенных директорий
            must_exist: Должны ли пути существовать
            must_be_file: Должны ли пути указывать на файлы
            
        Returns:
            Список валидных путей
        """
        valid_paths = []
        for path in paths:
            if PathValidator.is_safe_path(path, allowed_dirs, must_exist, must_be_file):
                valid_paths.append(path)
            else:
                logger.warning(f"Небезопасный путь отклонен: {path}")
        return valid_paths
    
    @staticmethod
    def normalize_path(path: str) -> Optional[Path]:
        """Нормализация пути с использованием pathlib.
        
        Args:
            path: Путь для нормализации
            
        Returns:
            Нормализованный Path объект или None если путь невалиден
        """
        try:
            if not path or not isinstance(path, str):
                return None
            return Path(path).resolve()
        except (OSError, ValueError) as e:
            logger.debug(f"Ошибка нормализации пути {path}: {e}")
            return None


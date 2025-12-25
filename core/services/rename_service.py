"""Сервис переименования файлов."""

import logging
import os
from typing import List, Optional

from core.domain.file_info import FileInfo, FileStatus
from core.domain.rename_result import RenameResult, RenamedFile
from core.rename_methods.base import RenameMethod
from core.rename_methods import validate_filename

logger = logging.getLogger(__name__)


class RenameService:
    """Сервис переименования файлов.
    
    Унифицированная логика для CLI и GUI.
    """
    
    def __init__(
        self,
        metadata_extractor=None,
        backup_manager=None
    ):
        """Инициализация сервиса.
        
        Args:
            metadata_extractor: Экстрактор метаданных (опционально)
            backup_manager: Менеджер резервных копий (опционально)
        """
        self.metadata_extractor = metadata_extractor
        self.backup_manager = backup_manager
    
    def rename_files(
        self,
        files: List[FileInfo],
        methods: List[RenameMethod],
        dry_run: bool = False
    ) -> RenameResult:
        """Переименование файлов.
        
        Args:
            files: Список файлов для переименования
            methods: Список методов переименования
            dry_run: Только предпросмотр без переименования
            
        Returns:
            Результат переименования
        """
        result = RenameResult()
        
        for file in files:
            try:
                # Начинаем с исходного имени
                new_name = file.old_name
                new_ext = file.extension
                
                # Применяем методы переименования
                for method in methods:
                    new_name, new_ext = method.apply(
                        new_name, new_ext, str(file.path)
                    )
                
                # Обновляем файл
                file.new_name = new_name
                file.extension = new_ext
                
                # Валидация
                validation_status = validate_filename(
                    new_name, new_ext, str(file.path), 0
                )
                
                if validation_status != 'Готов':
                    file.set_error(validation_status)
                    result.add_error(file, validation_status)
                    continue
                
                # Проверяем, изменилось ли имя
                if not file.is_renamed():
                    # Имя не изменилось, пропускаем
                    continue
                
                # Переименование
                if not dry_run:
                    try:
                        new_path = file.new_path
                        # Проверяем, не существует ли уже файл с таким именем
                        if new_path.exists():
                            error_msg = f"Файл '{file.new_full_name}' уже существует"
                            file.set_error(error_msg)
                            result.add_error(file, error_msg)
                            continue
                        
                        # Создаем резервную копию, если нужно
                        if self.backup_manager:
                            try:
                                self.backup_manager.create_backup(str(file.path))
                            except Exception as e:
                                logger.warning(f"Не удалось создать резервную копию: {e}")
                        
                        # Выполняем переименование
                        file.path.rename(new_path)
                        file.path = new_path
                        file.set_ready()
                        
                        result.add_success(file, str(new_path))
                    except Exception as e:
                        error_msg = str(e)
                        file.set_error(error_msg)
                        result.add_error(file, error_msg)
                else:
                    # Только предпросмотр
                    result.add_success(file, str(file.new_path), preview=True)
                    file.set_ready()
                
            except Exception as e:
                error_msg = f"Ошибка обработки файла: {str(e)}"
                file.set_error(error_msg)
                result.add_error(file, error_msg)
                logger.error(f"Ошибка переименования {file.path}: {e}", exc_info=True)
        
        return result


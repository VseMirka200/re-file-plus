"""Основной класс извлечения метаданных из файлов.

Объединяет все модули извлечения метаданных в единый интерфейс.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

from .image_metadata import ImageMetadataExtractor
from .file_metadata import FileMetadataExtractor


class MetadataExtractor:
    """Класс для извлечения метаданных из файлов."""
    
    def __init__(self):
        """Инициализация экстрактора метаданных."""
        self.image_extractor = ImageMetadataExtractor()
        self.file_extractor = FileMetadataExtractor()
    
    def clear_cache(self):
        """Очистка кэша метаданных."""
        self.image_extractor.clear_cache()
    
    def extract(self, tag: str, file_path: str) -> Optional[str]:
        """Извлечение значения метаданных по тегу.
        
        Args:
            tag: Тег метаданных (например, "{width}x{height}", "{date_created}")
            file_path: Путь к файлу
            
        Returns:
            Значение метаданных в виде строки или None
        """
        if not os.path.exists(file_path):
            return None
        
        # Обработка составных тегов
        if "x" in tag and "{width}" in tag and "{height}" in tag:
            return self.image_extractor.extract_dimensions(file_path)
        
        # Обработка отдельных тегов
        if tag == "{width}":
            return self.image_extractor.extract_width(file_path)
        elif tag == "{height}":
            return self.image_extractor.extract_height(file_path)
        elif tag == "{date_created}" or tag == "{date}":
            return self.file_extractor.extract_date_created(file_path)
        elif tag == "{date_modified}":
            return self.file_extractor.extract_date_modified(file_path)
        elif tag == "{date_created_time}":
            return self.file_extractor.extract_date_created_time(file_path)
        elif tag == "{date_modified_time}":
            return self.file_extractor.extract_date_modified_time(file_path)
        elif tag == "{year}":
            return self.file_extractor.extract_year(file_path)
        elif tag == "{month}":
            return self.file_extractor.extract_month(file_path)
        elif tag == "{day}":
            return self.file_extractor.extract_day(file_path)
        elif tag == "{hour}":
            return self.file_extractor.extract_hour(file_path)
        elif tag == "{minute}":
            return self.file_extractor.extract_minute(file_path)
        elif tag == "{second}":
            return self.file_extractor.extract_second(file_path)
        elif tag == "{file_size}":
            return self.file_extractor.extract_file_size(file_path)
        elif tag == "{filename}":
            return self.file_extractor.extract_filename(file_path)
        elif tag == "{dirname}":
            return self.file_extractor.extract_dirname(file_path)
        elif tag == "{parent_dir}":
            return self.file_extractor.extract_parent_dir(file_path)
        elif tag == "{format}":
            return self.file_extractor.extract_format(file_path)
        # Метаданные изображений (EXIF)
        elif tag == "{camera}":
            return self.image_extractor.extract_camera(file_path)
        elif tag == "{iso}":
            return self.image_extractor.extract_iso(file_path)
        elif tag == "{focal_length}":
            return self.image_extractor.extract_focal_length(file_path)
        elif tag == "{aperture}":
            return self.image_extractor.extract_aperture(file_path)
        elif tag == "{exposure_time}":
            return self.image_extractor.extract_exposure_time(file_path)
        elif tag.startswith("{") and tag.endswith("}"):
            # Попытка извлечь пользовательский тег
            return self._extract_custom_tag(tag, file_path)
        
        return None
    
    def _extract_custom_tag(self, tag: str, file_path: str) -> Optional[str]:
        """Извлечение пользовательского тега (расширяемая функция)."""
        if not self.image_extractor.Image:
            return None
        
        image_data = self.image_extractor.get_image_data(file_path)
        if image_data:
            _, _, exifdata = image_data
            if exifdata:
                for tag_id, value in exifdata.items():
                    tag_name = self.image_extractor.TAGS.get(tag_id, tag_id)
                    if tag.lower() == f"{{{tag_name.lower()}}}":
                        return str(value)
        
        return None


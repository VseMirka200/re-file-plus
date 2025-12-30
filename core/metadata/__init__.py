"""Модуль извлечения метаданных из файлов.

Разбит на подмодули для лучшей организации кода:
- extractor: Основной класс MetadataExtractor
- image_metadata: Метаданные изображений (EXIF, размеры)
- file_metadata: Общие метаданные файлов (даты, размер, путь)
"""

from .extractor import MetadataExtractor

__all__ = ['MetadataExtractor']


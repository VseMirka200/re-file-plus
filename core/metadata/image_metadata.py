"""Модуль извлечения метаданных изображений.

Содержит функции для извлечения метаданных из изображений:
- Размеры (ширина, высота)
- EXIF данные (камера, ISO, фокусное расстояние, диафрагма, выдержка)
"""

import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ImageMetadataExtractor:
    """Класс для извлечения метаданных изображений."""
    
    def __init__(self):
        """Инициализация."""
        self._image_cache: Dict[str, Tuple[int, int, Optional[object]]] = {}
        
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            self.Image = Image
            self.TAGS = TAGS
        except ImportError:
            self.Image = None
            self.TAGS = None
    
    def clear_cache(self):
        """Очистка кэша метаданных изображений."""
        self._image_cache.clear()
    
    def get_image_data(self, file_path: str) -> Optional[Tuple[int, int, Optional[object]]]:
        """Получение данных изображения с кэшированием.
        
        Args:
            file_path: Путь к файлу изображения
            
        Returns:
            Кортеж (width, height, exifdata) или None
        """
        if not self.Image:
            return None
        
        if file_path in self._image_cache:
            return self._image_cache[file_path]
        
        try:
            with self.Image.open(file_path) as img:
                width, height = img.size
                exifdata = img.getexif()
                result = (width, height, exifdata)
                self._image_cache[file_path] = result
                return result
        except (OSError, PermissionError, IOError, FileNotFoundError) as e:
            logger.debug(f"Ошибка доступа при извлечении данных изображения {file_path}: {e}")
            return None
        except (ValueError, TypeError, AttributeError) as e:
            logger.debug(f"Ошибка данных при извлечении данных изображения {file_path}: {e}")
            return None
        except (MemoryError, RecursionError) as e:

            # Ошибки памяти/рекурсии

            pass

        # Финальный catch для неожиданных исключений (критично для стабильности)

        except BaseException as e:

            if isinstance(e, (KeyboardInterrupt, SystemExit)):

                raise
            logger.debug(f"Неожиданная ошибка при извлечении данных изображения {file_path}: {e}")
            return None
    
    def extract_dimensions(self, file_path: str) -> Optional[str]:
        """Извлечение размеров изображения (ширина x высота)."""
        image_data = self.get_image_data(file_path)
        if image_data:
            width, height, _ = image_data
            return f"{width}x{height}"
        return None
    
    def extract_width(self, file_path: str) -> Optional[str]:
        """Извлечение ширины изображения."""
        image_data = self.get_image_data(file_path)
        if image_data:
            return str(image_data[0])
        return None
    
    def extract_height(self, file_path: str) -> Optional[str]:
        """Извлечение высоты изображения."""
        image_data = self.get_image_data(file_path)
        if image_data:
            return str(image_data[1])
        return None
    
    def extract_camera(self, file_path: str) -> Optional[str]:
        """Извлечение модели камеры из EXIF данных."""
        if not self.Image:
            return None
        
        image_data = self.get_image_data(file_path)
        if image_data:
            _, _, exifdata = image_data
            if exifdata:
                make_tag = 271  # Make
                model_tag = 272  # Model
                
                make = exifdata.get(make_tag)
                model = exifdata.get(model_tag)
                
                if make and model:
                    return f"{make} {model}".strip()
                elif make:
                    return str(make).strip()
                elif model:
                    return str(model).strip()
        
        return None
    
    def extract_iso(self, file_path: str) -> Optional[str]:
        """Извлечение ISO из EXIF данных."""
        if not self.Image:
            return None
        
        image_data = self.get_image_data(file_path)
        if image_data:
            _, _, exifdata = image_data
            if exifdata:
                iso_tag = 34855  # ISOSpeedRatings
                iso = exifdata.get(iso_tag)
                if iso:
                    return str(iso)
        
        return None
    
    def extract_focal_length(self, file_path: str) -> Optional[str]:
        """Извлечение фокусного расстояния из EXIF данных."""
        if not self.Image:
            return None
        
        image_data = self.get_image_data(file_path)
        if image_data:
            _, _, exifdata = image_data
            if exifdata:
                focal_tag = 37386  # FocalLength
                focal = exifdata.get(focal_tag)
                if focal:
                    if isinstance(focal, tuple) and len(focal) == 2:
                        return f"{focal[0]/focal[1]:.1f}mm"
                    return f"{focal}mm"
        
        return None
    
    def extract_aperture(self, file_path: str) -> Optional[str]:
        """Извлечение диафрагмы из EXIF данных."""
        if not self.Image:
            return None
        
        image_data = self.get_image_data(file_path)
        if image_data:
            _, _, exifdata = image_data
            if exifdata:
                aperture_tag = 37378  # FNumber
                aperture = exifdata.get(aperture_tag)
                if aperture:
                    if isinstance(aperture, tuple) and len(aperture) == 2:
                        return f"f/{aperture[0]/aperture[1]:.1f}"
                    return f"f/{aperture}"
        
        return None
    
    def extract_exposure_time(self, file_path: str) -> Optional[str]:
        """Извлечение выдержки из EXIF данных."""
        if not self.Image:
            return None
        
        image_data = self.get_image_data(file_path)
        if image_data:
            _, _, exifdata = image_data
            if exifdata:
                exposure_tag = 33434  # ExposureTime
                exposure = exifdata.get(exposure_tag)
                if exposure:
                    if isinstance(exposure, tuple) and len(exposure) == 2:
                        val = exposure[0] / exposure[1]
                        if val < 1:
                            return f"1/{int(1/val)}s"
                        return f"{val:.3f}s"
                    return f"{exposure}s"
        
        return None


"""Модуль для извлечения метаданных из файлов.

Обеспечивает извлечение метаданных из различных типов файлов:
- Изображения: EXIF данные, размеры, даты (через Pillow)
- Аудио: ID3 теги, длительность, битрейт (через mutagen)
- Видео: длительность, разрешение, кодек
- Документы: даты создания/изменения, размер
"""

import logging
import os
from datetime import datetime
from functools import lru_cache
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Класс для извлечения метаданных из файлов."""
    
    def __init__(self):
        """Инициализация экстрактора метаданных."""
        self.pillow_available = False
        self.mutagen_available = False
        
        # Кэш для метаданных изображений (чтобы не открывать файл несколько раз)
        self._image_cache: Dict[str, Tuple[int, int, Optional[object]]] = {}
        # Кэш для аудио метаданных
        self._audio_cache: Dict[str, Optional[object]] = {}
        
        # Попытка импортировать Pillow для работы с изображениями
        try:
            from PIL import Image
            from PIL.ExifTags import TAGS
            self.Image = Image
            self.TAGS = TAGS
            self.pillow_available = True
        except ImportError:
            self.pillow_available = False
        
        # Попытка импортировать mutagen для работы с аудио
        try:
            from mutagen import File as MutagenFile
            from mutagen.id3 import ID3NoHeaderError
            self.MutagenFile = MutagenFile
            self.ID3NoHeaderError = ID3NoHeaderError
            self.mutagen_available = True
        except ImportError:
            self.mutagen_available = False
    
    def clear_cache(self):
        """Очистка кэша метаданных."""
        self._image_cache.clear()
        self._audio_cache.clear()
    
    def extract(self, tag: str, file_path: str) -> Optional[str]:
        """
        Извлечение значения метаданных по тегу
        
        Args:
            tag: Тег метаданных (например, "{width}x{height}", "{date_created}")
            file_path: Путь к файлу
            
        Returns:
            Значение метаданных в виде строки или None
        """
        if not os.path.exists(file_path):
            return None
        
        # Обработка составных тегов (например, "{width}x{height}")
        if "x" in tag and "{width}" in tag and "{height}" in tag:
            return self._extract_dimensions(file_path)
        
        # Обработка отдельных тегов
        if tag == "{width}":
            return self._extract_width(file_path)
        elif tag == "{height}":
            return self._extract_height(file_path)
        elif tag == "{date_created}" or tag == "{date}":
            # {date} - алиас для {date_created} (обратная совместимость)
            return self._extract_date_created(file_path)
        elif tag == "{date_modified}":
            return self._extract_date_modified(file_path)
        elif tag == "{date_created_time}":
            return self._extract_date_created_time(file_path)
        elif tag == "{date_modified_time}":
            return self._extract_date_modified_time(file_path)
        elif tag == "{year}":
            return self._extract_year(file_path)
        elif tag == "{month}":
            return self._extract_month(file_path)
        elif tag == "{day}":
            return self._extract_day(file_path)
        elif tag == "{hour}":
            return self._extract_hour(file_path)
        elif tag == "{minute}":
            return self._extract_minute(file_path)
        elif tag == "{second}":
            return self._extract_second(file_path)
        elif tag == "{file_size}":
            return self._extract_file_size(file_path)
        elif tag == "{filename}":
            return os.path.basename(file_path)
        elif tag == "{dirname}":
            return os.path.basename(os.path.dirname(file_path))
        elif tag == "{parent_dir}":
            return os.path.dirname(file_path)
        elif tag == "{format}":
            return self._extract_format(file_path)
        # Метаданные изображений (EXIF)
        elif tag == "{camera}":
            return self._extract_camera(file_path)
        elif tag == "{iso}":
            return self._extract_iso(file_path)
        elif tag == "{focal_length}":
            return self._extract_focal_length(file_path)
        elif tag == "{aperture}":
            return self._extract_aperture(file_path)
        elif tag == "{exposure_time}":
            return self._extract_exposure_time(file_path)
        # Метаданные аудио
        elif tag == "{artist}":
            return self._extract_audio_tag(file_path, 'artist')
        elif tag == "{title}":
            return self._extract_audio_tag(file_path, 'title')
        elif tag == "{album}":
            return self._extract_audio_tag(file_path, 'album')
        elif tag == "{audio_year}":
            return self._extract_audio_tag(file_path, 'date')
        elif tag == "{track}":
            return self._extract_audio_tag(file_path, 'tracknumber')
        elif tag == "{genre}":
            return self._extract_audio_tag(file_path, 'genre')
        elif tag == "{duration}":
            return self._extract_duration(file_path)
        elif tag == "{bitrate}":
            return self._extract_bitrate(file_path)
        elif tag.startswith("{") and tag.endswith("}"):
            # Попытка извлечь пользовательский тег
            return self._extract_custom_tag(tag, file_path)
        
        return None
    
    def _get_image_data(self, file_path: str) -> Optional[Tuple[int, int, Optional[object]]]:
        """Получение данных изображения с кэшированием.
        
        Args:
            file_path: Путь к файлу изображения
            
        Returns:
            Кортеж (width, height, exifdata) или None
        """
        if not self.pillow_available:
            return None
        
        # Проверяем кэш
        if file_path in self._image_cache:
            return self._image_cache[file_path]
        
        try:
            with self.Image.open(file_path) as img:
                width, height = img.size
                exifdata = img.getexif()
                result = (width, height, exifdata)
                # Кэшируем результат
                self._image_cache[file_path] = result
                return result
        except Exception as e:
            logger.debug(f"Не удалось извлечь данные изображения {file_path}: {e}")
            return None
    
    def _extract_dimensions(self, file_path: str) -> Optional[str]:
        """Извлечение размеров изображения (ширина x высота).
        
        Args:
            file_path: Путь к файлу изображения
            
        Returns:
            Строка с размерами в формате "widthxheight" или None
        """
        image_data = self._get_image_data(file_path)
        if image_data:
            width, height, _ = image_data
            return f"{width}x{height}"
        return None
    
    def _extract_width(self, file_path: str) -> Optional[str]:
        """Извлечение ширины изображения.
        
        Args:
            file_path: Путь к файлу изображения
            
        Returns:
            Ширина изображения в пикселях или None
        """
        image_data = self._get_image_data(file_path)
        if image_data:
            return str(image_data[0])
        return None
    
    def _extract_height(self, file_path: str) -> Optional[str]:
        """Извлечение высоты изображения.
        
        Args:
            file_path: Путь к файлу изображения
            
        Returns:
            Высота изображения в пикселях или None
        """
        image_data = self._get_image_data(file_path)
        if image_data:
            return str(image_data[1])
        return None
    
    def _extract_date_created(self, file_path: str) -> Optional[str]:
        """Извлечение даты создания файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Дата создания в формате YYYY-MM-DD или None
        """
        try:
            # В Windows используется st_ctime, в Unix - st_birthtime (если доступно)
            stat = os.stat(file_path)
            
            # Попытка получить дату создания
            if hasattr(stat, 'st_birthtime'):
                # macOS и некоторые версии Linux
                timestamp = stat.st_birthtime
            else:
                # Windows и другие системы (используем дату изменения как fallback)
                timestamp = stat.st_ctime
            
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d")
        except Exception as e:
            logger.debug(f"Не удалось извлечь дату создания {file_path}: {e}")
            return None
    
    def _extract_date_modified(self, file_path: str) -> Optional[str]:
        """Извлечение даты изменения файла.
        
        Args:
            file_path: Путь к файлу
            
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
    
    def _extract_file_size(self, file_path: str) -> Optional[str]:
        """Извлечение размера файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Размер файла в отформатированном виде (B, KB, MB, GB) или None
        """
        try:
            size = os.path.getsize(file_path)
            
            # Форматирование размера
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
    
    def _get_audio_tags(self, file_path: str) -> Optional[object]:
        """Получение тегов аудио файла с кэшированием.
        
        Args:
            file_path: Путь к аудио файлу
            
        Returns:
            Объект тегов или None
        """
        if not self.mutagen_available:
            return None
        
        # Проверяем кэш
        if file_path in self._audio_cache:
            return self._audio_cache[file_path]
        
        try:
            audio_file = self.MutagenFile(file_path)
            if audio_file is None:
                self._audio_cache[file_path] = None
                return None
            
            # Получаем теги
            tags = audio_file.tags
            if tags is None:
                self._audio_cache[file_path] = None
                return None
            
            # Кэшируем результат
            self._audio_cache[file_path] = tags
            return tags
        except self.ID3NoHeaderError:
            self._audio_cache[file_path] = None
            return None
        except Exception as e:
            logger.debug(f"Не удалось извлечь аудио теги из {file_path}: {e}")
            self._audio_cache[file_path] = None
            return None
    
    def _extract_audio_tag(self, file_path: str, tag_name: str) -> Optional[str]:
        """Извлечение метаданных аудио файла.
        
        Args:
            file_path: Путь к аудио файлу
            tag_name: Имя тега (artist, title, album, date, tracknumber, genre)
            
        Returns:
            Значение тега или None
        """
        tags = self._get_audio_tags(file_path)
        if tags is None:
            return None
        
        try:
            
            # Маппинг имен тегов для разных форматов (кэшируем как константу)
            tag_mapping = {
                'artist': ['TPE1', 'ARTIST', '©ART'],
                'title': ['TIT2', 'TITLE', '©nam'],
                'album': ['TALB', 'ALBUM', '©alb'],
                'date': ['TDRC', 'DATE', '©day'],
                'tracknumber': ['TRCK', 'TRACKNUMBER', 'TRACK', 'trkn'],
                'genre': ['TCON', 'GENRE', '©gen']
            }
            
            # Получаем список возможных ключей для тега
            possible_keys = tag_mapping.get(tag_name.lower(), [tag_name.upper()])
            
            # Пытаемся получить значение по разным ключам
            for key in possible_keys:
                if key in tags:
                    value = tags[key]
                    # Обработка списков и кортежей
                    if isinstance(value, (list, tuple)) and len(value) > 0:
                        value = value[0]
                    # Обработка объектов с текстовым представлением
                    if hasattr(value, 'text'):
                        value = value.text[0] if value.text else None
                    if value:
                        return str(value).strip()
            
            return None
        except Exception as e:
            logger.debug(f"Не удалось извлечь аудио тег {tag_name} из {file_path}: {e}")
            return None
    
    def _extract_date_created_time(self, file_path: str) -> Optional[str]:
        """Извлечение даты и времени создания файла.
        
        Args:
            file_path: Путь к файлу
            
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
    
    def _extract_date_modified_time(self, file_path: str) -> Optional[str]:
        """Извлечение даты и времени изменения файла.
        
        Args:
            file_path: Путь к файлу
            
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
    
    def _extract_year(self, file_path: str) -> Optional[str]:
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
    
    def _extract_month(self, file_path: str) -> Optional[str]:
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
    
    def _extract_day(self, file_path: str) -> Optional[str]:
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
    
    def _extract_hour(self, file_path: str) -> Optional[str]:
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
    
    def _extract_minute(self, file_path: str) -> Optional[str]:
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
    
    def _extract_second(self, file_path: str) -> Optional[str]:
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
    
    def _extract_format(self, file_path: str) -> Optional[str]:
        """Извлечение формата файла (расширение без точки)."""
        try:
            _, ext = os.path.splitext(file_path)
            return ext.lstrip('.').upper() if ext else None
        except Exception:
            return None
    
    def _extract_camera(self, file_path: str) -> Optional[str]:
        """Извлечение модели камеры из EXIF данных."""
        if not self.pillow_available:
            return None
        
        image_data = self._get_image_data(file_path)
        if image_data:
            _, _, exifdata = image_data
            if exifdata:
                # EXIF теги для камеры
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
    
    def _extract_iso(self, file_path: str) -> Optional[str]:
        """Извлечение ISO из EXIF данных."""
        if not self.pillow_available:
            return None
        
        image_data = self._get_image_data(file_path)
        if image_data:
            _, _, exifdata = image_data
            if exifdata:
                # EXIF тег для ISO
                iso_tag = 34855  # ISOSpeedRatings
                iso = exifdata.get(iso_tag)
                if iso:
                    return str(iso)
        
        return None
    
    def _extract_focal_length(self, file_path: str) -> Optional[str]:
        """Извлечение фокусного расстояния из EXIF данных."""
        if not self.pillow_available:
            return None
        
        image_data = self._get_image_data(file_path)
        if image_data:
            _, _, exifdata = image_data
            if exifdata:
                # EXIF тег для фокусного расстояния
                focal_tag = 37386  # FocalLength
                focal = exifdata.get(focal_tag)
                if focal:
                    # Может быть рациональным числом
                    if isinstance(focal, tuple) and len(focal) == 2:
                        return f"{focal[0]/focal[1]:.1f}mm"
                    return f"{focal}mm"
        
        return None
    
    def _extract_aperture(self, file_path: str) -> Optional[str]:
        """Извлечение диафрагмы из EXIF данных."""
        if not self.pillow_available:
            return None
        
        image_data = self._get_image_data(file_path)
        if image_data:
            _, _, exifdata = image_data
            if exifdata:
                # EXIF тег для диафрагмы
                aperture_tag = 37378  # FNumber
                aperture = exifdata.get(aperture_tag)
                if aperture:
                    # Может быть рациональным числом
                    if isinstance(aperture, tuple) and len(aperture) == 2:
                        return f"f/{aperture[0]/aperture[1]:.1f}"
                    return f"f/{aperture}"
        
        return None
    
    def _extract_exposure_time(self, file_path: str) -> Optional[str]:
        """Извлечение выдержки из EXIF данных."""
        if not self.pillow_available:
            return None
        
        image_data = self._get_image_data(file_path)
        if image_data:
            _, _, exifdata = image_data
            if exifdata:
                # EXIF тег для выдержки
                exposure_tag = 33434  # ExposureTime
                exposure = exifdata.get(exposure_tag)
                if exposure:
                    # Может быть рациональным числом
                    if isinstance(exposure, tuple) and len(exposure) == 2:
                        val = exposure[0] / exposure[1]
                        if val < 1:
                            return f"1/{int(1/val)}s"
                        return f"{val:.3f}s"
                    return f"{exposure}s"
        
        return None
    
    def _extract_duration(self, file_path: str) -> Optional[str]:
        """Извлечение длительности аудио/видео файла."""
        if self.mutagen_available:
            try:
                audio_file = self.MutagenFile(file_path)
                if audio_file is not None:
                    length = audio_file.info.length
                    if length:
                        # Форматирование в MM:SS или HH:MM:SS
                        hours = int(length // 3600)
                        minutes = int((length % 3600) // 60)
                        seconds = int(length % 60)
                        if hours > 0:
                            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        return f"{minutes:02d}:{seconds:02d}"
            except Exception as e:
                logger.debug(f"Не удалось извлечь длительность {file_path}: {e}")
        return None
    
    def _extract_bitrate(self, file_path: str) -> Optional[str]:
        """Извлечение битрейта аудио файла."""
        if self.mutagen_available:
            try:
                audio_file = self.MutagenFile(file_path)
                if audio_file is not None and hasattr(audio_file.info, 'bitrate'):
                    bitrate = audio_file.info.bitrate
                    if bitrate:
                        # Битрейт в kbps
                        return f"{bitrate // 1000}kbps"
            except Exception as e:
                logger.debug(f"Не удалось извлечь битрейт {file_path}: {e}")
        return None
    
    def _extract_custom_tag(self, tag: str, file_path: str) -> Optional[str]:
        """Извлечение пользовательского тега (расширяемая функция).
        
        Args:
            tag: Тег для извлечения
            file_path: Путь к файлу
            
        Returns:
            Значение тега или None
        """
        # Здесь можно добавить поддержку дополнительных тегов
        # Например, EXIF данные из изображений
        
        if not self.pillow_available:
            return None
        
        # Используем кэшированные данные изображения
        image_data = self._get_image_data(file_path)
        if image_data:
            _, _, exifdata = image_data
            if exifdata:
                # Поиск тега в EXIF данных
                for tag_id, value in exifdata.items():
                    tag_name = self.TAGS.get(tag_id, tag_id)
                    if tag.lower() == f"{{{tag_name.lower()}}}":
                        return str(value)
        
        return None


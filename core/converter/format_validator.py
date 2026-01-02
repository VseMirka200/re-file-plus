"""Модуль для валидации форматов файлов.

Содержит функции для проверки возможности конвертации файлов
и определения поддерживаемых форматов.
"""

import logging
import os
import sys
from typing import List, Optional

logger = logging.getLogger(__name__)


class FormatValidator:
    """Класс для валидации форматов файлов."""
    
    def __init__(
        self,
        supported_image_formats: dict,
        supported_document_formats: dict,
        supported_presentation_formats: dict,
        supported_document_target_formats: dict,
        supported_presentation_target_formats: dict,
        supported_audio_formats: dict,
        supported_video_formats: dict,
        supported_audio_target_formats: dict,
        supported_video_target_formats: dict,
        Image_module,
        fitz_module,
        Converter_class,
        win32com,
        comtypes,
        docx2pdf_convert,
        docx_module,
        check_word_installed
    ):
        """Инициализация валидатора форматов.
        
        Args:
            supported_image_formats: Словарь поддерживаемых форматов изображений
            supported_document_formats: Словарь поддерживаемых форматов документов
            supported_presentation_formats: Словарь поддерживаемых форматов презентаций
            supported_document_target_formats: Словарь целевых форматов для документов
            supported_presentation_target_formats: Словарь целевых форматов для презентаций
            supported_audio_formats: Словарь поддерживаемых форматов аудио
            supported_video_formats: Словарь поддерживаемых форматов видео
            supported_audio_target_formats: Словарь целевых форматов для аудио
            supported_video_target_formats: Словарь целевых форматов для видео
            Image_module: Модуль Pillow (PIL.Image) или None
            fitz_module: Модуль PyMuPDF (fitz) или None
            Converter_class: Класс pdf2docx.Converter или None
            win32com: Модуль win32com или None
            comtypes: Модуль comtypes или None
            docx2pdf_convert: Функция docx2pdf.convert или None
            docx_module: Модуль python-docx или None
            check_word_installed: Функция проверки установки Word
        """
        self.supported_image_formats = supported_image_formats
        self.supported_document_formats = supported_document_formats
        self.supported_presentation_formats = supported_presentation_formats
        self.supported_document_target_formats = supported_document_target_formats
        self.supported_presentation_target_formats = supported_presentation_target_formats
        self.supported_audio_formats = supported_audio_formats
        self.supported_video_formats = supported_video_formats
        self.supported_audio_target_formats = supported_audio_target_formats
        self.supported_video_target_formats = supported_video_target_formats
        self.Image = Image_module
        self.fitz = fitz_module
        self.Converter = Converter_class
        self.win32com = win32com
        self.comtypes = comtypes
        self.docx2pdf_convert = docx2pdf_convert
        self.docx_module = docx_module
        self.check_word_installed = check_word_installed
    
    def can_convert(self, file_path: str, target_format: str) -> bool:
        """Проверка возможности конвертации файла.
        
        Args:
            file_path: Путь к исходному файлу
            target_format: Целевой формат (расширение с точкой, например '.png')
            
        Returns:
            True если можно конвертировать, False иначе
        """
        if not os.path.exists(file_path):
            return False
        
        # Проверяем, что это файл, а не папка
        if os.path.isdir(file_path):
            return False
        
        source_ext = os.path.splitext(file_path)[1].lower()
        target_ext = target_format.lower()
        
        # Не конвертируем в тот же формат
        if source_ext == target_ext:
            return False
        
        # Проверяем конвертацию изображений
        if source_ext in self.supported_image_formats:
            # Изображения в изображения (через Pillow)
            if target_ext in self.supported_image_formats:
                return self.Image is not None
            # Изображения в PDF (через PyMuPDF)
            elif target_ext == '.pdf':
                return self.fitz is not None and self.Image is not None
        
        # Проверяем конвертацию документов Word
        if source_ext in self.supported_document_formats:
            logger.debug(f"can_convert: source_ext={source_ext} в supported_document_formats, target_ext={target_ext}")
            # Специальная обработка для ODT файлов - поддерживаем больше форматов
            if source_ext == '.odt':
                # ODT в ODT не поддерживается (тот же формат)
                if target_ext == '.odt':
                    return False
                # ODT в другие форматы
                if target_ext in ('.pdf', '.doc', '.rtf', '.docx', '.txt', '.html', '.htm'):
                    # Проверяем Word (только на Windows)
                    if sys.platform == 'win32' and (self.win32com or self.comtypes):
                        word_installed, _ = self.check_word_installed()
                        if word_installed:
                            return True
                    # Для TXT, HTML, DOCX есть fallback методы без Office
                    if target_ext in ('.txt', '.html', '.htm', '.docx'):
                        return True
                    # Для PDF, DOC, RTF требуется Word
                    return False
                # Для других форматов возвращаем False
                return False
            
            # Для остальных форматов документов проверяем стандартный список
            logger.debug(f"can_convert: проверка target_ext={target_ext} в supported_document_target_formats={list(self.supported_document_target_formats.keys())}")
            if target_ext in self.supported_document_target_formats:
                # DOCX в DOCX не поддерживается (тот же формат)
                if source_ext == '.docx' and target_ext == '.docx':
                    return False
                # DOC в DOC не поддерживается (тот же формат)
                if source_ext == '.doc' and target_ext == '.doc':
                    return False
                # PDF в PDF не поддерживается (тот же формат)
                if source_ext == '.pdf' and target_ext == '.pdf':
                    return False
                # DOCX в PDF
                if source_ext == '.docx' and target_ext == '.pdf':
                    # Проверяем доступность win32com, comtypes или docx2pdf
                    if sys.platform == 'win32' and (self.win32com or self.comtypes):
                        word_installed, _ = self.check_word_installed()
                        if word_installed:
                            return True
                    return self.docx2pdf_convert is not None
                # DOC в PDF (через COM)
                if source_ext == '.doc' and target_ext == '.pdf':
                    # Проверяем доступность win32com или comtypes
                    if sys.platform == 'win32' and (self.win32com or self.comtypes):
                        word_installed, _ = self.check_word_installed()
                        if word_installed:
                            return True
                    return False
                # PDF в DOCX
                if source_ext == '.pdf' and target_ext == '.docx':
                    if self.Converter is None:
                        try:
                            from pdf2docx import Converter
                            self.Converter = Converter
                        except ImportError:
                            return False
                    return self.Converter is not None
                # DOCX/DOC в ODT/ODP (через Word)
                if (source_ext == '.docx' or source_ext == '.doc') and target_ext in ('.odt', '.odp'):
                    # Проверяем Word (только на Windows, только для ODT)
                    if target_ext == '.odt' and sys.platform == 'win32' and (self.win32com or self.comtypes):
                        word_installed, _ = self.check_word_installed()
                        if word_installed:
                            return True
                    return False
                # Для других форматов документов в документы
                if self.docx_module is not None:
                    return True
        
        # Проверяем конвертацию презентаций PowerPoint
        if source_ext in self.supported_presentation_formats:
            if target_ext in self.supported_presentation_target_formats:
                # PPTX в PPTX не поддерживается (тот же формат)
                if source_ext == '.pptx' and target_ext == '.pptx':
                    return False
                # ODP в ODP не поддерживается (тот же формат)
                if source_ext == '.odp' and target_ext == '.odp':
                    return False
                # Конвертация не поддерживается без LibreOffice
                return False
        
        # Проверяем конвертацию аудио (через ffmpeg)
        if source_ext in self.supported_audio_formats:
            if target_ext in self.supported_audio_target_formats:
                # Проверяем, установлен ли ffmpeg
                try:
                    from core.converter.audio_video_converter import check_ffmpeg_installed
                    return check_ffmpeg_installed()
                except ImportError:
                    return False
        
        # Проверяем конвертацию видео (через ffmpeg)
        if source_ext in self.supported_video_formats:
            if target_ext in self.supported_video_target_formats:
                # Проверяем, установлен ли ffmpeg
                try:
                    from core.converter.audio_video_converter import check_ffmpeg_installed
                    return check_ffmpeg_installed()
                except ImportError:
                    return False
        
        return False
    
    def get_supported_formats(self) -> List[str]:
        """Получение списка поддерживаемых форматов.
        
        Returns:
            Список расширений форматов (с точкой)
        """
        formats = list(self.supported_image_formats.keys())
        # Всегда включаем форматы документов (png, jpg, jpeg, pdf, doc, docx, odt)
        formats.extend(list(self.supported_document_formats.keys()))
        # Всегда включаем форматы презентаций (LibreOffice может быть установлен)
        formats.extend(list(self.supported_presentation_formats.keys()))
        # Добавляем форматы аудио
        formats.extend(list(self.supported_audio_formats.keys()))
        # Добавляем форматы видео
        formats.extend(list(self.supported_video_formats.keys()))
        # Удаляем дубликаты и сортируем
        formats = sorted(list(set(formats)))
        return formats
    
    def get_target_formats_for_file(self, file_path: str) -> List[str]:
        """Получение списка доступных целевых форматов для конкретного файла.
        
        Args:
            file_path: Путь к исходному файлу
            
        Returns:
            Список расширений целевых форматов (с точкой), исключая исходный формат
        """
        if not os.path.exists(file_path):
            return []
        
        # Проверяем, что это файл, а не папка
        if os.path.isdir(file_path):
            return []
        
        source_ext = os.path.splitext(file_path)[1].lower()
        target_formats = []
        
        # Изображения
        if source_ext in self.supported_image_formats:
            # Изображения можно конвертировать в другие форматы изображений
            for ext in self.supported_image_formats.keys():
                if ext != source_ext and self.can_convert(file_path, ext):
                    target_formats.append(ext)
            # Изображения можно конвертировать в PDF
            if self.can_convert(file_path, '.pdf'):
                target_formats.append('.pdf')
        
        # Документы Word
        if source_ext in self.supported_document_formats:
            for ext in self.supported_document_target_formats.keys():
                if ext != source_ext and self.can_convert(file_path, ext):
                    target_formats.append(ext)
        
        # Презентации PowerPoint
        if source_ext in self.supported_presentation_formats:
            for ext in self.supported_presentation_target_formats.keys():
                if ext != source_ext and self.can_convert(file_path, ext):
                    target_formats.append(ext)
        
        # Аудио файлы
        if source_ext in self.supported_audio_formats:
            for ext in self.supported_audio_target_formats.keys():
                if ext != source_ext and self.can_convert(file_path, ext):
                    target_formats.append(ext)
        
        # Видео файлы
        if source_ext in self.supported_video_formats:
            for ext in self.supported_video_target_formats.keys():
                if ext != source_ext and self.can_convert(file_path, ext):
                    target_formats.append(ext)
        
        # Удаляем дубликаты и сортируем
        target_formats = sorted(list(set(target_formats)))
        
        # Если нет доступных форматов, возвращаем все поддерживаемые (кроме исходного)
        if not target_formats:
            all_formats = self.get_supported_formats()
            target_formats = [f for f in all_formats if f != source_ext]
        
        return target_formats
    
    def get_file_type_category(self, file_path: str) -> Optional[str]:
        """Определение категории типа файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Категория файла: 'image', 'document', 'presentation' или None
        """
        if not os.path.exists(file_path):
            return None
        
        ext = os.path.splitext(file_path)[1].lower()
        
        # Изображения (включая все поддерживаемые форматы)
        image_extensions = {
            '.png', '.jpg', '.jpeg', '.ico', '.webp', '.gif', '.pdf',
            '.bmp', '.tiff', '.tif', '.jfif', '.jpe', '.jp2', '.jpx', '.j2k', '.j2c'
        }
        if ext in image_extensions:
            return 'image'
        
        # Документы Word (без изображений)
        document_extensions = {
            '.pdf', '.doc', '.docx', '.odt'
        }
        if ext in document_extensions:
            return 'document'
        
        # Презентации PowerPoint
        presentation_extensions = {
            '.pptx', '.ppt', '.odp'
        }
        if ext in presentation_extensions:
            return 'presentation'
        
        # Аудио файлы
        audio_extensions = {
            '.mp3', '.wav', '.aac', '.ogg', '.flac', '.wma', '.m4a', '.opus'
        }
        if ext in audio_extensions:
            return 'audio'
        
        # Видео файлы
        video_extensions = {
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'
        }
        if ext in video_extensions:
            return 'video'
        
        return None


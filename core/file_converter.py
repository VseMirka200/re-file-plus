"""Модуль для конвертации файлов.

Обеспечивает конвертацию файлов между различными форматами:
- Изображения: JPG, PNG, BMP, TIFF, WEBP и др. (через Pillow)
- Изображения в PDF и PDF в изображения (через PyMuPDF и Pillow)
- Документы: DOCX в PDF, PDF в DOCX
  (через COM или специализированные библиотеки)
"""

# Стандартная библиотека
import io
import importlib
import importlib.util
import logging
import os
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from typing import Any, Dict, List, Optional, Tuple

# Локальные импорты
try:
    from config.constants import (
        COM_OPERATION_DELAY,
        DEFAULT_JPEG_QUALITY,
    )
except ImportError:
    # Fallback если константы недоступны
    COM_OPERATION_DELAY = 0.5
    DEFAULT_JPEG_QUALITY = 95

logger = logging.getLogger(__name__)

# ============================================================================
# COM УТИЛИТЫ (перенесены в core/converter/com_utils.py)
# ============================================================================

# Импортируем COM утилиты из отдельного модуля
try:
    from core.converter.com_utils import (
        cleanup_word_application,
        cleanup_word_document,
        word_application_context,
        check_word_installed,
        create_word_application,
        convert_docx_with_word,
    )
except ImportError:
    # Fallback для обратной совместимости (если модуль еще не создан)
    logger.warning("Не удалось импортировать COM утилиты из core.converter.com_utils")
    # Определяем заглушки
    def cleanup_word_application(word_app: Optional[Any]) -> None:
        pass
    def cleanup_word_document(doc: Optional[Any]) -> None:
        pass
    @contextmanager
    def word_application_context(com_client: Any):
        yield None
    def check_word_installed() -> Tuple[bool, str]:
        return False, "COM утилиты не доступны"
    def create_word_application(com_client: Any) -> Tuple[Optional[Any], Optional[str]]:
        return None, "COM утилиты не доступны"
    def convert_docx_with_word(word_app: Any, file_path: str, output_path: str, com_client_type: str = "win32com") -> Tuple[bool, Optional[str]]:
        return False, "COM утилиты не доступны"




class FileConverter:
    """Класс для конвертации файлов."""
    
    def __init__(self) -> None:
        """Инициализация конвертера файлов."""
        # Импорт Pillow для работы с изображениями
        try:
            from PIL import Image
            self.Image = Image
        except ImportError:
            self.Image = None
        
        # Поддерживаемые форматы изображений для конвертации
        # ВАЖНО: PDF не является изображением, это документ, поэтому он не включен здесь
        self.supported_image_formats = {
            '.gif': 'GIF',
            '.png': 'PNG',
            '.webp': 'WEBP',
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG',
            '.ico': 'ICO'
        }
        
        # Импорт python-docx для работы с Word документами
        try:
            import docx
            self.docx_module = docx
        except ImportError:
            self.docx_module = None
        
        # Импорт библиотек для конвертации документов
        self.docx2pdf_convert = None
        self.comtypes = None
        self.win32com = None
        self.pythoncom = None
        self.use_docx2pdf = False
        
        # Импорт pdf2docx для конвертации PDF в DOCX
        self.Converter = None
        try:
            from pdf2docx import Converter
            self.Converter = Converter
        except ImportError:
            pass
        
        # Импорт COM библиотек (Windows)
        if sys.platform == 'win32':
            try:
                import win32com.client
                self.win32com = win32com.client
            except ImportError:
                pass
            
            try:
                import comtypes.client
                self.comtypes = comtypes.client
            except ImportError:
                pass
            
            try:
                import pythoncom
                self.pythoncom = pythoncom
            except ImportError:
                pass
        
        # Импорт docx2pdf как fallback метод
        try:
            from docx2pdf import convert as docx2pdf_convert
            self.docx2pdf_convert = docx2pdf_convert
            if not self.win32com and not self.comtypes:
                self.use_docx2pdf = True
        except ImportError:
            pass
        
        # Импорт PyMuPDF для конвертации PDF
        try:
            import fitz  # PyMuPDF
            self.fitz = fitz
        except ImportError:
            self.fitz = None
        
        # Поддерживаемые форматы документов (Word, без изображений)
        self.supported_document_formats = {
            '.pdf': 'PDF',
            '.doc': 'DOC',  # Формат Word (поддержка через COM)
            '.docx': 'DOCX',
            '.odt': 'ODT'  # LibreOffice Writer
        }
        
        # Поддерживаемые форматы презентаций (PowerPoint)
        self.supported_presentation_formats = {
            '.pptx': 'PPTX',
            '.ppt': 'PPT',
            '.odp': 'ODP'  # LibreOffice Impress
        }
        
        # Поддерживаемые целевые форматы для документов
        self.supported_document_target_formats = {
            '.docx': 'DOCX',
            '.pdf': 'PDF',
            '.odt': 'ODT'
        }
        
        # Поддерживаемые целевые форматы для презентаций
        self.supported_presentation_target_formats = {
            '.pptx': 'PPTX',
            '.pdf': 'PDF',
            '.odp': 'ODP'
        }
        
        # Инициализируем валидатор форматов
        from core.converter.format_validator import FormatValidator
        self.format_validator = FormatValidator(
            self.supported_image_formats,
            self.supported_document_formats,
            self.supported_presentation_formats,
            self.supported_document_target_formats,
            self.supported_presentation_target_formats,
            self.Image,
            self.fitz,
            self.Converter,
            self.win32com,
            self.comtypes,
            self.docx2pdf_convert,
            self.docx_module,
            check_word_installed
        )
    

    
    def can_convert(self, file_path: str, target_format: str) -> bool:
        """Проверка возможности конвертации файла (делегируется format_validator).
        
        Args:
            file_path: Путь к исходному файлу
            target_format: Целевой формат (расширение с точкой, например '.png')
            
        Returns:
            True если можно конвертировать, False иначе
        """
        return self.format_validator.can_convert(file_path, target_format)
    
    def get_supported_formats(self) -> List[str]:
        """Получение списка поддерживаемых форматов (делегируется format_validator).
        
        Returns:
            Список расширений форматов (с точкой)
        """
        return self.format_validator.get_supported_formats()
    
    def get_target_formats_for_file(self, file_path: str) -> List[str]:
        """Получение списка доступных целевых форматов для конкретного файла (делегируется format_validator).
        
        Args:
            file_path: Путь к исходному файлу
            
        Returns:
            Список расширений целевых форматов (с точкой), исключая исходный формат
        """
        return self.format_validator.get_target_formats_for_file(file_path)
    
    def get_file_type_category(self, file_path: str) -> Optional[str]:
        """Определение категории типа файла (делегируется format_validator).
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Категория файла: 'image', 'document', 'presentation' или None
        """
        return self.format_validator.get_file_type_category(file_path)
    
    def convert(self, file_path: str, target_format: str, output_path: Optional[str] = None, 
                quality: int = 95) -> Tuple[bool, str, Optional[str]]:
        """Конвертация файла.
        
        Args:
            file_path: Путь к исходному файлу
            target_format: Целевой формат (расширение с точкой, например '.png')
            output_path: Путь для сохранения (если None, заменяет исходный файл)
            quality: Качество для JPEG (1-100)
            
        Returns:
            Кортеж (успех, сообщение, путь к выходному файлу)
        """
        if not os.path.exists(file_path):
            return False, "Файл не найден", None
        
        # Проверяем, что это файл, а не папка
        if os.path.isdir(file_path):
            return False, "Нельзя конвертировать папку, выберите файл", None
        
        if not self.can_convert(file_path, target_format):
            source_ext = os.path.splitext(file_path)[1].lower()
            target_ext = target_format.lower()
            
            # Формируем более информативное сообщение об ошибке
            error_msg = "Конвертация в этот формат не поддерживается"
            if source_ext in self.supported_image_formats and target_ext == '.pdf':
                missing_libs = []
                if not self.fitz:
                    missing_libs.append("PyMuPDF")
                if not self.Image:
                    missing_libs.append("Pillow")
                if missing_libs:
                    error_msg = f"Для конвертации изображений в PDF необходимо установить: {', '.join(missing_libs)}. Установите: pip install {' '.join(missing_libs)}"
            elif source_ext == '.pdf' and target_ext == '.docx':
                # Специальное сообщение для PDF в DOCX
                if not self.Converter:
                    error_msg = "Для конвертации PDF в DOCX необходимо установить библиотеку pdf2docx. Установите: python -m pip install pdf2docx"
                else:
                    error_msg = "Конвертация PDF в DOCX не поддерживается. Проверьте, что библиотека pdf2docx установлена и доступна."
            
            logger.warning(f"Конвертация {source_ext} в {target_ext} не поддерживается")
            return False, error_msg, None
        
        source_ext = os.path.splitext(file_path)[1].lower()
        target_ext = target_format.lower()
        
        # Определяем путь для выходного файла
        if output_path is None:
            # Заменяем расширение исходного файла
            base_name = os.path.splitext(file_path)[0]
            output_path = base_name + target_ext
        else:
            # Убеждаемся, что выходной файл имеет правильное расширение
            if not output_path.lower().endswith(target_ext):
                output_path = os.path.splitext(output_path)[0] + target_ext
        
        try:
            # Проверяем тип файла и конвертируем соответственно
            # Сначала проверяем, не является ли это конвертация изображения
            # PNG, JPG, JPEG могут быть как в supported_image_formats, так и в supported_document_formats
            # Поэтому обрабатываем их как изображения в первую очередь
            if source_ext in ('.png', '.jpg', '.jpeg') and source_ext in self.supported_image_formats:
                # Конвертация изображений
                if not self.Image:
                    return False, "Pillow не установлен", None
                
                # Конвертация изображений в PDF
                if target_ext == '.pdf':
                    if not self.fitz:
                        return False, "PyMuPDF не установлен. Для конвертации изображений в PDF установите: pip install PyMuPDF", None
                    # Используем модуль конвертации изображений
                    try:
                        from core.converter.image_converter import convert_image_to_pdf
                        return convert_image_to_pdf(
                            file_path, output_path, quality,
                            self.fitz, self.Image
                        )
                    except ImportError:
                        return False, "Модуль конвертации изображений недоступен", None
                
                # Конвертация изображений в другие форматы изображений
                if target_ext in self.supported_image_formats:
                    try:
                        from core.converter.image_converter import convert_image_to_image
                        return convert_image_to_image(
                            file_path, output_path, target_ext, quality,
                            self.Image, self.supported_image_formats
                        )
                    except ImportError:
                        return False, "Модуль конвертации изображений недоступен", None
                else:
                    return False, "Неподдерживаемый формат файла", None
            
            if source_ext in self.supported_document_formats:
                # Конвертация документов Word в PDF
                if (source_ext == '.docx' or source_ext == '.doc') and target_ext == '.pdf':
                    try:
                        from core.converter.document_converter import convert_docx_to_pdf
                        from core.converter.com_utils import convert_docx_with_word_com
                        return convert_docx_to_pdf(
                            file_path, output_path,
                            self.win32com, self.comtypes,
                            self.docx2pdf_convert,
                            self.docx2pdf_convert is not None,
                            self.use_docx2pdf,
                            check_word_installed,
                            create_word_application,
                            convert_docx_with_word_com
                        )
                    except ImportError:
                        return False, "Модуль конвертации документов недоступен", None
                elif source_ext == '.pdf' and target_ext == '.docx':
                    try:
                        from core.converter.document_converter import convert_pdf_to_docx
                        return convert_pdf_to_docx(
                            file_path, output_path,
                            self.win32com, self.comtypes,
                            check_word_installed,
                            cleanup_word_document,
                            cleanup_word_application
                        )
                    except ImportError:
                        # Fallback на pdf2docx
                        if self.Converter:
                            try:
                                converter = self.Converter(file_path)
                                converter.convert(output_path)
                                converter.close()
                                if os.path.exists(output_path):
                                    return True, "PDF успешно конвертирован в DOCX", output_path
                            except Exception as e:
                                return False, f"Ошибка конвертации: {str(e)}", None
                        return False, "Модуль конвертации PDF недоступен", None
                # Конвертация DOCX/DOC в ODT/ODP (через LibreOffice или Word)
                elif (source_ext == '.docx' or source_ext == '.doc') and target_ext in ('.odt', '.odp'):
                    try:
                        from core.converter.libreoffice_converter import convert_with_libreoffice
                        from core.converter.odt_converter import convert_odt_with_word
                        from core.converter.com_utils import convert_docx_with_word_com
                        result = convert_with_libreoffice(
                            file_path, output_path, target_ext
                        )
                        # Если LibreOffice недоступен и это ODT, пробуем Word (только на Windows)
                        if not result[0] and target_ext == '.odt' and sys.platform == 'win32' and (self.win32com or self.comtypes):
                            word_result = convert_odt_with_word(
                                file_path, output_path, target_ext,
                                self.win32com, self.comtypes,
                                check_word_installed,
                                create_word_application,
                                cleanup_word_document,
                                cleanup_word_application
                            )
                            if word_result[0]:
                                result = word_result
                        return result
                    except ImportError:
                        return False, "Модуль конвертации ODT недоступен", None
                # Конвертация ODT и других форматов LibreOffice
                elif source_ext in ('.odt', '.odp') or target_ext in ('.odt', '.odp'):
                    try:
                        from core.converter.libreoffice_converter import convert_with_libreoffice
                        from core.converter.odt_converter import (
                            convert_odt_with_word,
                            convert_odt_without_libreoffice
                        )
                        from core.converter.com_utils import convert_docx_with_word_com
                        result = convert_with_libreoffice(
                            file_path, output_path, target_ext
                        )
                        # Если LibreOffice недоступен и это ODT файл, пробуем Word или другие fallback методы
                        if not result[0] and source_ext == '.odt':
                            # Пробуем через Word (если еще не пробовали)
                            if sys.platform == 'win32' and (self.win32com or self.comtypes):
                                word_result = convert_odt_with_word(
                                    file_path, output_path, target_ext,
                                    self.win32com, self.comtypes,
                                    check_word_installed,
                                    create_word_application,
                                    cleanup_word_document,
                                    cleanup_word_application
                                )
                                if word_result[0]:
                                    result = word_result
                            # Если Word тоже не сработал, пробуем другие fallback методы
                            if not result[0]:
                                result = convert_odt_without_libreoffice(
                                    file_path, output_path, target_ext
                                )
                        return result
                    except ImportError:
                        return False, "Модуль конвертации ODT недоступен", None
                else:
                    try:
                        from core.converter.document_converter import convert_document
                        return convert_document(
                            file_path, target_ext, output_path,
                            self.docx_module
                        )
                    except ImportError:
                        return False, "Модуль конвертации документов недоступен", None
            # PDF в изображения
            elif source_ext == '.pdf' and target_ext in self.supported_image_formats:
                try:
                    from core.converter.image_converter import convert_pdf_to_image
                    return convert_pdf_to_image(
                        file_path, output_path, target_ext, quality,
                        self.fitz, self.Image, self.supported_image_formats
                    )
                except ImportError:
                    return False, "Модуль конвертации PDF недоступен", None
            # Изображения в другие форматы
            elif source_ext in self.supported_image_formats:
                # Конвертация изображений в PDF
                if target_ext == '.pdf':
                    try:
                        from core.converter.image_converter import convert_image_to_pdf
                        return convert_image_to_pdf(
                            file_path, output_path, quality,
                            self.fitz, self.Image
                        )
                    except ImportError:
                        return False, "Модуль конвертации изображений недоступен", None
                # Конвертация изображений в другие форматы изображений
                else:
                    try:
                        from core.converter.image_converter import convert_image_to_image
                        return convert_image_to_image(
                            file_path, output_path, target_ext, quality,
                            self.Image, self.supported_image_formats
                        )
                    except ImportError:
                        return False, "Модуль конвертации изображений недоступен", None
            else:
                return False, "Неподдерживаемый формат файла", None
            
        except Exception as e:
            logger.error(f"Ошибка при конвертации файла {file_path}: {e}", exc_info=True)
            return False, f"Ошибка: {str(e)}", None
    
    def convert_file(self, file_path: str, target_format: str) -> Optional[str]:
        """Упрощенный метод конвертации файла (для обратной совместимости).
        
        Args:
            file_path: Путь к исходному файлу
            target_format: Целевой формат (расширение с точкой)
            
        Returns:
            Путь к выходному файлу или None при ошибке
        """
        success, message, output_path = self.convert(file_path, target_format)
        return output_path if success else None
    
    # Старые методы _convert_* удалены - теперь используется делегирование к модулям конвертации
    # Методы конвертации находятся в:
    # - core/converter/image_converter.py (изображения)
    # - core/converter/document_converter.py (документы)
    # - core/converter/odt_converter.py (ODT)
    # - core/converter/libreoffice_converter.py (LibreOffice)
    
    def convert_batch(self, file_paths: List[str], target_format: str, 
                     output_dir: Optional[str] = None, quality: int = 95) -> List[Tuple[str, bool, str, Optional[str]]]:
        """Конвертация нескольких файлов.
        
        Args:
            file_paths: Список путей к файлам
            target_format: Целевой формат (расширение с точкой)
            output_dir: Директория для сохранения (если None, сохраняет рядом с исходными)
            quality: Качество для JPEG (1-100)
            
        Returns:
            Список кортежей (путь, успех, сообщение, путь к выходному файлу)
        """
        results = []
        for file_path in file_paths:
            output_path = None
            if output_dir:
                base_name = os.path.basename(os.path.splitext(file_path)[0])
                output_path = os.path.join(output_dir, base_name + target_format.lower())
            
            success, message, converted_path = self.convert(
                file_path, target_format, output_path, quality
            )
            results.append((file_path, success, message, converted_path))
        return results

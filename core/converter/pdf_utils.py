"""Модуль для работы с PDF файлами."""

import logging
import os
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def find_pdf_in_source_directory(file_path: str) -> Optional[str]:
    """Поиск PDF файла в директории исходного файла.
    
    Args:
        file_path: Путь к исходному файлу
        
    Returns:
        Путь к PDF файлу или None
    """
    try:
        file_dir = os.path.dirname(file_path)
        file_name_without_ext = os.path.splitext(os.path.basename(file_path))[0]
        pdf_path = os.path.join(file_dir, file_name_without_ext + '.pdf')
        
        if os.path.exists(pdf_path):
            return pdf_path
        return None
    except Exception as e:
        logger.debug(f"Ошибка поиска PDF в директории: {e}")
        return None


def get_pdf_library() -> Tuple[Optional[type], Optional[type], bool]:
    """Получение библиотеки для работы с PDF.
    
    Returns:
        Tuple[PdfReader, PdfWriter, available] - классы и доступность
    """
    try:
        import PyPDF2
        return PyPDF2.PdfReader, PyPDF2.PdfWriter, True
    except ImportError:
        try:
            import pypdf
            return pypdf.PdfReader, pypdf.PdfWriter, True
        except ImportError:
            return None, None, False


"""Модуль конвертации файлов.

Разбит на подмодули для лучшей организации кода:
- com_utils: Утилиты для работы с COM (Microsoft Word)
- image_converter: Конвертация изображений
- document_converter: Конвертация документов
- libreoffice_converter: Конвертация через LibreOffice
"""

from .com_utils import (
    cleanup_word_application,
    cleanup_word_document,
    word_application_context,
    check_word_installed,
    create_word_application,
    convert_docx_with_word,
    convert_docx_with_word_com,
)

__all__ = [
    'cleanup_word_application',
    'cleanup_word_document',
    'word_application_context',
    'check_word_installed',
    'create_word_application',
    'convert_docx_with_word',
    'convert_docx_with_word_com',
]


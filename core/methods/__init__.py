"""Модуль методов re-file операций.

Разбит на подмодули для лучшей организации кода:
- base: Базовый класс ReFileMethod
- implementations: Конкретные реализации методов
- validation: Функции валидации имен файлов
- conflicts: Функции проверки конфликтов
"""

from .base import ReFileMethod
from .implementations import (
    AddRemoveMethod,
    ReplaceMethod,
    CaseMethod,
    NumberingMethod,
    MetadataMethod,
    RegexMethod,
    NewNameMethod,
)
from .file_validation import validate_filename, check_conflicts

__all__ = [
    'ReFileMethod',
    'AddRemoveMethod',
    'ReplaceMethod',
    'CaseMethod',
    'NumberingMethod',
    'MetadataMethod',
    'RegexMethod',
    'NewNameMethod',
    'validate_filename',
    'check_conflicts',
]


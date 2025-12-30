"""Пакет приложения.

Содержит основные классы и функции для работы приложения.
"""

from app.app_core import ReFilePlusApp
from app.cli_utils import process_cli_args
from app.entry_point import main, run_gui

__all__ = [
    'ReFilePlusApp',
    'process_cli_args',
    'main',
    'run_gui',
]


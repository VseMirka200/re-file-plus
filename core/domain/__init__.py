"""Доменные модели приложения."""

from .file_info import FileInfo, FileStatus
from .application_state import ApplicationState
from .rename_result import RenameResult, RenamedFile

__all__ = [
    'FileInfo',
    'FileStatus',
    'ApplicationState',
    'RenameResult',
    'RenamedFile',
]


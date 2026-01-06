"""Модуль для обработки drag and drop."""

import logging
import os
from typing import List
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

logger = logging.getLogger(__name__)


class DragDropMixin:
    """Миксин для добавления поддержки drag and drop к виджетам."""
    
    def __init__(self):
        """Инициализация drag and drop."""
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Обработка входа перетаскивания."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event: QDropEvent):
        """Обработка отпускания файлов."""
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.exists(file_path):
                    files.append(file_path)
            
            if files:
                self.on_files_dropped(files)
            
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def on_files_dropped(self, files: List[str]):
        """Обработка перетащенных файлов (переопределить в подклассах).
        
        Args:
            files: Список путей к файлам
        """
        logger.info(f"Перетащено файлов: {len(files)}")


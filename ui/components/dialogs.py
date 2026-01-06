"""Диалоги для приложения."""

import logging
from PyQt6.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QLabel, QPushButton,
    QProgressDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

logger = logging.getLogger(__name__)


class ConfirmationDialog:
    """Класс для диалогов подтверждения."""
    
    @staticmethod
    def askyesno(parent, title: str, message: str) -> bool:
        """Показать диалог подтверждения.
        
        Args:
            parent: Родительский виджет
            title: Заголовок диалога
            message: Сообщение
            
        Returns:
            True если пользователь нажал "Да", False в противном случае
        """
        reply = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def askokcancel(parent, title: str, message: str) -> bool:
        """Показать диалог подтверждения с OK/Cancel.
        
        Args:
            parent: Родительский виджет
            title: Заголовок диалога
            message: Сообщение
            
        Returns:
            True если пользователь нажал "OK", False в противном случае
        """
        reply = QMessageBox.question(
            parent,
            title,
            message,
            QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel
        )
        return reply == QMessageBox.StandardButton.Ok


class InfoDialog:
    """Класс для информационных диалогов."""
    
    @staticmethod
    def showinfo(parent, title: str, message: str):
        """Показать информационный диалог.
        
        Args:
            parent: Родительский виджет
            title: Заголовок диалога
            message: Сообщение
        """
        QMessageBox.information(parent, title, message)
    
    @staticmethod
    def showwarning(parent, title: str, message: str):
        """Показать диалог предупреждения.
        
        Args:
            parent: Родительский виджет
            title: Заголовок диалога
            message: Сообщение
        """
        QMessageBox.warning(parent, title, message)
    
    @staticmethod
    def showerror(parent, title: str, message: str):
        """Показать диалог ошибки.
        
        Args:
            parent: Родительский виджет
            title: Заголовок диалога
            message: Сообщение
        """
        QMessageBox.critical(parent, title, message)


class ProgressDialog(QDialog):
    """Диалог прогресса для длительных операций."""
    
    def __init__(self, parent=None, title: str = "Выполнение операции", 
                 message: str = "Пожалуйста, подождите..."):
        """Инициализация диалога прогресса.
        
        Args:
            parent: Родительский виджет
            title: Заголовок диалога
            message: Сообщение
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        
        self.label = QLabel(message)
        layout.addWidget(self.label)
        
        self.progress = QProgressDialog(self)
        self.progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress.setMinimum(0)
        self.progress.setMaximum(0)  # Неопределенный прогресс
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
    
    def set_message(self, message: str):
        """Установить сообщение.
        
        Args:
            message: Новое сообщение
        """
        self.label.setText(message)
    
    def set_progress(self, value: int, maximum: int = 100):
        """Установить значение прогресса.
        
        Args:
            value: Текущее значение
            maximum: Максимальное значение
        """
        self.progress.setMaximum(maximum)
        self.progress.setValue(value)
    
    def set_range(self, minimum: int, maximum: int):
        """Установить диапазон прогресса.
        
        Args:
            minimum: Минимальное значение
            maximum: Максимальное значение
        """
        self.progress.setMinimum(minimum)
        self.progress.setMaximum(maximum)


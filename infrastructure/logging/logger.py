"""Модуль логирования для UI (PyQt6 версия)."""

import logging
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QTextEdit
    from PyQt6.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)


class Logger:
    """Класс для управления логированием.
    
    Обеспечивает запись логов в файл и отображение в виджете QTextEdit.
    Поддерживает различные уровни логирования (DEBUG, INFO, WARNING, ERROR).
    """
    
    def __init__(self, log_text_widget: Optional['QTextEdit'] = None):
        """Инициализация логгера.
        
        Args:
            log_text_widget: Виджет QTextEdit для отображения лога (опционально)
        """
        self.log_text = log_text_widget
    
    def set_log_widget(self, log_text_widget: 'QTextEdit') -> None:
        """Установка виджета для логирования.
        
        Args:
            log_text_widget: Виджет QTextEdit для отображения лога
        """
        self.log_text = log_text_widget
    
    def log(self, message: str) -> None:
        """Добавление сообщения в лог.
        
        Args:
            message: Сообщение для логирования
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # Выводим в консоль для отладки (только в режиме отладки)
        if logger.isEnabledFor(logging.DEBUG):
            print(log_message.strip())
        
        # Добавляем в лог, если виджет доступен
        if self.log_text is not None:
            try:
                # Используем QMetaObject.invokeMethod для безопасного обновления из других потоков
                from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
                try:
                    QMetaObject.invokeMethod(
                        self.log_text,
                        "append",
                        Qt.ConnectionType.QueuedConnection,
                        Q_ARG(str, log_message.strip())
                    )
                except (TypeError, AttributeError):
                    # Если invokeMethod не работает, используем прямой вызов
                    self._insert_log_message(log_message)
            except (Exception, AttributeError, RuntimeError):
                # Окно было закрыто или виджет недоступен
                self.log_text = None
    
    def _insert_log_message(self, log_message: str) -> None:
        """Вставка сообщения в виджет лога (вызывается из главного потока)"""
        if self.log_text is not None:
            try:
                # Проверяем, что виджет еще существует
                if not hasattr(self.log_text, 'isVisible') or not self.log_text.isVisible():
                    self.log_text = None
                    return
                
                self.log_text.append(log_message.strip())
                # Прокручиваем вниз
                scrollbar = self.log_text.verticalScrollBar()
                if scrollbar:
                    scrollbar.setValue(scrollbar.maximum())
            except (Exception, AttributeError, RuntimeError):
                # Окно было закрыто или виджет недоступен
                self.log_text = None
    
    def clear(self) -> None:
        """Очистка лога операций."""
        if self.log_text is not None:
            try:
                self.log_text.clear()
                self.log("Лог очищен")
            except (AttributeError, RuntimeError):
                self.log_text = None
            except (MemoryError, RecursionError):
                self.log_text = None
            # Финальный catch для неожиданных исключений (критично для стабильности)
            except BaseException:
                self.log_text = None
    
    def save(self) -> None:
        """Сохранение/выгрузка лога в файл."""
        try:
            from PyQt6.QtWidgets import QFileDialog, QMessageBox
        except ImportError:
            logger.warning("PyQt6 недоступен для сохранения лога")
            return
        
        if self.log_text is None:
            QMessageBox.warning(None, "Предупреждение", "Окно лога не открыто.")
            return
        
        try:
            log_content = self.log_text.toPlainText()
            if not log_content.strip():
                QMessageBox.warning(None, "Предупреждение", "Лог пуст, нечего сохранять.")
                return
            
            filename, _ = QFileDialog.getSaveFileName(
                None,
                "Выгрузить лог",
                "",
                "Текстовые файлы (*.txt);;Лог файлы (*.log);;Все файлы (*.*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                QMessageBox.information(None, "Успех", f"Лог успешно выгружен в файл:\n{filename}")
                self.log(f"Лог выгружен в файл: {filename}")
        except (OSError, PermissionError, IOError) as e:
            logger.error(f"Ошибка доступа при выгрузке лога: {e}", exc_info=True)
            try:
                QMessageBox.critical(None, "Ошибка", f"Ошибка доступа при выгрузке лога:\n{str(e)}")
            except (AttributeError, RuntimeError):
                pass
            except (MemoryError, RecursionError):
                pass
            # Финальный catch для неожиданных исключений (критично для стабильности)
            except BaseException:
                pass
        except (MemoryError, RecursionError) as e:
            # Ошибки памяти/рекурсии
            pass
        # Финальный catch для неожиданных исключений (критично для стабильности)
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            logger.error(f"Неожиданная ошибка при выгрузке лога: {e}", exc_info=True)
            try:
                QMessageBox.critical(None, "Ошибка", f"Неожиданная ошибка при выгрузке лога:\n{str(e)}")
            except (AttributeError, RuntimeError):
                pass
            except (MemoryError, RecursionError):
                pass
            # Финальный catch для неожиданных исключений (критично для стабильности)
            except BaseException:
                pass

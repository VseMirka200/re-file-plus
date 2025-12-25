"""Модуль логирования для UI."""

import logging
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk
    from tkinter import filedialog, messagebox

logger = logging.getLogger(__name__)


class Logger:
    """Класс для управления логированием.
    
    Обеспечивает запись логов в файл и отображение в виджете Text.
    Поддерживает различные уровни логирования (DEBUG, INFO, WARNING, ERROR).
    """
    
    def __init__(self, log_text_widget: Optional['tk.Text'] = None):
        """Инициализация логгера.
        
        Args:
            log_text_widget: Виджет Text для отображения лога (опционально)
        """
        self.log_text = log_text_widget
    
    def set_log_widget(self, log_text_widget: 'tk.Text') -> None:
        """Установка виджета для логирования.
        
        Args:
            log_text_widget: Виджет Text для отображения лога
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
                # Используем after для безопасного обновления из других потоков
                if hasattr(self.log_text, 'after'):
                    self.log_text.after(0, lambda: self._insert_log_message(log_message))
                else:
                    self._insert_log_message(log_message)
            except (Exception, AttributeError):
                # Окно было закрыто или виджет недоступен
                self.log_text = None
    
    def _insert_log_message(self, log_message: str) -> None:
        """Вставка сообщения в виджет лога (вызывается из главного потока)"""
        if self.log_text is not None:
            try:
                import tkinter as tk
                # Проверяем, что виджет еще существует
                if not self.log_text.winfo_exists():
                    self.log_text = None
                    return
                
                self.log_text.insert(tk.END, log_message)
                self.log_text.see(tk.END)
            except (Exception, AttributeError, RuntimeError):
                # Окно было закрыто или виджет недоступен
                self.log_text = None
    
    def clear(self) -> None:
        """Очистка лога операций."""
        if self.log_text is not None:
            try:
                import tkinter as tk
                self.log_text.delete(1.0, tk.END)
                self.log("Лог очищен")
            except Exception:
                self.log_text = None
    
    def save(self) -> None:
        """Сохранение/выгрузка лога в файл."""
        try:
            import tkinter as tk
            from tkinter import filedialog, messagebox
        except ImportError:
            logger.warning("tkinter недоступен для сохранения лога")
            return
        
        if self.log_text is None:
            messagebox.showwarning("Предупреждение", "Окно лога не открыто.")
            return
        
        try:
            log_content = self.log_text.get(1.0, tk.END)
            if not log_content.strip():
                messagebox.showwarning("Предупреждение", "Лог пуст, нечего сохранять.")
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[
                    ("Текстовые файлы", "*.txt"),
                    ("Лог файлы", "*.log"),
                    ("Все файлы", "*.*")
                ],
                title="Выгрузить лог"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(log_content)
                messagebox.showinfo("Успех", f"Лог успешно выгружен в файл:\n{filename}")
                self.log(f"Лог выгружен в файл: {filename}")
        except Exception as e:
            logger.error(f"Не удалось выгрузить лог: {e}", exc_info=True)
            try:
                messagebox.showerror("Ошибка", f"Не удалось выгрузить лог:\n{str(e)}")
            except:
                pass


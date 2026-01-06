"""Панель методов переименования."""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QListWidget, QListWidgetItem, QFrame, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class MethodsPanel(QWidget):
    """Панель для управления методами переименования."""
    
    def __init__(self, app, parent=None):
        """Инициализация панели методов.
        
        Args:
            app: Экземпляр главного приложения
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.app = app
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок
        title = QLabel("Методы переименования")
        title.setFont(QFont("Robot", 10, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Список методов
        self.methods_list = QListWidget()
        self.methods_list.setAlternatingRowColors(True)
        layout.addWidget(self.methods_list)
        
        # Кнопки управления методами - в одну линию
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)
        
        add_btn = QPushButton("+")
        add_btn.setFixedSize(15, 15)
        add_btn.setObjectName("addButton")
        add_btn.setToolTip("Добавить метод")
        add_btn.clicked.connect(self._add_method)
        buttons_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("-")
        remove_btn.setFixedSize(15, 15)
        remove_btn.setObjectName("clearButton")
        remove_btn.setToolTip("Удалить метод")
        remove_btn.clicked.connect(self._remove_method)
        buttons_layout.addWidget(remove_btn)
        
        up_btn = QPushButton("↑")
        up_btn.setFixedSize(15, 15)
        up_btn.setToolTip("Вверх")
        up_btn.clicked.connect(self._move_up)
        buttons_layout.addWidget(up_btn)
        
        down_btn = QPushButton("↓")
        down_btn.setFixedSize(15, 15)
        down_btn.setToolTip("Вниз")
        down_btn.clicked.connect(self._move_down)
        buttons_layout.addWidget(down_btn)
        
        # Кнопка применения методов - в ту же линию
        apply_btn = QPushButton("✓")
        apply_btn.setFixedSize(15, 15)
        apply_btn.setObjectName("applyButton")
        apply_btn.setToolTip("Применить методы")
        apply_btn.clicked.connect(self._apply_methods)
        buttons_layout.addWidget(apply_btn)
        
        # Кнопка переименования - в ту же линию
        rename_btn = QPushButton("🔄")
        rename_btn.setFixedSize(15, 15)
        rename_btn.setObjectName("convertButton")
        rename_btn.setToolTip("Переименовать")
        rename_btn.clicked.connect(self._rename_files)
        buttons_layout.addWidget(rename_btn)
        
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
        
        # Обновляем список методов
        self.refresh_methods()
    
    def refresh_methods(self):
        """Обновление списка методов."""
        self.methods_list.clear()
        
        if hasattr(self.app, 'methods_manager'):
            methods = self.app.methods_manager.get_methods()
            for method in methods:
                # Используем отображаемое имя метода
                method_name = self.app.methods_manager.get_method_display_name(method)
                item = QListWidgetItem(method_name)
                self.methods_list.addItem(item)
    
    def _add_method(self):
        """Добавление метода."""
        from ui.components.method_dialog import MethodDialog
        
        dialog = MethodDialog(self.app, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            method = dialog.get_method()
            if method and hasattr(self.app, 'methods_manager'):
                self.app.methods_manager.add_method(method)
                self.refresh_methods()
                logger.info(f"Добавлен метод: {method.__class__.__name__}")
    
    def _remove_method(self):
        """Удаление выбранного метода."""
        current_item = self.methods_list.currentItem()
        if current_item:
            index = self.methods_list.row(current_item)
            if hasattr(self.app, 'methods_manager'):
                self.app.methods_manager.remove_method(index)
                self.refresh_methods()
    
    def _move_up(self):
        """Переместить метод вверх."""
        current_item = self.methods_list.currentItem()
        if current_item:
            index = self.methods_list.row(current_item)
            if index > 0 and hasattr(self.app, 'methods_manager'):
                methods = self.app.methods_manager.get_methods()
                if index < len(methods):
                    methods[index], methods[index - 1] = methods[index - 1], methods[index]
                    self.refresh_methods()
                    self.methods_list.setCurrentRow(index - 1)
    
    def _move_down(self):
        """Переместить метод вниз."""
        current_item = self.methods_list.currentItem()
        if current_item:
            index = self.methods_list.row(current_item)
            if hasattr(self.app, 'methods_manager'):
                methods = self.app.methods_manager.get_methods()
                if index < len(methods) - 1:
                    methods[index], methods[index + 1] = methods[index + 1], methods[index]
                    self.refresh_methods()
                    self.methods_list.setCurrentRow(index + 1)
    
    def _apply_methods(self):
        """Применение методов к файлам."""
        if not hasattr(self.app, 'methods_manager') or not hasattr(self.app, 'files'):
            return
        
        methods = self.app.methods_manager.get_methods()
        if not methods:
            from ui.components.dialogs import InfoDialog
            InfoDialog.showinfo(self, "Информация", "Нет методов для применения")
            return
        
        # Получаем список файлов
        files = []
        if hasattr(self.app, 'state') and self.app.state:
            files = self.app.state.files
        elif hasattr(self.app, 'files'):
            files = self.app.files
        
        if not files:
            from ui.components.dialogs import InfoDialog
            InfoDialog.showinfo(self, "Информация", "Нет файлов для обработки")
            return
        
        # Создаем поток для применения методов
        from ui.operations.re_file_operations import ApplyMethodsWorker
        from ui.components.dialogs import ProgressDialog
        
        progress_dialog = ProgressDialog(
            self,
            "Применение методов",
            "Применение методов к файлам..."
        )
        
        worker = ApplyMethodsWorker(self.app, files, methods)
        worker.progress.connect(lambda curr, total: progress_dialog.set_progress(curr, total))
        worker.finished.connect(lambda: (
            progress_dialog.close(),
            self.app.file_list_manager.refresh_treeview() if hasattr(self.app, 'file_list_manager') else None
        ))
        
        worker.start()
        progress_dialog.exec()
    
    def _rename_files(self):
        """Переименование файлов."""
        if not hasattr(self.app, 'files'):
            return
        
        # Получаем список файлов
        files = []
        if hasattr(self.app, 'state') and self.app.state:
            files = [f for f in self.app.state.files if f.is_renamed()]
        elif hasattr(self.app, 'files'):
            files = [f for f in self.app.files if hasattr(f, 'is_renamed') and f.is_renamed()]
        
        if not files:
            from ui.components.dialogs import InfoDialog
            InfoDialog.showinfo(self, "Информация", "Нет файлов для переименования")
            return
        
        # Подтверждение
        from ui.components.dialogs import ConfirmationDialog
        if not ConfirmationDialog.askyesno(
            self,
            "Подтверждение",
            f"Переименовать {len(files)} файл(ов)?"
        ):
            return
        
        # Получаем методы
        methods = []
        if hasattr(self.app, 'methods_manager'):
            methods = self.app.methods_manager.get_methods()
        
        # Создаем поток для переименования
        from ui.operations.re_file_operations import ReFileWorker
        from ui.components.dialogs import ProgressDialog
        
        progress_dialog = ProgressDialog(
            self,
            "Переименование файлов",
            "Выполняется переименование..."
        )
        
        worker = ReFileWorker(self.app, files, methods)
        worker.progress.connect(lambda curr, total: progress_dialog.set_progress(curr, total))
        worker.file_processed.connect(lambda path, success, msg: progress_dialog.set_message(f"{'✓' if success else '✗'} {path}"))
        worker.finished.connect(lambda success, msg: (
            progress_dialog.close(),
            self._on_rename_finished(success, msg)
        ))
        
        # Сохраняем ссылку на worker для возможности отмены
        progress_dialog.button_box.rejected.connect(worker.cancel)
        
        worker.start()
        progress_dialog.exec()
    
    def _on_rename_finished(self, success: bool, message: str):
        """Обработка завершения переименования.
        
        Args:
            success: Успешно ли завершено
            message: Сообщение
        """
        from ui.components.dialogs import InfoDialog
        
        if success:
            InfoDialog.showinfo(self, "Успешно", message)
        else:
            InfoDialog.showerror(self, "Ошибка", message)
        
        # Обновляем список файлов
        if hasattr(self.app, 'file_list_manager'):
            self.app.file_list_manager.refresh_treeview()


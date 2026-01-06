"""Вкладка Сжатие."""

import logging
import os
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel, QComboBox,
    QHeaderView, QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.components.drag_drop import DragDropMixin

logger = logging.getLogger(__name__)


class ZipTab(QWidget, DragDropMixin):
    """Вкладка Сжатие."""
    
    def __init__(self, app, parent=None):
        """Инициализация вкладки.
        
        Args:
            app: Экземпляр главного приложения
            parent: Родительский виджет
        """
        QWidget.__init__(self, parent)
        DragDropMixin.__init__(self)
        self.app = app
        
        # Основной layout - вертикальный
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Панель управления - под вкладками, в одну линию
        self._create_control_panel(main_layout)
        
        # Список файлов - на всю ширину
        self._create_files_panel(main_layout)
        
        # Инициализация списка файлов для сжатия
        if not hasattr(self.app, 'zip_files'):
            self.app.zip_files = []
        
        logger.info("ZipTab создана")
    
    def _create_control_panel(self, parent):
        """Создание панели управления под вкладками."""
        control_layout = QHBoxLayout()
        control_layout.setSpacing(5)
        
        # Кнопка добавления файлов
        add_btn = QPushButton("+")
        add_btn.setFixedSize(15, 15)
        add_btn.setObjectName("addButton")
        add_btn.clicked.connect(self._add_files)
        control_layout.addWidget(add_btn)
        
        # Кнопка очистки
        clear_btn = QPushButton("🗑")
        clear_btn.setFixedSize(15, 15)
        clear_btn.setObjectName("clearButton")
        clear_btn.clicked.connect(self._clear_files)
        control_layout.addWidget(clear_btn)
        
        # Метка "Сжатие:"
        compression_label = QLabel("Сжатие:")
        compression_label.setFont(QFont("Robot", 9))
        control_layout.addWidget(compression_label)
        
        # Выпадающий список степени сжатия
        self.compression_combo = QComboBox()
        self.compression_combo.addItems([
            "0 - Без сжатия",
            "1 - Минимальное",
            "2", "3", "4", "5",
            "6 - Стандартное",
            "7", "8",
            "9 - Максимальное"
        ])
        self.compression_combo.setCurrentText("6 - Стандартное")
        control_layout.addWidget(self.compression_combo)
        
        # Кнопка сжатия
        compress_btn = QPushButton("📦")
        compress_btn.setFixedSize(15, 15)
        compress_btn.setObjectName("compressButton")
        compress_btn.setToolTip("Сжать")
        compress_btn.clicked.connect(self._compress_files)
        control_layout.addWidget(compress_btn)
        
        parent.addLayout(control_layout)
    
    def _create_files_panel(self, parent):
        """Создание панели со списком файлов."""
        # Таблица файлов
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Файл", "Размер", "После сжатия"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        parent.addWidget(self.tree)
        self.app.zip_tree = self.tree
        
        # Метка с количеством файлов (скрытая, но доступная для обновления)
        self.app.zip_files_label = QLabel("Список файлов (Файлов: 0)")
        self.app.zip_files_label.setVisible(False)
    
    def _add_files(self):
        """Добавление файлов."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите файлы для сжатия", "", "Все файлы (*.*)"
        )
        if files:
            self._add_files_to_list(files)
    
    def _add_files_to_list(self, file_paths: List[str]):
        """Добавление файлов в список сжатия.
        
        Args:
            file_paths: Список путей к файлам
        """
        if not hasattr(self.app, 'zip_files'):
            self.app.zip_files = []
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                # Проверяем на дубликаты
                if file_path not in self.app.zip_files:
                    self.app.zip_files.append(file_path)
        
        self._refresh_files_list()
    
    def _refresh_files_list(self):
        """Обновление списка файлов."""
        self.tree.clear()
        
        if not hasattr(self.app, 'zip_files'):
            return
        
        def format_size(size_bytes):
            """Форматирование размера файла."""
            for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.1f} ТБ"
        
        for file_path in self.app.zip_files:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, os.path.basename(file_path) if os.path.isfile(file_path) else file_path)
            
            # Размер файла
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                item.setText(1, format_size(file_size))
                
                # Примерный размер после сжатия (зависит от типа файла и уровня сжатия)
                # Для простоты используем примерную оценку 50% для большинства файлов
                estimated_size = file_size * 0.5
                item.setText(2, format_size(estimated_size))
            else:
                item.setText(1, "—")
                item.setText(2, "—")
            
            item.setData(0, Qt.ItemDataRole.UserRole, file_path)
        
        if hasattr(self.app, 'zip_files_label'):
            count = len(self.app.zip_files)
            self.app.zip_files_label.setText(f"Список файлов (Файлов: {count})")
    
    def _clear_files(self):
        """Очистка списка файлов."""
        if hasattr(self.app, 'zip_files'):
            self.app.zip_files.clear()
        self.tree.clear()
        if hasattr(self.app, 'zip_files_label'):
            self.app.zip_files_label.setText("Список файлов (Файлов: 0)")
    
    def _compress_files(self):
        """Сжатие файлов."""
        if not hasattr(self.app, 'zip_files') or not self.app.zip_files:
            from ui.components.dialogs import InfoDialog
            InfoDialog.showinfo(self, "Информация", "Нет файлов для сжатия")
            return
        
        # Получаем уровень сжатия
        compression_text = self.compression_combo.currentText()
        compression_level = 6  # По умолчанию
        if compression_text.startswith("0"):
            compression_level = 0
        elif compression_text.startswith("1"):
            compression_level = 1
        elif compression_text.startswith("9"):
            compression_level = 9
        else:
            try:
                compression_level = int(compression_text.split()[0])
            except (ValueError, IndexError):
                compression_level = 6
        
        # Выбираем путь для сохранения
        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить архив как",
            "",
            "ZIP архивы (*.zip);;Все файлы (*.*)"
        )
        
        if not output_path:
            return
        
        if not output_path.endswith('.zip'):
            output_path += '.zip'
        
        # Подтверждение
        from ui.components.dialogs import ConfirmationDialog
        if not ConfirmationDialog.askyesno(
            self,
            "Подтверждение",
            f"Создать архив из {len(self.app.zip_files)} файл(ов)?"
        ):
            return
        
        # Создаем поток для сжатия
        from ui.operations.zip_operations import ZipWorker
        from ui.components.dialogs import ProgressDialog
        
        progress_dialog = ProgressDialog(
            self,
            "Сжатие файлов",
            "Создание архива..."
        )
        
        worker = ZipWorker(self.app, self.app.zip_files, compression_level, output_path)
        worker.progress.connect(lambda curr, total: progress_dialog.set_progress(curr, total))
        worker.file_processed.connect(lambda path, success, msg: progress_dialog.set_message(f"{'✓' if success else '✗'} {os.path.basename(path)}"))
        worker.finished.connect(lambda success, msg, zip_path: (
            progress_dialog.close(),
            self._on_compress_finished(success, msg, zip_path)
        ))
        
        progress_dialog.button_box.rejected.connect(worker.cancel)
        
        worker.start()
        progress_dialog.exec()
    
    def _on_compress_finished(self, success: bool, message: str, zip_path: str):
        """Обработка завершения сжатия.
        
        Args:
            success: Успешно ли завершено
            message: Сообщение
            zip_path: Путь к созданному архиву
        """
        from ui.components.dialogs import InfoDialog
        
        if success:
            InfoDialog.showinfo(self, "Успешно", message)
        else:
            InfoDialog.showerror(self, "Ошибка", message)
    
    def on_files_dropped(self, files):
        """Обработка перетащенных файлов.
        
        Args:
            files: Список путей к файлам
        """
        logger.info(f"Перетащено файлов на вкладку Сжатие: {len(files)}")
        self._add_files_to_list(files)


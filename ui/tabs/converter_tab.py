"""Вкладка Конвертация."""

import logging
import os
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
    QComboBox, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.components.drag_drop import DragDropMixin

logger = logging.getLogger(__name__)


class ConverterTab(QWidget, DragDropMixin):
    """Вкладка Конвертация."""
    
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
        
        # Инициализация списка файлов конвертации
        if not hasattr(self.app, 'converter_files'):
            self.app.converter_files = []
        
        logger.info("ConverterTab создана")
    
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
        
        # Метка "Фильтр:"
        filter_label = QLabel("Фильтр:")
        filter_label.setFont(QFont("Robot", 9))
        control_layout.addWidget(filter_label)
        
        # Выпадающий список фильтра
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Все", "Изображения", "Документы", "Презентации", "Аудио", "Видео"])
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        control_layout.addWidget(self.filter_combo)
        
        # Метка "Формат:"
        format_label = QLabel("Формат:")
        format_label.setFont(QFont("Robot", 9))
        control_layout.addWidget(format_label)
        
        # Выпадающий список формата
        self.format_combo = QComboBox()
        if hasattr(self.app, 'file_converter') and self.app.file_converter:
            formats = self.app.file_converter.get_supported_formats()
            unique_formats = sorted(set(formats))
            self.format_combo.addItems(unique_formats)
        control_layout.addWidget(self.format_combo, 1)  # stretch=1
        
        # Кнопка конвертации
        convert_btn = QPushButton("✓")
        convert_btn.setFixedSize(15, 15)
        convert_btn.setObjectName("convertButton")
        convert_btn.setToolTip("Конвертировать")
        convert_btn.clicked.connect(self._convert_files)
        control_layout.addWidget(convert_btn)
        
        parent.addLayout(control_layout)
    
    def _on_filter_changed(self, filter_text: str):
        """Обработка изменения фильтра.
        
        Args:
            filter_text: Текст фильтра
        """
        if not hasattr(self.app, 'file_converter') or not self.app.file_converter:
            return
        
        # Обновляем список форматов в зависимости от фильтра
        all_formats = self.app.file_converter.get_supported_formats()
        
        if filter_text == "Все":
            formats = all_formats
        elif filter_text == "Изображения":
            formats = [f for f in all_formats if f.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.ico', '.tiff']]
        elif filter_text == "Документы":
            formats = [f for f in all_formats if f.lower() in ['.pdf', '.docx', '.doc', '.odt', '.rtf', '.txt']]
        elif filter_text == "Презентации":
            formats = [f for f in all_formats if f.lower() in ['.pptx', '.ppt', '.odp']]
        elif filter_text == "Аудио":
            formats = [f for f in all_formats if f.lower() in ['.mp3', '.wav', '.aac', '.ogg', '.flac', '.wma', '.m4a']]
        elif filter_text == "Видео":
            formats = [f for f in all_formats if f.lower() in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']]
        else:
            formats = all_formats
        
        self.format_combo.clear()
        self.format_combo.addItems(sorted(set(formats)))
    
    def _create_files_panel(self, parent):
        """Создание панели со списком файлов."""
        # Таблица файлов
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Файл", "Формат", "Новый формат", "Статус"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        parent.addWidget(self.tree)
        self.app.converter_tree = self.tree
        
        # Метка с количеством файлов
        self.app.converter_files_label = QLabel("Список файлов (Файлов: 0)")
        parent.addWidget(self.app.converter_files_label)
    
    def _add_files(self):
        """Добавление файлов."""
        from PyQt6.QtWidgets import QFileDialog
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите файлы для конвертации", "", "Все файлы (*.*)"
        )
        if files:
            self._add_files_to_list(files)
    
    def _add_files_to_list(self, file_paths: List[str]):
        """Добавление файлов в список конвертации.
        
        Args:
            file_paths: Список путей к файлам
        """
        if not hasattr(self.app, 'converter_files'):
            self.app.converter_files = []
        
        from ui.operations.converter_operations import ConverterFile
        
        for file_path in file_paths:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                # Проверяем на дубликаты
                if not any(cf.file_path == file_path for cf in self.app.converter_files):
                    converter_file = ConverterFile(file_path)
                    self.app.converter_files.append(converter_file)
        
        self._refresh_files_list()
    
    def _refresh_files_list(self):
        """Обновление списка файлов."""
        self.tree.clear()
        
        if not hasattr(self.app, 'converter_files'):
            return
        
        for converter_file in self.app.converter_files:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, os.path.basename(converter_file.file_path))
            item.setText(1, converter_file.source_format)
            item.setText(2, converter_file.target_format)
            item.setText(3, converter_file.status)
            item.setData(0, Qt.ItemDataRole.UserRole, converter_file)
        
        if hasattr(self.app, 'converter_files_label'):
            count = len(self.app.converter_files)
            self.app.converter_files_label.setText(f"Список файлов (Файлов: {count})")
    
    def _clear_files(self):
        """Очистка списка файлов."""
        if hasattr(self.app, 'converter_files'):
            self.app.converter_files.clear()
        self.tree.clear()
        if hasattr(self.app, 'converter_files_label'):
            self.app.converter_files_label.setText("Список файлов (Файлов: 0)")
    
    def _convert_files(self):
        """Конвертация файлов."""
        if not hasattr(self.app, 'converter_files') or not self.app.converter_files:
            from ui.components.dialogs import InfoDialog
            InfoDialog.showinfo(self, "Информация", "Нет файлов для конвертации")
            return
        
        # Получаем целевой формат
        target_format = self.format_combo.currentText()
        if not target_format.startswith('.'):
            target_format = '.' + target_format
        
        # Устанавливаем целевой формат для всех файлов
        for converter_file in self.app.converter_files:
            converter_file.target_format = target_format
        
        # Обновляем список
        self._refresh_files_list()
        
        # Подтверждение
        from ui.components.dialogs import ConfirmationDialog
        if not ConfirmationDialog.askyesno(
            self,
            "Подтверждение",
            f"Конвертировать {len(self.app.converter_files)} файл(ов) в {target_format}?"
        ):
            return
        
        # Создаем поток для конвертации
        from ui.operations.converter_operations import ConverterWorker
        from ui.components.dialogs import ProgressDialog
        
        progress_dialog = ProgressDialog(
            self,
            "Конвертация файлов",
            "Выполняется конвертация..."
        )
        
        worker = ConverterWorker(self.app, self.app.converter_files)
        worker.progress.connect(lambda curr, total: progress_dialog.set_progress(curr, total))
        worker.file_processed.connect(lambda path, success, msg: progress_dialog.set_message(f"{'✓' if success else '✗'} {os.path.basename(path)}"))
        worker.finished.connect(lambda success, msg: (
            progress_dialog.close(),
            self._on_convert_finished(success, msg)
        ))
        
        progress_dialog.button_box.rejected.connect(worker.cancel)
        
        worker.start()
        progress_dialog.exec()
    
    def _on_convert_finished(self, success: bool, message: str):
        """Обработка завершения конвертации.
        
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
        self._refresh_files_list()
    
    def on_files_dropped(self, files):
        """Обработка перетащенных файлов.
        
        Args:
            files: Список путей к файлам
        """
        logger.info(f"Перетащено файлов на вкладку Конвертация: {len(files)}")
        self._add_files_to_list(files)

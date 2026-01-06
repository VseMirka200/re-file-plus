"""Вкладка Сортировка."""

import logging
import os
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
    QLineEdit, QCheckBox, QFileDialog, QGroupBox,
    QFormLayout, QHeaderView, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.components.drag_drop import DragDropMixin

logger = logging.getLogger(__name__)


class SorterTab(QWidget, DragDropMixin):
    """Вкладка Сортировка."""
    
    def __init__(self, app, parent=None):
        """Инициализация вкладки.
        
        Args:
            app: Экземпляр главного приложения
            parent: Родительский виджет
        """
        QWidget.__init__(self, parent)
        DragDropMixin.__init__(self)
        self.app = app
        
        # Основной layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Splitter для разделения на панели
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Левая панель: список файлов
        self._create_files_panel(splitter)
        
        # Правая панель: настройки сортировки
        self._create_settings_panel(splitter)
        
        # Устанавливаем пропорции splitter
        splitter.setSizes([400, 300])
        
        # Инициализация фильтров
        if not hasattr(self.app, 'sorter_filters'):
            self.app.sorter_filters = []
        
        # Инициализация списка файлов
        if not hasattr(self.app, 'sorter_files'):
            self.app.sorter_files = []
        
        logger.info("SorterTab создана")
    
    def _create_files_panel(self, parent):
        """Создание панели со списком файлов."""
        files_frame = QFrame()
        files_frame.setFrameShape(QFrame.Shape.StyledPanel)
        files_layout = QVBoxLayout(files_frame)
        files_layout.setContentsMargins(5, 5, 5, 5)
        files_layout.setSpacing(5)
        
        # Заголовок
        files_label = QLabel("Список файлов (Файлов: 0)")
        files_label.setFont(QFont("Robot", 10, QFont.Weight.Bold))
        files_layout.addWidget(files_label)
        self.app.sorter_files_label = files_label
        
        # Таблица файлов
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Файл", "Папка назначения", "Статус"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        files_layout.addWidget(self.tree)
        self.app.sorter_tree = self.tree
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        add_btn = QPushButton("+ Добавить")
        add_btn.clicked.connect(self._add_files)
        buttons_layout.addWidget(add_btn)
        
        clear_btn = QPushButton("Очистить")
        clear_btn.clicked.connect(self._clear_files)
        buttons_layout.addWidget(clear_btn)
        
        files_layout.addLayout(buttons_layout)
        
        parent.addWidget(files_frame)
    
    def _create_settings_panel(self, parent):
        """Создание панели настроек."""
        settings_frame = QFrame()
        settings_frame.setFrameShape(QFrame.Shape.StyledPanel)
        settings_layout = QVBoxLayout(settings_frame)
        settings_layout.setContentsMargins(5, 5, 5, 5)
        settings_layout.setSpacing(10)
        
        # Папка назначения
        folder_group = QGroupBox("Папка назначения")
        folder_layout = QFormLayout()
        
        self.folder_path = QLineEdit()
        self.folder_path.setPlaceholderText("Выберите папку для сортировки...")
        # По умолчанию - рабочий стол
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.exists(desktop_path):
            self.folder_path.setText(desktop_path)
        else:
            desktop_path = os.path.join(os.path.expanduser("~"), "Рабочий стол")
            if os.path.exists(desktop_path):
                self.folder_path.setText(desktop_path)
            else:
                self.folder_path.setText(os.path.expanduser("~"))
        
        folder_browse_btn = QPushButton("Обзор...")
        folder_browse_btn.clicked.connect(self._browse_folder)
        
        folder_path_layout = QHBoxLayout()
        folder_path_layout.addWidget(self.folder_path)
        folder_path_layout.addWidget(folder_browse_btn)
        folder_layout.addRow("Путь:", folder_path_layout)
        
        folder_group.setLayout(folder_layout)
        settings_layout.addWidget(folder_group)
        
        # Фильтры
        filters_group = QGroupBox("Фильтры")
        filters_layout = QVBoxLayout()
        
        # Кнопки управления фильтрами
        filters_buttons = QHBoxLayout()
        filters_buttons.setSpacing(5)
        
        add_filter_btn = QPushButton("+ Добавить фильтр")
        add_filter_btn.clicked.connect(self._add_filter)
        filters_buttons.addWidget(add_filter_btn)
        
        remove_filter_btn = QPushButton("- Удалить")
        remove_filter_btn.clicked.connect(self._remove_filter)
        filters_buttons.addWidget(remove_filter_btn)
        
        filters_layout.addLayout(filters_buttons)
        
        # Список фильтров
        self.filters_list = QTreeWidget()
        self.filters_list.setHeaderLabels(["Папка", "Тип", "Значение", "Вкл."])
        self.filters_list.setRootIsDecorated(False)
        self.filters_list.header().setStretchLastSection(False)
        self.filters_list.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.filters_list.header().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.filters_list.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.filters_list.header().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        filters_layout.addWidget(self.filters_list)
        
        filters_group.setLayout(filters_layout)
        settings_layout.addWidget(filters_group)
        
        # Кнопка сортировки
        sort_btn = QPushButton("📁 Сортировать")
        sort_btn.setFont(QFont("Robot", 11, QFont.Weight.Bold))
        sort_btn.clicked.connect(self._sort_files)
        settings_layout.addWidget(sort_btn)
        
        settings_layout.addStretch()
        
        parent.addWidget(settings_frame)
        
        # Загружаем фильтры из настроек
        self._load_filters()
    
    def _load_filters(self):
        """Загрузка фильтров из настроек."""
        if hasattr(self.app, 'sorter_filters') and self.app.sorter_filters:
            for filter_data in self.app.sorter_filters:
                self._add_filter_item(filter_data)
        else:
            # Добавляем фильтры по умолчанию
            self._add_default_filters()
    
    def _add_default_filters(self):
        """Добавление фильтров по умолчанию."""
        default_filters = [
            {'folder_name': 'Изображения', 'type': 'extension', 'value': '.jpg,.jpeg,.png,.gif,.bmp,.webp', 'enabled': True},
            {'folder_name': 'Документы', 'type': 'extension', 'value': '.pdf,.doc,.docx,.txt,.rtf', 'enabled': True},
            {'folder_name': 'Видео', 'type': 'extension', 'value': '.mp4,.avi,.mkv,.mov,.wmv', 'enabled': True},
            {'folder_name': 'Аудио', 'type': 'extension', 'value': '.mp3,.wav,.aac,.ogg,.flac', 'enabled': True},
        ]
        
        for filter_data in default_filters:
            self._add_filter_item(filter_data)
    
    def _add_filter_item(self, filter_data: Dict[str, Any] = None):
        """Добавление элемента фильтра в список.
        
        Args:
            filter_data: Данные фильтра (если None, создается новый)
        """
        item = QTreeWidgetItem(self.filters_list)
        
        if filter_data:
            item.setText(0, filter_data.get('folder_name', ''))
            item.setText(1, filter_data.get('type', 'extension'))
            item.setText(2, filter_data.get('value', ''))
            enabled = filter_data.get('enabled', True)
            item.setCheckState(3, Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
        else:
            item.setText(0, "Новая папка")
            item.setText(1, "extension")
            item.setText(2, "")
            item.setCheckState(3, Qt.CheckState.Checked)
        
        item.setData(0, Qt.ItemDataRole.UserRole, filter_data)
        self.filters_list.addTopLevelItem(item)
    
    def _add_filter(self):
        """Добавление нового фильтра."""
        self._add_filter_item()
    
    def _remove_filter(self):
        """Удаление выбранного фильтра."""
        current_item = self.filters_list.currentItem()
        if current_item:
            index = self.filters_list.indexOfTopLevelItem(current_item)
            self.filters_list.takeTopLevelItem(index)
    
    def _browse_folder(self):
        """Выбор папки для сортировки."""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку для сортировки")
        if folder:
            self.folder_path.setText(folder)
    
    def _add_files(self):
        """Добавление файлов."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выберите файлы для сортировки", "", "Все файлы (*.*)"
        )
        if files:
            self._add_files_to_list(files)
    
    def _add_files_to_list(self, file_paths: List[str]):
        """Добавление файлов в список сортировки.
        
        Args:
            file_paths: Список путей к файлам
        """
        if not hasattr(self.app, 'sorter_files'):
            self.app.sorter_files = []
        
        for file_path in file_paths:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                if file_path not in self.app.sorter_files:
                    self.app.sorter_files.append(file_path)
        
        self._refresh_files_list()
    
    def _refresh_files_list(self):
        """Обновление списка файлов."""
        self.tree.clear()
        
        if not hasattr(self.app, 'sorter_files'):
            return
        
        for file_path in self.app.sorter_files:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, os.path.basename(file_path))
            
            # Определяем папку назначения по фильтрам
            target_folder = self._get_target_folder(file_path)
            item.setText(1, target_folder if target_folder else "Не определено")
            item.setText(2, "Готов")
            item.setData(0, Qt.ItemDataRole.UserRole, file_path)
        
        if hasattr(self.app, 'sorter_files_label'):
            count = len(self.app.sorter_files)
            self.app.sorter_files_label.setText(f"Список файлов (Файлов: {count})")
    
    def _get_target_folder(self, file_path: str) -> str:
        """Определение папки назначения для файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Имя папки назначения или пустая строка
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        for i in range(self.filters_list.topLevelItemCount()):
            item = self.filters_list.topLevelItem(i)
            if item.checkState(3) == Qt.CheckState.Checked:
                folder_name = item.text(0)
                filter_type = item.text(1)
                filter_value = item.text(2)
                
                if filter_type == "extension":
                    extensions = [ext.strip().lower() for ext in filter_value.split(',')]
                    if file_ext in extensions:
                        return folder_name
        
        return ""
    
    def _clear_files(self):
        """Очистка списка файлов."""
        if hasattr(self.app, 'sorter_files'):
            self.app.sorter_files.clear()
        self.tree.clear()
        if hasattr(self.app, 'sorter_files_label'):
            self.app.sorter_files_label.setText("Список файлов (Файлов: 0)")
    
    def _sort_files(self):
        """Сортировка файлов."""
        if not hasattr(self.app, 'sorter_files') or not self.app.sorter_files:
            from ui.components.dialogs import InfoDialog
            InfoDialog.showinfo(self, "Информация", "Нет файлов для сортировки")
            return
        
        folder_path = self.folder_path.text()
        if not folder_path or not os.path.exists(folder_path):
            from ui.components.dialogs import InfoDialog
            InfoDialog.showwarning(self, "Предупреждение", "Выберите папку для сортировки")
            return
        
        # Подтверждение
        from ui.components.dialogs import ConfirmationDialog
        if not ConfirmationDialog.askyesno(
            self,
            "Подтверждение",
            f"Отсортировать {len(self.app.sorter_files)} файл(ов) в папку {folder_path}?"
        ):
            return
        
        # Собираем активные фильтры
        filters = []
        for i in range(self.filters_list.topLevelItemCount()):
            item = self.filters_list.topLevelItem(i)
            if item.checkState(3) == Qt.CheckState.Checked:
                filter_data = item.data(0, Qt.ItemDataRole.UserRole)
                if filter_data:
                    filters.append(filter_data)
                else:
                    filters.append({
                        'folder_name': item.text(0),
                        'type': item.text(1),
                        'value': item.text(2),
                        'enabled': True
                    })
        
        # Создаем поток для сортировки
        from ui.operations.sorter_operations import SorterWorker
        from ui.components.dialogs import ProgressDialog
        
        progress_dialog = ProgressDialog(
            self,
            "Сортировка файлов",
            "Выполняется сортировка..."
        )
        
        worker = SorterWorker(self.app, self.app.sorter_files, folder_path, filters)
        worker.progress.connect(lambda curr, total: progress_dialog.set_progress(curr, total))
        worker.file_processed.connect(lambda path, success, msg: progress_dialog.set_message(f"{'✓' if success else '✗'} {os.path.basename(path)}"))
        worker.finished.connect(lambda success, msg: (
            progress_dialog.close(),
            self._on_sort_finished(success, msg)
        ))
        
        progress_dialog.button_box.rejected.connect(worker.cancel)
        
        worker.start()
        progress_dialog.exec()
    
    def _on_sort_finished(self, success: bool, message: str):
        """Обработка завершения сортировки.
        
        Args:
            success: Успешно ли завершено
            message: Сообщение
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
        logger.info(f"Перетащено файлов на вкладку Сортировка: {len(files)}")
        self._add_files_to_list(files)

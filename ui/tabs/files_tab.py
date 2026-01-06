"""Вкладка Переименовщик."""

import logging
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QPushButton, QLabel,
    QHeaderView, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from ui.components.drag_drop import DragDropMixin

logger = logging.getLogger(__name__)


class FilesTab(QWidget, DragDropMixin):
    """Вкладка Переименовщик."""
    
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
        
        logger.info("FilesTab создана")
    
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
        
        # Метка "Шаблон:"
        template_label = QLabel("Шаблон:")
        template_label.setFont(QFont("Robot", 9))
        control_layout.addWidget(template_label)
        
        # Поле ввода шаблона
        self.template_input = QLineEdit()
        self.template_input.setPlaceholderText("Введите шаблон для переименования...")
        control_layout.addWidget(self.template_input, 1)  # stretch=1
        
        # Кнопка справки
        help_btn = QPushButton("?")
        help_btn.setFixedSize(15, 15)
        help_btn.setObjectName("helpButton")
        help_btn.setToolTip("Справка")
        help_btn.clicked.connect(self._show_help)
        control_layout.addWidget(help_btn)
        
        # Кнопка применения
        apply_btn = QPushButton("✓")
        apply_btn.setFixedSize(15, 15)
        apply_btn.setObjectName("applyButton")
        apply_btn.setToolTip("Применить шаблон")
        apply_btn.clicked.connect(self._apply_template)
        control_layout.addWidget(apply_btn)
        
        parent.addLayout(control_layout)
    
    def _create_files_panel(self, parent):
        """Создание панели со списком файлов."""
        # Таблица файлов
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Имя файла", "Старое имя", "Новое имя", "Путь"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setRootIsDecorated(False)
        self.tree.header().setStretchLastSection(True)
        self.tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        parent.addWidget(self.tree)
        self.app.tree = self.tree
        
        # Метка с количеством файлов
        self.app.files_label = QLabel("Список файлов (Файлов: 0)")
        parent.addWidget(self.app.files_label)
    
    def _apply_template(self):
        """Применение шаблона к файлам."""
        template = self.template_input.text()
        if not template:
            return
        
        # Применяем шаблон через методы
        if hasattr(self.app, '_apply_template_immediate'):
            self.app._apply_template_immediate()
        else:
            logger.info(f"Применение шаблона: {template}")
    
    def _show_help(self):
        """Показать справку по шаблонам."""
        from ui.components.dialogs import InfoDialog
        help_text = """Справка по шаблонам переименования:

Используйте следующие теги для создания шаблонов:

{name} - имя файла без расширения
{ext} - расширение файла
{date} - дата создания файла
{time} - время создания файла
{num} - порядковый номер файла
{size} - размер файла

Примеры:
- {name}_{num}{ext} - добавит номер к имени
- {date}_{name}{ext} - добавит дату в начало
- Фото_{num:03d}{ext} - нумерация с нулями (001, 002, ...)

Для более подробной информации см. документацию."""
        InfoDialog.showinfo(self, "Справка", help_text)
    
    def _add_files(self):
        """Добавление файлов."""
        if hasattr(self.app, 'file_list_manager'):
            self.app.file_list_manager.add_files()
        else:
            from PyQt6.QtWidgets import QFileDialog
            files, _ = QFileDialog.getOpenFileNames(
                self, "Выберите файлы", "", "Все файлы (*.*)"
            )
            if files:
                logger.info(f"Выбрано файлов: {len(files)}")
    
    def _clear_files(self):
        """Очистка списка файлов."""
        self.tree.clear()
        if hasattr(self.app, 'file_list_manager'):
            self.app.file_list_manager.clear_files()
        if hasattr(self.app, 'files_label'):
            self.app.files_label.setText("Список файлов (Файлов: 0)")
    
    def on_files_dropped(self, files):
        """Обработка перетащенных файлов.
        
        Args:
            files: Список путей к файлам
        """
        logger.info(f"Перетащено файлов на вкладку Переименовщик: {len(files)}")
        if hasattr(self.app, 'file_list_manager'):
            for file_path in files:
                self.app.file_list_manager.add_file(file_path)
            self.app.file_list_manager.refresh_treeview()
            self.app.file_list_manager.update_status()

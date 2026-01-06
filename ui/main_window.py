"""Главное окно приложения.

Содержит основную структуру интерфейса с верхними вкладками-кнопками.
"""

import logging
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Главное окно приложения."""
    
    def __init__(self, app, parent=None):
        """Инициализация главного окна.
        
        Args:
            app: Экземпляр главного приложения
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.app = app
        
        # Настройка окна
        try:
            from config.constants import APP_VERSION, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
            self.setWindowTitle(f"Ре-Файл+ v{APP_VERSION}")
            self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        except ImportError:
            self.setWindowTitle("Ре-Файл+")
            self.resize(700, 450)
        
        # Размеры окна из констант
        try:
            from config.constants import MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT
            self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        except ImportError:
            self.setMinimumSize(600, 400)
        
        # Установка иконки окна
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "materials", "icon", "Логотип.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout - вертикальный
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Верхние вкладки-кнопки
        self._create_top_tabs(main_layout)
        
        # Контейнер для содержимого вкладок
        self._create_tabs_content(main_layout)
        
        # Инициализация вкладок
        self._init_tabs()
        
        # Сохраняем ссылку на главное окно в app
        self.app.main_window = self
        
        # Устанавливаем текущую вкладку
        self.switch_tab("files")
        
        logger.info("MainWindow создано")
    
    def _create_top_tabs(self, parent):
        """Создание верхних вкладок-кнопок."""
        tabs_frame = QWidget()
        tabs_layout = QHBoxLayout(tabs_frame)
        tabs_layout.setContentsMargins(5, 5, 5, 5)
        tabs_layout.setSpacing(2)
        
        # Словарь для хранения кнопок вкладок
        self.tab_buttons = {}
        
        # Список вкладок
        tabs_list = [
            ("files", "Переименовщик"),
            ("convert", "Конвертация"),
            ("sort", "Сортировка"),
            ("settings", "Настройки"),
        ]
        
        # Создаем кнопки для вкладок
        for tab_id, tab_text in tabs_list:
            btn = QPushButton(tab_text)
            btn.setFont(QFont("Robot", 11, QFont.Weight.Bold))
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, t=tab_id: self.switch_tab(t))
            tabs_layout.addWidget(btn)
            self.tab_buttons[tab_id] = btn
        
        tabs_layout.addStretch()
        
        parent.addWidget(tabs_frame)
    
    def _create_tabs_content(self, parent):
        """Создание контейнера для содержимого вкладок."""
        # Stacked widget для переключения содержимого вкладок
        self.stacked_widget = QStackedWidget()
        parent.addWidget(self.stacked_widget)
    
    def _init_tabs(self):
        """Инициализация вкладок."""
        # Импортируем вкладки
        from ui.tabs.files_tab import FilesTab
        from ui.tabs.converter_tab import ConverterTab
        from ui.tabs.sorter_tab import SorterTab
        from ui.tabs.settings_tab import SettingsTab
        
        # Создаем вкладки
        self.files_tab = FilesTab(self.app)
        self.converter_tab = ConverterTab(self.app)
        self.sorter_tab = SorterTab(self.app)
        self.settings_tab = SettingsTab(self.app)
        
        # Добавляем вкладки в stacked widget
        self.stacked_widget.addWidget(self.files_tab)
        self.stacked_widget.addWidget(self.converter_tab)
        self.stacked_widget.addWidget(self.sorter_tab)
        self.stacked_widget.addWidget(self.settings_tab)
    
    def switch_tab(self, tab_id: str):
        """Переключение между вкладками.
        
        Args:
            tab_id: Идентификатор вкладки ('files', 'convert', 'sort', 'settings')
        """
        # Обновляем текущую вкладку
        self.app.current_tab = tab_id
        
        # Обновляем стиль кнопок
        tab_map = {
            'files': 0,
            'convert': 1,
            'sort': 2,
            'settings': 3
        }
        
        if tab_id in tab_map:
            # Устанавливаем активную кнопку
            for tid, btn in self.tab_buttons.items():
                if tid == tab_id:
                    btn.setChecked(True)
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {self.app.colors.get('primary', '#0078D4')};
                            color: white;
                            border: none;
                            padding: 8px 16px;
                            border-radius: 8px;
                        }}
                        QPushButton:hover {{
                            background-color: {self.app.colors.get('primary_hover', '#0063B1')};
                        }}
                    """)
                else:
                    btn.setChecked(False)
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {self.app.colors.get('bg_main', '#FFFFFF')};
                            color: {self.app.colors.get('text_primary', '#000000')};
                            border: none;
                            padding: 8px 16px;
                            border-radius: 8px;
                        }}
                        QPushButton:hover {{
                            background-color: {self.app.colors.get('bg_secondary', '#F5F5F5')};
                        }}
                    """)
            
            # Переключаем содержимое
            self.stacked_widget.setCurrentIndex(tab_map[tab_id])
            
            logger.info(f"Переключение на вкладку: {tab_id}")
    
    def create_widgets(self):
        """Создание всех виджетов (для совместимости)."""
        # Виджеты уже созданы в __init__
        pass

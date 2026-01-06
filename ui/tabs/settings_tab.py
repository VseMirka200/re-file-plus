"""Вкладка Настройки."""

import logging
import os
import subprocess
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QCheckBox, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class SettingsTab(QWidget):
    """Вкладка Настройки."""
    
    def __init__(self, app, parent=None):
        """Инициализация вкладки.
        
        Args:
            app: Экземпляр главного приложения
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.app = app
        self.current_section = None
        self.section_widgets = {}
        
        # Основной layout - горизонтальный (левое меню + правое содержимое)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Левое меню
        self._create_menu_panel(main_layout)
        
        # Правое содержимое
        self._create_content_panel(main_layout)
        
        # Выбираем первый раздел
        self.switch_section("remove_files")
        
        logger.info("SettingsTab создана")
    
    def _create_menu_panel(self, parent):
        """Создание левой панели меню."""
        menu_frame = QFrame()
        menu_frame.setFixedWidth(200)
        menu_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.app.colors.get('bg_main', '#FFFFFF')};
                border-right: 1px solid #CCCCCC;
            }}
        """)
        
        menu_layout = QVBoxLayout(menu_frame)
        menu_layout.setContentsMargins(0, 0, 0, 0)
        menu_layout.setSpacing(0)
        
        # Список пунктов меню
        menu_items = [
            ("Удаление файлов", "remove_files"),
            ("Логи", "logs")
        ]
        
        # Создаем кнопки меню
        self.menu_buttons = {}
        for text, value in menu_items:
            btn = QPushButton(text)
            btn.setFont(QFont("Robot", 10))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, v=value: self.switch_section(v))
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.app.colors.get('bg_main', '#FFFFFF')};
                    color: {self.app.colors.get('text_primary', '#000000')};
                    border: none;
                    text-align: left;
                    padding: 10px 15px;
                }}
                QPushButton:hover {{
                    background-color: {self.app.colors.get('bg_secondary', '#F5F5F5')};
                }}
            """)
            menu_layout.addWidget(btn)
            self.menu_buttons[value] = btn
        
        menu_layout.addStretch()
        
        # Кнопка "О программе" внизу
        about_btn = QPushButton("О программе")
        about_btn.setFont(QFont("Robot", 10))
        about_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        about_btn.clicked.connect(self._open_about_window)
        about_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.app.colors.get('bg_main', '#FFFFFF')};
                color: {self.app.colors.get('text_secondary', '#666666')};
                border: none;
                text-align: left;
                padding: 10px 15px;
            }}
            QPushButton:hover {{
                background-color: {self.app.colors.get('bg_secondary', '#F5F5F5')};
            }}
        """)
        menu_layout.addWidget(about_btn)
        self.menu_buttons["about"] = about_btn
        
        parent.addWidget(menu_frame)
    
    def _create_content_panel(self, parent):
        """Создание правой панели содержимого."""
        # Stacked widget для переключения между разделами
        self.content_stack = QStackedWidget()
        parent.addWidget(self.content_stack, 1)  # stretch=1
    
    def switch_section(self, section_name: str):
        """Переключение между разделами настроек.
        
        Args:
            section_name: Имя раздела
        """
        # Обновляем выделение в меню
        for value, btn in self.menu_buttons.items():
            if value == section_name:
                if value == "about":
                    pass  # Для "О программе" не меняем стиль
                else:
                    btn.setChecked(True)
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {self.app.colors.get('primary', '#0078D4')};
                            color: white;
                            border: none;
                            text-align: left;
                            padding: 10px 15px;
                        }}
                        QPushButton:hover {{
                            background-color: {self.app.colors.get('primary_hover', '#0063B1')};
                        }}
                    """)
            else:
                if value == "about":
                    pass
                else:
                    btn.setChecked(False)
                    btn.setStyleSheet(f"""
                        QPushButton {{
                            background-color: {self.app.colors.get('bg_main', '#FFFFFF')};
                            color: {self.app.colors.get('text_primary', '#000000')};
                            border: none;
                            text-align: left;
                            padding: 10px 15px;
                        }}
                        QPushButton:hover {{
                            background-color: {self.app.colors.get('bg_secondary', '#F5F5F5')};
                        }}
                    """)
        
        # Создаем или показываем выбранный раздел
        if section_name not in self.section_widgets:
            self._create_section_content(section_name)
        
        widget = self.section_widgets[section_name]
        self.content_stack.setCurrentWidget(widget)
        self.current_section = section_name
    
    def _create_section_content(self, section_name: str):
        """Создание содержимого для конкретного раздела настроек.
        
        Args:
            section_name: Имя раздела
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        if section_name == "remove_files":
            self._create_remove_files_section(layout)
        elif section_name == "logs":
            self._create_logs_section(layout)
        elif section_name == "about":
            self._create_about_section(layout)
        
        layout.addStretch()
        self.section_widgets[section_name] = widget
        self.content_stack.addWidget(widget)
    
    def _create_remove_files_section(self, layout):
        """Создание секции настроек удаления файлов.
        
        Args:
            layout: Layout для размещения элементов
        """
        # Заголовок
        title = QLabel("Удаление файлов")
        title.setFont(QFont("Robot", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Описание
        description = QLabel("Настройки поведения при удалении файлов")
        description.setFont(QFont("Robot", 10))
        description.setStyleSheet(f"color: {self.app.colors.get('text_secondary', '#666666')};")
        layout.addWidget(description)
        
        # Чекбокс
        if not hasattr(self.app, 'remove_files_after_operation_var'):
            default_value = False
            if hasattr(self.app, 'settings_manager'):
                default_value = self.app.settings_manager.get('remove_files_after_operation', False)
            self.app.remove_files_after_operation_var = default_value
        
        checkbox = QCheckBox("Удалять файлы из списка после операции")
        checkbox.setFont(QFont("Robot", 10))
        checkbox.setChecked(self.app.remove_files_after_operation_var)
        checkbox.stateChanged.connect(self._on_remove_files_changed)
        layout.addWidget(checkbox)
    
    def _on_remove_files_changed(self, state):
        """Обработчик изменения настройки удаления файлов."""
        value = state == Qt.CheckState.Checked.value
        self.app.remove_files_after_operation_var = value
        if hasattr(self.app, 'settings_manager'):
            self.app.settings_manager.set('remove_files_after_operation', value)
            self.app.settings_manager.save_settings()
    
    def _create_logs_section(self, layout):
        """Создание секции настроек логов.
        
        Args:
            layout: Layout для размещения элементов
        """
        # Заголовок
        title = QLabel("Логи")
        title.setFont(QFont("Robot", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Описание
        description = QLabel("Настройки логирования приложения")
        description.setFont(QFont("Robot", 10))
        description.setStyleSheet(f"color: {self.app.colors.get('text_secondary', '#666666')};")
        layout.addWidget(description)
        
        # Путь к логам
        logs_path = self._get_logs_path()
        
        path_label = QLabel(f"Путь к логам: {logs_path}")
        path_label.setFont(QFont("Robot", 9))
        path_label.setStyleSheet(f"color: {self.app.colors.get('text_secondary', '#666666')};")
        layout.addWidget(path_label)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        open_folder_btn = QPushButton("Открыть папку")
        open_folder_btn.setFont(QFont("Robot", 9))
        open_folder_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.app.colors.get('primary', '#0078D4')};
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.app.colors.get('primary_hover', '#0063B1')};
            }}
        """)
        open_folder_btn.clicked.connect(lambda: self._open_logs_folder(logs_path))
        buttons_layout.addWidget(open_folder_btn)
        
        open_file_btn = QPushButton("Открыть файл логов")
        open_file_btn.setFont(QFont("Robot", 9))
        open_file_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.app.colors.get('info', '#17A2B8')};
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {self.app.colors.get('info_hover', '#138496')};
            }}
        """)
        open_file_btn.clicked.connect(self._open_log_file)
        buttons_layout.addWidget(open_file_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
    
    def _create_about_section(self, layout):
        """Создание секции 'О программе'.
        
        Args:
            layout: Layout для размещения элементов
        """
        from ui.tabs.about_tab import AboutTab
        
        # Создаем экземпляр AboutTab для использования его метода создания содержимого
        about_tab_handler = AboutTab(
            None,  # notebook не нужен
            self.app.colors,
            None,  # bind_mousewheel не нужен
            None   # icon_photos не нужен
        )
        
        # Используем метод создания содержимого
        about_tab_handler._create_content(self)
    
    def _get_logs_path(self):
        """Получение пути к директории с логами.
        
        Returns:
            str: Путь к директории с логами
        """
        return os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "logs"
        )
    
    def _open_logs_folder(self, logs_path):
        """Открытие папки с логами."""
        try:
            self._open_path_in_system(logs_path)
        except Exception as e:
            from ui.components.dialogs import InfoDialog
            InfoDialog.showerror(self, "Ошибка", f"Не удалось открыть папку с логами:\n{e}")
    
    def _open_log_file(self):
        """Открытие файла логов."""
        logs_path = self._get_logs_path()
        log_file_path = os.path.join(logs_path, "re-file-plus.log")
        
        try:
            if os.path.exists(log_file_path):
                self._open_path_in_system(log_file_path)
            else:
                from ui.components.dialogs import InfoDialog
                InfoDialog.showinfo(self, "Информация", "Файл логов не найден")
        except Exception as e:
            from ui.components.dialogs import InfoDialog
            InfoDialog.showerror(self, "Ошибка", f"Не удалось открыть файл логов:\n{e}")
    
    def _open_path_in_system(self, path):
        """Открытие пути в системе по умолчанию.
        
        Args:
            path: Путь к файлу или директории
        """
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            logger.error(f"Ошибка при открытии пути {path}: {e}")
            raise
    
    def _open_about_window(self):
        """Открытие отдельного окна 'О программе'."""
        from PyQt6.QtWidgets import QDialog
        from ui.tabs.about_tab import AboutTab
        
        # Проверяем, не открыто ли уже окно
        if hasattr(self.app, '_about_window') and self.app._about_window is not None:
            try:
                if self.app._about_window.isVisible():
                    self.app._about_window.raise_()
                    self.app._about_window.activateWindow()
                    return
            except:
                pass
        
        # Создаем новое окно
        about_window = QDialog(self)
        about_window.setWindowTitle("О программе")
        about_window.resize(800, 600)
        about_window.setMinimumSize(600, 400)
        
        # Создаем содержимое окна
        about_tab_handler = AboutTab(
            None,
            self.app.colors,
            None,
            None
        )
        about_tab_handler._create_content(about_window)
        
        # Сохраняем ссылку на окно
        self.app._about_window = about_window
        
        about_window.exec()

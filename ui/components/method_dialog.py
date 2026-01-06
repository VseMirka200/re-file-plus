"""Диалог для добавления/редактирования методов переименования."""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QLineEdit, QSpinBox, QCheckBox,
    QGroupBox, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

logger = logging.getLogger(__name__)


class MethodDialog(QDialog):
    """Диалог для добавления/редактирования методов."""
    
    def __init__(self, app, parent=None):
        """Инициализация диалога.
        
        Args:
            app: Экземпляр приложения
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.app = app
        self.method = None
        
        self.setWindowTitle("Добавить метод")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Выбор типа метода
        type_label = QLabel("Тип метода:")
        type_label.setFont(QFont("Robot", 9, QFont.Weight.Bold))
        layout.addWidget(type_label)
        
        self.method_type = QComboBox()
        self.method_type.addItems([
            "Добавить/Удалить текст",
            "Заменить текст",
            "Изменить регистр",
            "Нумерация",
            "Метаданные",
            "Регулярное выражение",
            "Новое имя"
        ])
        self.method_type.currentIndexChanged.connect(self._on_type_changed)
        layout.addWidget(self.method_type)
        
        # Форма с параметрами метода
        self.params_group = QGroupBox("Параметры")
        self.params_layout = QFormLayout()
        self.params_group.setLayout(self.params_layout)
        layout.addWidget(self.params_group)
        
        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Инициализация формы
        self._on_type_changed()
    
    def _on_type_changed(self):
        """Обработка изменения типа метода."""
        # Очищаем форму
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        method_type = self.method_type.currentText()
        
        if method_type == "Добавить/Удалить текст":
            self._setup_add_remove_form()
        elif method_type == "Заменить текст":
            self._setup_replace_form()
        elif method_type == "Изменить регистр":
            self._setup_case_form()
        elif method_type == "Нумерация":
            self._setup_numbering_form()
        elif method_type == "Метаданные":
            self._setup_metadata_form()
        elif method_type == "Регулярное выражение":
            self._setup_regex_form()
        elif method_type == "Новое имя":
            self._setup_newname_form()
    
    def _setup_add_remove_form(self):
        """Настройка формы для добавления/удаления текста."""
        self.operation = QComboBox()
        self.operation.addItems(["Добавить", "Удалить"])
        self.params_layout.addRow("Операция:", self.operation)
        
        self.text_input = QLineEdit()
        self.params_layout.addRow("Текст:", self.text_input)
        
        self.position = QComboBox()
        self.position.addItems(["Перед именем", "После имени", "В начало", "В конец"])
        self.params_layout.addRow("Позиция:", self.position)
    
    def _setup_replace_form(self):
        """Настройка формы для замены текста."""
        self.find_input = QLineEdit()
        self.params_layout.addRow("Найти:", self.find_input)
        
        self.replace_input = QLineEdit()
        self.params_layout.addRow("Заменить на:", self.replace_input)
        
        self.case_sensitive = QCheckBox("Учитывать регистр")
        self.params_layout.addRow("", self.case_sensitive)
        
        self.full_match = QCheckBox("Только полное совпадение")
        self.params_layout.addRow("", self.full_match)
    
    def _setup_case_form(self):
        """Настройка формы для изменения регистра."""
        self.case_type = QComboBox()
        self.case_type.addItems(["Верхний", "Нижний", "Заглавная буква", "Заголовок"])
        self.params_layout.addRow("Регистр:", self.case_type)
        
        self.apply_to = QComboBox()
        self.apply_to.addItems(["Имя", "Расширение", "Все"])
        self.params_layout.addRow("Применить к:", self.apply_to)
    
    def _setup_numbering_form(self):
        """Настройка формы для нумерации."""
        self.start = QSpinBox()
        self.start.setMinimum(1)
        self.start.setMaximum(999999)
        self.start.setValue(1)
        self.params_layout.addRow("Начальный номер:", self.start)
        
        self.step = QSpinBox()
        self.step.setMinimum(1)
        self.step.setMaximum(100)
        self.step.setValue(1)
        self.params_layout.addRow("Шаг:", self.step)
        
        self.digits = QSpinBox()
        self.digits.setMinimum(1)
        self.digits.setMaximum(10)
        self.digits.setValue(3)
        self.params_layout.addRow("Количество цифр:", self.digits)
        
        self.format_str = QLineEdit("({n})")
        self.params_layout.addRow("Формат:", self.format_str)
        
        self.position = QComboBox()
        self.position.addItems(["В начало", "В конец"])
        self.params_layout.addRow("Позиция:", self.position)
    
    def _setup_metadata_form(self):
        """Настройка формы для метаданных."""
        self.metadata_type = QComboBox()
        self.metadata_type.addItems([
            "Дата создания",
            "Дата изменения",
            "Размер файла",
            "Разрешение (изображение)"
        ])
        self.params_layout.addRow("Тип метаданных:", self.metadata_type)
        
        self.format_str = QLineEdit("YYYY-MM-DD")
        self.params_layout.addRow("Формат:", self.format_str)
    
    def _setup_regex_form(self):
        """Настройка формы для регулярного выражения."""
        self.pattern = QLineEdit()
        self.params_layout.addRow("Шаблон (regex):", self.pattern)
        
        self.replacement = QLineEdit()
        self.params_layout.addRow("Замена:", self.replacement)
    
    def _setup_newname_form(self):
        """Настройка формы для нового имени."""
        self.template = QLineEdit()
        self.params_layout.addRow("Шаблон:", self.template)
    
    def get_method(self):
        """Получение созданного метода.
        
        Returns:
            Экземпляр метода или None
        """
        if not hasattr(self.app, 'methods_manager'):
            return None
        
        method_type = self.method_type.currentText()
        
        try:
            if method_type == "Добавить/Удалить текст":
                operation = "add" if self.operation.currentText() == "Добавить" else "remove"
                position_map = {
                    "Перед именем": "before",
                    "После имени": "after",
                    "В начало": "start",
                    "В конец": "end"
                }
                return self.app.methods_manager.create_add_remove_method(
                    operation,
                    self.text_input.text(),
                    position_map.get(self.position.currentText(), "before")
                )
            
            elif method_type == "Заменить текст":
                return self.app.methods_manager.create_replace_method(
                    self.find_input.text(),
                    self.replace_input.text(),
                    self.case_sensitive.isChecked(),
                    self.full_match.isChecked()
                )
            
            elif method_type == "Изменить регистр":
                case_map = {
                    "Верхний": "upper",
                    "Нижний": "lower",
                    "Заглавная буква": "capitalize",
                    "Заголовок": "title"
                }
                apply_map = {
                    "Имя": "name",
                    "Расширение": "ext",
                    "Все": "all"
                }
                return self.app.methods_manager.create_case_method(
                    case_map.get(self.case_type.currentText(), "lower"),
                    apply_map.get(self.apply_to.currentText(), "name")
                )
            
            elif method_type == "Нумерация":
                position_map = {
                    "В начало": "start",
                    "В конец": "end"
                }
                return self.app.methods_manager.create_numbering_method(
                    self.start.value(),
                    self.step.value(),
                    self.digits.value(),
                    self.format_str.text(),
                    position_map.get(self.position.currentText(), "end")
                )
            
            elif method_type == "Метаданные":
                metadata_map = {
                    "Дата создания": "creation_date",
                    "Дата изменения": "modification_date",
                    "Размер файла": "file_size",
                    "Разрешение (изображение)": "image_resolution"
                }
                return self.app.methods_manager.create_metadata_method(
                    metadata_map.get(self.metadata_type.currentText(), "creation_date"),
                    "end"  # position
                )
            
            elif method_type == "Регулярное выражение":
                return self.app.methods_manager.create_regex_method(
                    self.pattern.text(),
                    self.replacement.text()
                )
            
            elif method_type == "Новое имя":
                return self.app.methods_manager.create_new_name_method(
                    self.template.text()
                )
            
        except Exception as e:
            logger.error(f"Ошибка при создании метода: {e}", exc_info=True)
            return None
        
        return None


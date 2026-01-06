"""Модуль стилей для PyQt6 интерфейса.

Содержит стили, соответствующие оригинальному Tkinter интерфейсу.
"""

from PyQt6.QtCore import Qt


def get_application_stylesheet(colors: dict) -> str:
    """Получить стиль приложения на основе цветовой схемы.
    
    Args:
        colors: Словарь с цветами из app.colors
        
    Returns:
        Строка со стилями QSS
    """
    bg_main = colors.get('bg_main', '#FFFFFF')
    bg_secondary = colors.get('bg_secondary', '#F5F5F5')
    text_primary = colors.get('text_primary', '#000000')
    text_secondary = colors.get('text_secondary', '#666666')
    accent = colors.get('accent', '#0078D4')
    success = colors.get('success', '#107C10')
    warning = colors.get('warning', '#FFB900')
    error = colors.get('error', '#D13438')
    
    return f"""
    /* Главное окно */
    QMainWindow {{
        background-color: {bg_main};
        color: {text_primary};
    }}
    
    /* Центральный виджет */
    QWidget {{
        background-color: {bg_main};
        color: {text_primary};
        font-family: "Segoe UI", "Arial", sans-serif;
        font-size: 9pt;
    }}
    
    /* Вкладки */
    QTabWidget::pane {{
        border: 1px solid #CCCCCC;
        background-color: {bg_main};
        top: -1px;
    }}
    
    QTabBar::tab {{
        background-color: {bg_secondary};
        color: {text_primary};
        border: 1px solid #CCCCCC;
        border-bottom-color: #CCCCCC;
        padding: 8px 16px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {bg_main};
        color: {text_primary};
        border-bottom-color: {bg_main};
    }}
    
    QTabBar::tab:hover {{
        background-color: #E5E5E5;
    }}
    
    /* Кнопки */
    QPushButton {{
        background-color: {bg_secondary};
        color: {text_primary};
        border: 1px solid #CCCCCC;
        border-radius: 4px;
        padding: 6px 12px;
        min-height: 24px;
        min-width: 24px;
        font-weight: normal;
    }}
    
    QPushButton:hover {{
        background-color: #E5E5E5;
        border-color: #999999;
    }}
    
    QPushButton:pressed {{
        background-color: #D0D0D0;
    }}
    
    QPushButton:disabled {{
        background-color: {bg_secondary};
        color: {text_secondary};
        border-color: #E0E0E0;
    }}
    
    /* Цветные кнопки (маленькие квадратные) */
    QPushButton#addButton {{
        background-color: #107C10;
        color: white;
        border-color: #0E6B0E;
        padding: 0px;
        margin: 0px;
        min-height: 0px;
        min-width: 0px;
        max-height: 15px;
        max-width: 15px;
        font-size: 10px;
    }}
    
    QPushButton#addButton:hover {{
        background-color: #0E6B0E;
    }}
    
    QPushButton#clearButton {{
        background-color: #D13438;
        color: white;
        border-color: #B02A2E;
        padding: 0px;
        margin: 0px;
        min-height: 0px;
        min-width: 0px;
        max-height: 15px;
        max-width: 15px;
        font-size: 10px;
    }}
    
    QPushButton#clearButton:hover {{
        background-color: #B02A2E;
    }}
    
    QPushButton#helpButton {{
        background-color: #0078D4;
        color: white;
        border-color: #0063B1;
        padding: 0px;
        margin: 0px;
        min-height: 0px;
        min-width: 0px;
        max-height: 15px;
        max-width: 15px;
        font-size: 10px;
    }}
    
    QPushButton#helpButton:hover {{
        background-color: #0063B1;
    }}
    
    QPushButton#applyButton {{
        background-color: #107C10;
        color: white;
        border-color: #0E6B0E;
        padding: 0px;
        margin: 0px;
        min-height: 0px;
        min-width: 0px;
        max-height: 15px;
        max-width: 15px;
        font-size: 10px;
    }}
    
    QPushButton#applyButton:hover {{
        background-color: #0E6B0E;
    }}
    
    QPushButton#convertButton {{
        background-color: #0078D4;
        color: white;
        border-color: #0063B1;
        padding: 0px;
        margin: 0px;
        min-height: 0px;
        min-width: 0px;
        max-height: 15px;
        max-width: 15px;
        font-size: 10px;
    }}
    
    QPushButton#convertButton:hover {{
        background-color: #0063B1;
    }}
    
    QPushButton#compressButton {{
        background-color: #FFB900;
        color: white;
        border-color: #E6A600;
        padding: 0px;
        margin: 0px;
        min-height: 0px;
        min-width: 0px;
        max-height: 15px;
        max-width: 15px;
        font-size: 10px;
    }}
    
    QPushButton#compressButton:hover {{
        background-color: #E6A600;
    }}
    
    /* Метки */
    QLabel {{
        color: {text_primary};
        background-color: transparent;
    }}
    
    /* Поля ввода */
    QLineEdit {{
        background-color: {bg_main};
        color: {text_primary};
        border: 1px solid #CCCCCC;
        border-radius: 3px;
        padding: 4px 8px;
        selection-background-color: {accent};
        selection-color: white;
    }}
    
    QLineEdit:focus {{
        border-color: {accent};
    }}
    
    /* Выпадающие списки */
    QComboBox {{
        background-color: {bg_main};
        color: {text_primary};
        border: 1px solid #CCCCCC;
        border-radius: 3px;
        padding: 4px 8px;
        min-height: 24px;
    }}
    
    QComboBox:hover {{
        border-color: #999999;
    }}
    
    QComboBox:focus {{
        border-color: {accent};
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {text_primary};
        margin-right: 5px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: {bg_main};
        color: {text_primary};
        border: 1px solid #CCCCCC;
        selection-background-color: {accent};
        selection-color: white;
    }}
    
    /* Списки */
    QListWidget {{
        background-color: {bg_main};
        color: {text_primary};
        border: 1px solid #CCCCCC;
        border-radius: 3px;
        selection-background-color: {accent};
        selection-color: white;
    }}
    
    QListWidget::item {{
        padding: 4px;
        border: none;
    }}
    
    QListWidget::item:hover {{
        background-color: {bg_secondary};
    }}
    
    QListWidget::item:selected {{
        background-color: {accent};
        color: white;
    }}
    
    /* Таблицы/Деревья */
    QTreeWidget {{
        background-color: {bg_main};
        color: {text_primary};
        border: 1px solid #CCCCCC;
        border-radius: 3px;
        alternate-background-color: {bg_secondary};
        selection-background-color: {accent};
        selection-color: white;
    }}
    
    QTreeWidget::item {{
        padding: 2px;
        border: none;
    }}
    
    QTreeWidget::item:hover {{
        background-color: {bg_secondary};
    }}
    
    QTreeWidget::item:selected {{
        background-color: {accent};
        color: white;
    }}
    
    QHeaderView::section {{
        background-color: {bg_secondary};
        color: {text_primary};
        padding: 6px;
        border: 1px solid #CCCCCC;
        border-left: none;
        border-top: none;
        font-weight: bold;
    }}
    
    QHeaderView::section:first {{
        border-left: 1px solid #CCCCCC;
    }}
    
    /* Фреймы */
    QFrame {{
        background-color: {bg_main};
        border: none;
    }}
    
    QFrame[frameShape="5"] {{
        border: 1px solid #CCCCCC;
        border-radius: 3px;
        background-color: {bg_main};
    }}
    
    /* Группы */
    QGroupBox {{
        border: 1px solid #CCCCCC;
        border-radius: 4px;
        margin-top: 8px;
        padding-top: 12px;
        background-color: {bg_main};
        font-weight: bold;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 4px;
        background-color: {bg_main};
    }}
    
    /* Спинбоксы */
    QSpinBox {{
        background-color: {bg_main};
        color: {text_primary};
        border: 1px solid #CCCCCC;
        border-radius: 3px;
        padding: 4px 8px;
        min-height: 24px;
    }}
    
    QSpinBox:focus {{
        border-color: {accent};
    }}
    
    QSpinBox::up-button, QSpinBox::down-button {{
        background-color: {bg_secondary};
        border: 1px solid #CCCCCC;
        width: 16px;
    }}
    
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: #E5E5E5;
    }}
    
    /* Чекбоксы */
    QCheckBox {{
        color: {text_primary};
        spacing: 6px;
    }}
    
    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid #CCCCCC;
        border-radius: 3px;
        background-color: {bg_main};
    }}
    
    QCheckBox::indicator:hover {{
        border-color: #999999;
    }}
    
    QCheckBox::indicator:checked {{
        background-color: {accent};
        border-color: {accent};
    }}
    
    /* Скроллбары */
    QScrollBar:vertical {{
        background-color: {bg_secondary};
        width: 12px;
        border: none;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: #CCCCCC;
        min-height: 20px;
        border-radius: 6px;
        margin: 2px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: #999999;
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background-color: {bg_secondary};
        height: 12px;
        border: none;
    }}
    
    QScrollBar::handle:horizontal {{
        background-color: #CCCCCC;
        min-width: 20px;
        border-radius: 6px;
        margin: 2px;
    }}
    
    QScrollBar::handle:horizontal:hover {{
        background-color: #999999;
    }}
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    
    /* Разделители */
    QSplitter::handle {{
        background-color: {bg_secondary};
    }}
    
    QSplitter::handle:horizontal {{
        width: 4px;
    }}
    
    QSplitter::handle:vertical {{
        height: 4px;
    }}
    
    /* Область прокрутки */
    QScrollArea {{
        border: none;
        background-color: {bg_main};
    }}
    
    /* Диалоги */
    QDialog {{
        background-color: {bg_main};
        color: {text_primary};
    }}
    
    QMessageBox {{
        background-color: {bg_main};
    }}
    
    QMessageBox QPushButton {{
        min-width: 80px;
    }}
    
    /* Прогресс-бар */
    QProgressBar {{
        border: 1px solid #CCCCCC;
        border-radius: 3px;
        text-align: center;
        background-color: {bg_secondary};
        color: {text_primary};
    }}
    
    QProgressBar::chunk {{
        background-color: {accent};
        border-radius: 2px;
    }}
    """


def apply_styles(app):
    """Применить стили к приложению.
    
    Args:
        app: Экземпляр QApplication или ReFilePlusApp
    """
    # Получаем цвета из app
    if hasattr(app, 'colors'):
        colors = app.colors
    else:
        # Цвета по умолчанию
        colors = {
            'bg_main': '#FFFFFF',
            'bg_secondary': '#F5F5F5',
            'text_primary': '#000000',
            'text_secondary': '#666666',
            'accent': '#0078D4',
            'success': '#107C10',
            'warning': '#FFB900',
            'error': '#D13438'
        }
    
    # Получаем QApplication
    from PyQt6.QtWidgets import QApplication
    qapp = QApplication.instance()
    if qapp:
        stylesheet = get_application_stylesheet(colors)
        qapp.setStyleSheet(stylesheet)


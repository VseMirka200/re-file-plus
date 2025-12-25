"""Основной класс приложения для переименования файлов.

Содержит главный класс FileRenamerApp и функцию обработки аргументов командной строки.
Использует модульную архитектуру с делегированием ответственности специализированным обработчикам.
"""

# Стандартная библиотека
import logging
import os
import sys
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk

# Локальные импорты
from app.app_initializer import AppInitializer

logger = logging.getLogger(__name__)

# Импорт функции валидации путей
try:
    try:
        from infrastructure.system.paths import is_safe_path
    except ImportError:
        from config.constants import is_safe_path
    HAS_PATH_VALIDATION = True
except ImportError:
    HAS_PATH_VALIDATION = False
    logger.warning("Функция is_safe_path недоступна, валидация путей отключена")

# Импорт структурированного логирования
try:
    from utils.structured_logging import log_action, log_batch_action
except ImportError:
    # Fallback если модуль недоступен
    def log_action(logger, level, action, message, **kwargs):
        logger.log(level, f"[{action}] {message}")
    def log_batch_action(logger, action, message, file_count, **kwargs):
        logger.info(f"[{action}] {message} (файлов: {file_count})")


def process_cli_args() -> List[str]:
    """Обработка аргументов командной строки.
    
    Фильтрует аргументы командной строки, оставляя только существующие файлы.
    Игнорирует опции (аргументы, начинающиеся с -), если они не являются путями к файлам.
    Поддерживает различные форматы путей, включая URL-формат (file://) и пути в кавычках.
    
    Returns:
        List[str]: Список путей к файлам из аргументов командной строки
    """
    files_from_args = []
    
    if len(sys.argv) > 1:
        logger.info(f"Аргументы командной строки: {sys.argv[1:]}")
        
        for arg in sys.argv[1:]:
            if not arg or not arg.strip():
                continue
            
            # Обработка URL-формата (file://) - используется LibreOffice и другими приложениями
            if arg.startswith('file://'):
                try:
                    # Удаляем префикс file:// и декодируем URL
                    import urllib.parse
                    file_path = urllib.parse.unquote(arg[7:])  # Убираем file://
                    # Убираем начальный слеш для Windows путей (file:///C:/...)
                    if sys.platform == 'win32' and file_path.startswith('/') and len(file_path) > 2:
                        if file_path[1].isalpha() and file_path[2] == ':':
                            file_path = file_path[1:]  # Убираем лишний слеш
                    normalized_path = os.path.normpath(file_path)
                    # Валидация безопасности пути
                    if HAS_PATH_VALIDATION and not is_safe_path(normalized_path):
                        logger.warning(f"Небезопасный URL-путь отклонен: {normalized_path}")
                        continue
                    if os.path.exists(normalized_path) and os.path.isfile(normalized_path):
                        files_from_args.append(normalized_path)
                        logger.info(f"Обработан URL-путь: {arg} -> {normalized_path}")
                        continue
                except Exception as e:
                    logger.debug(f"Ошибка обработки URL-пути {arg}: {e}")
            
            # Обработка коротких опций (начинаются с одного дефиса)
            if arg.startswith('-') and not arg.startswith('--'):
                normalized_arg = os.path.normpath(arg)
                # Проверяем, не является ли это путем к файлу, начинающимся с дефиса
                if os.path.exists(normalized_arg) and os.path.isfile(normalized_arg):
                    files_from_args.append(normalized_arg)
                    continue
                # Если это не файл, пропускаем (это опция)
                continue
            
            # Обработка длинных опций (начинаются с двух дефисов)
            if arg.startswith('--'):
                normalized_arg = os.path.normpath(arg)
                if os.path.exists(normalized_arg) and os.path.isfile(normalized_arg):
                    files_from_args.append(normalized_arg)
                # Пропускаем опции, которые не являются файлами
                continue
            
            # Обработка путей в кавычках (для путей с пробелами)
            cleaned_arg = arg.strip('"').strip("'")
            
            # Обработка обычных путей
            normalized_arg = os.path.normpath(cleaned_arg)
            
            # Валидация безопасности пути
            if HAS_PATH_VALIDATION and not is_safe_path(normalized_arg):
                logger.warning(f"Небезопасный путь отклонен: {normalized_arg}")
                continue
            
            # Проверяем существование файла
            if os.path.exists(normalized_arg) and os.path.isfile(normalized_arg):
                files_from_args.append(normalized_arg)
            else:
                # Попытка обработать как абсолютный путь
                try:
                    abs_path = os.path.abspath(normalized_arg)
                    # Валидация абсолютного пути
                    if HAS_PATH_VALIDATION and not is_safe_path(abs_path):
                        logger.warning(f"Небезопасный абсолютный путь отклонен: {abs_path}")
                        continue
                    if os.path.exists(abs_path) and os.path.isfile(abs_path):
                        files_from_args.append(abs_path)
                        logger.info(f"Обработан относительный путь: {arg} -> {abs_path}")
                except (OSError, ValueError) as e:
                    logger.debug(f"Не удалось обработать путь {arg}: {e}")
    
    logger.info(f"Обработано файлов из аргументов: {len(files_from_args)}")
    return files_from_args


class FileRenamerApp:
    """Главный класс приложения для переименования файлов.
    
    Управляет всем жизненным циклом приложения, включая:
    - Создание и управление пользовательским интерфейсом
    - Операции с файлами (переименование, конвертация)
    - Управление настройками и шаблонами
    - Интеграция системы плагинов
    
    Attributes:
        root: Корневое окно Tkinter
        state: Состояние приложения (ApplicationState)
        files: Список файлов для обработки (для обратной совместимости)
        methods_manager: Менеджер методов переименования
        settings_manager: Менеджер настроек приложения
        colors: Цветовая схема интерфейса
    """
    
    @property
    def files(self) -> List[Dict]:
        """Получение списка файлов (для обратной совместимости).
        
        Returns:
            Список файлов как словари
        """
        if self.state:
            # Конвертируем FileInfo в словари для обратной совместимости
            result = []
            for f in self.state.files:
                if hasattr(f, 'to_dict'):
                    # FileInfo объект
                    result.append(f.to_dict())
                elif isinstance(f, dict):
                    # Уже словарь (для обратной совместимости)
                    result.append(f)
                else:
                    # Неизвестный тип, пропускаем
                    logger.warning(f"Неизвестный тип файла в списке: {type(f)}")
            return result
        return self._files_compat if hasattr(self, '_files_compat') else []
    
    @files.setter
    def files(self, value: List[Dict]):
        """Установка списка файлов (для обратной совместимости).
        
        Args:
            value: Список файлов как словари
        """
        if self.state:
            # Конвертируем словари в FileInfo
            from core.domain.file_info import FileInfo
            self.state.files = [FileInfo.from_dict(f) for f in value]
        else:
            if not hasattr(self, '_files_compat'):
                self._files_compat = []
            self._files_compat = value
    
    def _get_files_list(self) -> List:
        """Получение реального списка файлов для модификации.
        
        Returns:
            Список файлов (FileInfo или Dict) для прямого доступа
        """
        if self.state:
            return self.state.files
        else:
            if not hasattr(self, '_files_compat'):
                self._files_compat = []
            return self._files_compat
    
    @property
    def undo_stack(self) -> List[List[Dict]]:
        """Получение стека отмены (для обратной совместимости)."""
        if self.state:
            # Конвертируем FileInfo в словари
            return [[f.to_dict() for f in files] for files in self.state.undo_stack]
        return []
    
    @undo_stack.setter
    def undo_stack(self, value: List[List[Dict]]):
        """Установка стека отмены (для обратной совместимости)."""
        if self.state:
            from core.domain.file_info import FileInfo
            self.state.undo_stack = [[FileInfo.from_dict(f) for f in files] for files in value]
    
    @property
    def redo_stack(self) -> List[List[Dict]]:
        """Получение стека повтора (для обратной совместимости)."""
        if self.state:
            return [[f.to_dict() for f in files] for files in self.state.redo_stack]
        return []
    
    @redo_stack.setter
    def redo_stack(self, value: List[List[Dict]]):
        """Установка стека повтора (для обратной совместимости)."""
        if self.state:
            from core.domain.file_info import FileInfo
            self.state.redo_stack = [[FileInfo.from_dict(f) for f in files] for files in value]
    """Главный класс приложения для переименования файлов.
    
    Управляет всем жизненным циклом приложения, включая:
    - Создание и управление пользовательским интерфейсом
    - Операции с файлами (переименование, конвертация)
    - Управление настройками и шаблонами
    - Интеграция системы плагинов
    
    Attributes:
        root: Корневое окно Tkinter
        files: Список файлов для обработки
        methods_manager: Менеджер методов переименования
        settings_manager: Менеджер настроек приложения
        colors: Цветовая схема интерфейса
    """
    
    def __init__(self, root: 'tk.Tk', files_from_args: List[str] = None):
        """Инициализация приложения.
        
        Args:
            root: Корневое окно Tkinter
            files_from_args: Список файлов из аргументов командной строки (опционально)
        """
        import logging
        logger = logging.getLogger(__name__)
        log_action(
            logger=logger,
            level=logging.INFO,
            action='APP_STARTED',
            message="Запуск приложения Ре-Файл+",
            method_name='__init__',
            file_count=len(files_from_args) if files_from_args else 0,
            details={'files_from_args': len(files_from_args) if files_from_args else 0}
        )
        
        # Состояние приложения (используем новую модель)
        try:
            from core.domain.application_state import ApplicationState
            self.state = ApplicationState()
            # Для обратной совместимости - создаем свойства files, undo_stack, redo_stack
            # которые обращаются к state
        except ImportError:
            # Fallback если модели еще не созданы
            self.state = None
            self.files: List[Dict] = []  # Список файлов: {path, old_name, new_name, extension, status}
            self.undo_stack: List[List[Dict]] = []  # Стек для отмены операций
            self.redo_stack: List[List[Dict]] = []  # Стек для повтора операций
        else:
            # Создаем свойства для обратной совместимости
            self._files_compat = []  # Временное хранилище для совместимости
        
        self.cancel_rename_var = None  # Флаг отмены переименования
        
        # Управление окнами
        self.windows = {
            'actions': None,  # Окно действий (прогресс переименования)
            'tabs': None,     # Окно с вкладками (логи, настройки, о программе, поддержка)
            'methods': None   # Окно методов переименования
        }
        self.tabs_window_notebook = None  # Notebook для окна с вкладками
        
        # Данные для вкладок (используем state если доступен)
        if self.state:
            self.converter_files = self.state.converter_files
            self.sorter_filters = self.state.sorter_filters
        else:
            self.converter_files = []  # Файлы для конвертации
            self.sorter_filters = []  # Фильтры для сортировки файлов
        
        # Инициализация приложения через AppInitializer
        self.files_from_args = files_from_args or []
        log_action(
            logger=logger,
            level=logging.INFO,
            action='APP_INIT_STARTED',
            message="Начало инициализации компонентов приложения",
            method_name='__init__'
        )
        initializer = AppInitializer(self)
        initializer.initialize(root, files_from_args)
        log_action(
            logger=logger,
            level=logging.INFO,
            action='APP_INIT_COMPLETED',
            message="Инициализация приложения завершена",
            method_name='__init__'
        )
    
    def _check_updates_background(self):
        """Проверка обновлений в фоновом режиме."""
        if hasattr(self, 'update_checker') and self.update_checker:
            try:
                update_info = self.update_checker.check_for_updates()
                if update_info and update_info.get('available'):
                    # Показываем уведомление об обновлении
                    if hasattr(self, 'notification_manager') and self.notification_manager:
                        self.notification_manager.notify_info(
                            f"Доступно обновление {update_info['latest_version']}"
                        )
            except Exception as e:
                logger.debug(f"Ошибка проверки обновлений: {e}")
    
    def bind_mousewheel(self, widget, canvas=None):
        """Привязка прокрутки колесом мыши к виджету."""
        from ui.ui_components import bind_mousewheel
        bind_mousewheel(widget, canvas)
    
    def create_rounded_button(self, parent, text, command, bg_color, fg_color='white', 
                             font=('Robot', 10, 'bold'), padx=16, pady=10, 
                             active_bg=None, active_fg='white', width=None, expand=True):
        """Создание кнопки с закругленными углами через Canvas"""
        if hasattr(self, 'ui_components'):
            return self.ui_components.create_rounded_button(
                parent, text, command, bg_color, fg_color, font, padx, pady,
                active_bg, active_fg, width, expand
            )
        return None
    
    def on_window_resize(self, event=None):
        """Обработчик изменения размера окна для адаптивного масштабирования."""
        if hasattr(self, 'main_window_handler'):
            self.main_window_handler.on_window_resize(event)
        else:
            # Fallback для обратной совместимости
            if event and event.widget == self.root:
                if hasattr(self, 'list_frame') and self.list_frame:
                    try:
                        self.root.after(50, self.update_tree_columns)
                        self.root.after(200, self.update_tree_columns)
                    except (AttributeError, Exception):
                        pass
    
    def load_settings(self):
        """Загрузка настроек из файла."""
        if hasattr(self, 'settings_tab_handler'):
            return self.settings_tab_handler.load_settings()
        return self.settings_manager.load_settings()
    
    def save_settings(self, settings_dict):
        """Сохранение настроек в файл."""
        if hasattr(self, 'settings_tab_handler'):
            return self.settings_tab_handler.save_settings(settings_dict)
        return self.settings_manager.save_settings(settings_dict)
    
    def load_templates(self):
        """Загрузка сохраненных шаблонов из файла"""
        return self.templates_manager.load_templates()
    
    def save_templates(self):
        """Сохранение шаблонов в файл"""
        return self.templates_manager.save_templates(self.saved_templates)
    
    def setup_window_resize_handler(self, window, canvas=None, canvas_window=None):
        """Настройка обработчика изменения размера для окна с canvas"""
        from ui.ui_components import setup_window_resize_handler
        setup_window_resize_handler(window, canvas, canvas_window)
    
    def update_tree_columns(self):
        """Обновление размеров колонок таблицы в соответствии с размером окна."""
        if hasattr(self, 'main_window_handler'):
            self.main_window_handler.update_tree_columns()
    
    def update_scrollbar_visibility(self, widget, scrollbar, orientation='vertical'):
        """Автоматическое управление видимостью скроллбара.
        
        Args:
            widget: Виджет (Treeview, Listbox, Text, Canvas)
            scrollbar: Скроллбар для управления
            orientation: Ориентация ('vertical' или 'horizontal')
        """
        if hasattr(self, 'main_window_handler'):
            self.main_window_handler.update_scrollbar_visibility(widget, scrollbar, orientation)
    
    def log(self, message: str):
        """Добавление сообщения в лог"""
        if hasattr(self, 'logger'):
            self.logger.log(message)
    
    # ============================================================================
    # МЕТОДЫ-ОБЕРТКИ ДЛЯ ДЕЛЕГИРОВАНИЯ ВЫЗОВОВ
    # 
    # Эти методы обеспечивают обратную совместимость и единый интерфейс.
    # Они делегируют выполнение соответствующим обработчикам, что позволяет
    # сохранить существующий API при рефакторинге внутренней структуры.
    # ============================================================================
    
    def add_files(self):
        """Добавление файлов через диалог выбора"""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.add_files()
    
    def add_folder(self):
        """Добавление папки с рекурсивным поиском"""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.add_folder()
    
    def add_file(self, file_path: str):
        """Добавление одного файла в список"""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.add_file(file_path)
    
    def delete_selected(self):
        """Удаление выбранных файлов из списка"""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.delete_selected()
    
    def clear_files(self):
        """Очистка списка файлов"""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.clear_files()
    
    def refresh_treeview(self):
        """Обновление таблицы для синхронизации с списком файлов"""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.refresh_treeview()
    
    def update_status(self):
        """Обновление статусной строки"""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.update_status()
    
    def focus_search(self):
        """Фокус на поле поиска (Ctrl+F)"""
        if hasattr(self, 'search_handler'):
            self.search_handler.focus_search()
    
    def clear_search(self):
        """Очистка поля поиска"""
        if hasattr(self, 'search_handler'):
            self.search_handler.clear_search()
    
    def select_all(self):
        """Выделение всех файлов"""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.select_all()
    
    def deselect_all(self):
        """Снятие выделения со всех файлов"""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.deselect_all()
    
    def show_file_context_menu(self, event):
        """Показ контекстного меню для файла"""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.show_file_context_menu(event)
    
    def close_window(self, window_name: str):
        """Закрытие окна по имени"""
        if hasattr(self, 'window_management_handler'):
            self.window_management_handler.close_window(window_name)
    
    def start_rename(self):
        """Начало переименования файлов"""
        if hasattr(self, 'rename_operations_handler'):
            self.rename_operations_handler.start_rename()
    
    def undo_rename(self):
        """Отмена последнего переименования"""
        if hasattr(self, 'rename_operations_handler'):
            self.rename_operations_handler.undo_rename()
    
    def redo_rename(self):
        """Повтор последнего переименования"""
        if hasattr(self, 'rename_operations_handler'):
            self.rename_operations_handler.redo_rename()
    
    def save_template_quick(self):
        """Быстрое сохранение шаблона"""
        if hasattr(self, 'ui_templates_manager'):
            self.ui_templates_manager.save_template_quick()
    
    def save_current_template(self):
        """Сохранение текущего шаблона"""
        if hasattr(self, 'ui_templates_manager'):
            self.ui_templates_manager.save_current_template()
    
    def show_saved_templates(self):
        """Показать окно с сохраненными шаблонами"""
        if hasattr(self, 'ui_templates_manager'):
            self.ui_templates_manager.show_saved_templates()
    
    def _apply_template_immediate(self):
        """Немедленное применение шаблона"""
        if hasattr(self, 'ui_templates_manager'):
            self.ui_templates_manager._apply_template_immediate()
    
    def _apply_template_delayed(self):
        """Отложенное применение шаблона"""
        if hasattr(self, 'ui_templates_manager'):
            self.ui_templates_manager._apply_template_delayed()
    
    def _create_new_name_method(self, template: str):
        """Создание метода нового имени из шаблона"""
        if hasattr(self, 'methods_panel'):
            return self.methods_panel._create_new_name_method(template)
        return None
    
    def sort_column(self, col: str):
        """Сортировка по колонке"""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.sort_column(col)
    
    def on_method_selected(self, event=None):
        """Обработка выбора метода переименования"""
        if hasattr(self, 'methods_panel'):
            self.methods_panel.on_method_selected(event)
    
    def _create_settings_tab(self, notebook):
        """Создание вкладки настроек в notebook"""
        if hasattr(self, 'settings_tab_handler'):
            self.settings_tab_handler.create_tab_for_notebook(notebook)
    
    def _create_about_tab(self, notebook):
        """Создание вкладки 'О программе' в notebook"""
        from ui.about_tab import AboutTab
        about_tab = AboutTab(
            notebook,
            self.colors,
            self.bind_mousewheel,
            self._icon_photos
        )
        about_tab.create_tab()
    
    def _create_support_tab(self, notebook):
        """Создание вкладки 'Поддержка' в notebook"""
        from ui.about_tab import SupportTab
        support_tab = SupportTab(
            notebook,
            self.colors
        )
        support_tab.create_tab()
    
    def _create_help_tab(self, notebook):
        """Создание вкладки 'Справка' в notebook"""
        from ui.help_tab import HelpTab
        help_tab = HelpTab(
            notebook,
            self.colors,
            self.bind_mousewheel
        )
        help_tab.create_tab()
    
    
    def update_scroll_region(self):
        """Обновление области прокрутки.
        
        Примечание: Этот метод создается динамически в main_window.create_widgets().
        Если он не был создан, вызов игнорируется.
        """
        pass
    
    def remove_method(self):
        """Удаление метода из списка"""
        if hasattr(self, 'methods_listbox') and hasattr(self, 'methods_manager'):
            import tkinter as tk
            selection = self.methods_listbox.curselection()
            if selection:
                index = selection[0]
                self.methods_listbox.delete(index)
                self.methods_manager.remove_method(index)
                self.log(f"Удален метод: {index + 1}")
                # Автоматически применяем методы после удаления
                self.apply_methods()
    
    def clear_methods(self):
        """Очистка всех методов"""
        if hasattr(self, 'methods_manager') and hasattr(self, 'methods_listbox'):
            from tkinter import messagebox
            if self.methods_manager.get_methods():
                if messagebox.askyesno("Подтверждение", "Очистить все методы?"):
                    self.methods_manager.clear_methods()
                    self.methods_listbox.delete(0, 'end')
                    self.log("Все методы очищены")
    
    def apply_methods(self):
        """Применение всех методов к файлам."""
        if hasattr(self, 'rename_operations_handler'):
            self.rename_operations_handler.apply_methods()
    
    def rename_complete(self, success: int, error: int, renamed_files: list = None):
        """Обработка завершения переименования.
        
        Args:
            success: Количество успешных операций
            error: Количество ошибок
            renamed_files: Список переименованных файлов
        """
        if hasattr(self, 'rename_operations_handler'):
            self.rename_operations_handler.rename_complete(success, error, renamed_files)
    
    def _process_files_from_args(self):
        """Обработка файлов из аргументов командной строки."""
        if not self.files_from_args:
            return
        
        # Добавляем файлы в основной список файлов
        if hasattr(self, 'file_list_manager'):
            files_before = len(self.files)
            for file_path in self.files_from_args:
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    self.file_list_manager.add_file(file_path)
            
            # Применяем методы, если они есть
            if self.methods_manager.get_methods():
                self.apply_methods()
            else:
                # Обновляем интерфейс
                self.file_list_manager.refresh_treeview()
            
            self.file_list_manager.update_status()
            actual_count = len(self.files) - files_before
            if actual_count > 0:
                self.log(f"Добавлено файлов из аргументов командной строки: {actual_count}")
        
        # Также добавляем файлы в конвертер (для совместимости)
        if hasattr(self, 'converter_tab_handler'):
            self.converter_tab_handler.process_files_from_args()


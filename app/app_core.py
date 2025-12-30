"""Основной класс приложения для переименования файлов.

Содержит главный класс ReFilePlusApp и функцию обработки аргументов командной строки.
Использует модульную архитектуру с делегированием ответственности специализированным обработчикам.
"""

# Стандартная библиотека
import logging
import os
from typing import Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk

# Локальные импорты
from app.app_initializer import AppInitializer

logger = logging.getLogger(__name__)

# Импорт UIComponents для создания кнопок
try:
    from ui.ui_components import UIComponents
except ImportError:
    UIComponents = None

# Импорт структурированного логирования
try:
    from utils.structured_logging import log_action, log_batch_action
except ImportError:
    # Fallback если модуль недоступен
    def log_action(logger, level, action, message, **kwargs):
        logger.log(level, f"[{action}] {message}")
    def log_batch_action(logger, action, message, file_count, **kwargs):
        logger.info(f"[{action}] {message} (файлов: {file_count})")


# Импорт process_cli_args из cli_utils для обратной совместимости
from app.cli_utils import process_cli_args


class ReFilePlusApp:
    """Главный класс приложения Ре-Файл+.
    
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
    
    def __init__(self, root: 'tk.Tk', files_from_args: List[str] = None):
        """Инициализация приложения.
        
        Args:
            root: Корневое окно Tkinter
            files_from_args: Список файлов из аргументов командной строки (опционально)
        """
        import logging
        logger = logging.getLogger(__name__)
        # Упрощенное логирование: только важные события
        if files_from_args:
            logger.info(f"Запуск приложения. Файлов из аргументов: {len(files_from_args)}")
        
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
        initializer = AppInitializer(self)
        initializer.initialize(root, files_from_args)
    
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
    
    def bind_mousewheel(self, widget: 'tk.Widget', canvas: Optional['tk.Canvas'] = None) -> None:
        """Привязка прокрутки колесом мыши к виджету.
        
        Args:
            widget: Виджет для привязки прокрутки
            canvas: Опциональный canvas для прокрутки
        """
        from ui.ui_components import bind_mousewheel
        bind_mousewheel(widget, canvas)
    
    def create_rounded_button(self, parent: 'tk.Widget', text: str, command: Callable, 
                             bg_color: str, fg_color: str = 'white', 
                             font: Tuple[str, int, str] = ('Robot', 10, 'bold'), 
                             padx: int = 16, pady: int = 10, 
                             active_bg: Optional[str] = None, active_fg: str = 'white', 
                             width: Optional[int] = None, expand: bool = True) -> Optional['tk.Widget']:
        """Создание кнопки с закругленными углами через Canvas"""
        if hasattr(self, 'ui_components'):
            return self.ui_components.create_rounded_button(
                parent, text, command, bg_color, fg_color, font, padx, pady,
                active_bg, active_fg, width, expand
            )
        return None
    
    def create_square_icon_button(self, parent: 'tk.Widget', icon: str, command: Callable, 
                                  bg_color: str = '#667EEA', fg_color: str = 'white', 
                                  size: int = 40, active_bg: Optional[str] = None, 
                                  tooltip: Optional[str] = None) -> Optional['tk.Widget']:
        """Создание квадратной кнопки со значком.
        
        Args:
            parent: Родительский виджет
            icon: Эмодзи или символ для иконки
            command: Функция-обработчик клика
            bg_color: Цвет фона
            fg_color: Цвет текста
            size: Размер кнопки
            active_bg: Цвет фона при наведении
            tooltip: Текст подсказки
            
        Returns:
            Созданный виджет кнопки или None
        """
        if UIComponents:
            return UIComponents.create_square_icon_button(
                parent, icon, command, bg_color, fg_color, size, active_bg, tooltip
            )
        return None
    
    def create_rounded_icon_button(self, parent: 'tk.Widget', icon: str, command: Callable,
                                   bg_color: str = '#667EEA', fg_color: str = 'white', 
                                   size: int = 40, active_bg: Optional[str] = None, 
                                   tooltip: Optional[str] = None, radius: int = 8) -> Optional['tk.Widget']:
        """Создание округлой кнопки со значком.
        
        Args:
            parent: Родительский виджет
            icon: Эмодзи или символ для иконки
            command: Функция-обработчик клика
            bg_color: Цвет фона
            fg_color: Цвет текста
            size: Размер кнопки
            active_bg: Цвет фона при наведении
            tooltip: Текст подсказки
            radius: Радиус скругления
            
        Returns:
            Созданный виджет кнопки или None
        """
        if UIComponents:
            return UIComponents.create_rounded_icon_button(
                parent, icon, command, bg_color, fg_color, size, active_bg, tooltip, radius
            )
        return None
    
    def create_rounded_top_tab_button(self, parent: 'tk.Widget', text: str, command: Callable, 
                                      bg_color: str, fg_color: str = '#1A202C',
                                      font: Tuple[str, int, str] = ('Robot', 11, 'bold'), 
                                      padx: int = 20, pady: int = 1, 
                                      active_bg: Optional[str] = None, active_fg: str = 'white', 
                                      radius: int = 8) -> Optional['tk.Widget']:
        """Создание кнопки вкладки с закругленными верхними углами.
        
        Args:
            parent: Родительский виджет
            text: Текст кнопки
            command: Функция-обработчик клика
            bg_color: Цвет фона
            fg_color: Цвет текста
            font: Кортеж (шрифт, размер, стиль)
            padx: Горизонтальный отступ
            pady: Вертикальный отступ
            active_bg: Цвет фона при наведении
            active_fg: Цвет текста при наведении
            radius: Радиус скругления
            
        Returns:
            Созданный виджет кнопки или None
        """
        if UIComponents:
            return UIComponents.create_rounded_top_tab_button(
                parent, text, command, bg_color, fg_color, font, padx, pady, active_bg, active_fg, radius
            )
        return None
    
    def on_window_resize(self, event: Optional['tk.Event'] = None) -> None:
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
    
    def load_settings(self) -> Dict:
        """Загрузка настроек из файла.
        
        Returns:
            Словарь с настройками
        """
        if hasattr(self, 'settings_tab_handler'):
            return self.settings_tab_handler.load_settings()
        return self.settings_manager.load_settings()
    
    def save_settings(self, settings_dict: Dict) -> bool:
        """Сохранение настроек в файл.
        
        Args:
            settings_dict: Словарь с настройками для сохранения
            
        Returns:
            True если сохранение успешно, False иначе
        """
        if hasattr(self, 'settings_tab_handler'):
            return self.settings_tab_handler.save_settings(settings_dict)
        return self.settings_manager.save_settings(settings_dict)
    
    def load_templates(self) -> List[Dict]:
        """Загрузка сохраненных шаблонов из файла.
        
        Returns:
            Список сохраненных шаблонов
        """
        return self.templates_manager.load_templates()
    
    def save_templates(self) -> bool:
        """Сохранение шаблонов в файл.
        
        Returns:
            True если сохранение успешно, False иначе
        """
        return self.templates_manager.save_templates(self.saved_templates)
    
    def setup_window_resize_handler(self, window: 'tk.Toplevel', 
                                   canvas: Optional['tk.Canvas'] = None, 
                                   canvas_window: Optional['tk.Widget'] = None) -> None:
        """Настройка обработчика изменения размера для окна с canvas.
        
        Args:
            window: Окно для обработки изменения размера
            canvas: Опциональный canvas
            canvas_window: Опциональное окно canvas
        """
        from ui.ui_components import setup_window_resize_handler
        setup_window_resize_handler(window, canvas, canvas_window)
    
    def update_tree_columns(self) -> None:
        """Обновление размеров колонок таблицы в соответствии с размером окна."""
        if hasattr(self, 'main_window_handler'):
            self.main_window_handler.update_tree_columns()
    
    def update_scrollbar_visibility(self, widget: 'tk.Widget', scrollbar: 'tk.Scrollbar', 
                                   orientation: str = 'vertical') -> None:
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
    
    def add_files(self) -> None:
        """Добавление файлов через диалог выбора."""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.add_files()
    
    def add_folder(self) -> None:
        """Добавление папки с рекурсивным поиском."""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.add_folder()
    
    def add_file(self, file_path: str) -> None:
        """Добавление одного файла в список.
        
        Args:
            file_path: Путь к файлу для добавления
        """
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.add_file(file_path)
    
    def delete_selected(self) -> None:
        """Удаление выбранных файлов из списка."""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.delete_selected()
    
    def clear_files(self) -> None:
        """Очистка списка файлов."""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.clear_files()
    
    def refresh_treeview(self) -> None:
        """Обновление таблицы для синхронизации с списком файлов."""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.refresh_treeview()
    
    def update_status(self) -> None:
        """Обновление статусной строки."""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.update_status()
    
    def focus_search(self) -> None:
        """Фокус на поле поиска (Ctrl+F)."""
        if hasattr(self, 'search_handler'):
            self.search_handler.focus_search()
    
    def clear_search(self) -> None:
        """Очистка поля поиска."""
        if hasattr(self, 'search_handler'):
            self.search_handler.clear_search()
    
    def select_all(self) -> None:
        """Выделение всех файлов."""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.select_all()
    
    def deselect_all(self) -> None:
        """Снятие выделение со всех файлов."""
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.deselect_all()
    
    def clear_all_caches(self) -> None:
        """Очистка всех кешей приложения."""
        try:
            # Очистка кешей валидации и путей
            from core.methods.file_validation import clear_all_caches
            clear_all_caches()
            
            # Очистка кеша метаданных изображений
            if hasattr(self, 'metadata_extractor') and self.metadata_extractor:
                self.metadata_extractor.clear_cache()
            
            self.log("Все кеши очищены")
            logger.info("Все кеши приложения очищены")
        except Exception as e:
            logger.error(f"Ошибка при очистке кешей: {e}", exc_info=True)
            self.log(f"Ошибка при очистке кешей: {e}")
    
    def show_file_context_menu(self, event: 'tk.Event') -> None:
        """Показ контекстного меню для файла.
        
        Args:
            event: Событие мыши
        """
        if hasattr(self, 'file_list_manager'):
            self.file_list_manager.show_file_context_menu(event)
    
    def close_window(self, window_name: str) -> None:
        """Закрытие окна по имени.
        
        Args:
            window_name: Имя окна для закрытия
        """
        if hasattr(self, 'window_management_handler'):
            self.window_management_handler.close_window(window_name)
    
    def start_re_file(self) -> None:
        """Начало re-file операций."""
        if hasattr(self, 're_file_operations_handler'):
            self.re_file_operations_handler.start_re_file()
    
    def undo_re_file(self) -> None:
        """Отмена последней re-file операции."""
        if hasattr(self, 're_file_operations_handler'):
            self.re_file_operations_handler.undo_re_file()
    
    def redo_re_file(self) -> None:
        """Повтор последней re-file операции."""
        if hasattr(self, 're_file_operations_handler'):
            self.re_file_operations_handler.redo_re_file()
    
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
    
    def _apply_template_immediate(self, force=False):
        """Немедленное применение шаблона
        
        Args:
            force: Принудительно применить шаблон, даже если он не изменился
        """
        if hasattr(self, 'ui_templates_manager'):
            self.ui_templates_manager._apply_template_immediate(force=force)
    
    def _apply_template_delayed(self):
        """Отложенное применение шаблона"""
        if hasattr(self, 'ui_templates_manager'):
            self.ui_templates_manager._apply_template_delayed()
    
    def _apply_template_debounced(self):
        """Применение шаблона с задержкой (debounce)"""
        if hasattr(self, 'ui_templates_manager'):
            self.ui_templates_manager._apply_template_debounced()
    
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
    
    
    
    def update_scroll_region(self) -> None:
        """Обновление области прокрутки.
        
        Примечание: Этот метод создается динамически в main_window.create_widgets().
        Если он не был создан, вызов игнорируется.
        """
        pass
    
    def remove_method(self) -> None:
        """Удаление метода из списка."""
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
    
    def clear_methods(self) -> None:
        """Очистка всех методов."""
        if hasattr(self, 'methods_manager') and hasattr(self, 'methods_listbox'):
            from tkinter import messagebox
            if self.methods_manager.get_methods():
                if messagebox.askyesno("Подтверждение", "Очистить все методы?"):
                    self.methods_manager.clear_methods()
                    self.methods_listbox.delete(0, 'end')
                    self.log("Все методы очищены")
    
    def apply_methods(self) -> None:
        """Применение всех методов к файлам."""
        if hasattr(self, 're_file_operations_handler'):
            self.re_file_operations_handler.apply_methods()
    
    def rename_complete(self, success: int, error: int, renamed_files: Optional[List[Dict]] = None) -> None:
        """Обработка завершения переименования.
        
        Args:
            success: Количество успешных операций
            error: Количество ошибок
            renamed_files: Список переименованных файлов
        """
        if hasattr(self, 're_file_operations_handler'):
            self.re_file_operations_handler.re_file_complete(success, error, renamed_files)
    
    def _process_files_from_args(self) -> None:
        """Обработка файлов из аргументов командной строки."""
        if not self.files_from_args:
            return
        
        # Добавляем файлы в основной список файлов
        # Оптимизация: проверяем существование один раз
        if hasattr(self, 'file_list_manager'):
            files_before = len(self.files)
            for file_path in self.files_from_args:
                # Оптимизация: os.path.isfile уже проверяет существование
                if os.path.isfile(file_path):
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


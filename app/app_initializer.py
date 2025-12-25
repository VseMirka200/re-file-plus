"""Модуль для инициализации компонентов приложения.

Отвечает за последовательную инициализацию всех компонентов приложения:
менеджеров, обработчиков UI, настроек и других систем.
"""

import logging
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    import tkinter as tk

logger = logging.getLogger(__name__)


class AppInitializer:
    """Класс для инициализации компонентов приложения."""
    
    def __init__(self, app) -> None:
        """Инициализация инициализатора приложения.
        
        Args:
            app: Экземпляр FileRenamerApp
        """
        self.app = app
    
    def initialize(self, root: 'tk.Tk', files_from_args: Optional[List[str]] = None) -> None:
        """Инициализация всех компонентов приложения.
        
        Args:
            root: Корневое окно Tkinter
            files_from_args: Список файлов из аргументов командной строки (опционально)
        """
        logger.info("Настройка базовых параметров окна")
        self._setup_root_window_basic(root)
        logger.info("Инициализация менеджеров")
        self._initialize_managers()
        logger.info("Настройка цветовой схемы")
        self._setup_root_window_colors(root)
        logger.info("Инициализация опциональных менеджеров")
        self._initialize_optional_managers()
        logger.info("Инициализация обработчиков")
        self._initialize_handlers()
        logger.info("Настройка пользовательского интерфейса")
        self._setup_ui()
        logger.info("Обработка файлов из аргументов командной строки")
        self._process_files_from_args(files_from_args or [])
    
    def _setup_root_window_basic(self, root: 'tk.Tk'):
        """Базовая настройка корневого окна приложения (до инициализации менеджеров)."""
        from ui.ui_components import set_window_icon
        
        self.app.root = root
        self.app.files_from_args = getattr(self.app, 'files_from_args', [])
        
        # Устанавливаем версию программы из констант
        try:
            from config.constants import APP_VERSION
        except ImportError:
            APP_VERSION = "1.0.0"  # Fallback если константы недоступны
        
        root.title(f"Ре-Файл+ v{APP_VERSION}")
        
        # Используем константы для размеров окна
        try:
            from config.constants import (
                DEFAULT_WINDOW_HEIGHT,
                DEFAULT_WINDOW_WIDTH,
                MIN_WINDOW_HEIGHT,
                MIN_WINDOW_WIDTH,
            )
            window_size = f"{DEFAULT_WINDOW_WIDTH}x{DEFAULT_WINDOW_HEIGHT}"
            root.geometry(window_size)
            root.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        except ImportError:
            # Fallback если константы недоступны
            root.geometry("1000x600")
            root.minsize(1000, 600)
        
        # Установка иконки приложения (как можно раньше для меню Пуск)
        self.app._icon_photos = []
        # Устанавливаем иконку сразу после создания окна
        set_window_icon(root, self.app._icon_photos)
        
        # Обновляем окно для применения иконки
        root.update_idletasks()
        
        # Повторная установка иконки после полной инициализации окна (для надежности)
        # Это важно для меню Пуск, так как Windows может кэшировать иконки процессов
        def set_icon_delayed():
            set_window_icon(root, self.app._icon_photos)
            # Принудительно обновляем окно
            root.update_idletasks()
        root.after(500, set_icon_delayed)  # Первая попытка через 500мс
        root.after(2000, set_icon_delayed)  # Вторая попытка через 2 секунды
        
        # Настройка адаптивности
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
    
    def _setup_root_window_colors(self, root: 'tk.Tk'):
        """Настройка цветов корневого окна (после инициализации менеджеров)."""
        # Настройка фона окна
        root.configure(bg=self.app.colors['bg_main'])
        
        # Привязка изменения размера окна для адаптивного масштабирования
        root.bind('<Configure>', self.app.on_window_resize)
    
    def _initialize_managers(self):
        """Инициализация основных менеджеров."""
        from core.settings_manager import SettingsManager, TemplatesManager
        from ui.ui_components import StyleManager, UIComponents
        from core.metadata import MetadataExtractor
        from core.file_converter import FileConverter
        from core.methods_manager import MethodsManager
        from utils.helpers import Logger
        
        # Менеджеры настроек и шаблонов (нужно создать раньше для использования в теме)
        self.app.settings_manager = SettingsManager()
        self.app.settings = self.app.settings_manager.settings
        self.app.templates_manager = TemplatesManager()
        self.app.saved_templates = self.app.templates_manager.templates
        
        # Настройка цветовой схемы и стилей
        self.app.style_manager = StyleManager()
        
        # Менеджер тем
        try:
            from ui.ui_components import ThemeManager
            theme_name = self.app.settings_manager.get('theme', 'light')
            self.app.theme_manager = ThemeManager(theme_name)
            self.app.colors = self.app.theme_manager.colors
        except ImportError:
            self.app.colors = self.app.style_manager.colors
        
        self.app.style = self.app.style_manager.style
        self.app.ui_components = UIComponents()
        
        # Инициализация логгера
        try:
            try:
                from infrastructure.logging.logger import Logger
            except ImportError:
                from utils.helpers import Logger
            self.app.logger = Logger()
        except (ImportError, Exception) as e:
            logger.debug(f"Не удалось инициализировать логгер: {e}")
            # Создаем заглушку
            class DummyLogger:
                def log(self, message): pass
                def set_log_widget(self, widget): pass
                def clear(self): pass
                def save(self): pass
            self.app.logger = DummyLogger()
        
        # Инициализация модуля метаданных
        self.app.metadata_extractor = MetadataExtractor()
        
        # Инициализация модуля конвертации файлов
        self.app.file_converter = FileConverter()
        
        # Инициализация менеджера методов
        self.app.methods_manager = MethodsManager(self.app.metadata_extractor)
        
        # Инициализация состояния приложения (если еще не создано)
        if not hasattr(self.app, 'state') or self.app.state is None:
            try:
                from core.domain.application_state import ApplicationState
                self.app.state = ApplicationState()
            except ImportError:
                # Fallback - состояние будет создано в app_core
                pass
    
    def _initialize_optional_managers(self):
        """Инициализация опциональных менеджеров."""
        # Менеджер резервных копий
        self.app.backup_manager = None
        try:
            from core.backup_manager import BackupManager
            backup_enabled = self.app.settings_manager.get('backup', False)
            if backup_enabled:
                self.app.backup_manager = BackupManager()
        except (ImportError, Exception) as e:
            logger.debug(f"Не удалось инициализировать менеджер резервных копий: {e}")
        
        # Менеджер истории операций
        self.app.history_manager = None
        try:
            from core.history_manager import HistoryManager
            self.app.history_manager = HistoryManager()
        except (ImportError, Exception) as e:
            logger.debug(f"Не удалось инициализировать менеджер истории: {e}")
        
        # Менеджер уведомлений
        self.app.notification_manager = None
        try:
            # Пробуем импортировать из нового модуля
            try:
                from infrastructure.system.notifications import NotificationManager
            except ImportError:
                # Fallback на старый импорт для обратной совместимости
                from utils.helpers import NotificationManager
            notifications_enabled = self.app.settings_manager.get('notifications', True)
            self.app.notification_manager = NotificationManager(enabled=notifications_enabled)
        except (ImportError, Exception) as e:
            logger.debug(f"Не удалось инициализировать менеджер уведомлений: {e}")
        
        # Менеджер статистики
        self.app.statistics_manager = None
        try:
            try:
                from infrastructure.system.statistics import StatisticsManager
            except ImportError:
                from utils.helpers import StatisticsManager
            self.app.statistics_manager = StatisticsManager()
        except (ImportError, Exception) as e:
            logger.debug(f"Не удалось инициализировать менеджер статистики: {e}")
        
        # Обработчик ошибок
        self.app.error_handler = None
        try:
            try:
                from infrastructure.system.error_handler import ErrorHandler
            except ImportError:
                from utils.helpers import ErrorHandler
            self.app.error_handler = ErrorHandler()
        except (ImportError, Exception) as e:
            logger.debug(f"Не удалось инициализировать обработчик ошибок: {e}")
        
        # Менеджер плагинов
        self.app.plugin_manager = None
        try:
            from core.plugins import PluginManager
            self.app.plugin_manager = PluginManager()
            logger.debug(f"Загружено плагинов: {len(self.app.plugin_manager.list_plugins())}")
        except (ImportError, Exception) as e:
            logger.debug(f"Не удалось инициализировать менеджер плагинов: {e}")
        
        # Менеджер переводов
        self.app.i18n_manager = None
        try:
            try:
                from infrastructure.system.i18n import I18nManager
            except ImportError:
                from utils.helpers import I18nManager
            language = self.app.settings_manager.get('language', 'ru')
            self.app.i18n_manager = I18nManager(language=language)
        except (ImportError, Exception) as e:
            logger.debug(f"Не удалось инициализировать менеджер переводов: {e}")
        
        # Проверка обновлений
        self.app.update_checker = None
        try:
            try:
                from infrastructure.system.updates import UpdateChecker
            except ImportError:
                from utils.helpers import UpdateChecker
            check_updates = self.app.settings_manager.get('check_updates', True)
            if check_updates:
                self.app.update_checker = UpdateChecker()
                # Проверяем обновления в фоне
                self.app.root.after(5000, self.app._check_updates_background)
        except (ImportError, Exception) as e:
            logger.debug(f"Не удалось инициализировать проверку обновлений: {e}")
    
    def _initialize_handlers(self):
        """Инициализация обработчиков UI."""
        from ui.main_window import HotkeysHandler, SearchHandler
        from ui.dialogs import Dialogs
        from ui.drag_drop_handler import DragDropHandler
        from ui.templates_manager import TemplatesManager as UITemplatesManager
        from ui.file_list_manager import FileListManager
        from ui.methods_panel import MethodsPanel
        from ui.converter_tab import ConverterTab
        from ui.sorter_tab import SorterTab
        from ui.settings_tab import SettingsTab
        from ui.methods_window import MethodsWindow
        from ui.main_window import MainWindow
        from ui.rename_operations import RenameOperations
        from ui.dialogs import WindowManagement
        # FileImportExport объединен с FileListManager
        
        # Инициализация обработчиков (перед созданием интерфейса)
        self.app.hotkeys_handler = HotkeysHandler(self.app.root, self.app)
        self.app.search_handler = SearchHandler(self.app)
        self.app.dialogs = Dialogs(self.app)
        self.app.drag_drop_handler = DragDropHandler(self.app)
        self.app.ui_templates_manager = UITemplatesManager(self.app)
        self.app.file_list_manager = FileListManager(self.app)
        self.app.methods_panel = MethodsPanel(self.app)
        self.app.converter_tab_handler = ConverterTab(self.app)
        self.app.sorter_tab_handler = SorterTab(self.app)
        self.app.settings_tab_handler = SettingsTab(self.app)
        self.app.methods_window_handler = MethodsWindow(self.app)
        self.app.main_window_handler = MainWindow(self.app)
        self.app.rename_operations_handler = RenameOperations(self.app)
        # FileTreeviewOperations объединен с FileListManager
        self.app.file_treeview_operations_handler = self.app.file_list_manager
        self.app.window_management_handler = WindowManagement(self.app)
        # FileImportExport объединен с FileListManager - используем методы напрямую
        self.app.file_import_export_handler = self.app.file_list_manager
    
    def _setup_ui(self):
        """Настройка пользовательского интерфейса."""
        # Создание интерфейса (после инициализации всех обработчиков)
        self.app.main_window_handler.create_widgets()
        
        # Настройка drag and drop для файлов из проводника
        # Используем after с задержкой для регистрации после того, как окно полностью отрисовано и видимо
        def setup_drag_drop_delayed():
            """Отложенная настройка drag and drop с проверками."""
            try:
                # Проверяем, что окно видимо и готово
                if hasattr(self.app.root, 'winfo_viewable') and self.app.root.winfo_viewable():
                    self.app.drag_drop_handler.setup_drag_drop()
                else:
                    # Если окно еще не готово, пробуем еще раз
                    self.app.root.after(500, setup_drag_drop_delayed)
            except Exception as e:
                logger.error(f"Ошибка при отложенной настройке drag and drop: {e}", exc_info=True)
                # Пробуем еще раз через секунду
                self.app.root.after(1000, setup_drag_drop_delayed)
        
        # Регистрация через 1000мс после создания интерфейса (одна попытка)
        self.app.root.after(1000, setup_drag_drop_delayed)
        
        # Настройка перестановки файлов в таблице
        self.app.drag_drop_handler.setup_treeview_drag_drop()
        
        # Обработчик закрытия окна - закрытие приложения
        self.app.root.protocol("WM_DELETE_WINDOW", self._on_close_window)
    
    def _process_files_from_args(self, files_from_args: list):
        """Обработка файлов из аргументов командной строки."""
        # Файлы будут обработаны через main_window_handler.create_widgets()
        # который вызывает app._process_files_from_args() с задержкой
        pass
    
    def _on_close_window(self):
        """Обработчик закрытия окна - закрытие приложения."""
        self.app.root.quit()
        self.app.root.destroy()


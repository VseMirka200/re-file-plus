"""Модуль для инициализации компонентов приложения.

Отвечает за последовательную инициализацию всех компонентов приложения:
менеджеров, обработчиков UI, настроек и других систем.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class AppInitializer:
    """Класс для инициализации всех компонентов приложения."""
    
    def __init__(self, app) -> None:
        """Инициализация инициализатора приложения.
        
        Args:
            app: Экземпляр ReFilePlusApp
        """
        self.app = app
    
    def initialize(self, files_from_args: Optional[List[str]] = None) -> None:
        """Инициализация всех компонентов приложения.
        
        Args:
            files_from_args: Список файлов из аргументов командной строки (опционально)
        """
        logger.info("Инициализация менеджеров")
        self._initialize_managers()
        logger.info("Инициализация опциональных менеджеров")
        self._initialize_optional_managers()
        logger.info("Инициализация обработчиков")
        self._initialize_handlers()
        logger.info("Настройка пользовательского интерфейса")
        self._setup_ui()
        logger.info("Обработка файлов из аргументов командной строки")
        self._process_files_from_args(files_from_args or [])
    
    def _initialize_managers(self):
        """Инициализация основных менеджеров."""
        from core.managers.settings_manager import SettingsManager
        from core.managers.methods_manager import MethodsManager
        from core.managers.history_manager import HistoryManager
        from core.metadata.extractor import MetadataExtractor
        from core.file_converter import FileConverter
        
        self.app.settings_manager = SettingsManager()
        self.app.settings = self.app.settings_manager.settings
        self.app.history_manager = HistoryManager()
        
        # Загружаем настройки
        self.app.settings_manager.load_settings()
        
        # Инициализация метаданных и конвертера
        self.app.metadata_extractor = MetadataExtractor()
        self.app.file_converter = FileConverter()
        
        # Инициализация менеджера методов (нужен metadata_extractor)
        self.app.methods_manager = MethodsManager(self.app.metadata_extractor)
        
        # Инициализация состояния приложения
        try:
            from core.domain.application_state import ApplicationState
            self.app.state = ApplicationState()
        except ImportError:
            self.app.state = None
            self.app.files = []
            self.app.converter_files = []
            self.app.sorter_filters = []
            self.app.zip_files = []
            self.app.sorter_files = []
        else:
            if self.app.state:
                self.app.converter_files = self.app.state.converter_files
                self.app.sorter_filters = self.app.state.sorter_filters
                # Убеждаемся, что files доступен через state
                if not hasattr(self.app.state, 'files'):
                    self.app.state.files = []
            else:
                self.app.converter_files = []
                self.app.sorter_filters = []
                self.app.zip_files = []
                self.app.sorter_files = []
                self.app.files = []
        
        # Инициализация списков файлов для вкладок (если не в state)
        if not hasattr(self.app, 'zip_files'):
            self.app.zip_files = []
        if not hasattr(self.app, 'sorter_files'):
            self.app.sorter_files = []
        
        # Убеждаемся, что files доступен (для совместимости)
        if not hasattr(self.app, 'files'):
            if hasattr(self.app, 'state') and self.app.state:
                # Используем state.files как app.files для совместимости
                self.app.files = self.app.state.files
            else:
                self.app.files = []
        
        # Инициализация сервиса переименования
        try:
            from core.services.re_file_service import ReFileService
            from core.error_handling.errors import ErrorHandler
            error_handler = getattr(self.app, 'error_handler', None) or ErrorHandler()
            self.app.re_file_service = ReFileService(
                metadata_extractor=self.app.metadata_extractor,
                error_handler=error_handler
            )
        except Exception as e:
            logger.debug(f"Не удалось инициализировать сервис re-file: {e}")
            self.app.re_file_service = None
    
    def _initialize_optional_managers(self):
        """Инициализация опциональных менеджеров."""
        # FileConverter уже инициализирован в _initialize_managers
        pass
    
    def _initialize_handlers(self):
        """Инициализация обработчиков UI."""
        from ui.main_window import MainWindow
        from ui.file_list.manager import FileListManager
        
        # Создаем главное окно
        self.app.main_window = MainWindow(self.app)
        self.app.main_window_handler = self.app.main_window
        
        # Инициализация менеджера списка файлов
        self.app.file_list_manager = FileListManager(self.app)
    
    def _setup_ui(self):
        """Настройка пользовательского интерфейса."""
        # Применяем стили
        try:
            from ui.styles import apply_styles
            apply_styles(self.app)
        except Exception as e:
            logger.warning(f"Не удалось применить стили: {e}")
        
        # Создание виджетов
        if hasattr(self.app, 'main_window_handler'):
            self.app.main_window_handler.create_widgets()
        
        # Показываем главное окно
        if hasattr(self.app, 'main_window'):
            self.app.main_window.show()
    
    def _process_files_from_args(self, files_from_args: List[str]):
        """Обработка файлов из аргументов командной строки."""
        if files_from_args and hasattr(self.app, 'main_window_handler'):
            # Обработка файлов будет реализована позже
            logger.info(f"Получено файлов из аргументов: {len(files_from_args)}")


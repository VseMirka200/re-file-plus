"""Константы приложения.

Содержит все константы, используемые в приложении:
размеры окон, таймауты, форматы файлов и другие настройки.

Примечание: Функции работы с путями перенесены в infrastructure/system/paths.py
"""

# Версия приложения
APP_VERSION = "1.0.0"

# Таймауты
PACKAGE_INSTALL_TIMEOUT = 300  # 5 минут для установки пакетов
COM_OPERATION_DELAY = 0.5  # Задержка после COM операций (секунды)

# Размеры окна
DEFAULT_WINDOW_WIDTH = 700
DEFAULT_WINDOW_HEIGHT = 450
MIN_WINDOW_WIDTH = 600  # Минимальная ширина для комфортной работы
MIN_WINDOW_HEIGHT = 400  # Минимальная высота для комфортной работы

# Форматы файлов (только популярные)
SUPPORTED_IMAGE_FORMATS = {
    '.png', '.jpg', '.jpeg', '.ico', '.webp', '.gif', '.pdf'
}

SUPPORTED_DOCUMENT_FORMATS = {
    '.png', '.jpg', '.jpeg', '.pdf', '.doc', '.docx', '.odt'
}

SUPPORTED_AUDIO_FORMATS = {
    '.mp3', '.wav'
}

SUPPORTED_VIDEO_FORMATS = {
    '.mp4', '.mov', '.mkv', '.gif'
}

# Качество по умолчанию
DEFAULT_JPEG_QUALITY = 95

# Лимиты
MAX_OPERATIONS_HISTORY = 100
MAX_UNDO_STACK_SIZE = 50
MAX_PATH_CACHE_SIZE = 10000  # Максимальный размер кеша путей
WINDOWS_MAX_FILENAME_LENGTH = 255  # Максимальная длина имени файла в Windows
WINDOWS_MAX_PATH_LENGTH = 260  # Максимальная длина пути в Windows (MAX_PATH)
FILE_OPERATION_DELAY = 0.5  # Задержка для операций с файлами (секунды)
MIN_PYTHON_VERSION = (3, 7)  # Минимальная версия Python

# Интервалы обновления UI
PROGRESS_UPDATE_INTERVAL = 10  # Обновлять прогресс каждые N файлов

# Зарезервированные имена Windows
WINDOWS_RESERVED_NAMES = frozenset(
    ['CON', 'PRN', 'AUX', 'NUL'] +
    [f'COM{i}' for i in range(1, 10)] +
    [f'LPT{i}' for i in range(1, 10)]
)

# Запрещенные символы в именах файлов
INVALID_FILENAME_CHARS = frozenset(['<', '>', ':', '"', '/', '\\', '|', '?', '*'])

# Имена файлов конфигурации и логов
LOG_FILE = "re-file-plus.log"
SETTINGS_FILE = "re-file-plus_settings.json"
TEMPLATES_FILE = "re-file-plus_templates.json"
STATS_FILE = ".re_file_plus_stats.json"  # Файл статистики (хранится в домашней директории)

# Для обратной совместимости - импортируем функции из infrastructure/system/paths.py
# Эти функции перенесены в infrastructure/system/paths.py
try:
    from infrastructure.system.paths import (
        get_app_data_dir,
        get_logs_dir,
        get_data_dir,
        get_log_file_path,
        get_settings_file_path,
        get_templates_file_path,
        ensure_directory_exists,
        is_safe_path,
        check_windows_path_length
    )
except ImportError:
    # Fallback для обратной совместимости (если infrastructure еще не создан)
    # В этом случае функции должны быть определены в infrastructure/system/paths.py
    # Если они недоступны, это критическая ошибка инициализации
    import logging
    logger = logging.getLogger(__name__)
    logger.error("Критическая ошибка: не удалось импортировать функции из infrastructure.system.paths")
    
    # Минимальные fallback функции для предотвращения полного краха
    import os
    import tempfile
    from typing import Optional, List
    
    def get_app_data_dir():
        current_file = os.path.abspath(__file__)
        config_dir = os.path.dirname(current_file)
        app_dir = os.path.dirname(config_dir)
        return os.path.normpath(app_dir)
    
    def get_logs_dir():
        app_dir = get_app_data_dir()
        logs_dir = os.path.join(app_dir, "logs")
        logs_dir = os.path.normpath(logs_dir)
        if not os.path.exists(logs_dir):
            try:
                os.makedirs(logs_dir, exist_ok=True)
            except (OSError, PermissionError):
                temp_logs_dir = os.path.join(tempfile.gettempdir(), "re-file-plus-logs")
                os.makedirs(temp_logs_dir, exist_ok=True)
                return temp_logs_dir
        return logs_dir
    
    def get_data_dir():
        data_dir = os.path.join(get_app_data_dir(), "data")
        if not os.path.exists(data_dir):
            try:
                os.makedirs(data_dir, exist_ok=True)
            except (OSError, PermissionError):
                pass
        return data_dir
    
    def get_log_file_path():
        return os.path.join(get_logs_dir(), LOG_FILE)
    
    def get_settings_file_path():
        return os.path.join(get_data_dir(), SETTINGS_FILE)
    
    def get_templates_file_path():
        return os.path.join(get_data_dir(), TEMPLATES_FILE)
    
    def ensure_directory_exists(path: str) -> bool:
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except (OSError, PermissionError):
            return False
    
    # is_safe_path и check_windows_path_length должны быть импортированы из infrastructure/system/paths.py
    # Здесь не определяем их, чтобы избежать дублирования
    def is_safe_path(path: str, allowed_dirs: Optional[List[str]] = None) -> bool:
        """Fallback версия - должна использоваться только в крайнем случае."""
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Используется fallback версия is_safe_path - рекомендуется исправить импорты")
        try:
            if not isinstance(path, str) or not path or not path.strip():
                return False
            # Улучшенная проверка на path traversal
            path_parts = path.split(os.sep)
            if '..' in path_parts or path.startswith('~'):
                return False
            # Проверка на NULL байты
            if '\0' in path:
                return False
            abs_path = os.path.abspath(path)
            if not os.path.isfile(abs_path):
                return False
            if allowed_dirs:
                for allowed_dir in allowed_dirs:
                    if abs_path.startswith(os.path.abspath(allowed_dir)):
                        return True
                return False
            return True
        except (OSError, ValueError, TypeError):
            return False
    
    def check_windows_path_length(full_path: str) -> bool:
        import sys
        if sys.platform == 'win32':
            return len(full_path) <= WINDOWS_MAX_PATH_LENGTH or full_path.startswith('\\\\?\\')
        return True
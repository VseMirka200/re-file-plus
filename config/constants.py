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
DEFAULT_WINDOW_WIDTH = 900
DEFAULT_WINDOW_HEIGHT = 650
MIN_WINDOW_WIDTH = 800  # Минимальная ширина для комфортной работы
MIN_WINDOW_HEIGHT = 500  # Минимальная высота для комфортной работы

# Форматы файлов (только популярные)
SUPPORTED_IMAGE_FORMATS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif',
    '.ico', '.svg', '.heic', '.heif', '.avif', '.dng', '.cr2', '.nef', '.raw'
}

SUPPORTED_DOCUMENT_FORMATS = {
    '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
    '.txt', '.rtf', '.csv', '.html', '.htm', '.odt', '.ods', '.odp'
}

SUPPORTED_AUDIO_FORMATS = {
    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus'
}

SUPPORTED_VIDEO_FORMATS = {
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v',
    '.mpg', '.mpeg', '.3gp'
}

# Качество по умолчанию
DEFAULT_JPEG_QUALITY = 95

# Лимиты
MAX_OPERATIONS_HISTORY = 100
MAX_UNDO_STACK_SIZE = 50
MAX_PATH_CACHE_SIZE = 10000  # Максимальный размер кеша путей
WINDOWS_MAX_FILENAME_LENGTH = 255  # Максимальная длина имени файла в Windows
WINDOWS_MAX_PATH_LENGTH = 260  # Максимальная длина пути в Windows (MAX_PATH)
CONTEXT_MENU_DELAY = 0.8  # Задержка для сбора файлов из контекстного меню (секунды)
FILE_OPERATION_DELAY = 0.5  # Задержка для операций с файлами (секунды)
MIN_PYTHON_VERSION = (3, 7)  # Минимальная версия Python

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
CONTEXT_MENU_WRAPPER_LOG = "context_menu_wrapper.log"
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
        get_context_menu_wrapper_log_path,
        get_settings_file_path,
        get_templates_file_path,
        ensure_directory_exists,
        is_safe_path,
        check_windows_path_length
    )
except ImportError:
    # Fallback для обратной совместимости (если infrastructure еще не создан)
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
            except Exception:
                pass
        return data_dir
    
    def get_log_file_path():
        return os.path.join(get_logs_dir(), LOG_FILE)
    
    def get_context_menu_wrapper_log_path():
        return os.path.join(get_logs_dir(), CONTEXT_MENU_WRAPPER_LOG)
    
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
    
    def is_safe_path(path: str, allowed_dirs: Optional[List[str]] = None) -> bool:
        try:
            if not isinstance(path, str) or not path or not path.strip():
                return False
            if '..' in path or path.startswith('~'):
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
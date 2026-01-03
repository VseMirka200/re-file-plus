"""Модуль для управления настройками и шаблонами.

Обеспечивает сохранение и загрузку настроек приложения и шаблонов переименования
в JSON формате. Настройки сохраняются в директории данных приложения.
"""

import json
import logging
import os
from typing import Dict, Any, Optional

try:
    # Импорт функций работы с путями
    try:
        from infrastructure.system.paths import get_settings_file_path, get_templates_file_path
    except ImportError:
        # Fallback на старый импорт для обратной совместимости
        from config.constants import get_settings_file_path, get_templates_file_path
    SETTINGS_FILE_PATH = get_settings_file_path()
    TEMPLATES_FILE_PATH = get_templates_file_path()
except ImportError:
    # Fallback если константы не доступны
    # Используем директорию текущего файла как fallback
    app_data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(app_data_dir, "data")
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.debug(f"Не удалось создать директорию data: {e}")
            pass
    SETTINGS_FILE_PATH = os.path.join(data_dir, "re-file-plus_settings.json")
    TEMPLATES_FILE_PATH = os.path.join(data_dir, "re-file-plus_templates.json")

# Настройка логирования
logger = logging.getLogger(__name__)

# Импорт структурированного логирования
try:
    from utils.logging_utils import log_action, log_file_action
except ImportError:
    # Fallback если модуль недоступен
    def log_action(logger, level, action, message, **kwargs):
        logger.log(level, f"[{action}] {message}")
    def log_file_action(logger, action, message, **kwargs):
        logger.info(f"[{action}] {message}")


class SettingsManager:
    """Класс для управления настройками приложения.
    
    Обеспечивает загрузку, сохранение и управление настройками приложения.
    Настройки хранятся в JSON файле в домашней директории пользователя.
    Поддерживает значения по умолчанию для всех настроек.
    """
    
    DEFAULT_SETTINGS = {
        'auto_apply': False,
        'show_warnings': True,
        'font_size': '10',
        'remove_files_after_operation': False,  # Удалять файлы из списка после переименования/конвертации
        'numbering_start_number': '1',  # Начальный номер для {n} в шаблонах
        'numbering_zeros_count': '0',  # Количество ведущих нулей для {n} в шаблонах
        'numbering_method_start': '1',  # Начальный индекс для метода Нумерация
        'numbering_method_step': '1',  # Шаг для метода Нумерация
        'numbering_method_digits': '3',  # Количество цифр (ведущие нули) для метода Нумерация
        'numbering_method_format': '({n})',  # Формат для метода Нумерация
        'numbering_method_position': 'end'  # Позиция (start/end) для метода Нумерация
    }
    
    REQUIRED_SETTINGS_KEYS = {'auto_apply', 'show_warnings', 'font_size', 'remove_files_after_operation', 
                              'numbering_start_number', 'numbering_zeros_count',
                              'numbering_method_start', 'numbering_method_step', 'numbering_method_digits',
                              'numbering_method_format', 'numbering_method_position'}
    
    @staticmethod
    def validate_settings(settings: Dict[str, Any]) -> bool:
        """Валидация структуры настроек.
        
        Args:
            settings: Словарь с настройками
            
        Returns:
            True если настройки валидны, False в противном случае
        """
        if not isinstance(settings, dict):
            return False
        
        # Проверяем наличие обязательных ключей
        if not all(key in settings for key in SettingsManager.REQUIRED_SETTINGS_KEYS):
            return False
        
        # Проверяем типы значений
        if not isinstance(settings.get('auto_apply'), bool):
            return False
        if not isinstance(settings.get('show_warnings'), bool):
            return False
        if not isinstance(settings.get('remove_files_after_operation'), bool):
            return False
        if not isinstance(settings.get('font_size'), (str, int)):
            return False
        
        return True
    
    def __init__(self, settings_file: Optional[str] = None):
        """Инициализация менеджера настроек.
        
        Args:
            settings_file: Путь к файлу настроек
        """
        if settings_file is None:
            try:
                settings_file = SETTINGS_FILE_PATH
            except NameError:
                # Fallback если константы не загружены
                app_data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                data_dir = os.path.join(app_data_dir, "data")
                if not os.path.exists(data_dir):
                    try:
                        os.makedirs(data_dir, exist_ok=True)
                    except (OSError, PermissionError):
                        pass
                settings_file = os.path.join(data_dir, "re-file-plus_settings.json")
        self.settings_file = settings_file
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Загрузка настроек из файла.
        
        Returns:
            Словарь с настройками
        """
        settings = self.DEFAULT_SETTINGS.copy()
        try:
            if os.path.exists(self.settings_file):
                log_action(
                    logger=logger,
                    level=logging.INFO,
                    action='SETTINGS_LOAD_STARTED',
                    message=f"Загрузка настроек из файла",
                    method_name='load_settings',
                    file_path=self.settings_file
                )
                
                # Валидация размера файла перед загрузкой
                try:
                    from utils.security_utils import validate_json_size
                    is_valid, error_msg = validate_json_size(self.settings_file, max_size_mb=10)
                    if not is_valid:
                        log_action(
                            logger=logger,
                            level=logging.ERROR,
                            action='SETTINGS_LOAD_ERROR',
                            message=f"Файл настроек слишком большой: {error_msg}",
                            method_name='load_settings',
                            file_path=self.settings_file
                        )
                        logger.error(f"Файл настроек слишком большой: {error_msg}")
                        return settings
                except ImportError:
                    # Если утилита недоступна, пропускаем проверку
                    pass
                
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        # Валидируем загруженные настройки
                        if self.validate_settings(loaded):
                            settings.update(loaded)
                            log_action(
                                logger=logger,
                                level=logging.INFO,
                                action='SETTINGS_LOAD_SUCCESS',
                                message=f"Настройки успешно загружены",
                                method_name='load_settings',
                                file_path=self.settings_file,
                                details={'settings_count': len(settings)}
                            )
                        else:
                            log_action(
                                logger=logger,
                                level=logging.WARNING,
                                action='SETTINGS_LOAD_INVALID',
                                message=f"Файл настроек содержит неверный формат, используются настройки по умолчанию",
                                method_name='load_settings',
                                file_path=self.settings_file
                            )
                    else:
                        log_action(
                            logger=logger,
                            level=logging.WARNING,
                            action='SETTINGS_LOAD_INVALID',
                            message=f"Файл настроек содержит неверный формат",
                            method_name='load_settings',
                            file_path=self.settings_file
                        )
            else:
                log_action(
                    logger=logger,
                    level=logging.INFO,
                    action='SETTINGS_LOAD_DEFAULT',
                    message=f"Файл настроек не найден, используются настройки по умолчанию",
                    method_name='load_settings',
                    file_path=self.settings_file
                )
        except json.JSONDecodeError as e:
            log_action(
                logger=logger,
                level=logging.ERROR,
                action='SETTINGS_LOAD_ERROR',
                message=f"Ошибка парсинга JSON в настройках: {e}",
                method_name='load_settings',
                file_path=self.settings_file,
                details={'error_type': 'JSONDecodeError'}
            )
            logger.error(f"Ошибка парсинга JSON в настройках: {e}", exc_info=True)
        except (OSError, PermissionError) as e:
            log_action(
                logger=logger,
                level=logging.ERROR,
                action='SETTINGS_LOAD_ERROR',
                message=f"Ошибка доступа к файлу настроек: {e}",
                method_name='load_settings',
                file_path=self.settings_file,
                details={'error_type': type(e).__name__}
            )
            logger.error(f"Ошибка доступа к файлу настроек: {e}", exc_info=True)
        except (ValueError, TypeError) as e:
            log_action(
                logger=logger,
                level=logging.ERROR,
                action='SETTINGS_LOAD_ERROR',
                message=f"Ошибка валидации данных настроек: {e}",
                method_name='load_settings',
                file_path=self.settings_file,
                details={'error_type': type(e).__name__}
            )
            logger.error(f"Ошибка валидации данных настроек: {e}", exc_info=True)
        except (KeyboardInterrupt, SystemExit):
            # Не перехватываем системные исключения
            raise
        except (UnicodeDecodeError, IOError, MemoryError) as e:
            log_action(
                logger=logger,
                level=logging.ERROR,
                action='SETTINGS_LOAD_ERROR',
                message=f"Ошибка чтения/памяти при загрузке настроек: {e}",
                method_name='load_settings',
                file_path=self.settings_file,
                details={'error_type': type(e).__name__}
            )
            logger.error(f"Ошибка чтения/памяти при загрузке настроек: {e}", exc_info=True)
        except (MemoryError, RecursionError) as e:

            # Ошибки памяти/рекурсии

            pass

        # Финальный catch для неожиданных исключений (критично для стабильности)

        except BaseException as e:

            if isinstance(e, (KeyboardInterrupt, SystemExit)):

                raise
            log_action(
                logger=logger,
                level=logging.ERROR,
                action='SETTINGS_LOAD_ERROR',
                message=f"Неожиданная ошибка загрузки настроек: {e}",
                method_name='load_settings',
                file_path=self.settings_file,
                details={'error_type': type(e).__name__}
            )
            logger.error(f"Неожиданная ошибка загрузки настроек: {e}", exc_info=True)
        return settings
    
    def save_settings(self, settings_dict: Optional[Dict[str, Any]] = None) -> bool:
        """Сохранение настроек в файл.
        
        Args:
            settings_dict: Словарь с настройками (если None, используется self.settings)
        
        Returns:
            True если успешно, False в противном случае
        """
        if settings_dict is None:
            settings_dict = self.settings
        try:
            log_action(
                logger=logger,
                level=logging.INFO,
                action='SETTINGS_SAVE_STARTED',
                message=f"Сохранение настроек в файл",
                method_name='save_settings',
                file_path=self.settings_file,
                details={'settings_count': len(settings_dict)}
            )
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_dict, f, ensure_ascii=False, indent=2)
            self.settings = settings_dict
            log_action(
                logger=logger,
                level=logging.INFO,
                action='SETTINGS_SAVE_SUCCESS',
                message=f"Настройки успешно сохранены",
                method_name='save_settings',
                file_path=self.settings_file
            )
            return True
        except (OSError, PermissionError) as e:
            log_action(
                logger=logger,
                level=logging.ERROR,
                action='SETTINGS_SAVE_ERROR',
                message=f"Ошибка доступа при сохранении настроек: {e}",
                method_name='save_settings',
                file_path=self.settings_file,
                details={'error_type': type(e).__name__}
            )
            logger.error(f"Ошибка доступа при сохранении настроек: {e}", exc_info=True)
            return False
        except (ValueError, TypeError) as e:
            log_action(
                logger=logger,
                level=logging.ERROR,
                action='SETTINGS_SAVE_ERROR',
                message=f"Ошибка сериализации настроек: {e}",
                method_name='save_settings',
                file_path=self.settings_file,
                details={'error_type': type(e).__name__}
            )
            logger.error(f"Ошибка сериализации настроек: {e}", exc_info=True)
            return False
        except (UnicodeEncodeError, IOError, MemoryError) as e:
            log_action(
                logger=logger,
                level=logging.ERROR,
                action='SETTINGS_SAVE_ERROR',
                message=f"Ошибка записи/памяти при сохранении настроек: {e}",
                method_name='save_settings',
                file_path=self.settings_file,
                details={'error_type': type(e).__name__}
            )
            logger.error(f"Ошибка записи/памяти при сохранении настроек: {e}", exc_info=True)
            return False
        except (MemoryError, RecursionError) as e:

            # Ошибки памяти/рекурсии

            pass

        # Финальный catch для неожиданных исключений (критично для стабильности)

        except BaseException as e:

            if isinstance(e, (KeyboardInterrupt, SystemExit)):

                raise
            log_action(
                logger=logger,
                level=logging.ERROR,
                action='SETTINGS_SAVE_ERROR',
                message=f"Неожиданная ошибка сохранения настроек: {e}",
                method_name='save_settings',
                file_path=self.settings_file,
                details={'error_type': type(e).__name__}
            )
            logger.error(f"Неожиданная ошибка сохранения настроек: {e}", exc_info=True)
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получение значения настройки.
        
        Args:
            key: Ключ настройки
            default: Значение по умолчанию
        
        Returns:
            Значение настройки или default
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Установка значения настройки.
        
        Args:
            key: Ключ настройки
            value: Значение
        """
        self.settings[key] = value


class TemplatesManager:
    """Класс для управления шаблонами."""
    
    def __init__(self, templates_file: Optional[str] = None):
        """Инициализация менеджера шаблонов.
        
        Args:
            templates_file: Путь к файлу шаблонов
        """
        if templates_file is None:
            try:
                templates_file = TEMPLATES_FILE_PATH
            except NameError:
                # Fallback если константы не загружены
                app_data_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                data_dir = os.path.join(app_data_dir, "data")
                if not os.path.exists(data_dir):
                    try:
                        os.makedirs(data_dir, exist_ok=True)
                    except (OSError, PermissionError):
                        pass
                templates_file = os.path.join(data_dir, "re-file-plus_templates.json")
        self.templates_file = templates_file
        self.templates = self.load_templates()
        # Инициализируем шаблоны по умолчанию, если файл пустой
        if not self.templates:
            self._init_default_templates()
    
    def _init_default_templates(self) -> None:
        """Инициализация шаблонов по умолчанию при первом запуске."""
        default_templates = {
            "Нумерация": {
                "template": "{n}",
                "start_number": "1",
                "zeros_count": "0"
            },
            "Нумерация с префиксом": {
                "template": "Файл_{n}",
                "start_number": "1",
                "zeros_count": "0"
            },
            "Дата и имя": {
                "template": "{date_created}_{name}",
                "start_number": "1",
                "zeros_count": "0"
            },
            "Имя и дата": {
                "template": "{name}_{date_created}",
                "start_number": "1",
                "zeros_count": "0"
            },
            "Дата и нумерация": {
                "template": "{date_created}_{n}",
                "start_number": "1",
                "zeros_count": "0"
            },
            "Префикс, дата и номер": {
                "template": "IMG_{date_created}_{n}",
                "start_number": "1",
                "zeros_count": "3"
            },
            "Год-месяц-день и номер": {
                "template": "{year}-{month}-{day}_{n}",
                "start_number": "1",
                "zeros_count": "3"
            },
            "Дата и время с именем": {
                "template": "{date_created_time}_{name}",
                "start_number": "1",
                "zeros_count": "0"
            },
            "Папка и номер": {
                "template": "{dirname}_{n}",
                "start_number": "1",
                "zeros_count": "3"
            },
            "Фото: камера и ISO": {
                "template": "{camera}_ISO{iso}_{n}",
                "start_number": "1",
                "zeros_count": "3"
            },
            "Фото: размеры и номер": {
                "template": "{width}x{height}_{n}",
                "start_number": "1",
                "zeros_count": "3"
            },
            "Аудио: исполнитель - трек": {
                "template": "{artist} - {title}",
                "start_number": "1",
                "zeros_count": "0"
            },
            "Аудио: альбом - номер трека": {
                "template": "{album}_{track}",
                "start_number": "1",
                "zeros_count": "2"
            },
            "Формат и номер": {
                "template": "{format}_{n}",
                "start_number": "1",
                "zeros_count": "3"
            }
        }
        self.templates = default_templates
        self.save_templates()
        logger.info(f"Инициализировано {len(default_templates)} шаблонов по умолчанию")
    
    def load_templates(self) -> Dict[str, Any]:
        """Загрузка сохраненных шаблонов из файла.
        
        Поддерживает два формата:
        - Старый формат: строка -> строка (шаблон)
        - Новый формат: строка -> dict {'template': строка, 'start_number': строка}
        
        Returns:
            Словарь с шаблонами (в новом формате - словарь, для обратной совместимости - строка)
        """
        templates = {}
        try:
            if os.path.exists(self.templates_file):
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        for key, value in loaded.items():
                            if isinstance(key, str):
                                # Поддерживаем оба формата: строку и словарь
                                if isinstance(value, str):
                                    # Старый формат (строка) - оставляем как есть для обратной совместимости
                                    templates[key] = value
                                elif isinstance(value, dict):
                                    # Новый формат (словарь с ключом 'template')
                                    templates[key] = value
                                else:
                                    logger.warning(f"Неверный формат шаблона '{key}': ожидается строка или словарь")
                            else:
                                logger.warning(f"Неверный ключ шаблона '{key}': ожидается строка")
                    else:
                        logger.warning(f"Файл шаблонов содержит неверный формат: {self.templates_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON в шаблонах: {e}", exc_info=True)
        except (OSError, PermissionError) as e:
            logger.error(f"Ошибка доступа к файлу шаблонов: {e}", exc_info=True)
        except (ValueError, TypeError) as e:
            logger.error(f"Ошибка валидации данных шаблонов: {e}", exc_info=True)
        except (UnicodeDecodeError, IOError, MemoryError) as e:
            logger.error(f"Ошибка чтения/памяти при загрузке шаблонов: {e}", exc_info=True)
        except (MemoryError, RecursionError) as e:

            # Ошибки памяти/рекурсии

            pass

        # Финальный catch для неожиданных исключений (критично для стабильности)

        except BaseException as e:

            if isinstance(e, (KeyboardInterrupt, SystemExit)):

                raise
            logger.error(f"Неожиданная ошибка загрузки шаблонов: {e}", exc_info=True)
        return templates
    
    def save_templates(self, templates: Optional[Dict[str, Any]] = None) -> bool:
        """Сохранение шаблонов в файл.
        
        Args:
            templates: Словарь с шаблонами (если None, используется self.templates)
        
        Returns:
            True если успешно, False в противном случае
        """
        if templates is None:
            templates = self.templates
        try:
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            self.templates = templates
            return True
        except (OSError, PermissionError) as e:
            logger.error(f"Ошибка доступа при сохранении шаблонов: {e}", exc_info=True)
            return False
        except (ValueError, TypeError) as e:
            logger.error(f"Ошибка сериализации шаблонов: {e}", exc_info=True)
            return False
        except (UnicodeEncodeError, IOError, MemoryError) as e:
            logger.error(f"Ошибка записи/памяти при сохранении шаблонов: {e}", exc_info=True)
            return False
        except (MemoryError, RecursionError) as e:

            # Ошибки памяти/рекурсии

            pass

        # Финальный catch для неожиданных исключений (критично для стабильности)

        except BaseException as e:

            if isinstance(e, (KeyboardInterrupt, SystemExit)):

                raise
            logger.error(f"Неожиданная ошибка сохранения шаблонов: {e}", exc_info=True)
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Получение шаблона.
        
        Args:
            key: Ключ шаблона
            default: Значение по умолчанию
        
        Returns:
            Шаблон или default
        """
        return self.templates.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Установка шаблона.
        
        Args:
            key: Ключ шаблона
            value: Значение шаблона
        """
        self.templates[key] = value

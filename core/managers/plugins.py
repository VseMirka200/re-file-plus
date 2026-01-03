"""Модуль для системы плагинов.

Обеспечивает загрузку и управление плагинами для расширения функциональности приложения.
"""

import importlib
import importlib.util
import inspect
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class PluginManager:
    """Класс для управления плагинами."""
    
    def __init__(self, plugins_dir: Optional[str] = None):
        """Инициализация менеджера плагинов.
        
        Args:
            plugins_dir: Директория с плагинами
        """
        if plugins_dir is None:
            plugins_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'plugins'
            )
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, Any] = {}
        self.load_plugins()
    
    def load_plugins(self) -> None:
        """Загрузка всех плагинов из директории."""
        if not os.path.exists(self.plugins_dir):
            try:
                os.makedirs(self.plugins_dir, exist_ok=True)
            except (OSError, PermissionError) as e:
                logger.error(f"Не удалось создать директорию плагинов: {e}")
                return
            except (ValueError, TypeError) as e:
                logger.error(f"Ошибка типа/значения при создании директории плагинов: {e}", exc_info=True)
                return
            except (MemoryError, RecursionError) as e:

                # Ошибки памяти/рекурсии

                pass

            # Финальный catch для неожиданных исключений (критично для стабильности)

            except BaseException as e:

                if isinstance(e, (KeyboardInterrupt, SystemExit)):

                    raise
                logger.error(f"Неожиданная ошибка при создании директории плагинов: {e}", exc_info=True)
                return
        
        # Создаем __init__.py если его нет
        init_file = os.path.join(self.plugins_dir, '__init__.py')
        if not os.path.exists(init_file):
            try:
                with open(init_file, 'w', encoding='utf-8') as f:
                    f.write('# Plugins directory\n')
            except (OSError, PermissionError, IOError) as e:
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Не удалось создать __init__.py для плагинов: {e}")
                pass
        
        # Загружаем плагины
        for file in os.listdir(self.plugins_dir):
            if file.endswith('.py') and file != '__init__.py':
                plugin_name = file[:-3]
                try:
                    self._load_plugin(plugin_name)
                except (ImportError, SyntaxError, AttributeError) as e:
                    logger.error(f"Ошибка загрузки плагина {plugin_name}: {e}")
                except (FileNotFoundError, PermissionError, OSError) as e:
                    logger.error(f"Ошибка доступа при загрузке плагина {plugin_name}: {e}", exc_info=True)
                except (MemoryError, RecursionError) as e:

                    # Ошибки памяти/рекурсии

                    pass

                # Финальный catch для неожиданных исключений (критично для стабильности)

                except BaseException as e:

                    if isinstance(e, (KeyboardInterrupt, SystemExit)):

                        raise
                    logger.error(f"Неожиданная ошибка загрузки плагина {plugin_name}: {e}", exc_info=True)
    
    def _load_plugin(self, plugin_name: str) -> None:
        """Загрузка одного плагина.
        
        Args:
            plugin_name: Имя плагина
        """
        try:
            spec = importlib.util.spec_from_file_location(
                plugin_name,
                os.path.join(self.plugins_dir, f"{plugin_name}.py")
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.plugins[plugin_name] = module
                if logger.isEnabledFor(logging.DEBUG):
                    logger.debug(f"Плагин {plugin_name} загружен")
        except (ImportError, SyntaxError, AttributeError, FileNotFoundError) as e:
            logger.error(f"Ошибка загрузки плагина {plugin_name}: {e}")
        except (PermissionError, OSError, ValueError, TypeError) as e:
            logger.error(f"Ошибка доступа/типа при загрузке плагина {plugin_name}: {e}", exc_info=True)
        except (MemoryError, RecursionError) as e:

            # Ошибки памяти/рекурсии

            pass

        # Финальный catch для неожиданных исключений (критично для стабильности)

        except BaseException as e:

            if isinstance(e, (KeyboardInterrupt, SystemExit)):

                raise
            logger.error(f"Неожиданная ошибка загрузки плагина {plugin_name}: {e}", exc_info=True)
    
    def get_plugin(self, plugin_name: str):
        """Получение плагина по имени.
        
        Args:
            plugin_name: Имя плагина
            
        Returns:
            Модуль плагина или None
        """
        return self.plugins.get(plugin_name)
    
    def list_plugins(self) -> List[str]:
        """Получение списка загруженных плагинов.
        
        Returns:
            Список имен плагинов
        """
        return list(self.plugins.keys())


"""Модуль обновления UI для re-file операций."""

import logging
import os

from utils.path_processing import normalize_path

logger = logging.getLogger(__name__)


class UIUpdater:
    """Класс для обновления UI во время re-file операций."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def set_file_in_progress(self, file_path: str):
        """Установка желтого тега "в работе" для файла в treeview."""
        if not hasattr(self.app, 'tree'):
            return
        
        file_path_normalized = normalize_path(file_path)
        actual_file_index = 0
        
        for item in self.app.tree.get_children():
            tags = self.app.tree.item(item, 'tags')
            if tags and 'path_row' in tags:
                continue
            
            if actual_file_index < len(self.app.files):
                file_item = self.app.files[actual_file_index]
                item_file_path = None
                if hasattr(file_item, 'full_path'):
                    item_file_path = file_item.full_path
                elif hasattr(file_item, 'path'):
                    item_file_path = str(file_item.path) if hasattr(file_item.path, '__str__') else file_item.path
                elif isinstance(file_item, dict):
                    item_file_path = file_item.get('full_path') or file_item.get('path', '')
                
                if item_file_path:
                    item_file_path_normalized = normalize_path(item_file_path)
                    if item_file_path_normalized == file_path_normalized:
                        item_values = self.app.tree.item(item, 'values')
                        display_text = item_values[0] if item_values and len(item_values) > 0 else ''
                        path_text = item_values[1] if item_values and len(item_values) > 1 else ''
                        self.app.tree.item(item, values=(display_text, path_text), tags=())
                        break
            actual_file_index += 1
    
    def set_file_ready(self, file_path: str):
        """Установка зеленого тега "готово" для файла в treeview."""
        if not hasattr(self.app, 'tree'):
            return
        
        file_path_normalized = normalize_path(file_path)
        actual_file_index = 0
        
        for item in self.app.tree.get_children():
            tags = self.app.tree.item(item, 'tags')
            if tags and 'path_row' in tags:
                continue
            
            if actual_file_index < len(self.app.files):
                file_item = self.app.files[actual_file_index]
                item_file_path = None
                if hasattr(file_item, 'full_path'):
                    item_file_path = file_item.full_path
                elif hasattr(file_item, 'path'):
                    item_file_path = str(file_item.path) if hasattr(file_item.path, '__str__') else file_item.path
                elif isinstance(file_item, dict):
                    item_file_path = file_item.get('full_path') or file_item.get('path', '')
                
                if item_file_path:
                    item_file_path_normalized = normalize_path(item_file_path)
                    if item_file_path_normalized == file_path_normalized:
                        item_values = self.app.tree.item(item, 'values')
                        display_text = item_values[0] if item_values and len(item_values) > 0 else ''
                        path_text = item_values[1] if item_values and len(item_values) > 1 else ''
                        self.app.tree.item(item, values=(display_text, path_text), tags=())
                        break
            actual_file_index += 1
    
    def set_file_error(self, file_path: str):
        """Установка красного тега "ошибка" для файла в treeview."""
        if not hasattr(self.app, 'tree'):
            return
        
        file_path_normalized = normalize_path(file_path)
        actual_file_index = 0
        
        for item in self.app.tree.get_children():
            tags = self.app.tree.item(item, 'tags')
            if tags and 'path_row' in tags:
                continue
            
            if actual_file_index < len(self.app.files):
                file_item = self.app.files[actual_file_index]
                item_file_path = None
                if hasattr(file_item, 'full_path'):
                    item_file_path = file_item.full_path
                elif hasattr(file_item, 'path'):
                    item_file_path = str(file_item.path) if hasattr(file_item.path, '__str__') else file_item.path
                elif isinstance(file_item, dict):
                    item_file_path = file_item.get('full_path') or file_item.get('path', '')
                
                if item_file_path:
                    item_file_path_normalized = normalize_path(item_file_path)
                    if item_file_path_normalized == file_path_normalized:
                        item_values = self.app.tree.item(item, 'values')
                        display_text = item_values[0] if item_values and len(item_values) > 0 else ''
                        path_text = item_values[1] if item_values and len(item_values) > 1 else ''
                        self.app.tree.item(item, values=(display_text, path_text), tags=())
                        break
            actual_file_index += 1
    
    def update_progress_ui(self, current: int, total: int, applied: int, errors: int, filename: str = None):
        """Обновление UI прогресса."""
        try:
            if hasattr(self.app, 'progress'):
                self.app.progress['value'] = (current / total) * 100
                self.app.progress['maximum'] = 100
            
            if hasattr(self.app, 'progress_label'):
                if filename:
                    self.app.progress_label.config(
                        text=f"Обрабатывается: {filename} ({current}/{total})"
                    )
                else:
                    self.app.progress_label.config(
                        text=f"Обработано: {current}/{total}"
                    )
            
            if current % 10 == 0 or current == total:
                self.app.refresh_treeview()
        except (tk.TclError, RuntimeError, AttributeError) as e:
            logger.debug(f"Ошибка выполнения при обновлении UI прогресса: {e}")
        except (ValueError, TypeError, KeyError, IndexError) as e:
            logger.debug(f"Ошибка данных при обновлении UI прогресса: {e}")
        except (MemoryError, RecursionError) as e:

            # Ошибки памяти/рекурсии

            pass

        # Финальный catch для неожиданных исключений (критично для стабильности)

        except BaseException as e:

            if isinstance(e, (KeyboardInterrupt, SystemExit)):

                raise
            logger.debug(f"Неожиданная ошибка обновления UI прогресса: {e}")


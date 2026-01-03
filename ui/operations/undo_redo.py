"""Модуль отмены и повтора операций переименования."""

import logging
import os
from tkinter import messagebox

logger = logging.getLogger(__name__)


class UndoRedoManager:
    """Класс для управления отменой и повтором операций переименования."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def undo_re_file(self):
        """Отмена последней re-file операции."""
        if not self.app.undo_stack:
            messagebox.showinfo("Информация", "Нет операций для отмены")
            return
        
        # Сохраняем текущее состояние для redo
        current_state = [f.copy() for f in self.app.files]
        self.app.redo_stack.append(current_state)
        
        undo_state = self.app.undo_stack.pop()
        
        # Восстановление файлов
        for i, old_file_data in enumerate(undo_state):
            if i < len(self.app.files):
                current_file = self.app.files[i]
                old_path = old_file_data.get('full_path') or old_file_data.get('path')
                new_path = current_file.get('full_path') or current_file.get('path')
                
                if not old_path or not new_path:
                    continue
                
                if old_path != new_path and os.path.exists(new_path):
                    try:
                        os.rename(new_path, old_path)
                        self.app.files[i] = old_file_data.copy()
                        new_basename = os.path.basename(new_path)
                        old_basename = os.path.basename(old_path)
                        self.app.log(f"Отменено: {new_basename} -> {old_basename}")
                    except (OSError, PermissionError, FileExistsError) as e:
                        logger.error(f"Ошибка файловой системы при отмене: {e}", exc_info=True)
                        self.app.log(f"Ошибка файловой системы при отмене: {e}")
                    except (ValueError, AttributeError, KeyError) as e:
                        logger.error(f"Ошибка данных при отмене: {e}", exc_info=True)
                        self.app.log(f"Ошибка данных при отмене: {e}")
                    except (IndexError, TypeError) as e:
                        logger.error(f"Ошибка типа/индекса при отмене: {e}", exc_info=True)
                        self.app.log(f"Ошибка типа/индекса при отмене: {e}")
                    except (MemoryError, RecursionError) as e:

                        # Ошибки памяти/рекурсии

                        pass

                    # Финальный catch для неожиданных исключений (критично для стабильности)

                    except BaseException as e:

                        if isinstance(e, (KeyboardInterrupt, SystemExit)):

                            raise
                        logger.error(f"Неожиданная ошибка при отмене: {e}", exc_info=True)
                        self.app.log(f"Неожиданная ошибка при отмене: {e}")
        
        # Обновление интерфейса
        self.app.refresh_treeview()
        messagebox.showinfo("Отменено", "Последняя операция переименования отменена")
    
    def redo_re_file(self):
        """Повтор последней отмененной операции переименования."""
        if not self.app.redo_stack:
            messagebox.showinfo("Информация", "Нет операций для повтора")
            return
        
        # Сохраняем текущее состояние для undo
        current_state = [f.copy() for f in self.app.files]
        self.app.undo_stack.append(current_state)
        
        redo_state = self.app.redo_stack.pop()
        
        # Восстановление файлов из redo
        for i, redo_file_data in enumerate(redo_state):
            if i < len(self.app.files):
                current_file = self.app.files[i]
                redo_path = redo_file_data.get('full_path') or redo_file_data.get('path')
                current_path = current_file.get('full_path') or current_file.get('path')
                
                if not redo_path or not current_path:
                    continue
                
                if redo_path != current_path and os.path.exists(current_path):
                    try:
                        os.rename(current_path, redo_path)
                        self.app.files[i] = redo_file_data.copy()
                        current_basename = os.path.basename(current_path)
                        redo_basename = os.path.basename(redo_path)
                        self.app.log(f"Повторено: {current_basename} -> {redo_basename}")
                    except (OSError, PermissionError, FileExistsError) as e:
                        logger.error(f"Ошибка файловой системы при повторе: {e}", exc_info=True)
                        self.app.log(f"Ошибка файловой системы при повторе: {e}")
                    except (ValueError, AttributeError, KeyError) as e:
                        logger.error(f"Ошибка данных при повторе: {e}", exc_info=True)
                        self.app.log(f"Ошибка данных при повторе: {e}")
                    except (IndexError, TypeError) as e:
                        logger.error(f"Ошибка типа/индекса при повторе: {e}", exc_info=True)
                        self.app.log(f"Ошибка типа/индекса при повторе: {e}")
                    except (MemoryError, RecursionError) as e:

                        # Ошибки памяти/рекурсии

                        pass

                    # Финальный catch для неожиданных исключений (критично для стабильности)

                    except BaseException as e:

                        if isinstance(e, (KeyboardInterrupt, SystemExit)):

                            raise
                        logger.error(f"Неожиданная ошибка при повторе: {e}", exc_info=True)
                        self.app.log(f"Неожиданная ошибка при повторе: {e}")
        
        # Обновление интерфейса
        self.app.refresh_treeview()
        messagebox.showinfo("Повторено", "Последняя отмененная операция повторена")


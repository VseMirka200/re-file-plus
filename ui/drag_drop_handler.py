"""Модуль для обработки Drag & Drop файлов.

Обеспечивает поддержку перетаскивания файлов в окно приложения
для быстрого добавления файлов в список переименования.
"""

# Стандартная библиотека
import logging
import os
import re
import sys
import tkinter as tk
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

# Импорт функции валидации путей
try:
    # Импорт функции валидации путей
    try:
        from infrastructure.system.paths import is_safe_path
    except ImportError:
        from config.constants import is_safe_path
    HAS_PATH_VALIDATION = True
except ImportError:
    HAS_PATH_VALIDATION = False
    logger.warning("Функция is_safe_path недоступна, валидация путей отключена")

# Лимиты для безопасности
MAX_FILES_FROM_DROP = 10000  # Максимальное количество файлов из drag and drop
MAX_RECURSION_DEPTH = 20     # Максимальная глубина рекурсии при обходе директорий

# Опциональные импорты
HAS_TKINTERDND2 = False
HAS_DRAGANDDROPTK = False
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_TKINTERDND2 = True
except ImportError:
    HAS_TKINTERDND2 = False

try:
    from DragAndDropTk import DragAndDropTk
    HAS_DRAGANDDROPTK = True
except ImportError:
    HAS_DRAGANDDROPTK = False


# ============================================================================
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ОБРАБОТКИ DROP СОБЫТИЙ
# ============================================================================

def _on_drop_files(event, callback: Callable[[List[str]], None]) -> None:
    """Обработчик события сброса файлов.
    
    Args:
        event: Событие drag and drop
        callback: Функция обратного вызова
    """
    if not HAS_TKINTERDND2:
        logger.warning("tkinterdnd2 недоступен")
        return
    
    try:
        # Получаем список файлов из события
        # В tkinterdnd2 данные могут быть в разных форматах
        data = None
        
        # Метод 1: Прямое получение через атрибут data (основной способ для tkinterdnd2)
        if hasattr(event, 'data'):
            try:
                data = event.data
            except Exception as e:
                logger.warning(f"Ошибка получения event.data: {e}")
        
        # Метод 2: Через getattr (для совместимости)
        if not data:
            try:
                data = getattr(event, 'data', None)
            except Exception as e:
                logger.warning(f"Ошибка получения через getattr: {e}")
        
        # Метод 3: Пробуем другие возможные атрибуты
        if not data and hasattr(event, '__dict__'):
            try:
                for attr in ['files', 'file', 'paths', 'path']:
                    if hasattr(event, attr):
                        data = getattr(event, attr)
                        break
            except Exception as e:
                logger.warning(f"Ошибка получения через другие атрибуты: {e}")
        
        # Метод 4: Пробуем получить через метод get() если есть
        if not data:
            try:
                if hasattr(event, 'get'):
                    data = event.get('data')
            except Exception:
                pass
        
        if not data:
            logger.error("Событие drag and drop не содержит данных")
            return
        
        # Преобразуем в строку если нужно
        if not isinstance(data, str):
            data = str(data)
        
        # Обрабатываем строку с путями (формат зависит от платформы)
        file_paths = []
        
        # Метод 1: Ищем все паттерны {путь} - основной формат tkinterdnd2 на Windows
        pattern = r'\{([^}]+)\}'
        matches = re.findall(pattern, data)
        
        if matches:
            # Найдены пути в фигурных скобках - это основной формат tkinterdnd2
            file_paths = [match.strip() for match in matches if match.strip()]
        else:
            # Метод 2: Если нет фигурных скобок, пробуем другие форматы
            if sys.platform == 'win32':
                # Пробуем найти пути в кавычках: "C:\path1" "C:\path2"
                quoted_paths = re.findall(r'"([^"]+)"', data)
                if quoted_paths:
                    file_paths = [p.strip() for p in quoted_paths if p.strip()]
                else:
                    # Пробуем найти пути, начинающиеся с буквы диска
                    win_path_pattern = r'([A-Za-z]:[\\/][^\s"]+)'
                    win_matches = re.findall(win_path_pattern, data)
                    if win_matches:
                        file_paths = [m.strip() for m in win_matches if m.strip()]
                    else:
                        # Последняя попытка: пробуем как один путь
                        data_clean = data.strip().strip('"').strip("'")
                        if data_clean and os.path.exists(data_clean):
                            file_paths = [data_clean]
            else:
                # Linux/Mac: пути разделены пробелами
                parts = data.split()
                for part in parts:
                    part_clean = part.strip('"').strip("'")
                    if part_clean:
                        file_paths.append(part_clean)
        
        # Очищаем пути от лишних символов и нормализуем
        valid_files = []
        file_count = 0
        
        for file_path in file_paths:
            # Проверяем лимит файлов
            if file_count >= MAX_FILES_FROM_DROP:
                logger.warning(f"Достигнут лимит файлов из drag and drop: {MAX_FILES_FROM_DROP}")
                break
            
            file_path = file_path.strip('{}').strip('"').strip("'").strip()
            if not file_path:
                continue
            
            # Нормализуем путь
            try:
                if not os.path.isabs(file_path):
                    file_path = os.path.abspath(file_path)
                else:
                    file_path = os.path.normpath(file_path)
            except (OSError, ValueError) as e:
                logger.debug(f"Ошибка нормализации пути {file_path}: {e}")
                continue
            
            # Проверяем существование
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    # ВАЛИДАЦИЯ БЕЗОПАСНОСТИ: Проверяем путь файла на безопасность
                    if HAS_PATH_VALIDATION:
                        if not is_safe_path(file_path):
                            logger.warning(f"Небезопасный путь отклонен: {file_path}")
                            continue
                    valid_files.append(file_path)
                    file_count += 1
                elif os.path.isdir(file_path):
                    # Если папка, добавляем саму папку как элемент (не файлы из неё)
                    # Папки не проходят через is_safe_path (она проверяет только файлы),
                    # поэтому пропускаем валидацию для папок и добавляем их напрямую
                    valid_files.append(file_path)
                    file_count += 1
        
        if valid_files:
            callback(valid_files)
        else:
            logger.warning("Не найдено валидных элементов для обработки")
    except Exception as e:
        logger.error(f"Ошибка при обработке drag and drop: {e}", exc_info=True)


# ============================================================================
# КЛАСС ОБРАБОТЧИКА DRAG AND DROP
# 
# Высокоуровневый API для обработки перетаскивания файлов.
# Интегрируется с основным приложением и управляет всеми аспектами DnD.
# ============================================================================


class DragDropHandler:
    """Класс для обработки перетаскивания файлов."""
    
    def __init__(self, app) -> None:
        """Инициализация обработчика Drag & Drop.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
        self._drag_drop_logged = False
        self._drag_drop_setup = False  # Флаг для предотвращения множественной регистрации
    
    def setup_drag_drop(self):
        """Настройка drag and drop для файлов из проводника"""
        # Предотвращаем множественную регистрацию
        if self._drag_drop_setup:
            logger.debug("Drag and drop уже настроен, пропускаем повторную регистрацию")
            return
        
        # Пробуем использовать DragAndDropTk как альтернативу, если tkinterdnd2 не работает
        if HAS_DRAGANDDROPTK and not HAS_TKINTERDND2:
            try:
                logger.info("Попытка использования DragAndDropTk (альтернатива tkinterdnd2)...")
                self._setup_draganddroptk()
                if self._drag_drop_setup:
                    return  # Успешно настроено
            except Exception as e:
                logger.warning(f"Не удалось настроить DragAndDropTk: {e}", exc_info=True)
        
        if not HAS_TKINTERDND2:
            if not self._drag_drop_logged:
                error_msg = (
                    "Перетаскивание файлов недоступно!\n\n"
                    "Библиотека tkinterdnd2 не установлена.\n"
                    "Для установки выполните команду:\n"
                    "pip install tkinterdnd2\n\n"
                    "Или установите все зависимости:\n"
                    "pip install -r requirements.txt"
                )
                self.app.log(error_msg)
                logger.warning("tkinterdnd2 не установлена - drag and drop недоступен")
                # Показываем сообщение пользователю
                try:
                    import tkinter.messagebox as messagebox
                    messagebox.showwarning(
                        "Drag and Drop недоступен",
                        "Библиотека tkinterdnd2 не установлена.\n\n"
                        "Для включения перетаскивания файлов установите:\n"
                        "pip install tkinterdnd2"
                    )
                except (tk.TclError, AttributeError, RuntimeError):
                    pass
                self._drag_drop_logged = True
            return
        
        try:
            # Проверяем тип root окна
            root_type = type(self.app.root).__name__
            logger.info(f"Тип root окна: {root_type}")
            
            # Проверяем, что root поддерживает drag and drop
            if not hasattr(self.app.root, 'drop_target_register'):
                # Если root не поддерживает DnD, возможно он создан как обычный tk.Tk()
                if not self._drag_drop_logged:
                    self.app.log("Перетаскивание файлов из проводника недоступно")
                    self.app.log("Root окно не поддерживает drag and drop")
                    self.app.log(f"Тип окна: {root_type}")
                    self.app.log("Перезапустите программу для активации drag and drop")
                    self.app.log("Убедитесь, что tkinterdnd2 установлена: pip install tkinterdnd2")
                    logger.error(f"Root окно не поддерживает drop_target_register - тип окна: {root_type}")
                    self._drag_drop_logged = True
                return
            
            # Регистрируем главное окно как цель для перетаскивания файлов
            try:
                # Регистрируем DND_FILES для root окна
                # Важно: регистрация должна происходить после того, как окно отображено
                self.app.root.update()
                self.app.root.update_idletasks()  # Убеждаемся, что окно полностью отрисовано
                
                # Проверяем, что окно видимо
                if not self.app.root.winfo_viewable():
                    logger.warning("Окно не видимо, откладываем регистрацию drag and drop")
                    self.app.root.after(500, self.setup_drag_drop)
                    return
                
                # Проверяем, что root действительно поддерживает DnD
                if not hasattr(self.app.root, 'drop_target_register'):
                    logger.error("Root окно не поддерживает drop_target_register")
                    if not self._drag_drop_logged:
                        self.app.log("Ошибка: Root окно не поддерживает drag and drop")
                        self.app.log("Убедитесь, что окно создано через TkinterDnD.Tk()")
                    self._drag_drop_logged = True
                    return
                
                # Регистрируем drag and drop на root окне
                # ВАЖНО: root окно должно перехватывать все события drag and drop,
                # так как ttk виджеты (ttk.LabelFrame, ttk.Frame, ttk.Treeview) обычно не поддерживают DnD напрямую
                try:
                    # Проверяем, что DND_FILES доступен
                    if DND_FILES is None:
                        logger.error("DND_FILES не определен")
                        return
                    
                    # Убеждаемся, что окно полностью готово
                    self.app.root.update_idletasks()
                    self.app.root.update()
                    
                    # Проверяем, что root окно поддерживает drag and drop
                    if not hasattr(self.app.root, 'drop_target_register'):
                        logger.error("Root окно не поддерживает drop_target_register")
                        if not self._drag_drop_logged:
                            self.app.log("Ошибка: Root окно не поддерживает drag and drop")
                            self.app.log("Убедитесь, что окно создано через TkinterDnD.Tk()")
                        self._drag_drop_logged = True
                        return
                    
                    # Регистрируем drop target
                    # Важно: регистрация должна быть ДО привязки обработчиков
                    try:
                        # Проверяем, не зарегистрирован ли уже
                        # (tkinterdnd2 может выбросить ошибку при повторной регистрации)
                        self.app.root.drop_target_register(DND_FILES)
                    except Exception as reg_error:
                        # Если уже зарегистрирован, это нормально
                        error_str = str(reg_error).lower()
                        if "already registered" not in error_str and "уже зарегистрирован" not in error_str:
                            logger.warning(f"Ошибка при регистрации DND_FILES: {reg_error}")
                            raise
                    
                    # Привязываем обработчик события Drop
                    # ВАЖНО: Используем простой подход - вызываем метод класса напрямую
                    def on_drop(event):
                        """Обработчик drop события"""
                        try:
                            # Вызываем метод класса для обработки события
                            self._on_drop_files(event)
                            return None
                        except Exception as e:
                            logger.error(f"Ошибка в обработчике drop: {e}", exc_info=True)
                            self.app.log(f"Ошибка в обработчике drop: {e}")
                            return None
                    
                    # Привязываем обработчик ПРОСТЫМ способом
                    # ВАЖНО: Используем add='+' чтобы не перезаписывать другие обработчики
                    try:
                        self.app.root.dnd_bind('<<Drop>>', on_drop, add='+')
                    except Exception as bind_error:
                        # Если add='+' не поддерживается, пробуем без него
                        self.app.root.dnd_bind('<<Drop>>', on_drop)
                    
                    # Проверяем, что регистрация прошла успешно
                    if hasattr(self.app.root, 'dnd_bind'):
                        logger.info("Drag and drop успешно зарегистрирован на root окне")
                    else:
                        logger.warning("Метод dnd_bind недоступен после регистрации")
                except Exception as e:
                    logger.error(f"Ошибка регистрации drag and drop на root: {e}", exc_info=True)
                    if not self._drag_drop_logged:
                        self.app.log(f"Ошибка регистрации drag and drop: {e}")
                        self.app.log("Попробуйте перезапустить приложение")
                    self._drag_drop_logged = True
                    return
                logger.info(
                    "Drag and drop зарегистрирован для root окна"
                )
                logger.info(
                    "Root окно будет перехватывать все события drag and drop, "
                    "включая перетаскивание на ttk виджеты"
                )
                if not self._drag_drop_logged:
                    self.app.log("Drag and drop файлов включен - можно перетаскивать файлы из проводника")
                    self._drag_drop_logged = True
                
                # Дополнительно регистрируем drag and drop на основных tk.Frame виджетах
                # Это необходимо, так как ttk виджеты могут блокировать события
                # Регистрируем только на tk.Frame (не ttk), чтобы события доходили до обработчика
                # Делаем это с небольшой задержкой, чтобы все виджеты были созданы
                def register_on_frames():
                    try:
                        frame_count = self._register_drag_drop_on_frames(self.app.root)
                        logger.info(f"Drag and drop также зарегистрирован на {frame_count} Frame виджетах")
                    except Exception as e:
                        logger.warning(f"Не удалось зарегистрировать drag and drop на Frame виджетах: {e}")
                
                # Регистрируем на Frame виджетах с задержкой
                self.app.root.after(500, register_on_frames)
                
                # Устанавливаем флаг, что drag and drop настроен
                self._drag_drop_setup = True
                
                logger.info("Drag and drop настроен на root окне и основных Frame виджетах")
            except Exception as e:
                logger.error(f"Не удалось зарегистрировать drag and drop для root: {e}", exc_info=True)
                if not self._drag_drop_logged:
                    self.app.log(f"Ошибка регистрации drag and drop: {e}")
                    # Пробуем еще раз через некоторое время
                    self.app.root.after(1000, self.setup_drag_drop)
                    self._drag_drop_logged = True
            
            # ВАЖНО: НЕ регистрируем на дочерних виджетах (ttk виджеты не поддерживают DnD)
            # Root окно должно перехватывать все события drag and drop
            # Регистрация на ttk виджетах может создавать конфликты и блокировать события
            logger.info("Регистрация только на root окне - этого достаточно для работы drag and drop")
        except Exception as e:
            logger.error(f"Ошибка настройки drag and drop (tkinterdnd2): {e}", exc_info=True)
            error_msg = f"Ошибка настройки drag and drop (tkinterdnd2): {e}"
            if not self._drag_drop_logged:
                self.app.log(error_msg)
                self.app.log("Установите библиотеку: pip install tkinterdnd2")
                self._drag_drop_logged = True
        
        # Если ничего не сработало
        if not self._drag_drop_logged:
            self.app.log("Перетаскивание файлов из проводника недоступно")
            self.app.log("Для включения установите: pip install tkinterdnd2")
            self.app.log("Или используйте кнопки 'Добавить файлы' / 'Добавить папку'")
            self.app.log("Перестановка файлов в таблице доступна - перетащите строку мышью")
            self._drag_drop_logged = True
    
    def _on_drop_files_callback(self, files: List[str]) -> None:
        """Обработчик сброса файлов."""
        self._process_dropped_files(files)
    
    def _on_drop_files(self, event):
        """Обработка события перетаскивания файлов"""
        try:
            _on_drop_files(event, self._process_dropped_files)
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ошибка drag and drop: {error_msg}", exc_info=True)
            self.app.log(f"Ошибка при обработке перетащенных файлов: {error_msg}")
    
    def _process_dropped_files(self, files):
        """Обработка перетащенных файлов"""
        if not files:
            return
        
        self.app.log(f"Получено файлов для обработки: {len(files)}")
        
        files_before = len(self.app.files)
        skipped = 0
        added = 0
        
        for file_path in files:
            try:
                if not os.path.exists(file_path):
                    logger.debug(f"Путь не существует: {file_path}")
                    skipped += 1
                    continue
                
                if os.path.isfile(file_path):
                    # Используем add_file через file_list_manager
                    if hasattr(self.app, 'file_list_manager'):
                        result = self.app.file_list_manager.add_file(file_path)
                        if result:
                            added += 1
                            logger.debug(f"Файл добавлен: {file_path}")
                        else:
                            skipped += 1
                            logger.debug(f"Файл не добавлен (возможно, уже в списке): {file_path}")
                    else:
                        # Fallback - используем прямой метод
                        self.app.add_file(file_path)
                        added += 1
                elif os.path.isdir(file_path):
                    # Добавляем папку как отдельный элемент
                    if hasattr(self.app, 'file_list_manager'):
                        result = self.app.file_list_manager.add_folder_item(file_path)
                        if result:
                            added += 1
                            logger.debug(f"Папка добавлена: {file_path}")
                        else:
                            skipped += 1
                            logger.debug(f"Папка не добавлена (возможно, уже в списке): {file_path}")
                    else:
                        skipped += 1
                        logger.warning("file_list_manager недоступен для добавления папки")
                else:
                    skipped += 1
                    logger.debug(f"Пропущен (не файл и не папка): {file_path}")
            except Exception as e:
                logger.error(f"Ошибка при добавлении пути {file_path}: {e}", exc_info=True)
                skipped += 1
        
        logger.info(f"Добавлено элементов (файлы и папки): {added}, пропущено: {skipped}")
        self.app.log(f"Обработка завершена: добавлено {added}, пропущено {skipped}")
        
        # ВАЖНО: Обновляем интерфейс ПЕРЕД применением методов
        # Это гарантирует, что файлы будут видны в списке
        if hasattr(self.app, 'refresh_treeview'):
            logger.info("Вызов refresh_treeview для обновления интерфейса...")
            self.app.refresh_treeview()
            logger.info("refresh_treeview вызван")
            # Дополнительное обновление через небольшую задержку для надежности
            self.app.root.after(100, self.app.refresh_treeview)
        else:
            logger.warning("refresh_treeview недоступен!")
        
        # Применяем методы (включая шаблон), если они есть
        if hasattr(self.app, 'methods_manager') and self.app.methods_manager.get_methods():
            logger.info("Применяются методы переименования...")
            self.app.apply_methods()
        else:
            # Если есть шаблон в поле, но нет метода, применяем шаблон
            if hasattr(self.app, 'new_name_template'):
                template = self.app.new_name_template.get().strip()
                if template:
                    if hasattr(self.app, 'ui_templates_manager'):
                        self.app.ui_templates_manager.apply_template_quick(auto=True)
        
        # Обновляем статус
        if hasattr(self.app, 'update_status'):
            self.app.update_status()
        
        # Пути теперь вставляются прямо в refresh_treeview, дополнительное обновление не нужно
        
        # Подсчитываем реальное количество добавленных файлов
        files_after = len(self.app.files)
        actual_count = files_after - files_before
        
        if actual_count > 0:
            msg = f"Добавлено элементов перетаскиванием: {actual_count}"
            if skipped > 0:
                msg += f" (пропущено: {skipped})"
            self.app.log(msg)
            logger.info(msg)
        else:
            msg = f"Не удалось добавить файлы (возможно, все файлы уже в списке). Попытка добавления: {added}, пропущено: {skipped}"
            self.app.log(msg)
            logger.warning(msg)
    
    def setup_treeview_drag_drop(self):
        """Настройка drag and drop для перестановки файлов в таблице"""
        # Переменные для отслеживания перетаскивания
        self.app.drag_item = None
        self.app.drag_start_index = None
        self.app.drag_start_y = None
        self.app.is_dragging = False
        
        # Привязка событий для drag and drop внутри таблицы
        # Используем отдельные привязки, чтобы не конфликтовать с обычным кликом
        self.app.tree.bind('<Button-1>', self.on_treeview_button_press, add='+')
        self.app.tree.bind('<B1-Motion>', self.on_treeview_drag_motion, add='+')
        self.app.tree.bind('<ButtonRelease-1>', self.on_treeview_drag_release, add='+')
        
        # Контекстное меню для таблицы файлов
        self.app.tree.bind('<Button-3>', self.app.show_file_context_menu)
    
    def on_treeview_button_press(self, event):
        """Начало нажатия кнопки мыши (определяем начало перетаскивания)"""
        # Проверяем, что клик по строке, а не по заголовку
        item = self.app.tree.identify_row(event.y)
        region = self.app.tree.identify_region(event.x, event.y)
        
        # Игнорируем клики по заголовкам и другим областям
        if region == "heading" or region == "separator":
            return
        
        # Игнорируем строку с путем (нельзя перетаскивать)
        if item:
            tags = self.app.tree.item(item, 'tags')
            if tags and 'path_row' in tags:
                return
        
        if item:
            self.app.drag_item = item
            self.app.drag_start_index = self.app.tree.index(item)
            self.app.drag_start_y = event.y
            self.app.is_dragging = False
    
    def on_treeview_drag_motion(self, event):
        """Перемещение при перетаскивании строки"""
        if self.app.drag_item is None:
            return
        
        # Проверяем, что мышь переместилась достаточно далеко для начала перетаскивания
        if not self.app.is_dragging:
            if self.app.drag_start_y is not None and abs(event.y - self.app.drag_start_y) > 5:
                self.app.is_dragging = True
                # Выделяем исходный элемент
                self.app.tree.selection_set(self.app.drag_item)
        
        if self.app.is_dragging:
            item = self.app.tree.identify_row(event.y)
            if item and item != self.app.drag_item:
                # Визуальная индикация текущей позиции
                self.app.tree.selection_set(item)
                # Прокручиваем к элементу, если он вне видимой области
                self.app.tree.see(item)
    
    def on_treeview_drag_release(self, event):
        """Завершение перетаскивания строки"""
        if self.app.drag_item and self.app.is_dragging:
            target_item = self.app.tree.identify_row(event.y)
            
            # Игнорируем строку с путем (нельзя перемещать на неё или с неё)
            if target_item:
                tags = self.app.tree.item(target_item, 'tags')
                if tags and 'path_row' in tags:
                    # Сброс состояния
                    self.app.drag_item = None
                    self.app.drag_start_index = None
                    self.app.drag_start_y = None
                    self.app.is_dragging = False
                    return
            
            if target_item and target_item != self.app.drag_item:
                try:
                    # Получаем индексы
                    start_idx = self.app.tree.index(self.app.drag_item)
                    target_idx = self.app.tree.index(target_item)
                    
                    # Игнорируем строку с путем (она всегда на позиции 0)
                    if start_idx == 0 or target_idx == 0:
                        # Проверяем, не является ли это строкой с путем
                        if start_idx == 0:
                            start_tags = self.app.tree.item(self.app.drag_item, 'tags')
                            if start_tags and 'path_row' in start_tags:
                                return
                        if target_idx == 0:
                            target_tags = self.app.tree.item(target_item, 'tags')
                            if target_tags and 'path_row' in target_tags:
                                return
                        # Корректируем индексы, если строка с путем присутствует
                        if start_idx > 0:
                            start_idx -= 1
                        if target_idx > 0:
                            target_idx -= 1
                    
                    # Перемещаем элемент в списке и в дереве
                    # Учитываем, что строка с путем всегда на позиции 0
                    # Индексы уже скорректированы выше
                    if 0 <= start_idx < len(self.app.files) and 0 <= target_idx < len(self.app.files):
                        # Сохраняем новое имя с исходной позиции (оно должно остаться на месте)
                        preserved_new_name = self.app.files[start_idx].get('new_name', '')
                        
                        # Сохраняем новое имя целевой позиции (его получит перемещенный файл)
                        target_new_name = self.app.files[target_idx].get('new_name', '')
                        
                        # Перемещаем файл (старое имя, путь, расширение)
                        file_data = self.app.files.pop(start_idx)
                        
                        # Если перемещаем вниз, корректируем target_idx после удаления
                        if start_idx < target_idx:
                            target_idx -= 1
                        
                        # Вставляем файл на новую позицию с новым именем целевой позиции
                        file_data['new_name'] = target_new_name
                        self.app.files.insert(target_idx, file_data)
                        
                        # Новое имя исходной позиции остается на месте и привязывается к файлу,
                        # который теперь находится на этой позиции
                        if start_idx < len(self.app.files):
                            self.app.files[start_idx]['new_name'] = preserved_new_name
                        
                        # Обновляем дерево
                        self.app.refresh_treeview()
                        
                        # Выделяем перемещенный элемент (учитываем строку с путем на позиции 0)
                        children = self.app.tree.get_children()
                        # target_idx + 1, так как строка с путем на позиции 0
                        display_idx = target_idx + 1
                        if display_idx < len(children):
                            self.app.tree.selection_set(children[display_idx])
                            self.app.tree.see(children[display_idx])  # Прокручиваем к элементу
                        
                        old_name = file_data.get('old_name', 'unknown')
                        self.app.log(f"Файл '{old_name}' перемещен с позиции {start_idx + 1} на {target_idx + 1}")
                except Exception as e:
                    self.app.log(f"Ошибка при перемещении файла: {e}")
        
        # Сброс состояния
        self.app.drag_item = None
        self.app.drag_start_index = None
        self.app.drag_start_y = None
        self.app.is_dragging = False
    
    def _register_drag_drop_on_frames(self, widget, max_depth=5, current_depth=0):
        """Рекурсивная регистрация drag and drop на tk.Frame виджетах.
        
        Args:
            widget: Виджет для регистрации
            max_depth: Максимальная глубина рекурсии
            current_depth: Текущая глубина рекурсии
            
        Returns:
            int: Количество зарегистрированных Frame виджетов
        """
        if current_depth >= max_depth:
            return 0
        
        count = 0
        try:
            # Регистрируем только на tk.Frame (не ttk виджеты)
            # ttk виджеты не поддерживают drag and drop напрямую
            if isinstance(widget, tk.Frame) and hasattr(widget, 'drop_target_register'):
                try:
                    widget.drop_target_register(DND_FILES)
                    
                    def on_drop_frame(event):
                        """Обработчик drop для Frame виджетов"""
                        try:
                            # Перенаправляем событие в основной обработчик
                            self._on_drop_files(event)
                            return None
                        except Exception as e:
                            logger.error(f"Ошибка в обработчике drop для Frame: {e}", exc_info=True)
                            return None
                    
                    def on_drag_enter_frame(event):
                        """Обработчик DragEnter для Frame виджетов"""
                        return None
                    
                    widget.dnd_bind('<<Drop>>', on_drop_frame)
                    widget.dnd_bind('<<DragEnter>>', on_drag_enter_frame)
                    count += 1
                    logger.debug(f"Drag and drop зарегистрирован на Frame: {widget}")
                except Exception as e:
                    # Игнорируем ошибки регистрации (виджет может не поддерживать DnD)
                    logger.debug(f"Не удалось зарегистрировать DnD на {widget}: {e}")
            
            # Рекурсивно обрабатываем дочерние виджеты
            try:
                for child in widget.winfo_children():
                    count += self._register_drag_drop_on_frames(child, max_depth, current_depth + 1)
            except (tk.TclError, AttributeError):
                pass
        except (tk.TclError, AttributeError) as e:
            logger.debug(f"Ошибка при регистрации DnD на виджете {widget}: {e}")
        
        return count
    
    def _setup_draganddroptk(self):
        """Настройка drag and drop с использованием библиотеки DragAndDropTk"""
        if not HAS_DRAGANDDROPTK:
            return False
        
        try:
            logger.info("Настройка DragAndDropTk...")
            
            # ВАЖНО: Не создаем виджет DragAndDropTk, который покрывает все окно
            # Это блокирует интерфейс! Вместо этого используем только tkinterdnd2
            logger.warning("DragAndDropTk отключен - может блокировать интерфейс при размещении поверх всех виджетов")
            return False
            
        except Exception as e:
            logger.error(f"Ошибка настройки DragAndDropTk: {e}", exc_info=True)
            self.app.log(f"Ошибка настройки DragAndDropTk: {e}")
            return False

"""Модуль утилит для работы с окнами.

Содержит функции для:
- Загрузки иконок
- Установки иконок окон
- Привязки прокрутки мыши
- Обработки изменения размера окон
"""

import os
import sys
import tkinter as tk
from typing import Optional, Tuple

# Попытка импортировать PIL для работы с иконками
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Попытка импортировать ctypes для Windows API (для установки иконки в панели задач)
if sys.platform == 'win32':
    try:
        import ctypes
        from ctypes import wintypes
        HAS_CTYPES = True
    except ImportError:
        HAS_CTYPES = False
else:
    HAS_CTYPES = False

# Константы для прокрутки мыши
MOUSEWHEEL_DELTA_DIVISOR = 120  # Делитель для нормализации прокрутки в Windows
LINUX_SCROLL_UP = 4  # Код прокрутки вверх для Linux
LINUX_SCROLL_DOWN = 5  # Код прокрутки вниз для Linux

# Глобальный словарь для отслеживания установленных иконок (чтобы не устанавливать повторно)
_icon_set_flags = {}


def load_image_icon(
    icon_name: str,
    size: Optional[Tuple[int, int]] = None,
    icons_list: Optional[list] = None
) -> Optional[tk.PhotoImage]:
    """Загрузка иконки из папки materials/icon.
    
    Универсальная функция для загрузки изображений иконок с автоматическим
    определением формата (PNG, ICO) и опциональным изменением размера.
    
    Args:
        icon_name: Имя файла иконки (например, "Логотип.png" или "ВКонтакте.png")
        size: Кортеж (width, height) для изменения размера. Если None, размер не изменяется.
        icons_list: Список для сохранения ссылки на изображение (предотвращает удаление GC).
    
    Returns:
        PhotoImage объект или None если загрузка не удалась.
    """
    if not HAS_PIL:
        return None
    
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Пробуем разные варианты путей
        possible_paths = [
            os.path.join(base_dir, "materials", "icon", icon_name),
            os.path.join(base_dir, "materials", "icon", icon_name.replace('.png', '.ico')),
            os.path.join(base_dir, "materials", "icon", icon_name.replace('.ico', '.png')),
        ]
        
        image_path = None
        for path in possible_paths:
            if os.path.exists(path):
                image_path = path
                break
        
        if not image_path:
            return None
        
        img = Image.open(image_path)
        
        # Изменяем размер если указан
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img)
        
        # Сохраняем ссылку если передан список
        if icons_list is not None:
            icons_list.append(photo)
        
        return photo
    except (OSError, PermissionError, IOError, FileNotFoundError):
        return None
    except (ValueError, TypeError, AttributeError):
        return None
    except (MemoryError, RecursionError):
        return None
    except (MemoryError, RecursionError):
        return None
    # Финальный catch для неожиданных исключений (критично для стабильности)
    except BaseException:
        return None


def set_window_icon(window: tk.Tk, icon_photos_list: Optional[list] = None) -> None:
    """Установка иконки приложения для окна и панели задач.
    
    Пытается загрузить иконку из файлов icon.ico (приоритет), Логотип.ico или Логотип.png.
    Использует iconbitmap для Windows (лучше всего для панели задач) и
    iconphoto для кроссплатформенной поддержки.
    Также использует Windows API для более надежной установки иконки в панели задач.
    
    Args:
        window: Окно Tkinter для установки иконки
        icon_photos_list: Список для хранения ссылок на изображения (опционально).
                         Необходим для предотвращения удаления изображений сборщиком мусора.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Инициализируем флаг для отслеживания установки иконки
    window_id = id(window)
    if window_id not in _icon_set_flags:
        _icon_set_flags[window_id] = {'icon_set': False, 'api_set': False}
    
    # Проверяем, была ли иконка уже установлена для этого окна
    if _icon_set_flags[window_id].get('icon_set', False):
        # Иконка уже установлена, пропускаем (но разрешаем одну повторную попытку через API)
        if _icon_set_flags[window_id].get('api_set', False):
            return  # Полностью пропускаем
        # Разрешаем только установку через Windows API (если еще не была установлена)
        if sys.platform != 'win32' or not HAS_CTYPES:
            return
    
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Приоритет: icon.ico -> Логотип.ico -> Логотип.png
        # Сначала пробуем использовать .ico файл для Windows (лучше всего для панели задач)
        ico_path = os.path.join(base_dir, "materials", "icon", "icon.ico")
        if not os.path.exists(ico_path):
            ico_path = os.path.join(base_dir, "materials", "icon", "Логотип.ico")
        ico_path = os.path.normpath(ico_path)
        
        if os.path.exists(ico_path):
            try:
                # Преобразуем в абсолютный путь для надежности
                ico_path = os.path.abspath(ico_path)
                
                # iconbitmap устанавливает иконку для окна и панели задач в Windows
                # Это самый надежный способ для панели задач
                if not _icon_set_flags[window_id]['icon_set']:
                    try:
                        window.iconbitmap(ico_path)
                        _icon_set_flags[window_id]['icon_set'] = True
                        logger.info(f"Иконка установлена через iconbitmap: {ico_path}")
                    except (tk.TclError, OSError, PermissionError) as iconbitmap_error:
                        logger.debug(f"iconbitmap не сработал: {iconbitmap_error}, пробуем через PIL")
                        # Если iconbitmap не работает, пробуем через PIL
                        if HAS_PIL:
                            try:
                                img = Image.open(ico_path)
                                photo = ImageTk.PhotoImage(img)
                                window.iconphoto(True, photo)
                                if icon_photos_list is not None:
                                    icon_photos_list.append(photo)
                                _icon_set_flags[window_id]['icon_set'] = True
                                logger.info(f"Иконка установлена через PIL из ICO: {ico_path}")
                            except (OSError, IOError, ValueError, TypeError, AttributeError):
                                pass
                            except (MemoryError, RecursionError):
                                pass
                            except (MemoryError, RecursionError):
                                pass
                            # Финальный catch для неожиданных исключений (критично для стабильности)
                            except BaseException:
                                pass
                    except (ValueError, KeyError, IndexError) as iconbitmap_error:
                        logger.debug(f"Ошибка данных при iconbitmap: {iconbitmap_error}, пробуем через PIL")
                    except (MemoryError, RecursionError) as iconbitmap_error:

                        # Ошибки памяти/рекурсии

                        pass

                    # Финальный catch для неожиданных исключений (критично для стабильности)

                    except BaseException as iconbitmap_error:

                        if isinstance(iconbitmap_error, (KeyboardInterrupt, SystemExit)):

                            raise
                        logger.debug(f"Неожиданная ошибка iconbitmap: {iconbitmap_error}, пробуем через PIL")
                        # Если iconbitmap не работает, пробуем через PIL
                        if HAS_PIL:
                            try:
                                img = Image.open(ico_path)
                                photo = ImageTk.PhotoImage(img)
                                window.iconphoto(True, photo)
                                if icon_photos_list is not None:
                                    icon_photos_list.append(photo)
                                _icon_set_flags[window_id]['icon_set'] = True
                                logger.info(f"Иконка установлена через PIL из ICO: {ico_path}")
                            except (OSError, IOError, ValueError, TypeError, AttributeError):
                                pass
                            except (MemoryError, RecursionError):
                                pass
                            except (MemoryError, RecursionError):
                                pass
                            # Финальный catch для неожиданных исключений (критично для стабильности)
                            except BaseException:
                                pass
                
                # Используем Windows API для установки иконки в панели задач и процесса
                # Это критически важно для отображения иконки в панели задач и диспетчере задач Windows
                if sys.platform == 'win32' and HAS_CTYPES and not _icon_set_flags[window_id]['api_set']:
                    def set_taskbar_icon():
                        """Установка иконки в панели задач и процесса через Windows API"""
                        # Проверяем, не была ли уже установлена иконка через API
                        if _icon_set_flags.get(window_id, {}).get('api_set', False):
                            return
                        try:
                            # Ждем полной инициализации окна
                            window.update_idletasks()
                            window.update()
                            
                            # Получаем HWND окна - правильный способ для Tkinter
                            hwnd = None
                            try:
                                # Метод 1: В Tkinter winfo_id() возвращает HWND напрямую для Windows
                                widget_id = window.winfo_id()
                                
                                # Проверяем, что это валидный HWND (должен быть > 0)
                                if widget_id and widget_id > 0:
                                    # В Tkinter для Windows winfo_id() может вернуть HWND окна или виджета
                                    # Проверяем, является ли это окном верхнего уровня
                                    window_style = ctypes.windll.user32.GetWindowLongW(widget_id, -16)  # GWL_STYLE
                                    # WS_OVERLAPPEDWINDOW = 0x00CF0000, проверяем что это окно
                                    if window_style & 0x80000000:  # WS_POPUP или WS_OVERLAPPED
                                        hwnd = widget_id
                                    else:
                                        # Если это виджет, получаем родительское окно
                                        parent_hwnd = ctypes.windll.user32.GetParent(widget_id)
                                        if parent_hwnd and parent_hwnd != 0:
                                            hwnd = parent_hwnd
                                        else:
                                            # Пробуем получить окно через GetAncestor
                                            hwnd = ctypes.windll.user32.GetAncestor(widget_id, 2)  # GA_ROOT
                                
                                # Метод 2: Если не получили, пробуем найти окно по заголовку
                                if not hwnd or hwnd == 0:
                                    window_title = window.title()
                                    if window_title:
                                        hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
                                        # Проверяем, что это действительно наше окно
                                        if hwnd:
                                            buffer = ctypes.create_unicode_buffer(256)
                                            ctypes.windll.user32.GetWindowTextW(hwnd, buffer, 256)
                                            if buffer.value != window_title:
                                                hwnd = 0
                                
                                # Метод 3: Пробуем через GetForegroundWindow (если окно активно)
                                if not hwnd or hwnd == 0:
                                    fg_hwnd = ctypes.windll.user32.GetForegroundWindow()
                                    if fg_hwnd and fg_hwnd != 0:
                                        # Проверяем, что это наше окно по заголовку
                                        window_title = window.title()
                                        if window_title:
                                            buffer = ctypes.create_unicode_buffer(256)
                                            ctypes.windll.user32.GetWindowTextW(fg_hwnd, buffer, 256)
                                            if buffer.value == window_title:
                                                hwnd = fg_hwnd
                                
                                # Метод 4: Последняя попытка - через класс окна Tkinter
                                if not hwnd or hwnd == 0:
                                    # Ищем окно по классу TkTopLevel (класс окон Tkinter)
                                    hwnd = ctypes.windll.user32.FindWindowW("TkTopLevel", None)
                                    
                            except (OSError, AttributeError, ctypes.ArgumentError) as hwnd_error:
                                logger.debug(f"Ошибка получения HWND: {hwnd_error}")
                                hwnd = None
                            except (ValueError, TypeError, KeyError) as hwnd_error:
                                logger.debug(f"Ошибка данных при получении HWND: {hwnd_error}")
                                hwnd = None
                            except (MemoryError, RecursionError) as hwnd_error:

                                # Ошибки памяти/рекурсии

                                pass

                            # Финальный catch для неожиданных исключений (критично для стабильности)

                            except BaseException as hwnd_error:

                                if isinstance(hwnd_error, (KeyboardInterrupt, SystemExit)):

                                    raise
                                logger.debug(f"Неожиданная ошибка получения HWND: {hwnd_error}")
                                hwnd = None
                            
                            if hwnd and hwnd != 0:
                                # Загружаем иконку через LoadImage для меню Пуск и панели задач
                                # IMAGE_ICON = 1, LR_LOADFROMFILE = 0x0010
                                ico_path_unicode = str(ico_path)
                                
                                # Константы для LoadImage
                                IMAGE_ICON = 1
                                LR_LOADFROMFILE = 0x0010
                                LR_DEFAULTSIZE = 0x0040
                                
                                # Загружаем иконки разных размеров для процесса
                                # Для меню Пуск нужны размеры: 16x16, 32x32, 48x48
                                hicon_16 = ctypes.windll.user32.LoadImageW(
                                    None,  # hInst = None для загрузки из файла
                                    ico_path_unicode,
                                    IMAGE_ICON,
                                    16, 16,
                                    LR_LOADFROMFILE
                                )
                                hicon_32 = ctypes.windll.user32.LoadImageW(
                                    None,
                                    ico_path_unicode,
                                    IMAGE_ICON,
                                    32, 32,
                                    LR_LOADFROMFILE
                                )
                                hicon_48 = ctypes.windll.user32.LoadImageW(
                                    None,
                                    ico_path_unicode,
                                    IMAGE_ICON,
                                    48, 48,
                                    LR_LOADFROMFILE
                                )
                                
                                # Если не удалось загрузить с конкретными размерами, пробуем без указания размеров
                                # (Windows выберет подходящий размер из файла)
                                if not hicon_16:
                                    hicon_16 = ctypes.windll.user32.LoadImageW(
                                        None, ico_path_unicode, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
                                    )
                                if not hicon_32:
                                    hicon_32 = ctypes.windll.user32.LoadImageW(
                                        None, ico_path_unicode, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
                                    )
                                if not hicon_48:
                                    hicon_48 = ctypes.windll.user32.LoadImageW(
                                        None, ico_path_unicode, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
                                    )
                                
                                # Используем 16x16 как маленькую иконку, 32x32 как большую
                                hicon_small = hicon_16 if hicon_16 else hicon_32
                                hicon_big = hicon_32 if hicon_32 else hicon_48
                                
                                if hicon_small or hicon_big:
                                    # Устанавливаем иконку для окна (WM_SETICON)
                                    # WM_SETICON = 0x0080, ICON_SMALL = 0, ICON_BIG = 1
                                    icon_set_success = False
                                    if hicon_small:
                                        ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon_small)  # ICON_SMALL
                                        icon_set_success = True
                                    if hicon_big:
                                        ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon_big)  # ICON_BIG
                                        icon_set_success = True
                                    
                                    # КРИТИЧНО: Устанавливаем иконку класса окна для процесса
                                    # Это влияет на отображение иконки в диспетчере задач, панели задач и меню Пуск
                                    try:
                                        # GCL_HICONSM = -34 (маленькая иконка класса, 16x16)
                                        # GCL_HICON = -14 (большая иконка класса, 32x32)
                                        # SetClassLongPtrW устанавливает иконку для всего класса окон
                                        
                                        # Определяем правильную функцию для установки иконки класса
                                        if sys.maxsize > 2**32:  # 64-bit
                                            SetClassLongPtr = ctypes.windll.user32.SetClassLongPtrW
                                        else:  # 32-bit
                                            SetClassLongPtr = ctypes.windll.user32.SetClassLongW
                                        
                                        # Устанавливаем маленькую иконку класса (для меню Пуск и панели задач)
                                        if hicon_small:
                                            old_small = SetClassLongPtr(hwnd, -34, hicon_small)  # GCL_HICONSM
                                            if old_small:
                                                # Освобождаем старую иконку, если она была
                                                try:
                                                    ctypes.windll.user32.DestroyIcon(old_small)
                                                except (OSError, AttributeError, ctypes.ArgumentError):
                                                    pass
                                        
                                        # Устанавливаем большую иконку класса (для панели задач)
                                        if hicon_big:
                                            old_big = SetClassLongPtr(hwnd, -14, hicon_big)  # GCL_HICON
                                            if old_big:
                                                # Освобождаем старую иконку, если она была
                                                try:
                                                    ctypes.windll.user32.DestroyIcon(old_big)
                                                except (OSError, AttributeError, ctypes.ArgumentError):
                                                    pass
                                        
                                        # Также устанавливаем иконку 48x48 для меню Пуск (если доступна)
                                        if hicon_48:
                                            # Пробуем установить через SendMessage для больших иконок
                                            try:
                                                # WM_SETICON с ICON_BIG = 1 для больших иконок
                                                ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon_48)
                                            except (OSError, AttributeError, ctypes.ArgumentError):
                                                pass
                                        
                                        # Устанавливаем флаг, что иконка установлена через API
                                        _icon_set_flags[window_id]['api_set'] = True
                                        if icon_set_success:
                                            logger.info(f"Иконка установлена для окна, процесса и меню Пуск: {ico_path}")
                                    except (OSError, AttributeError, ctypes.ArgumentError) as class_error:
                                        logger.debug(f"Ошибка доступа при установке иконки класса: {class_error}")
                                    except (ValueError, TypeError, KeyError) as class_error:
                                        logger.debug(f"Ошибка данных при установке иконки класса: {class_error}")
                                    except (MemoryError, RecursionError) as class_error:

                                        # Ошибки памяти/рекурсии

                                        pass

                                    # Финальный catch для неожиданных исключений (критично для стабильности)

                                    except BaseException as class_error:

                                        if isinstance(class_error, (KeyboardInterrupt, SystemExit)):

                                            raise
                                        logger.debug(f"Неожиданная ошибка установки иконки класса: {class_error}")
                                    
                                    # Принудительно обновляем окно
                                    ctypes.windll.user32.InvalidateRect(hwnd, None, True)
                                    ctypes.windll.user32.UpdateWindow(hwnd)
                                    
                                    # УБРАНО: Вызовы SHChangeNotify вызывают обновление всего проводника Windows,
                                    # включая рабочий стол, что нежелательно при запуске приложения.
                                    # Иконка окна и так обновится автоматически через UpdateWindow.
                                    # Если нужно обновить только панель задач, можно использовать более специфичные флаги,
                                    # но это обычно не требуется при установке иконки окна.
                                    
                                    # Дополнительно: принудительно обновляем иконку процесса
                                    # Это важно для меню Пуск в Windows 10/11
                                    try:
                                        # Получаем PID процесса
                                        process_id = ctypes.c_ulong()
                                        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
                                        
                                        # Обновляем иконку процесса через shell32
                                        # Это помогает Windows правильно отобразить иконку в меню Пуск
                                        if process_id.value:
                                            # Используем SHGetFileInfo для получения информации об иконке
                                            # Это обновит кэш иконок Windows
                                            try:
                                                SHGFI_ICON = 0x000000100
                                                SHGFI_LARGEICON = 0x000000000
                                                file_info = ctypes.create_string_buffer(ctypes.sizeof(ctypes.c_void_p) * 2 + 260)
                                                ctypes.windll.shell32.SHGetFileInfoW(
                                                    ico_path_unicode,
                                                    0,
                                                    file_info,
                                                    ctypes.sizeof(file_info),
                                                    SHGFI_ICON | SHGFI_LARGEICON
                                                )
                                            except (OSError, AttributeError, ctypes.ArgumentError):
                                                pass
                                    except (OSError, AttributeError, ctypes.ArgumentError):
                                        pass
                        except (OSError, AttributeError, ctypes.ArgumentError, RuntimeError) as api_error:
                            logger.debug(f"Ошибка выполнения при установке иконки через Windows API: {api_error}")
                        except (ValueError, TypeError, KeyError) as api_error:
                            logger.debug(f"Ошибка данных при установке иконки через Windows API: {api_error}")
                        except (MemoryError, RecursionError) as api_error:

                            # Ошибки памяти/рекурсии

                            pass

                        # Финальный catch для неожиданных исключений (критично для стабильности)

                        except BaseException as api_error:

                            if isinstance(api_error, (KeyboardInterrupt, SystemExit)):

                                raise
                            logger.debug(f"Неожиданная ошибка установки иконки через Windows API: {api_error}")
                    
                    # Устанавливаем иконку сразу и с одной задержкой для надежности
                    set_taskbar_icon()
                    window.after(500, set_taskbar_icon)  # Одна повторная попытка через 500мс
                
                # Принудительно обновляем окно для применения иконки
                window.update_idletasks()
                window.update()
                return
            except (OSError, PermissionError, tk.TclError) as e:
                logger.debug(f"Ошибка доступа при установке иконки через iconbitmap: {e}")
            except (ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Ошибка данных при установке иконки через iconbitmap: {e}")
            except (MemoryError, RecursionError) as e:

                # Ошибки памяти/рекурсии

                pass

            # Финальный catch для неожиданных исключений (критично для стабильности)

            except BaseException as e:

                if isinstance(e, (KeyboardInterrupt, SystemExit)):

                    raise
                logger.debug(f"Неожиданная ошибка при установке иконки через iconbitmap: {e}")
        
        # Если .ico не найден или не сработал, используем PNG иконку (если еще не использовали)
        png_path = os.path.join(base_dir, "materials", "icon", "Логотип.png")
        png_path = os.path.normpath(png_path)
        
        if os.path.exists(png_path):
            if HAS_PIL:
                try:
                    png_path = os.path.abspath(png_path)
                    img = Image.open(png_path)
                    # Для панели задач лучше использовать иконку по умолчанию (True)
                    photo = ImageTk.PhotoImage(img)
                    window.iconphoto(True, photo)  # True = установить как иконку по умолчанию для всех окон
                    if icon_photos_list is not None:
                        icon_photos_list.append(photo)
                    # Принудительно обновляем окно для применения иконки
                    window.update_idletasks()
                    window.update()
                    logger.info(f"Иконка установлена через PNG (fallback): {png_path}")
                except (OSError, IOError, PermissionError) as e:
                    logger.debug(f"Ошибка доступа при установке PNG иконки через PIL: {e}")
                except (ValueError, TypeError, AttributeError) as e:
                    logger.debug(f"Ошибка данных при установке PNG иконки через PIL: {e}")
                except (MemoryError, RecursionError) as e:
                    logger.debug(f"Ошибка памяти/рекурсии при установке PNG иконки через PIL: {e}")
                except (MemoryError, RecursionError) as e:

                    # Ошибки памяти/рекурсии

                    pass

                # Финальный catch для неожиданных исключений (критично для стабильности)

                except BaseException as e:

                    if isinstance(e, (KeyboardInterrupt, SystemExit)):

                        raise
                    logger.debug(f"Неожиданная ошибка при установке PNG иконки через PIL: {e}")
            else:
                    try:
                        png_path = os.path.abspath(png_path)
                        photo = tk.PhotoImage(file=png_path)
                        window.iconphoto(True, photo)  # True = установить как иконку по умолчанию
                        if icon_photos_list is not None:
                            icon_photos_list.append(photo)
                        # Принудительно обновляем окно для применения иконки
                        window.update_idletasks()
                        window.update()
                    except (OSError, PermissionError, tk.TclError) as e:
                        logger.debug(f"Ошибка доступа при установке PNG иконки: {e}")
                    except (ValueError, TypeError, AttributeError) as e:
                        logger.debug(f"Ошибка данных при установке PNG иконки: {e}")
                    except (MemoryError, RecursionError) as e:
                        logger.debug(f"Ошибка памяти/рекурсии при установке PNG иконки: {e}")
                    except (MemoryError, RecursionError) as e:

                        # Ошибки памяти/рекурсии

                        pass

                    # Финальный catch для неожиданных исключений (критично для стабильности)

                    except BaseException as e:

                        if isinstance(e, (KeyboardInterrupt, SystemExit)):

                            raise
                        logger.debug(f"Неожиданная ошибка при установке PNG иконки: {e}")
    except (OSError, PermissionError, IOError) as e:
        logger.debug(f"Ошибка доступа при установке иконки: {e}")
    except (ValueError, TypeError, AttributeError) as e:
        logger.debug(f"Ошибка данных при установке иконки: {e}")
    except (MemoryError, RecursionError) as e:
        logger.debug(f"Ошибка памяти/рекурсии при установке иконки: {e}")
    except (MemoryError, RecursionError) as e:

        # Ошибки памяти/рекурсии

        pass

    # Финальный catch для неожиданных исключений (критично для стабильности)

    except BaseException as e:

        if isinstance(e, (KeyboardInterrupt, SystemExit)):

            raise
        logger.debug(f"Неожиданная ошибка при установке иконки: {e}")


def bind_mousewheel(widget: tk.Widget, canvas: Optional[tk.Canvas] = None) -> None:
    """Привязка прокрутки колесом мыши к виджету.
    
    Args:
        widget: Виджет для привязки прокрутки
        canvas: Опциональный Canvas для прокрутки
    """
    def on_mousewheel(event):
        """Обработчик прокрутки для Windows и macOS."""
        scroll_amount = int(-1 * (event.delta / MOUSEWHEEL_DELTA_DIVISOR))
        target = canvas if canvas else widget
        if hasattr(target, 'yview_scroll'):
            target.yview_scroll(scroll_amount, "units")
    
    def on_mousewheel_linux(event):
        """Обработчик прокрутки для Linux."""
        target = canvas if canvas else widget
        if hasattr(target, 'yview_scroll'):
            if event.num == LINUX_SCROLL_UP:
                target.yview_scroll(-1, "units")
            elif event.num == LINUX_SCROLL_DOWN:
                target.yview_scroll(1, "units")
    
    # Windows и macOS
    widget.bind("<MouseWheel>", on_mousewheel)
    # Linux
    widget.bind("<Button-4>", on_mousewheel_linux)
    widget.bind("<Button-5>", on_mousewheel_linux)
    
    # Привязка к дочерним виджетам
    def bind_to_children(parent):
        """Рекурсивная привязка прокрутки к дочерним виджетам."""
        for child in parent.winfo_children():
            try:
                child.bind("<MouseWheel>", on_mousewheel)
                child.bind("<Button-4>", on_mousewheel_linux)
                child.bind("<Button-5>", on_mousewheel_linux)
                bind_to_children(child)
            except (AttributeError, tk.TclError):
                pass
    
    bind_to_children(widget)


def setup_window_resize_handler(window: tk.Toplevel, canvas: Optional[tk.Canvas] = None, 
                                canvas_window: Optional[int] = None) -> None:
    """Настройка обработчика изменения размера для окна с canvas.
    
    Args:
        window: Окно для обработки изменения размера
        canvas: Canvas виджет (опционально)
        canvas_window: ID окна canvas (опционально)
    """
    def on_resize(event):
        if canvas and canvas_window is not None:
            try:
                canvas_width = window.winfo_width() - 20
                canvas.itemconfig(canvas_window, width=max(canvas_width, 100))
            except (AttributeError, tk.TclError):
                pass
    
    window.bind('<Configure>', on_resize)


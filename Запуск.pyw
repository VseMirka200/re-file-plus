"""Файл запуска приложения "Ре-Файл+".

Этот файл предназначен для запуска приложения по двойному клику.
Использует расширение .pyw для запуска без отображения консольного окна.

Основные функции:
- Настройка логирования
- Установка кодировки UTF-8 для Windows
- Импорт и запуск основного модуля приложения
- Обработка критических ошибок с показом диалогового окна
"""

import logging
import os
import sys

# Проверка версии Python
if sys.version_info < (3, 7):
    print("Ошибка: Требуется Python 3.7 или выше")
    print(f"Текущая версия: {sys.version}")
    sys.exit(1)

# Настройка логирования
# Логируем все действия (INFO и выше)
log_level = logging.INFO

# Получаем путь к файлу лога из констант
# Важно: используем абсолютный путь к файлу скрипта, чтобы работать корректно
# при запуске через ярлык (когда рабочая директория может быть другой)
log_file_path = None
logs_dir = None

# Определяем абсолютный путь к директории скрипта независимо от рабочей директории
script_file = os.path.abspath(__file__)
script_dir = os.path.dirname(script_file)

try:
    from config.constants import get_log_file_path, get_logs_dir
    logs_dir = get_logs_dir()
    log_file_path = get_log_file_path()
    # Проверяем, что путь определен корректно
    if not logs_dir or not log_file_path:
        raise ValueError("Путь к директории логов не определен")
except (ImportError, ValueError, Exception) as e:
    # Если не удалось импортировать или получить путь, используем директорию скрипта
    app_data_dir = script_dir
    logs_dir = os.path.join(app_data_dir, "logs")
    log_file_path = os.path.join(logs_dir, "re-file-plus.log")
    # Выводим информацию для отладки (только если есть проблемы)
    if isinstance(e, ImportError):
        print(f"Информация: Не удалось импортировать config.constants, используется директория скрипта: {app_data_dir}")

# Убеждаемся, что директория логов существует
if logs_dir:
    # Нормализуем путь (убираем двойные слеши и т.д.)
    logs_dir = os.path.normpath(logs_dir)
    log_file_path = os.path.normpath(log_file_path) if log_file_path else None
    
    if not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir, exist_ok=True)
            # Проверяем, что директория действительно создана
            if not os.path.exists(logs_dir):
                raise OSError(f"Директория {logs_dir} не была создана")
        except (OSError, PermissionError) as e:
            # Если не удалось создать директорию, выводим ошибку в консоль
            print(f"Ошибка: Не удалось создать директорию логов {logs_dir}: {e}")
            print(f"Текущая рабочая директория: {os.getcwd()}")
            print(f"Директория скрипта: {script_dir}")
            logs_dir = None
            log_file_path = None
else:
    print(f"Ошибка: Путь к директории логов не определен")
    print(f"Текущая рабочая директория: {os.getcwd()}")
    print(f"Директория скрипта: {script_dir}")

# Проверяем, что можем создать файл лога
if log_file_path:
    # Проверяем, что директория существует перед созданием файла
    log_dir = os.path.dirname(log_file_path)
    if not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir, exist_ok=True)
        except (OSError, PermissionError) as e:
            print(f"Ошибка: Не удалось создать директорию для логов {log_dir}: {e}")
            log_file_path = None
    
    # Проверяем права на запись в директорию
    if log_file_path and os.path.exists(log_dir):
        try:
            # Пробуем создать тестовый файл для проверки прав
            test_file = os.path.join(log_dir, ".test_write")
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write('test')
            os.remove(test_file)
        except (OSError, PermissionError) as e:
            print(f"Ошибка: Нет прав на запись в директорию логов {log_dir}: {e}")
            log_file_path = None

# Импортируем структурированный форматтер
try:
    from utils.logging_utils import StructuredFormatter
except ImportError:
    # Fallback форматтер, если модуль недоступен
    class StructuredFormatter(logging.Formatter):
        def format(self, record):
            action = getattr(record, 'action', 'UNKNOWN')
            return f"[{self.formatTime(record, '%Y-%m-%d %H:%M:%S')}] [{record.levelname:8s}] [{record.name:25s}] [ACTION: {action:25s}] | {record.getMessage()}"

# Настройка логирования со структурированным форматтером
handlers = []

# Добавляем файловый обработчик только если путь к файлу лога доступен
if log_file_path:
    try:
        # Используем кастомный обработчик с ограничением количества записей (100 последних)
        try:
            from utils.logging_utils import RotatingLogHandler
            file_handler = RotatingLogHandler(log_file_path, max_lines=100, encoding='utf-8', mode='a')
        except ImportError:
            # Fallback на стандартный FileHandler, если кастомный недоступен
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8', mode='a')
        file_handler.setFormatter(StructuredFormatter())
        handlers.append(file_handler)
        # Проверяем, что файл действительно создан или существует
        if not os.path.exists(log_file_path):
            # Пробуем создать файл напрямую для проверки
            try:
                with open(log_file_path, 'a', encoding='utf-8') as f:
                    f.write('')
            except (OSError, PermissionError, IOError) as test_e:
                print(f"Предупреждение: Файл лога {log_file_path} не может быть создан: {test_e}")
    except (OSError, PermissionError, IOError) as e:
        print(f"Ошибка: Не удалось создать файловый обработчик логов {log_file_path}: {e}")
        print("Логирование будет производиться только в консоль")

# Консольный обработчик всегда добавляем
console_handler = logging.StreamHandler()
console_handler.setFormatter(StructuredFormatter())
handlers.append(console_handler)

logging.basicConfig(
    level=log_level,
    handlers=handlers
)
logger = logging.getLogger(__name__)

# Упрощенное логирование: логируем только ошибки при настройке
if log_file_path:
    try:
        # Принудительно сбрасываем буферы всех обработчиков
        for handler in handlers:
            if hasattr(handler, 'flush'):
                handler.flush()
        
        # Проверяем, что файл существует
        if os.path.exists(log_file_path):
            logger.debug(f"Файл лога успешно создан: {log_file_path}")
            # Проверяем, что можем записать в файл
            try:
                with open(log_file_path, 'a', encoding='utf-8') as test_f:
                    test_f.write('')
            except (OSError, PermissionError) as write_test:
                logger.warning(f"Не удалось записать в файл лога: {write_test}")
        else:
            error_msg = (
                f"Предупреждение: Файл лога {log_file_path} не был создан после настройки логирования\n"
                f"Рабочая директория: {os.getcwd()}\n"
                f"Директория скрипта: {script_dir}\n"
                f"Директория логов: {logs_dir}\n"
                f"Проверьте права доступа к директории: {os.path.dirname(log_file_path)}"
            )
            print(error_msg)
            logger.warning("Логирование в файл недоступно. Логи выводятся только в консоль.")
    except (OSError, PermissionError, IOError) as log_e:
        print(f"Ошибка доступа при проверке файла лога: {log_e}")
        import traceback
        print(traceback.format_exc())
    except (ValueError, TypeError, AttributeError) as log_e:
        print(f"Ошибка данных при проверке файла лога: {log_e}")
        import traceback
        print(traceback.format_exc())
    except (MemoryError, RecursionError) as log_e:
        # Ошибки памяти/рекурсии
        print(f"Ошибка памяти/рекурсии при проверке файла лога: {log_e}")
        import traceback
        print(traceback.format_exc())
    except BaseException as log_e:
        if isinstance(log_e, (KeyboardInterrupt, SystemExit)):
            raise
        print(f"Неожиданная ошибка при проверке файла лога: {log_e}")
        import traceback
        print(traceback.format_exc())
else:
    logger.warning("Логирование в файл недоступно. Логи выводятся только в консоль.")
    print(f"Информация для отладки:")
    print(f"  Рабочая директория: {os.getcwd()}")
    print(f"  Директория скрипта: {script_dir}")
    print(f"  Директория логов: {logs_dir}")

# Установка кодировки UTF-8 для корректного отображения русских символов
# В Python 3 кодировка по умолчанию уже UTF-8, поэтому setdefaultencoding не нужен
# Если нужна настройка для вывода в консоль Windows:
if sys.platform == 'win32':
    try:
        # Настройка кодировки для stdout/stderr в Windows
        # Проверяем, что stdout/stderr имеют атрибут encoding
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
            import io
            try:
                # Пробуем установить кодировку только если это возможно
                if hasattr(sys.stdout, 'buffer'):
                    sys.stdout = io.TextIOWrapper(
                        sys.stdout.buffer, encoding='utf-8', errors='replace'
                    )
                if hasattr(sys.stderr, 'buffer'):
                    sys.stderr = io.TextIOWrapper(
                        sys.stderr.buffer, encoding='utf-8', errors='replace'
                    )
                logger.debug("Кодировка UTF-8 успешно установлена для stdout/stderr")
            except (OSError, AttributeError, ValueError, RuntimeError) as e:
                logger.debug(f"Не удалось установить кодировку UTF-8: {e}")
                # Продолжаем работу без изменения кодировки
        else:
            logger.debug(f"Кодировка stdout уже установлена: {sys.stdout.encoding if hasattr(sys.stdout, 'encoding') else 'N/A'}")
    except (AttributeError, RuntimeError) as e:
        logger.debug(f"Ошибка при проверке кодировки: {e}")

# Переход в директорию скрипта
# script_dir уже определен выше, используем его
os.chdir(script_dir)

# Проверка прав администратора отключена для работы drag and drop
# Программа теперь работает без прав администратора

# Импорт и запуск основного приложения
try:
    # Фильтруем аргументы командной строки ПЕРЕД любыми импортами
    # Удаляем аргументы, которые выглядят как опции, но не являются файлами
    # ВАЖНО: Эта фильтрация должна происходить ДО любого импорта, который может использовать argparse
    
    # Логирование для отладки - ВСЕГДА логируем, даже если аргументов нет
    try:
        debug_msg = f"Запуск программы. Исходные аргументы (всего {len(sys.argv)}): {sys.argv}"
        logger.info(debug_msg)
        if len(sys.argv) > 1:
            logger.info(f"Аргументы для обработки: {sys.argv[1:]}")
        else:
            logger.info("Аргументы командной строки отсутствуют")
    except (OSError, AttributeError) as e:
        logger.error(f"Ошибка при логировании аргументов: {e}")
    
    filtered_args = [sys.argv[0]]  # Сохраняем имя скрипта
    
    # Используем общую функцию для обработки аргументов
    try:
        from utils.path_processing import filter_cli_args
        file_paths = filter_cli_args(sys.argv[1:])
        filtered_args.extend(file_paths)
    except ImportError:
        # Fallback на старую логику, если модуль недоступен
        logger.warning("Модуль utils.path_processing недоступен, используется fallback логика")
        for arg in sys.argv[1:]:
            # Пропускаем пустые аргументы
            if not arg or not arg.strip():
                continue
            
            # Обработка URL-формата (file://) - используется LibreOffice и другими приложениями
            if arg.startswith('file://'):
                try:
                    # Удаляем префикс file:// и декодируем URL
                    import urllib.parse
                    file_path = urllib.parse.unquote(arg[7:])  # Убираем file://
                    # Убираем начальный слеш для Windows путей (file:///C:/...)
                    if sys.platform == 'win32' and file_path.startswith('/') and len(file_path) > 2:
                        if file_path[1].isalpha() and file_path[2] == ':':
                            file_path = file_path[1:]  # Убираем лишний слеш
                    normalized_path = os.path.normpath(file_path)
                    if os.path.exists(normalized_path) and os.path.isfile(normalized_path):
                        filtered_args.append(normalized_path)
                        logger.info(f"Обработан URL-путь: {arg} -> {normalized_path}")
                        continue
                except (ValueError, AttributeError, TypeError) as e:
                    logger.debug(f"Ошибка типа/значения при обработке URL-пути {arg}: {e}")
                except (KeyError, IndexError) as e:
                    logger.debug(f"Ошибка доступа к данным при обработке URL-пути {arg}: {e}")
                except (MemoryError, RecursionError) as e:
                    # Ошибки памяти/рекурсии
                    logger.debug(f"Ошибка памяти/рекурсии при обработке URL-пути {arg}: {e}")
                except BaseException as e:
                    if isinstance(e, (KeyboardInterrupt, SystemExit)):
                        raise
                    logger.debug(f"Неожиданная ошибка обработки URL-пути {arg}: {e}")
            
            # Обработка путей в кавычках (для путей с пробелами)
            cleaned_arg = arg.strip('"').strip("'")
            
            # Пропускаем аргументы, которые выглядят как опции (начинаются с -)
            # но проверяем, не является ли это путем к файлу
            if arg.startswith('-'):
                # Проверяем, существует ли это как файл
                # Сначала пробуем как есть
                normalized_arg = os.path.normpath(arg)
                
                # Проверяем как абсолютный путь
                file_exists = False
                if os.path.exists(normalized_arg) and os.path.isfile(normalized_arg):
                    file_exists = True
                else:
                    # Проверяем как относительный путь от текущей директории
                    try:
                        abs_path = os.path.abspath(normalized_arg)
                        if os.path.exists(abs_path) and os.path.isfile(abs_path):
                            file_exists = True
                    except (OSError, ValueError):
                        pass
                
                # Если это файл, добавляем его
                if file_exists:
                    filtered_args.append(arg)
                # Иначе пропускаем (это опция, которую мы не знаем, например -state)
            else:
                # Обычный аргумент (не начинается с -), добавляем
                # Проверяем, что это действительно файл (для безопасности)
                normalized_arg = os.path.normpath(cleaned_arg)
                if os.path.exists(normalized_arg) and os.path.isfile(normalized_arg):
                    filtered_args.append(normalized_arg)
                else:
                    # Пробуем как абсолютный путь
                    try:
                        abs_path = os.path.abspath(normalized_arg)
                        if os.path.exists(abs_path) and os.path.isfile(abs_path):
                            filtered_args.append(abs_path)
                        else:
                            # Если не файл, все равно добавляем (может быть относительный путь)
                            filtered_args.append(arg)
                    except (OSError, ValueError):
                        # В случае ошибки добавляем как есть
                        filtered_args.append(arg)
    
    # Заменяем sys.argv на отфильтрованные аргументы ДО импорта
    # Это критически важно - если импорт использует argparse, он не увидит неизвестные опции
    sys.argv = filtered_args
    
    # Упрощенное логирование: убрано
    
    # Импортируем главную функцию из единой точки входа
    try:
        from app.entry_point import main
    except (ImportError, ModuleNotFoundError) as import_error:
        logger.error(f"Ошибка импорта app.entry_point: {import_error}", exc_info=True)
        raise
    except (SyntaxError, AttributeError) as import_error:
        logger.error(f"Ошибка синтаксиса/атрибутов при импорте app.entry_point: {import_error}", exc_info=True)
        raise
    except (ValueError, TypeError, KeyError, IndexError) as import_error:
        logger.error(f"Ошибка данных при импорте app.entry_point: {import_error}", exc_info=True)
        raise
    except (MemoryError, RecursionError) as import_error:
        # Ошибки памяти/рекурсии
        logger.error(f"Ошибка памяти/рекурсии при импорте app.entry_point: {import_error}", exc_info=True)
        raise
    except BaseException as import_error:
        if isinstance(import_error, (KeyboardInterrupt, SystemExit)):
            raise
        logger.error(f"Неожиданная ошибка при импорте app.entry_point: {import_error}", exc_info=True)
        raise
    
    if __name__ == "__main__":
        try:
            main()
        except (KeyboardInterrupt, SystemExit):
            # Не перехватываем системные исключения
            raise
        except (RuntimeError, AttributeError, TypeError) as main_error:
            logger.error(f"Ошибка выполнения при выполнении main(): {main_error}", exc_info=True)
            raise
        except (ValueError, KeyError, IndexError) as main_error:
            logger.error(f"Ошибка данных при выполнении main(): {main_error}", exc_info=True)
            raise
        except (MemoryError, RecursionError) as main_error:
            # Ошибки памяти/рекурсии
            logger.error(f"Ошибка памяти/рекурсии при выполнении main(): {main_error}", exc_info=True)
            raise
        except BaseException as main_error:
            if isinstance(main_error, (KeyboardInterrupt, SystemExit)):
                raise
            logger.error(f"Неожиданная ошибка при выполнении main(): {main_error}", exc_info=True)
            raise
except (KeyboardInterrupt, SystemExit):
    # Не перехватываем системные исключения
    raise
except (ImportError, ModuleNotFoundError, SyntaxError) as e:
    logger.error(f"Критическая ошибка импорта/синтаксиса при запуске программы: {e}", exc_info=True)
    # Если произошла ошибка, показываем сообщение
    try:
        import tkinter.messagebox as messagebox
        messagebox.showerror("Критическая ошибка", f"Не удалось запустить программу:\n{e}")
    except (tk.TclError, RuntimeError, AttributeError):
        print(f"Критическая ошибка: {e}")
    except (MemoryError, RecursionError):
        # Ошибки памяти/рекурсии
        print(f"Критическая ошибка памяти/рекурсии: {e}")
    except BaseException:
        # Финальный catch для неожиданных исключений (критично для стабильности)
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        print(f"Критическая ошибка: {e}")
except (ValueError, TypeError, KeyError, IndexError) as e:
    logger.error(f"Критическая ошибка данных при запуске программы: {e}", exc_info=True)
    try:
        import tkinter.messagebox as messagebox
        messagebox.showerror("Критическая ошибка", f"Ошибка данных при запуске программы:\n{e}")
    except (tk.TclError, RuntimeError, AttributeError):
        print(f"Критическая ошибка данных: {e}")
    except (MemoryError, RecursionError):
        # Ошибки памяти/рекурсии
        print(f"Критическая ошибка памяти/рекурсии: {e}")
    except BaseException:
        # Финальный catch для неожиданных исключений (критично для стабильности)
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        print(f"Критическая ошибка данных: {e}")
except (MemoryError, RecursionError) as e:
    # Ошибки памяти/рекурсии
    logger.error(f"Критическая ошибка памяти/рекурсии при запуске программы: {e}", exc_info=True)
    try:
        import tkinter as tk
        import tkinter.messagebox as messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ошибка памяти", "Критическая ошибка памяти при запуске программы.")
        root.destroy()
    except (tk.TclError, AttributeError, RuntimeError):
        print(f"Критическая ошибка памяти/рекурсии: {e}")
except BaseException as e:
    # Финальный catch для неожиданных исключений (критично для стабильности)
    if isinstance(e, (KeyboardInterrupt, SystemExit)):
        raise
    logger.error(f"Критическая ошибка при запуске программы: {e}", exc_info=True)
    # Если произошла ошибка, показываем сообщение
    try:
        import tkinter as tk
        import tkinter.messagebox as messagebox
        
        # Пробуем использовать TkinterDnD если доступно (для консистентности)
        try:
            from tkinterdnd2 import TkinterDnD
            root = TkinterDnD.Tk()
        except (ImportError, Exception):
            root = tk.Tk()
        
        root.withdraw()  # Скрываем главное окно
        
        # Формируем сообщение об ошибке с правильной кодировкой
        error_msg = "Не удалось запустить программу:\n\n"
        error_msg += str(e) + "\n\n"
        error_msg += "Убедитесь, что установлен Python 3.7+"
        
        messagebox.showerror("Ошибка запуска", error_msg)
        root.destroy()
    except (tk.TclError, AttributeError, RuntimeError) as dialog_error:
        logger.error(f"Не удалось показать диалог ошибки: {dialog_error}", exc_info=True)
        # Если даже диалог не работает, пробуем через консоль
        try:
            print("Ошибка запуска программы:")
            print(str(e))
            print("\nУбедитесь, что установлен Python 3.7+")
            input("\nНажмите Enter для выхода...")
        except (EOFError, KeyboardInterrupt, OSError):
            pass
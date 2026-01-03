"""Единая точка входа для приложения Ре-Файл+.

Этот модуль обеспечивает единую точку входа для GUI и CLI версий приложения.
"""

import logging
import os
import sys
from typing import List, Optional

# Локальные импорты
from app.app_core import ReFilePlusApp
from app.cli_utils import process_cli_args

logger = logging.getLogger(__name__)


def run_gui(files_from_args: Optional[List[str]] = None) -> None:
    """Запуск GUI версии приложения.
    
    Args:
        files_from_args: Список файлов из аргументов командной строки
    """
    import tkinter as tk
    
    # Опциональные сторонние библиотеки
    HAS_TKINTERDND2 = False
    try:
        from tkinterdnd2 import TkinterDnD
        HAS_TKINTERDND2 = True
    except ImportError:
        pass
    
    # Создание корневого окна
    logger.info("Создание корневого окна...")
    if HAS_TKINTERDND2:
        try:
            root = TkinterDnD.Tk()
            logger.info("Root окно создано как TkinterDnD.Tk()")
        except (AttributeError, RuntimeError, TypeError) as e:
            logger.error(f"Ошибка выполнения при создании TkinterDnD.Tk(): {e}", exc_info=True)
            root = tk.Tk()
            logger.warning("Root окно создано как обычный tk.Tk() - drag and drop недоступен")
        except (MemoryError, RecursionError) as e:

            # Ошибки памяти/рекурсии

            pass

        # Финальный catch для неожиданных исключений (критично для стабильности)

        except BaseException as e:

            if isinstance(e, (KeyboardInterrupt, SystemExit)):

                raise
            logger.error(f"Неожиданная ошибка при создании TkinterDnD.Tk(): {e}", exc_info=True)
            root = tk.Tk()
            logger.warning("Root окно создано как обычный tk.Tk() - drag and drop недоступен")
    else:
        root = tk.Tk()
        logger.warning("tkinterdnd2 недоступен - root окно создано как обычный tk.Tk()")
        logger.warning("Для включения drag and drop установите: pip install tkinterdnd2")
    
    # Создание и запуск приложения
    logger.info("Создание экземпляра ReFilePlusApp...")
    app = ReFilePlusApp(root, files_from_args=files_from_args)
    logger.info("ReFilePlusApp создан успешно")
    
    # Запуск главного цикла
    logger.info("Запуск главного цикла приложения...")
    try:
        root.mainloop()
    except KeyboardInterrupt:
        logger.info("Приложение прервано пользователем")
    except (SystemExit, RuntimeError) as e:
        logger.error(f"Системная ошибка в главном цикле: {e}", exc_info=True)
        raise
    except (MemoryError, RecursionError) as e:

        # Ошибки памяти/рекурсии

        pass

    # Финальный catch для неожиданных исключений (критично для стабильности)

    except BaseException as e:

        if isinstance(e, (KeyboardInterrupt, SystemExit)):

            raise
        logger.error(f"Критическая ошибка в главном цикле: {e}", exc_info=True)
        raise
    finally:
        logger.info("Приложение завершено")


def main() -> None:
    """Главная функция запуска приложения."""
    logger.info("Функция main() начала выполнение")
    
    # Обработка аргументов командной строки
    logger.info("Обработка аргументов командной строки...")
    files_from_args = process_cli_args()
    logger.info(f"Обработано файлов из аргументов: {len(files_from_args)}")
    
    # Запуск GUI версии
    run_gui(files_from_args)


if __name__ == '__main__':
    main()


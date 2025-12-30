"""Модуль для переименования файлов в отдельном потоке."""

import logging
import os
import threading
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


def re_file_files_thread(
    files_to_rename: List[Dict[str, Any]],
    callback: Callable[[int, int, List[Dict[str, Any]]], None],
    log_callback: Optional[Callable[[str], None]] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    cancel_var: Optional[Any] = None
) -> None:
    """Переименование файлов в отдельном потоке.
    
    Args:
        files_to_rename: Список файлов для переименования
        methods: Список методов re-file для применения
        log_callback: Функция для логирования (принимает сообщение)
        progress_callback: Функция для обновления прогресса (принимает current, total, filename)
        callback: Функция обратного вызова при завершении (принимает success_count, error_count, renamed_files)
    """
    if not files_to_rename:
        if callback:
            try:
                callback(0, 0, [])
            except Exception as e:
                logger.error(f"Ошибка при вызове callback для пустого списка: {e}", exc_info=True)
        return
    
    def re_file_worker():
        """Воркер для переименования файлов."""
        success_count = 0
        error_count = 0
        renamed_files = []
        total = len(files_to_rename)
        
        try:
            for i, file_data in enumerate(files_to_rename):
                # Проверка отмены
                if cancel_var and cancel_var.is_set():
                    if log_callback:
                        log_callback("Операция переименования отменена пользователем")
                    break
                try:
                    # Получаем old_path и is_folder
                    if hasattr(file_data, 'full_path'):
                        old_path = file_data.full_path or str(file_data.path)
                        # Если full_path не содержит имя файла, добавляем его
                        if old_path and hasattr(file_data, 'old_name') and file_data.old_name:
                            old_name_with_ext = file_data.old_name + (file_data.extension or '')
                            basename = os.path.basename(old_path)
                            # Проверяем, содержит ли путь имя файла
                            if not basename or basename != old_name_with_ext:
                                # Путь не содержит имя файла, добавляем его
                                old_path = os.path.join(old_path, old_name_with_ext)
                                logger.debug(f"Добавлено имя файла к пути: {old_path}")
                        is_folder = (file_data.metadata and file_data.metadata.get('is_folder', False)) if hasattr(file_data, 'metadata') else False
                    else:
                        old_path = file_data.get('full_path') or file_data.get('path')
                        # Если old_path не содержит имя файла, добавляем его
                        if old_path and file_data.get('old_name'):
                            old_name_with_ext = file_data.get('old_name', '') + file_data.get('extension', '')
                            basename = os.path.basename(old_path)
                            # Проверяем, содержит ли путь имя файла
                            if not basename or basename != old_name_with_ext:
                                # Путь не содержит имя файла, добавляем его
                                old_path = os.path.join(old_path, old_name_with_ext)
                                logger.debug(f"Добавлено имя файла к пути (dict): {old_path}")
                        is_folder = file_data.get('is_folder', False) or (
                            file_data.get('metadata', {}).get('is_folder', False) if isinstance(file_data.get('metadata'), dict) else False
                        )
                    
                    item_type = "папка" if is_folder else "файл"
                    
                    if not old_path:
                        error_msg = "Не указан путь к файлу/папке"
                        if log_callback:
                            log_callback(f"Ошибка: {error_msg}")
                        if hasattr(file_data, 'set_error'):
                            file_data.set_error(error_msg)
                        else:
                            file_data['status'] = f"Ошибка: {error_msg}"
                        error_count += 1
                        continue
                    
                    old_path = os.path.normpath(old_path)
                    
                    try:
                        if not os.path.exists(old_path):
                            error_msg = f"Исходный {item_type} не найден: {os.path.basename(old_path)}"
                            if log_callback:
                                log_callback(f"Ошибка: {error_msg}")
                            if hasattr(file_data, 'set_error'):
                                file_data.set_error(error_msg)
                            elif isinstance(file_data, dict):
                                file_data['status'] = f"Ошибка: {error_msg}"
                            error_count += 1
                            continue
                        
                        if not (os.path.isfile(old_path) or os.path.isdir(old_path)):
                            error_msg = f"Путь не является {item_type}: {os.path.basename(old_path)}"
                            if log_callback:
                                log_callback(f"Ошибка: {error_msg}")
                            if hasattr(file_data, 'set_error'):
                                file_data.set_error(error_msg)
                            elif isinstance(file_data, dict):
                                file_data['status'] = f"Ошибка: {error_msg}"
                            error_count += 1
                            continue
                        
                        if is_folder and not os.path.isdir(old_path):
                            error_msg = f"Путь указывает на файл, а не на папку: {os.path.basename(old_path)}"
                            if log_callback:
                                log_callback(f"Ошибка: {error_msg}")
                            if hasattr(file_data, 'set_error'):
                                file_data.set_error(error_msg)
                            elif isinstance(file_data, dict):
                                file_data['status'] = f"Ошибка: {error_msg}"
                            error_count += 1
                            continue
                        
                        if not is_folder and not os.path.isfile(old_path):
                            error_msg = f"Путь указывает на папку, а не на файл: {os.path.basename(old_path)}"
                            if log_callback:
                                log_callback(f"Ошибка: {error_msg}")
                            if hasattr(file_data, 'set_error'):
                                file_data.set_error(error_msg)
                            elif isinstance(file_data, dict):
                                file_data['status'] = f"Ошибка: {error_msg}"
                            error_count += 1
                            continue
                    except (OSError, ValueError) as e:
                        error_msg = f"Исходный {item_type} не найден: {os.path.basename(old_path) if old_path else 'неизвестный путь'}"
                        if log_callback:
                            log_callback(f"Ошибка: {error_msg}")
                        if hasattr(file_data, 'set_error'):
                            file_data.set_error(error_msg)
                        elif isinstance(file_data, dict):
                            file_data['status'] = f"Ошибка: {error_msg}"
                        error_count += 1
                        continue
                    
                    # Получаем new_name и extension
                    if hasattr(file_data, 'new_name'):
                        new_name = file_data.new_name
                        extension = '' if is_folder else file_data.extension
                    else:
                        new_name = file_data.get('new_name', '')
                        extension = '' if is_folder else file_data.get('extension', '')
                    
                    # Валидация нового имени
                    if not new_name or not new_name.strip():
                        item_type = "папки" if is_folder else "файла"
                        error_msg = f"Пустое имя {item_type}"
                        if log_callback:
                            log_callback(f"Ошибка: {error_msg}")
                        if hasattr(file_data, 'set_error'):
                            file_data.set_error(error_msg)
                        else:
                            file_data['status'] = f"Ошибка: {error_msg}"
                        error_count += 1
                        continue
                    
                    # Получаем директорию и создаем новый путь
                    directory = os.path.dirname(old_path)
                    new_path = os.path.join(directory, new_name + extension)
                    new_path = os.path.normpath(new_path)
                    
                    if old_path == new_path:
                        item_type = "папка" if is_folder else "файл"
                        if log_callback:
                            log_callback(f"Без изменений: '{os.path.basename(old_path)}' ({item_type})")
                        success_count += 1
                        continue
                    
                    # Переименовываем файл/папку
                    try:
                        os.rename(old_path, new_path)
                    except FileExistsError:
                        item_type = "папка" if is_folder else "файл"
                        item_name = new_name if is_folder else new_name + extension
                        error_msg = f"{item_type.capitalize()} '{item_name}' уже существует"
                        if log_callback:
                            log_callback(f"Ошибка: {error_msg}")
                        if hasattr(file_data, 'set_error'):
                            file_data.set_error(error_msg)
                        elif isinstance(file_data, dict):
                            file_data['status'] = f"Ошибка: {error_msg}"
                        error_count += 1
                        logger.warning(f"Файл уже существует при переименовании {old_path} -> {new_path}")
                        continue
                    except OSError as rename_error:
                        item_type = "папка" if is_folder else "файл"
                        try:
                            if not os.path.exists(old_path):
                                error_msg = f"Исходный {item_type} был удален при переименовании: {os.path.basename(old_path)}"
                            else:
                                error_msg = f"Ошибка переименования: {str(rename_error)}"
                        except (OSError, ValueError):
                            error_msg = f"Ошибка переименования: {str(rename_error)}"
                        if log_callback:
                            log_callback(f"Ошибка: {error_msg}")
                        if hasattr(file_data, 'set_error'):
                            file_data.set_error(error_msg)
                        elif isinstance(file_data, dict):
                            file_data['status'] = f"Ошибка: {error_msg}"
                        error_count += 1
                        logger.error(f"Ошибка переименования {old_path} -> {new_path}: {rename_error}", exc_info=True)
                        continue
                    
                    # Обновляем пути в file_data
                    # ВАЖНО: Сохраняем старое имя перед обновлением, чтобы можно было отследить изменение
                    old_name_before_update = None
                    if hasattr(file_data, 'old_name'):
                        old_name_before_update = file_data.old_name
                    elif isinstance(file_data, dict):
                        old_name_before_update = file_data.get('old_name')
                    
                    if hasattr(file_data, 'path'):
                        from pathlib import Path
                        if not hasattr(file_data, 'metadata') or file_data.metadata is None:
                            file_data.metadata = {}
                        if isinstance(file_data.metadata, dict):
                            file_data.metadata['_original_path'] = old_path
                        file_data.path = Path(new_path)
                        file_data.full_path = new_path
                        # Обновляем old_name на новое имя (после переименования новое имя становится старым)
                        file_data.old_name = new_name
                        file_data.new_name = new_name
                        # Обновляем статус на "готов" после успешного переименования
                        if hasattr(file_data, 'set_ready'):
                            file_data.set_ready()
                    else:
                        file_data['_original_path'] = old_path
                        file_data['path'] = new_path
                        file_data['full_path'] = new_path
                        # Обновляем old_name на новое имя (после переименования новое имя становится старым)
                        file_data['old_name'] = new_name
                        file_data['new_name'] = new_name
                        # Обновляем статус
                        file_data['status'] = 'Готов'
                    
                    renamed_files.append(file_data)
                    success_count += 1
                    
                    item_name = new_name if is_folder else new_name + extension
                    if log_callback:
                        log_callback(f"Переименован {item_type}: '{os.path.basename(old_path)}' -> '{item_name}'")
                    
                    if progress_callback:
                        try:
                            progress_callback(i + 1, total, file_data.get('old_name', 'unknown'))
                        except Exception:
                            pass
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Ошибка при переименовании '{file_data.get('old_name', 'unknown')}': {error_msg}", exc_info=True)
                    old_name = file_data.get('old_name', 'unknown') if isinstance(file_data, dict) else (file_data.old_name if hasattr(file_data, 'old_name') else 'unknown')
                    if log_callback:
                        log_callback(f"Ошибка при переименовании '{old_name}': {error_msg}")
                    if hasattr(file_data, 'set_error'):
                        file_data.set_error(error_msg)
                    elif isinstance(file_data, dict):
                        file_data['status'] = f"Ошибка: {error_msg}"
                    error_count += 1
                    if progress_callback:
                        try:
                            progress_callback(i + 1, total, file_data.get('old_name', 'unknown'))
                        except Exception:
                            pass
        except Exception as e:
            logger.error(f"Критическая ошибка в re_file_worker: {e}", exc_info=True)
            if log_callback:
                log_callback(f"Критическая ошибка: {e}")
        finally:
            if callback:
                try:
                    callback(success_count, error_count, renamed_files)
                except Exception as callback_error:
                    logger.error(f"Ошибка при вызове callback: {callback_error}", exc_info=True)
            else:
                logger.error("Критическая ошибка: Callback не предоставлен")
    
    # Запускаем worker в отдельном потоке
    try:
        thread = threading.Thread(target=re_file_worker, daemon=True, name="re_file_files")
        thread.start()
        
        def check_completion():
            """Проверка завершения операции через 10 секунд"""
            import time
            time.sleep(10)
            if thread.is_alive():
                logger.error("Операция переименования не завершилась за 10 секунд, возможно зависание")
                if callback:
                    try:
                        callback(0, len(files_to_rename), [])
                    except Exception as e:
                        logger.error(f"Ошибка при принудительном вызове callback: {e}", exc_info=True)
        
        timeout_thread = threading.Thread(target=check_completion, daemon=True)
        timeout_thread.start()
    except Exception as e:
        logger.error(f"Ошибка при запуске потока переименования: {e}", exc_info=True)
        if callback:
            try:
                callback(0, len(files_to_rename), [])
            except Exception as callback_error:
                logger.error(f"Ошибка при вызове callback после ошибки запуска: {callback_error}", exc_info=True)


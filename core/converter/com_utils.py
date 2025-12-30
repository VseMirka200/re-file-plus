"""Утилиты для работы с COM (Microsoft Word).

Содержит функции для работы с Microsoft Word через COM интерфейс:
- Создание и закрытие Word приложений
- Конвертация документов через Word
- Проверка наличия Word в системе
"""

import logging
import os
import sys
from contextlib import contextmanager
from typing import Any, Optional, Tuple

# Импорт winreg для проверки наличия Word (только на Windows)
if sys.platform == 'win32':
    try:
        import winreg
        HAS_WINREG = True
    except ImportError:
        HAS_WINREG = False
else:
    HAS_WINREG = False

logger = logging.getLogger(__name__)


def cleanup_word_application(word_app: Optional[Any]) -> None:
    """Безопасное закрытие Word приложения.
    
    Args:
        word_app: Объект Word.Application или None
    """
    if word_app:
        try:
            word_app.Quit(SaveChanges=False)
        except (AttributeError, OSError, RuntimeError) as e:
            logger.warning(f"Ошибка при закрытии Word: {e}")
        except Exception as e:
            logger.warning(f"Неожиданная ошибка при закрытии Word: {e}")


def cleanup_word_document(doc: Optional[Any]) -> None:
    """Безопасное закрытие Word документа.
    
    Args:
        doc: Объект Word.Document или None
    """
    if doc:
        try:
            # Проверяем, что документ еще открыт
            if hasattr(doc, 'Name'):
                doc.Close(SaveChanges=False)
        except (AttributeError, OSError, RuntimeError, TypeError):
            # Документ уже закрыт или объект невалиден - это нормально
            pass
        except Exception:
            # Игнорируем все остальные ошибки при закрытии
            pass


@contextmanager
def word_application_context(com_client: Any):
    """Context manager для безопасной работы с Word.Application.
    
    Гарантирует закрытие Word приложения даже при возникновении ошибок.
    
    Args:
        com_client: Клиент COM (win32com.client или comtypes.client)
        
    Yields:
        Word.Application объект или None
        
    Example:
        with word_application_context(com_client) as word_app:
            if word_app:
                # Работа с Word
                pass
    """
    word_app = None
    pythoncom_module = None
    com_initialized = False
    
    try:
        word_app, error_msg = create_word_application(com_client)
        if word_app:
            # Инициализация COM уже выполнена в create_word_application
            import pythoncom
            pythoncom_module = pythoncom
            com_initialized = True
        yield word_app
    finally:
        # Закрываем документы перед закрытием приложения
        if word_app is not None:
            try:
                # Проверяем наличие атрибута Documents
                if hasattr(word_app, 'Documents'):
                    # Закрываем все открытые документы
                    for doc in list(word_app.Documents):
                        if doc is not None:
                            cleanup_word_document(doc)
            except (AttributeError, OSError, RuntimeError):
                pass
        
        # Закрываем приложение
        cleanup_word_application(word_app)
        
        # Освобождаем COM
        if com_initialized and pythoncom_module:
            try:
                pythoncom_module.CoUninitialize()
            except (OSError, RuntimeError):
                pass


def check_word_installed() -> Tuple[bool, str]:
    """Проверка наличия Microsoft Word в системе.
    
    Проверяет реестр Windows на наличие установленного Microsoft Office/Word.
    
    Returns:
        Tuple[установлен, сообщение] - True если Word установлен, иначе False
    """
    if sys.platform != 'win32':
        return False, "Microsoft Word доступен только на Windows"
    
    if not HAS_WINREG:
        # Если winreg недоступен, возвращаем неопределенный результат
        return True, "Не удалось проверить наличие Word (проверка реестра недоступна)"
    
    # Проверяем наличие Word в реестре
    word_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Office"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Office"),
    ]
    
    for hkey, path in word_paths:
        try:
            with winreg.OpenKey(hkey, path) as key:
                # Проверяем установленные версии Office
                for i in range(winreg.QueryInfoKey(key)[0]):
                    subkey_name = winreg.EnumKey(key, i)
                    # Проверяем версии Office (16.0 = Office 2016+, 15.0 = Office 2013, 14.0 = Office 2010)
                    if any(ver in subkey_name for ver in ['16.0', '15.0', '14.0', '12.0']):
                        # Проверяем наличие Word в этой версии
                        try:
                            with winreg.OpenKey(key, subkey_name) as ver_key:
                                try:
                                    with winreg.OpenKey(ver_key, r"Word\InstallRoot") as word_key:
                                        return True, "Microsoft Word найден в системе"
                                except (OSError, FileNotFoundError):
                                    continue
                        except (OSError, FileNotFoundError):
                            continue
        except (OSError, FileNotFoundError):
            continue
    
    return False, "Microsoft Word не найден в системе. Установите Microsoft Office с Word."


def create_word_application(com_client: Any) -> Tuple[Optional[Any], Optional[str]]:
    """Создание объекта Word.Application с несколькими попытками.
    
    Args:
        com_client: Клиент COM (win32com.client или comtypes.client)
        
    Returns:
        Tuple[word_app, error_message] - объект Word или None и сообщение об ошибке
    """
    # Сначала проверяем, установлен ли Word
    word_installed, install_msg = check_word_installed()
    if not word_installed:
        return None, install_msg
    
    # Инициализируем COM перед созданием Word объекта
    pythoncom_module = None
    com_initialized = False
    try:
        import pythoncom
        pythoncom_module = pythoncom
        # Пробуем использовать CoInitializeEx (более надежный метод)
        if hasattr(pythoncom_module, 'CoInitializeEx'):
            try:
                # COINIT_APARTMENTTHREADED = 2
                pythoncom_module.CoInitializeEx(2)
            except (AttributeError, ValueError):
                pythoncom_module.CoInitialize()
        else:
            pythoncom_module.CoInitialize()
    except (OSError, RuntimeError, AttributeError) as init_error:
        # Если уже инициализирован, это нормально
        error_str = str(init_error).lower()
        if "already initialized" not in error_str and "rpc_e_changed_mode" not in error_str:
            logger.warning(f"Ошибка инициализации COM: {init_error}")
    except Exception as init_error:
        # Неожиданная ошибка
        logger.warning(f"Неожиданная ошибка инициализации COM: {init_error}")
    com_initialized = True
    
    # Пробуем разные способы создания Word объекта
    try:
        word = com_client.Dispatch('Word.Application')
        return word, None
    except (OSError, RuntimeError, AttributeError, TypeError) as e1:
        error_msg1 = str(e1)
        logger.warning(f"Первый способ создания Word.Application не удался: {error_msg1}")
        
        # Пробуем альтернативный способ через DispatchEx
        try:
            word = com_client.DispatchEx('Word.Application')
            logger.debug("Word.Application создан через DispatchEx")
            return word, None
        except (OSError, RuntimeError, AttributeError, TypeError) as e2:
            error_msg2 = str(e2)
            logger.warning(f"Второй способ создания Word.Application не удался: {error_msg2}")
            
            # Пробуем через GetActiveObject (если Word уже запущен)
            try:
                word = com_client.GetActiveObject('Word.Application')
                logger.debug("Word.Application получен через GetActiveObject (Word уже запущен)")
                return word, None
            except (OSError, RuntimeError, AttributeError, TypeError) as e3:
                error_msg3 = str(e3)
                logger.error(f"Все способы создания Word.Application не удались. Ошибки: {error_msg1}, {error_msg2}, {error_msg3}")
                
                # Освобождаем COM если Word не был создан
                if com_initialized and pythoncom_module:
                    try:
                        pythoncom_module.CoUninitialize()
                    except (OSError, RuntimeError, AttributeError):
                        pass
                    except Exception as uninit_error:
                        logger.debug(f"Неожиданная ошибка при освобождении COM: {uninit_error}")
                
                # Формируем понятное сообщение об ошибке
                if any(keyword in error_msg1.lower() for keyword in ['invalid class string', 'clsid', 'class not registered', 'progid']):
                    return None, "Microsoft Word не установлен или не зарегистрирован в системе. Установите Microsoft Office с Word."
                elif "access is denied" in error_msg1.lower() or "permission" in error_msg1.lower():
                    return None, "Нет доступа к Microsoft Word. Запустите программу от имени администратора или закройте все окна Word."
                elif "rpc" in error_msg1.lower() or "com" in error_msg1.lower():
                    return None, "Ошибка COM при подключении к Word. Попробуйте перезапустить Word или перезагрузить компьютер."
                else:
                    return None, f"Не удалось создать объект Word.Application: {error_msg1}"


def convert_docx_with_word(
    word_app: Any,
    file_path: str,
    output_path: str,
    com_client_type: str = "win32com"
) -> Tuple[bool, Optional[str]]:
    """Конвертация DOCX/DOC в PDF через Word приложение.
    
    Args:
        word_app: Объект Word.Application
        file_path: Путь к исходному DOCX или DOC файлу
        output_path: Путь для сохранения PDF
        com_client_type: Тип COM клиента ("win32com" или "comtypes")
        
    Returns:
        Tuple[success, error_message]
    """
    doc = None
    try:
        # Проверяем, что файл существует
        if not os.path.exists(file_path):
            return False, f"Исходный файл не найден: {file_path}"
        
        # Проверяем, что директория для выходного файла существует
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Настраиваем Word
        word_app.Visible = False
        word_app.DisplayAlerts = 0  # Отключаем предупреждения
        
        # Открываем документ
        if word_app is None:
            return False, "Word приложение не инициализировано"
        
        doc_path = os.path.abspath(file_path)
        logger.debug(f"Открываем документ Word: {doc_path}")
        try:
            if not hasattr(word_app, 'Documents'):
                return False, "Word приложение не поддерживает Documents"
            
            doc = word_app.Documents.Open(
                FileName=doc_path,
                ReadOnly=True,
                ConfirmConversions=False,
                AddToRecentFiles=False
            )
            logger.debug("Документ открыт успешно")
        except (OSError, RuntimeError, AttributeError, TypeError) as open_error:
            error_msg = str(open_error)
            logger.error(f"Ошибка при открытии документа: {error_msg}")
            if "не найден" in error_msg.lower() or "not found" in error_msg.lower():
                return False, f"Не удалось открыть документ: {file_path}"
            return False, f"Ошибка при открытии документа: {error_msg}"
        except Exception as open_error:
            # Неожиданная ошибка
            error_msg = str(open_error)
            logger.error(f"Неожиданная ошибка при открытии документа: {error_msg}")
            return False, f"Ошибка при открытии документа: {error_msg}"
        
        # Сохраняем как PDF
        pdf_path = os.path.abspath(output_path)
        logger.debug(f"Сохраняем как PDF: {pdf_path}")
        try:
            doc.SaveAs(FileName=pdf_path, FileFormat=17)  # 17 = PDF format
            logger.debug("Документ сохранен как PDF")
        except (OSError, RuntimeError, AttributeError, PermissionError) as save_error:
            error_msg = str(save_error)
            # Логируем только реальные ошибки (не общие COM-исключения)
            if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.'):
                logger.error(f"Ошибка при сохранении PDF: {error_msg}")
            # Проверяем, может быть файл уже существует и заблокирован
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                    doc.SaveAs(FileName=pdf_path, FileFormat=17)
                except (OSError, PermissionError, RuntimeError) as retry_error:
                    retry_msg = str(retry_error)
                    if retry_msg and len(retry_msg) > 10 and not retry_msg.startswith('Open.'):
                        return False, f"Не удалось сохранить PDF: {retry_msg}"
                    return False, "Не удалось сохранить PDF"
                except Exception as retry_error:
                    retry_msg = str(retry_error)
                    if retry_msg and len(retry_msg) > 10 and not retry_msg.startswith('Open.'):
                        return False, f"Неожиданная ошибка при повторной попытке сохранения: {retry_msg}"
                    return False, "Ошибка при сохранении PDF"
            else:
                return False, f"Ошибка при сохранении PDF: {error_msg if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.') else 'Ошибка сохранения'}"
        except Exception as save_error:
            # Неожиданная ошибка
            error_msg = str(save_error)
            # Логируем только реальные ошибки
            if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.'):
                logger.error(f"Неожиданная ошибка при сохранении PDF: {error_msg}")
            return False, f"Ошибка при сохранении PDF: {error_msg if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.') else 'Ошибка сохранения'}"
        
        return True, None
        
    except (OSError, RuntimeError, AttributeError, TypeError) as e:
        error_msg = str(e)
        logger.error(f"Ошибка при конвертации через {com_client_type}: {error_msg}")
        return False, error_msg
    except Exception as e:
        # Неожиданная ошибка
        error_msg = str(e)
        logger.error(f"Неожиданная ошибка при конвертации через {com_client_type}: {error_msg}", exc_info=True)
        return False, error_msg
    finally:
        cleanup_word_document(doc)


def convert_docx_with_word_com(
    file_path: str,
    output_path: str,
    file_format: int
) -> Tuple[bool, str, Optional[str]]:
    """Конвертация DOCX/DOC в другой формат через Word COM.
    
    Обертка над convert_docx_with_word, которая создает Word приложение
    и управляет его жизненным циклом.
    
    Args:
        file_path: Путь к исходному DOCX или DOC файлу
        output_path: Путь для сохранения результата
        file_format: Формат для сохранения (17 = PDF, 16 = DOCX, и т.д.)
        
    Returns:
        Tuple[успех, сообщение, путь к выходному файлу]
    """
    import sys
    
    # Определяем COM клиент
    com_client = None
    com_client_type = None
    
    if sys.platform == 'win32':
        try:
            import win32com.client
            com_client = win32com.client
            com_client_type = "win32com"
        except ImportError:
            try:
                import comtypes.client
                com_client = comtypes.client
                com_client_type = "comtypes"
            except ImportError:
                return False, "COM библиотеки не доступны. Установите pywin32 или comtypes", None
    
    if not com_client:
        return False, "COM библиотеки не доступны на этой платформе", None
    
    word_app = None
    pythoncom_module = None
    com_initialized = False
    
    try:
        # Создаем Word приложение
        word_app, error_msg = create_word_application(com_client)
        if not word_app:
            return False, error_msg or "Не удалось создать Word приложение", None
        
        # Инициализируем COM
        try:
            import pythoncom
            pythoncom_module = pythoncom
            com_initialized = True
        except ImportError:
            pass
        
        # Настраиваем Word
        word_app.Visible = False
        word_app.DisplayAlerts = 0  # Отключаем предупреждения
        
        # Открываем документ
        doc_path = os.path.abspath(file_path)
        logger.debug(f"Открываем документ Word: {doc_path}")
        
        doc = None
        try:
            if not hasattr(word_app, 'Documents'):
                return False, "Word приложение не поддерживает Documents", None
            
            doc = word_app.Documents.Open(
                FileName=doc_path,
                ReadOnly=True,
                ConfirmConversions=False,
                AddToRecentFiles=False
            )
            logger.debug("Документ открыт успешно")
        except (OSError, RuntimeError, AttributeError, TypeError) as open_error:
            error_msg = str(open_error)
            logger.error(f"Ошибка при открытии документа: {error_msg}")
            return False, f"Не удалось открыть документ: {error_msg}", None
        except Exception as open_error:
            error_msg = str(open_error)
            logger.error(f"Неожиданная ошибка при открытии документа: {error_msg}")
            return False, f"Ошибка при открытии документа: {error_msg}", None
        
        # Сохраняем в нужном формате
        output_file_path = os.path.abspath(output_path)
        logger.debug(f"Сохраняем документ: {output_file_path}, формат: {file_format}")
        
        try:
            # Проверяем директорию для выходного файла
            output_dir = os.path.dirname(output_file_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            doc.SaveAs(FileName=output_file_path, FileFormat=file_format)
            logger.debug(f"Документ сохранен в формате {file_format}")
            
            # Проверяем, что файл создан
            if os.path.exists(output_file_path):
                return True, f"Документ успешно конвертирован в формат {file_format}", output_file_path
            else:
                return False, "Файл не был создан", None
        except (OSError, RuntimeError, AttributeError, PermissionError) as save_error:
            error_msg = str(save_error)
            # Логируем только реальные ошибки (не общие COM-исключения)
            if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.'):
                logger.error(f"Ошибка при сохранении документа: {error_msg}")
            # Пробуем удалить существующий файл и повторить
            if os.path.exists(output_file_path):
                try:
                    os.remove(output_file_path)
                    doc.SaveAs(FileName=output_file_path, FileFormat=file_format)
                    if os.path.exists(output_file_path):
                        return True, f"Документ успешно конвертирован в формат {file_format}", output_file_path
                except Exception as retry_error:
                    retry_msg = str(retry_error)
                    if retry_msg and len(retry_msg) > 10 and not retry_msg.startswith('Open.'):
                        return False, f"Не удалось сохранить документ: {retry_msg}", None
                    return False, "Не удалось сохранить документ", None
            return False, f"Ошибка при сохранении документа: {error_msg if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.') else 'Ошибка сохранения'}", None
        except Exception as save_error:
            error_msg = str(save_error)
            # Логируем только реальные ошибки
            if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.'):
                logger.error(f"Неожиданная ошибка при сохранении документа: {error_msg}")
            return False, f"Ошибка при сохранении документа: {error_msg if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.') else 'Ошибка сохранения'}", None
        finally:
            # Закрываем документ
            if doc:
                cleanup_word_document(doc)
                doc = None
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка при конвертации через Word COM: {error_msg}", exc_info=True)
        return False, f"Ошибка конвертации: {error_msg}", None
    finally:
        # Закрываем Word приложение
        if word_app:
            try:
                # Закрываем все открытые документы
                if hasattr(word_app, 'Documents'):
                    for doc in list(word_app.Documents):
                        if doc:
                            cleanup_word_document(doc)
            except (AttributeError, OSError, RuntimeError):
                pass
            cleanup_word_application(word_app)
        
        # Освобождаем COM
        if com_initialized and pythoncom_module:
            try:
                pythoncom_module.CoUninitialize()
            except (OSError, RuntimeError, AttributeError):
                pass

"""Модуль конвертации документов.

Содержит функции для конвертации документов:
- DOCX/DOC в PDF
- PDF в DOCX
- DOCX/DOC в ODT
- ODT в различные форматы
- Универсальная конвертация документов
"""

import logging
import os
import sys
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Импорт функции проверки существования с поддержкой Unicode
try:
    from utils.security_utils import _check_file_exists_unicode
except ImportError:
    # Fallback если функция недоступна
    def _check_file_exists_unicode(path: str) -> bool:
        try:
            return os.path.exists(path) and os.path.isfile(path)
        except (OSError, UnicodeEncodeError, UnicodeDecodeError):
            try:
                with open(path, 'rb') as f:
                    return True
            except:
                return False


def convert_docx_to_pdf(
    file_path: str,
    output_path: str,
    win32com,
    comtypes,
    docx2pdf_convert,
    docx2pdf_available: bool,
    use_docx2pdf: bool,
    check_word_installed,
    create_word_application,
    convert_docx_with_word_com
) -> Tuple[bool, str, Optional[str]]:
    """Конвертация DOCX/DOC в PDF.
    
    Args:
        file_path: Путь к исходному DOCX или DOC файлу
        output_path: Путь для сохранения PDF
        win32com: Модуль win32com (или None)
        comtypes: Модуль comtypes (или None)
        docx2pdf_convert: Функция docx2pdf.convert (или None)
        docx2pdf_available: Доступна ли библиотека docx2pdf
        use_docx2pdf: Использовать ли docx2pdf
        check_word_installed: Функция проверки установки Word
        create_word_application: Функция создания Word приложения
        convert_docx_with_word_com: Функция конвертации через Word COM
        
    Returns:
        Tuple[успех, сообщение, путь к выходному файлу]
    """
    try:
        # Нормализуем пути
        file_path = os.path.abspath(file_path)
        output_path = os.path.abspath(output_path)
        
        # Определяем расширение исходного файла
        source_ext = os.path.splitext(file_path)[1].lower()
        
        logger.info(f"Начало конвертации DOCX/DOC в PDF: {file_path} (расширение: {source_ext}) -> {output_path}")
        
        # Пробуем разные методы конвертации по порядку
        tried_methods = []
        
        # Метод 1: Пробуем через Word COM (Windows) - приоритетный метод
        logger.info(f"Проверка доступности Word COM: platform={sys.platform}, win32com={win32com is not None}, comtypes={comtypes is not None}")
        if sys.platform == 'win32' and (win32com or comtypes):
            logger.info(f"Пробуем конвертировать через Word COM: {file_path} -> {output_path}")
            try:
                # Формат 17 = PDF
                result = convert_docx_with_word_com(file_path, output_path, 17)
                if result[0]:
                    logger.info("Конвертация через Word COM успешна")
                    return result
                else:
                    logger.warning(f"Word COM вернул ошибку: {result[1]}")
                    tried_methods.append(f"Word COM (ошибка: {result[1][:100]})")
            except (OSError, RuntimeError, AttributeError, TypeError) as e:
                logger.warning(f"Ошибка выполнения при конвертации через Word COM: {e}", exc_info=True)
                tried_methods.append(f"Word COM (ошибка: {str(e)[:100]})")
        else:
            if sys.platform != 'win32':
                logger.info("Word COM недоступен: не Windows платформа")
            elif not win32com and not comtypes:
                logger.warning("Word COM недоступен: не установлены win32com или comtypes. Установите: pip install pywin32 или pip install comtypes")
                tried_methods.append("Word COM (недоступен - не установлены библиотеки)")
            except (ValueError, KeyError, IndexError) as e:
                logger.warning(f"Ошибка данных при конвертации через Word COM: {e}")
                tried_methods.append(f"Word COM (ошибка: {str(e)[:100]})")
            except (MemoryError, RecursionError) as e:
                logger.warning(f"Ошибка памяти/рекурсии при конвертации через Word COM: {e}")
                tried_methods.append(f"Word COM (ошибка: {str(e)[:100]})")
            # Финальный catch для неожиданных исключений (критично для стабильности COM)
            except BaseException as e:
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                logger.warning(f"Критическая ошибка конвертации через Word COM: {e}", exc_info=True)
                tried_methods.append(f"Word COM (ошибка: {str(e)[:100]})")
        
        # Метод 2: Пробуем использовать docx2pdf (только если COM методы недоступны)
        if use_docx2pdf and docx2pdf_convert is not None and not win32com and not comtypes and source_ext == '.docx':
            logger.info(f"Пробуем конвертировать через docx2pdf: {file_path} -> {output_path}")
            try:
                output_dir = os.path.dirname(output_path)
                if not output_dir:
                    output_dir = os.path.dirname(file_path)
                
                os.makedirs(output_dir, exist_ok=True)
                
                # Перенаправляем stdout/stderr
                import io
                import sys as sys_module
                old_stdout = sys_module.stdout
                old_stderr = sys_module.stderr
                fake_stdout = io.StringIO()
                fake_stderr = io.StringIO()
                
                try:
                    sys_module.stdout = fake_stdout
                    sys_module.stderr = fake_stderr
                    docx2pdf_convert(file_path, output_dir)
                finally:
                    sys_module.stdout = old_stdout
                    sys_module.stderr = old_stderr
                
                # Проверяем, создан ли файл (с поддержкой Unicode)
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                expected_pdf = os.path.join(output_dir, base_name + '.pdf')
                
                if _check_file_exists_unicode(expected_pdf):
                    # Если имя файла отличается, переименовываем
                    if expected_pdf != output_path:
                        if _check_file_exists_unicode(output_path):
                            os.remove(output_path)
                        os.rename(expected_pdf, output_path)
                    
                    return True, "DOCX успешно конвертирован в PDF через docx2pdf", output_path
                else:
                    tried_methods.append("docx2pdf")
            except (OSError, PermissionError, ValueError, AttributeError) as e:
                logger.warning(f"Ошибка выполнения при конвертации через docx2pdf: {e}")
                tried_methods.append(f"docx2pdf (ошибка: {str(e)[:100]})")
            except (TypeError, KeyError, IndexError) as e:
                logger.warning(f"Ошибка данных при конвертации через docx2pdf: {e}")
                tried_methods.append(f"docx2pdf (ошибка: {str(e)[:100]})")
            except (MemoryError, RecursionError) as e:
                logger.warning(f"Ошибка памяти/рекурсии при конвертации через docx2pdf: {e}")
                tried_methods.append(f"docx2pdf (ошибка: {str(e)[:100]})")
            # Финальный catch для неожиданных исключений (критично для стабильности)
            except BaseException as e:
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                logger.warning(f"Критическая ошибка конвертации через docx2pdf: {e}", exc_info=True)
                tried_methods.append(f"docx2pdf (ошибка: {str(e)[:100]})")
        
        # Метод 3: Пробуем через LibreOffice как последнюю альтернативу
        try:
            from core.converter.libreoffice_converter import convert_with_libreoffice
            logger.info(f"Пробуем конвертировать через LibreOffice: {file_path} -> {output_path}")
            try:
                result = convert_with_libreoffice(file_path, output_path, '.pdf')
                if result[0]:
                    return result
                else:
                    tried_methods.append(f"LibreOffice (ошибка: {result[1][:100]})")
            except (OSError, RuntimeError, AttributeError, TypeError) as e:
                logger.warning(f"Ошибка выполнения при конвертации через LibreOffice: {e}")
                tried_methods.append(f"LibreOffice (ошибка: {str(e)[:100]})")
            except Exception as e:
                logger.warning(f"Ошибка при конвертации через LibreOffice: {e}")
                tried_methods.append(f"LibreOffice (ошибка: {str(e)[:100]})")
        except ImportError:
            logger.debug("Модуль LibreOffice недоступен")
            tried_methods.append("LibreOffice (недоступен)")
        
        # Если все методы не сработали
        if not tried_methods:
            if sys.platform == 'win32':
                return False, "Не удалось конвертировать файл. Убедитесь, что Microsoft Word или LibreOffice установлены и доступны.", None
            else:
                return False, "Конвертация DOC/DOCX в PDF доступна только на Windows с установленным Microsoft Word или при установленной библиотеке docx2pdf или LibreOffice.", None
        
        methods_str = ", ".join(tried_methods)
        return False, f"Не удалось конвертировать файл. Попробованы методы: {methods_str}", None
        
    except (OSError, PermissionError, ValueError, TypeError, AttributeError) as e:
        logger.error(f"Ошибка при конвертации DOCX в PDF {file_path}: {e}", exc_info=True)
        return False, f"Ошибка конвертации: {str(e)}", None
    except (KeyError, IndexError) as e:
        logger.error(f"Ошибка доступа к данным при конвертации DOCX в PDF {file_path}: {e}", exc_info=True)
        return False, f"Ошибка доступа к данным: {str(e)}", None
    except (MemoryError, RecursionError) as e:
        logger.error(f"Ошибка памяти/рекурсии при конвертации DOCX в PDF {file_path}: {e}", exc_info=True)
        return False, f"Ошибка памяти/рекурсии: {str(e)}", None
    # Финальный catch для неожиданных исключений (критично для стабильности)
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        logger.error(f"Критическая ошибка при конвертации DOCX в PDF {file_path}: {e}", exc_info=True)
        return False, f"Неожиданная ошибка конвертации: {str(e)}", None


def convert_pdf_to_docx(
    file_path: str,
    output_path: str,
    win32com,
    comtypes,
    check_word_installed,
    cleanup_word_document,
    cleanup_word_application
) -> Tuple[bool, str, Optional[str]]:
    """Конвертация PDF в DOCX через Microsoft Word (COM).
    
    Args:
        file_path: Путь к исходному PDF файлу
        output_path: Путь для сохранения DOCX
        win32com: Модуль win32com (или None)
        comtypes: Модуль comtypes (или None)
        check_word_installed: Функция проверки установки Word
        cleanup_word_document: Функция очистки документа Word
        cleanup_word_application: Функция очистки приложения Word
        
    Returns:
        Tuple[успех, сообщение, путь к выходному файлу]
    """
    if not sys.platform == 'win32':
        return False, "Конвертация через Word доступна только на Windows", None
    
    word = None
    doc = None
    com_initialized = False
    pythoncom_module = None
    
    try:
        # Проверяем доступность COM
        if win32com:
            try:
                import win32com.client
                import pythoncom
                pythoncom_module = pythoncom
                pythoncom.CoInitialize()
                com_initialized = True
                word = win32com.client.Dispatch("Word.Application")
            except (OSError, RuntimeError, AttributeError, TypeError) as e:
                logger.debug(f"Ошибка выполнения при использовании win32com: {e}")
                word = None
            except (ValueError, KeyError, IndexError) as e:
                logger.debug(f"Ошибка данных при использовании win32com: {e}")
                word = None
            except (MemoryError, RecursionError) as e:
                logger.debug(f"Ошибка памяти/рекурсии при использовании win32com: {e}")
                word = None
            # Финальный catch для неожиданных исключений (критично для стабильности COM)
            except BaseException as e:
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                logger.debug(f"Критическая ошибка при использовании win32com: {e}")
                word = None
        
        if not word and comtypes:
            try:
                from comtypes.client import CreateObject
                word = CreateObject("Word.Application")
            except (OSError, RuntimeError, AttributeError, TypeError) as e:
                logger.debug(f"Ошибка выполнения при использовании comtypes: {e}")
                word = None
            except (ValueError, KeyError, IndexError) as e:
                logger.debug(f"Ошибка данных при использовании comtypes: {e}")
                word = None
            except (MemoryError, RecursionError) as e:
                logger.debug(f"Ошибка памяти/рекурсии при использовании comtypes: {e}")
                word = None
            # Финальный catch для неожиданных исключений (критично для стабильности COM)
            except BaseException as e:
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                logger.debug(f"Критическая ошибка при использовании comtypes: {e}")
                word = None
        
        if not word:
            return False, "Microsoft Word недоступен через COM", None
        
        # Проверяем, установлен ли Word
        word_installed, _ = check_word_installed()
        if not word_installed:
            return False, "Microsoft Word не установлен", None
        
        # Настраиваем Word
        word.Visible = False
        word.DisplayAlerts = 0
        
        # Нормализуем пути
        pdf_path = os.path.abspath(file_path)
        docx_path = os.path.abspath(output_path)
        
        # Убеждаемся, что директория существует (с поддержкой Unicode)
        output_dir = os.path.dirname(docx_path)
        if output_dir and not os.path.isdir(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Конвертируем PDF в DOCX через Word: {pdf_path} -> {docx_path}")
        
        # Открываем PDF файл в Word
        try:
            doc = word.Documents.Open(
                FileName=pdf_path,
                ReadOnly=True,
                ConfirmConversions=True,
                AddToRecentFiles=False
            )
        except (OSError, RuntimeError, AttributeError, PermissionError) as e:
            error_msg = str(e)
            logger.error(f"Ошибка выполнения при открытии PDF в Word: {error_msg}")
            return False, f"Word не может открыть PDF файл: {error_msg}", None
        except (ValueError, TypeError, KeyError, IndexError) as e:
            error_msg = str(e)
            logger.error(f"Ошибка данных при открытии PDF в Word: {error_msg}")
            return False, f"Word не может открыть PDF файл: {error_msg}", None
        except (MemoryError, RecursionError) as e:
            error_msg = str(e)
            logger.error(f"Ошибка памяти/рекурсии при открытии PDF в Word: {error_msg}")
            return False, f"Word не может открыть PDF файл: {error_msg}", None
        # Финальный catch для неожиданных исключений (критично для стабильности COM)
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            error_msg = str(e)
            logger.error(f"Критическая ошибка при открытии PDF в Word: {error_msg}", exc_info=True)
            return False, f"Word не может открыть PDF файл: {error_msg}", None
        
        try:
            # Сохраняем как DOCX (FileFormat=16 для DOCX)
            doc.SaveAs(FileName=docx_path, FileFormat=16)
            logger.info(f"PDF успешно конвертирован в DOCX через Word: {docx_path}")
            
            # Проверяем существование файла с поддержкой Unicode
            if _check_file_exists_unicode(docx_path):
                return True, "PDF успешно конвертирован в DOCX через Word", docx_path
            else:
                return False, "Файл DOCX не был создан", None
        except (OSError, RuntimeError, AttributeError, PermissionError) as e:
            error_msg = str(e)
            # Логируем только реальные ошибки (не общие COM-исключения)
            if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.'):
                logger.error(f"Ошибка выполнения при сохранении DOCX: {error_msg}")
            return False, f"Ошибка при сохранении DOCX: {error_msg if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.') else 'Ошибка сохранения'}", None
        except (ValueError, TypeError, KeyError, IndexError) as e:
            error_msg = str(e)
            # Логируем только реальные ошибки (не общие COM-исключения)
            if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.'):
                logger.error(f"Ошибка данных при сохранении DOCX: {error_msg}")
            return False, f"Ошибка данных при сохранении DOCX: {error_msg if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.') else 'Ошибка сохранения'}", None
        except (MemoryError, RecursionError) as e:
            error_msg = str(e)
            # Логируем только реальные ошибки (не общие COM-исключения)
            if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.'):
                logger.error(f"Ошибка памяти/рекурсии при сохранении DOCX: {error_msg}", exc_info=True)
            return False, f"Ошибка памяти/рекурсии при сохранении DOCX: {error_msg if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.') else 'Ошибка сохранения'}", None
        # Финальный catch для неожиданных исключений (критично для стабильности COM)
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            error_msg = str(e)
            # Логируем только реальные ошибки (не общие COM-исключения)
            if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.'):
                logger.error(f"Критическая ошибка при сохранении DOCX: {error_msg}", exc_info=True)
            return False, f"Критическая ошибка при сохранении DOCX: {error_msg if error_msg and len(error_msg) > 10 and not error_msg.startswith('Open.') else 'Ошибка сохранения'}", None
        finally:
            # Закрываем документ
            if doc:
                try:
                    if hasattr(doc, 'Name'):
                        doc.Close(SaveChanges=False)
                except:
                    pass
                cleanup_word_document(doc)
                doc = None
            
            # Закрываем приложение
            if word:
                cleanup_word_application(word)
                word = None
            
            # Освобождаем COM
            if com_initialized and pythoncom_module:
                pythoncom_module.CoUninitialize()
                com_initialized = False
                
    except (OSError, RuntimeError, AttributeError, PermissionError) as e:
        logger.error(f"Ошибка выполнения при конвертации PDF в DOCX через Word {file_path}: {e}", exc_info=True)
        error_msg = str(e)
        if "Word.Application" in error_msg or "COM" in error_msg:
            return False, "Не удалось использовать Microsoft Word. Убедитесь, что Word установлен и доступен.", None
        return False, f"Ошибка: {error_msg}", None
    except (ValueError, TypeError, KeyError, IndexError) as e:
        logger.error(f"Ошибка данных при конвертации PDF в DOCX через Word {file_path}: {e}", exc_info=True)
        error_msg = str(e)
        if "Word.Application" in error_msg or "COM" in error_msg:
            return False, "Не удалось использовать Microsoft Word. Убедитесь, что Word установлен и доступен.", None
        return False, f"Ошибка данных: {error_msg}", None
    except (MemoryError, RecursionError) as e:
        logger.error(f"Ошибка памяти/рекурсии при конвертации PDF в DOCX через Word {file_path}: {e}", exc_info=True)
        error_msg = str(e)
        if "Word.Application" in error_msg or "COM" in error_msg:
            return False, "Не удалось использовать Microsoft Word. Убедитесь, что Word установлен и доступен.", None
        return False, f"Ошибка памяти/рекурсии: {error_msg}", None
    # Финальный catch для неожиданных исключений (критично для стабильности COM)
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        logger.error(f"Критическая ошибка при конвертации PDF в DOCX через Word {file_path}: {e}", exc_info=True)
        error_msg = str(e)
        if "Word.Application" in error_msg or "COM" in error_msg:
            return False, "Не удалось использовать Microsoft Word. Убедитесь, что Word установлен и доступен.", None
        return False, f"Неожиданная ошибка: {error_msg}", None
    finally:
        # Убеждаемся, что все закрыто
        if doc:
            try:
                cleanup_word_document(doc)
            except:
                pass
        if word:
            try:
                cleanup_word_application(word)
            except:
                pass
        if com_initialized and pythoncom_module:
            try:
                pythoncom_module.CoUninitialize()
            except:
                pass
    
    return False, "Не удалось конвертировать PDF в DOCX", None


def convert_document(
    file_path: str,
    target_ext: str,
    output_path: str,
    win32com,
    comtypes,
    check_word_installed,
    create_word_application,
    convert_docx_with_word_com,
    convert_with_libreoffice
) -> Tuple[bool, str, Optional[str]]:
    """Универсальная конвертация документов.
    
    Args:
        file_path: Путь к исходному файлу
        target_ext: Целевое расширение
        output_path: Путь для сохранения
        win32com: Модуль win32com (или None)
        comtypes: Модуль comtypes (или None)
        check_word_installed: Функция проверки установки Word
        create_word_application: Функция создания Word приложения
        convert_docx_with_word_com: Функция конвертации через Word COM
        convert_with_libreoffice: Функция конвертации через LibreOffice
        
    Returns:
        Tuple[успех, сообщение, путь к выходному файлу]
    """
    source_ext = os.path.splitext(file_path)[1].lower()
    
    # Определяем формат для Word
    word_format_map = {
        '.pdf': 17,  # PDF
        '.docx': 16,  # DOCX
        '.doc': 0,   # DOC
        '.rtf': 6,   # RTF
        '.txt': 2,   # TXT
        '.html': 8,  # HTML
        '.htm': 8,   # HTML
        '.odt': 23,  # ODT
    }
    
    word_format = word_format_map.get(target_ext.lower())
    
    # Пробуем через Word (если доступен и формат поддерживается)
    # Word поддерживает конвертацию из DOCX, DOC, RTF, TXT, HTML, ODT
    if sys.platform == 'win32' and (win32com or comtypes) and word_format is not None:
        if source_ext in ('.docx', '.doc', '.rtf', '.txt', '.html', '.htm', '.odt'):
            result = convert_docx_with_word_com(file_path, output_path, word_format)
            if result[0]:
                return result
    
    # Пробуем через LibreOffice как альтернативу
    result = convert_with_libreoffice(file_path, output_path, target_ext)
    if result[0]:
        return result
    
    # Если оба метода не сработали, возвращаем ошибку
    error_msg = f"Не удалось конвертировать {source_ext} в {target_ext}"
    if word_format is not None:
        error_msg += ". LibreOffice и Microsoft Word недоступны или не поддерживают этот формат"
    else:
        error_msg += ". LibreOffice недоступен"
    
    return False, error_msg, None


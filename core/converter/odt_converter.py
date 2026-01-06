"""Модуль конвертации ODT файлов.

Содержит функции для конвертации ODT файлов:
- Конвертация через Microsoft Word
- Конвертация без LibreOffice (fallback методы)
"""

import logging
import os
import sys
import zipfile
import xml.etree.ElementTree as ET
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def convert_odt_with_word(
    file_path: str,
    output_path: str,
    target_ext: str,
    win32com=None,
    comtypes=None,
    check_word_installed=None,
    create_word_application=None,
    cleanup_word_document=None,
    cleanup_word_application=None
) -> Tuple[bool, str, Optional[str]]:
    """Конвертация ODT файлов через Microsoft Word.
    
    Args:
        file_path: Путь к исходному ODT файлу
        output_path: Путь для сохранения
        target_ext: Целевое расширение (с точкой)
        win32com: Модуль win32com (опционально)
        comtypes: Модуль comtypes (опционально)
        check_word_installed: Функция проверки установки Word
        create_word_application: Функция создания Word приложения
        cleanup_word_document: Функция очистки документа Word
        cleanup_word_application: Функция очистки приложения Word
        
    Returns:
        Кортеж (успех, сообщение, путь к выходному файлу)
    """
    if sys.platform != 'win32':
        return False, "Microsoft Word доступен только на Windows", None
    
    if not win32com and not comtypes:
        return False, "COM утилиты недоступны", None
    
    com_client = None
    if win32com:
        com_client = win32com
    elif comtypes:
        com_client = comtypes
    else:
        return False, "COM клиент недоступен (win32com или comtypes не установлен)", None
    
    word_app = None
    doc = None
    try:
        word_installed, install_msg = check_word_installed()
        if not word_installed:
            return False, install_msg, None
        
        word_app, error_msg = create_word_application(com_client)
        if not word_app:
            return False, error_msg or "Не удалось создать Word приложение", None
        
        # Настраиваем Word
        word_app.Visible = False
        word_app.DisplayAlerts = 0
        
        # Определяем формат сохранения
        format_map = {
            '.pdf': 17,      # PDF
            '.docx': 16,      # DOCX
            '.doc': 0,        # DOC
            '.rtf': 6,        # RTF
            '.txt': 2,        # TXT
            '.html': 10,      # HTML
            '.htm': 10        # HTML
        }
        
        file_format = format_map.get(target_ext.lower())
        if file_format is None:
            return False, f"Неподдерживаемый целевой формат для Word: {target_ext}", None
        
        # Открываем ODT файл
        doc_path = os.path.abspath(file_path)
        logger.info(f"Открываем ODT файл в Word: {doc_path}")
        
        try:
            doc = word_app.Documents.Open(
                FileName=doc_path,
                ReadOnly=True,
                ConfirmConversions=False,
                AddToRecentFiles=False
            )
            logger.debug("ODT файл открыт успешно в Word")
        except (OSError, RuntimeError, AttributeError, TypeError) as open_error:
            error_msg = str(open_error)
            logger.error(f"Ошибка при открытии ODT файла в Word: {error_msg}")
            return False, f"Не удалось открыть ODT файл в Word: {error_msg[:200]}", None
        except (ValueError, TypeError) as open_error:
            error_msg = str(open_error)
            logger.error(f"Ошибка типа/значения при открытии ODT файла в Word: {error_msg}")
            return False, f"Не удалось открыть ODT файл в Word: {error_msg[:200]}", None
        except (KeyError, IndexError) as open_error:
            error_msg = str(open_error)
            logger.error(f"Ошибка доступа к данным при открытии ODT файла в Word: {error_msg}")
            return False, f"Не удалось открыть ODT файл в Word: {error_msg[:200]}", None
        except (MemoryError, RecursionError) as open_error:
            error_msg = str(open_error)
            logger.error(f"Ошибка памяти/рекурсии при открытии ODT файла в Word: {error_msg}")
            return False, f"Не удалось открыть ODT файл в Word: {error_msg[:200]}", None
        # Финальный catch для неожиданных исключений (критично для стабильности COM)
        except BaseException as open_error:
            if isinstance(open_error, (KeyboardInterrupt, SystemExit)):
                raise
            error_msg = str(open_error)
            logger.error(f"Критическая ошибка при открытии ODT файла в Word: {error_msg}", exc_info=True)
            return False, f"Не удалось открыть ODT файл в Word: {error_msg[:200]}", None
        
        # Сохраняем в нужном формате
        output_path_abs = os.path.abspath(output_path)
        output_dir = os.path.dirname(output_path_abs)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Сохраняем как {target_ext}: {output_path_abs}")
        try:
            if doc is None:
                return False, "Документ не был открыт", None
            
            if not hasattr(doc, 'SaveAs'):
                return False, "Документ не поддерживает SaveAs", None
            
            doc.SaveAs(FileName=output_path_abs, FileFormat=file_format)
            logger.debug(f"Файл сохранен как {target_ext}")
        except (OSError, RuntimeError, AttributeError, PermissionError) as save_error:
            error_msg = str(save_error)
            logger.error(f"Ошибка при сохранении файла: {error_msg}")
            if os.path.exists(output_path_abs):
                try:
                    os.remove(output_path_abs)
                    doc.SaveAs(FileName=output_path_abs, FileFormat=file_format)
                except (OSError, PermissionError, RuntimeError) as retry_error:
                    return False, f"Не удалось сохранить файл: {retry_error}", None
                except (ValueError, TypeError) as retry_error:
                    return False, f"Ошибка типа/значения при повторной попытке сохранения: {retry_error}", None
                except (KeyError, IndexError) as retry_error:
                    return False, f"Ошибка доступа к данным при повторной попытке сохранения: {retry_error}", None
                except (MemoryError, RecursionError) as retry_error:
                    return False, f"Ошибка памяти/рекурсии при повторной попытке сохранения: {retry_error}", None
                # Финальный catch для неожиданных исключений (критично для стабильности COM)
                except BaseException as retry_error:
                    if isinstance(retry_error, (KeyboardInterrupt, SystemExit)):
                        raise
                    return False, f"Критическая ошибка при повторной попытке сохранения: {retry_error}", None
        except (ValueError, TypeError) as save_error:
            error_msg = str(save_error)
            logger.error(f"Ошибка типа/значения при сохранении файла: {error_msg}")
            return False, f"Ошибка при сохранении файла: {error_msg[:200]}", None
        except (KeyError, IndexError) as save_error:
            error_msg = str(save_error)
            logger.error(f"Ошибка доступа к данным при сохранении файла: {error_msg}")
            return False, f"Ошибка доступа к данным при сохранении файла: {error_msg[:200]}", None
        except (MemoryError, RecursionError) as save_error:
            error_msg = str(save_error)
            logger.error(f"Ошибка памяти/рекурсии при сохранении файла: {error_msg}")
            return False, f"Ошибка памяти/рекурсии при сохранении файла: {error_msg[:200]}", None
        # Финальный catch для неожиданных исключений (критично для стабильности COM)
        except BaseException as save_error:
            if isinstance(save_error, (KeyboardInterrupt, SystemExit)):
                raise
            error_msg = str(save_error)
            logger.error(f"Критическая ошибка при сохранении файла: {error_msg}", exc_info=True)
            return False, f"Ошибка при сохранении файла: {error_msg[:200]}", None
        
        return True, f"ODT файл успешно конвертирован через Microsoft Word в {target_ext}", output_path_abs
        
    except (OSError, RuntimeError, AttributeError, PermissionError) as e:
        logger.error(f"Ошибка выполнения при конвертации ODT через Word {file_path}: {e}", exc_info=True)
        return False, f"Ошибка: {str(e)}", None
    except (ValueError, TypeError, KeyError, IndexError) as e:
        logger.error(f"Ошибка данных при конвертации ODT через Word {file_path}: {e}", exc_info=True)
        return False, f"Ошибка данных: {str(e)}", None
    except (MemoryError, RecursionError) as e:
        logger.error(f"Ошибка памяти/рекурсии при конвертации ODT через Word {file_path}: {e}", exc_info=True)
        return False, f"Ошибка памяти/рекурсии: {str(e)}", None
    # Финальный catch для неожиданных исключений (критично для стабильности COM)
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        logger.error(f"Критическая ошибка при конвертации ODT через Word {file_path}: {e}", exc_info=True)
        return False, f"Неожиданная ошибка: {str(e)}", None
    finally:
        cleanup_word_document(doc)
        cleanup_word_application(word_app)


def convert_odt_without_libreoffice(
    file_path: str,
    output_path: str,
    target_ext: str,
    win32com=None,
    comtypes=None,
    convert_odt_with_word=None,
    docx_module=None,
    docx_available: bool = False
) -> Tuple[bool, str, Optional[str]]:
    """Конвертация ODT файлов без LibreOffice (fallback методы).
    
    Args:
        file_path: Путь к исходному ODT файлу
        output_path: Путь для сохранения
        target_ext: Целевое расширение (с точкой)
        win32com: Модуль win32com (опционально)
        comtypes: Модуль comtypes (опционально)
        convert_odt_with_word: Функция конвертации через Word (опционально)
        docx_module: Модуль python-docx (опционально)
        docx_available: Доступен ли python-docx
        
    Returns:
        Кортеж (успех, сообщение, путь к выходному файлу)
    """
    # Сначала пробуем через Microsoft Word (если доступен)
    if sys.platform == 'win32' and (win32com or comtypes) and convert_odt_with_word:
        word_result = convert_odt_with_word(file_path, output_path, target_ext)
        if word_result[0]:
            return word_result
    
    # Если Word не доступен или не удалось, пробуем другие методы
    try:
        # ODT файлы - это ZIP архивы с XML файлами
        if target_ext == '.txt':
            # Извлекаем текст из content.xml
            try:
                with zipfile.ZipFile(file_path, 'r') as odt_zip:
                    if 'content.xml' in odt_zip.namelist():
                        content_xml = odt_zip.read('content.xml').decode('utf-8')
                        # Парсим XML и извлекаем текст
                        root = ET.fromstring(content_xml)
                        # Находим все текстовые узлы
                        text_content = []
                        for elem in root.iter():
                            if elem.text:
                                text_content.append(elem.text)
                            if elem.tail:
                                text_content.append(elem.tail)
                        
                        text = '\n'.join(text_content).strip()
                        if text:
                            with open(output_path, 'w', encoding='utf-8') as f:
                                f.write(text)
                            return True, "Текст успешно извлечен из ODT файла", output_path
            except (OSError, PermissionError, ValueError, TypeError, KeyError) as e:
                logger.debug(f"Ошибка выполнения при извлечении текста из ODT: {e}")
                return False, f"Не удалось извлечь текст: {str(e)}", None
            except (IndexError, AttributeError) as e:
                logger.debug(f"Ошибка доступа к данным при извлечении текста из ODT: {e}")
                return False, f"Ошибка доступа к данным: {str(e)}", None
            except (MemoryError, RecursionError) as e:
                logger.debug(f"Ошибка памяти/рекурсии при извлечении текста из ODT: {e}")
                return False, f"Ошибка памяти/рекурсии: {str(e)}", None
            # Финальный catch для неожиданных исключений (критично для стабильности)
            except BaseException as e:
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                logger.debug(f"Критическая ошибка извлечения текста из ODT: {e}", exc_info=True)
                return False, f"Не удалось извлечь текст: {str(e)}", None
        
        elif target_ext == '.html':
            # Конвертируем в HTML через извлечение текста
            try:
                with zipfile.ZipFile(file_path, 'r') as odt_zip:
                    if 'content.xml' in odt_zip.namelist():
                        content_xml = odt_zip.read('content.xml').decode('utf-8')
                        root = ET.fromstring(content_xml)
                        
                        # Конвертация в HTML
                        html_content = ['<html><head><meta charset="utf-8"></head><body>']
                        
                        # Извлекаем параграфы
                        for para in root.findall('.//{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p'):
                            text_parts = []
                            for elem in para.iter():
                                if elem.text:
                                    text_parts.append(elem.text)
                                if elem.tail:
                                    text_parts.append(elem.tail)
                            if text_parts:
                                html_content.append(f'<p>{"".join(text_parts)}</p>')
                        
                        html_content.append('</body></html>')
                        
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write('\n'.join(html_content))
                        return True, "ODT файл конвертирован в HTML", output_path
            except (OSError, PermissionError, ValueError, TypeError, KeyError) as e:
                logger.debug(f"Ошибка выполнения при конвертации ODT в HTML: {e}")
                return False, f"Не удалось конвертировать в HTML: {str(e)}", None
            except (IndexError, AttributeError) as e:
                logger.debug(f"Ошибка доступа к данным при конвертации ODT в HTML: {e}")
                return False, f"Ошибка доступа к данным: {str(e)}", None
            except (MemoryError, RecursionError) as e:
                logger.debug(f"Ошибка памяти/рекурсии при конвертации ODT в HTML: {e}")
                return False, f"Ошибка памяти/рекурсии: {str(e)}", None
            # Финальный catch для неожиданных исключений (критично для стабильности)
            except BaseException as e:
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                logger.debug(f"Критическая ошибка конвертации ODT в HTML: {e}", exc_info=True)
                return False, f"Не удалось конвертировать в HTML: {str(e)}", None
        
        elif target_ext == '.docx' and docx_available and docx_module:
            # Пробуем конвертировать через python-docx
            try:
                # Сначала извлекаем текст
                with zipfile.ZipFile(file_path, 'r') as odt_zip:
                    if 'content.xml' in odt_zip.namelist():
                        content_xml = odt_zip.read('content.xml').decode('utf-8')
                        root = ET.fromstring(content_xml)
                        
                        # Создаем новый DOCX документ
                        doc = docx_module.Document()
                        
                        # Извлекаем параграфы
                        for para in root.findall('.//{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p'):
                            text_parts = []
                            for elem in para.iter():
                                if elem.text:
                                    text_parts.append(elem.text)
                                if elem.tail:
                                    text_parts.append(elem.tail)
                            if text_parts:
                                doc.add_paragraph(''.join(text_parts))
                        
                        doc.save(output_path)
                        return True, "ODT файл конвертирован в DOCX (базовая конвертация)", output_path
            except (OSError, PermissionError, ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Ошибка выполнения при конвертации ODT в DOCX: {e}")
                return False, f"Не удалось конвертировать в DOCX: {str(e)}", None
            except (KeyError, IndexError) as e:
                logger.debug(f"Ошибка доступа к данным при конвертации ODT в DOCX: {e}")
                return False, f"Ошибка доступа к данным: {str(e)}", None
            except (MemoryError, RecursionError) as e:
                logger.debug(f"Ошибка памяти/рекурсии при конвертации ODT в DOCX: {e}")
                return False, f"Ошибка памяти/рекурсии: {str(e)}", None
            # Финальный catch для неожиданных исключений (критично для стабильности)
            except BaseException as e:
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                logger.debug(f"Критическая ошибка конвертации ODT в DOCX: {e}", exc_info=True)
                return False, f"Не удалось конвертировать в DOCX: {str(e)}", None
        
        return False, f"Конвертация ODT в {target_ext} без LibreOffice не поддерживается", None
        
    except (OSError, PermissionError, ValueError, TypeError, AttributeError) as e:
        logger.error(f"Ошибка выполнения при конвертации ODT без LibreOffice {file_path}: {e}", exc_info=True)
        return False, f"Ошибка: {str(e)}", None
    except (KeyError, IndexError) as e:
        logger.error(f"Ошибка доступа к данным при конвертации ODT без LibreOffice {file_path}: {e}", exc_info=True)
        return False, f"Ошибка доступа к данным: {str(e)}", None
    except (MemoryError, RecursionError) as e:
        logger.error(f"Ошибка памяти/рекурсии при конвертации ODT без LibreOffice {file_path}: {e}", exc_info=True)
        return False, f"Ошибка памяти/рекурсии: {str(e)}", None
    # Финальный catch для неожиданных исключений (критично для стабильности)
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        logger.error(f"Критическая ошибка при конвертации ODT без LibreOffice {file_path}: {e}", exc_info=True)
        return False, f"Неожиданная ошибка: {str(e)}", None


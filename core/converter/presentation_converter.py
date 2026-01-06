"""Модуль конвертации презентаций.

Содержит функции для конвертации презентаций:
- PPTX/PPT в PDF
- PPTX/PPT в ODP
- ODP в PPTX/PPT/PDF
- Через LibreOffice или PowerPoint COM
"""

import logging
import os
import sys
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Импорт утилит безопасности
try:
    from utils.security_utils import (
        sanitize_path_for_subprocess,
        validate_path_for_subprocess,
        _check_file_exists_unicode
    )
except ImportError:
    # Fallback если утилиты недоступны
    def sanitize_path_for_subprocess(path: str, check_existence: bool = True) -> Optional[str]:
        try:
            return os.path.abspath(os.path.normpath(path))
        except (OSError, ValueError):
            return None
    
    def validate_path_for_subprocess(path: str, must_exist: bool = True, must_be_file: bool = False) -> Tuple[bool, Optional[str]]:
        try:
            if must_exist and not os.path.exists(path):
                return False, "Путь не существует"
            if must_be_file and not os.path.isfile(path):
                return False, "Путь не является файлом"
            return True, None
        except (OSError, UnicodeEncodeError, UnicodeDecodeError):
            return False, "Ошибка проверки пути"
    
    def _check_file_exists_unicode(path: str) -> bool:
        try:
            return os.path.exists(path) and os.path.isfile(path)
        except (OSError, UnicodeEncodeError, UnicodeDecodeError):
            try:
                with open(path, 'rb') as f:
                    return True
            except:
                return False


def convert_pptx_with_powerpoint_com(
    file_path: str,
    output_path: str,
    file_format: int,
    win32com,
    comtypes
) -> Tuple[bool, str, Optional[str]]:
    """Конвертация PPTX/PPT в другой формат через PowerPoint COM.
    
    Args:
        file_path: Путь к исходному PPTX или PPT файлу
        output_path: Путь для сохранения результата
        file_format: Формат для сохранения (32 = PDF, 24 = PPTX, и т.д.)
        win32com: Модуль win32com (или None)
        comtypes: Модуль comtypes (или None)
        
    Returns:
        Tuple[успех, сообщение, путь к выходному файлу]
    """
    if not sys.platform == 'win32':
        return False, "Конвертация через PowerPoint доступна только на Windows", None
    
    powerpoint = None
    presentation = None
    pythoncom_module = None
    com_initialized = False
    
    try:
        # Проверяем доступность COM
        if win32com:
            try:
                import win32com.client
                import pythoncom
                pythoncom_module = pythoncom
                pythoncom.CoInitialize()
                com_initialized = True
                powerpoint = win32com.client.Dispatch("PowerPoint.Application")
            except (OSError, RuntimeError, AttributeError, TypeError) as e:
                logger.debug(f"Ошибка выполнения при использовании win32com для PowerPoint: {e}")
                powerpoint = None
            except (ValueError, KeyError, IndexError) as e:
                logger.debug(f"Ошибка данных при использовании win32com для PowerPoint: {e}")
                powerpoint = None
            except (MemoryError, RecursionError) as e:
                logger.debug(f"Ошибка памяти/рекурсии при использовании win32com для PowerPoint: {e}")
                powerpoint = None
            except BaseException as e:
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                logger.debug(f"Критическая ошибка при использовании win32com для PowerPoint: {e}")
                powerpoint = None
        
        if not powerpoint and comtypes:
            try:
                from comtypes.client import CreateObject
                powerpoint = CreateObject("PowerPoint.Application")
            except (OSError, RuntimeError, AttributeError, TypeError) as e:
                logger.debug(f"Ошибка выполнения при использовании comtypes для PowerPoint: {e}")
                powerpoint = None
            except (ValueError, KeyError, IndexError) as e:
                logger.debug(f"Ошибка данных при использовании comtypes для PowerPoint: {e}")
                powerpoint = None
            except (MemoryError, RecursionError) as e:
                logger.debug(f"Ошибка памяти/рекурсии при использовании comtypes для PowerPoint: {e}")
                powerpoint = None
            except BaseException as e:
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
                logger.debug(f"Критическая ошибка при использовании comtypes для PowerPoint: {e}")
                powerpoint = None
        
        if not powerpoint:
            return False, "Microsoft PowerPoint недоступен через COM", None
        
        # Настраиваем PowerPoint
        powerpoint.Visible = False
        powerpoint.DisplayAlerts = 0  # ppAlertsNone
        
        # Нормализуем пути
        ppt_path = os.path.abspath(file_path)
        output_file_path = os.path.abspath(output_path)
        
        # Убеждаемся, что директория существует
        output_dir = os.path.dirname(output_file_path)
        if output_dir and not os.path.isdir(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Конвертируем презентацию через PowerPoint: {ppt_path} -> {output_file_path}")
        
        # Открываем презентацию
        try:
            presentation = powerpoint.Presentations.Open(
                FileName=ppt_path,
                ReadOnly=True,
                WithWindow=False
            )
        except (OSError, RuntimeError, AttributeError, PermissionError) as e:
            error_msg = str(e)
            logger.error(f"Ошибка выполнения при открытии презентации в PowerPoint: {error_msg}")
            return False, f"PowerPoint не может открыть файл: {error_msg}", None
        except (ValueError, TypeError, KeyError, IndexError) as e:
            error_msg = str(e)
            logger.error(f"Ошибка данных при открытии презентации в PowerPoint: {error_msg}")
            return False, f"PowerPoint не может открыть файл: {error_msg}", None
        except (MemoryError, RecursionError) as e:
            error_msg = str(e)
            logger.error(f"Ошибка памяти/рекурсии при открытии презентации в PowerPoint: {error_msg}")
            return False, f"PowerPoint не может открыть файл: {error_msg}", None
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            error_msg = str(e)
            logger.error(f"Критическая ошибка при открытии презентации в PowerPoint: {error_msg}", exc_info=True)
            return False, f"PowerPoint не может открыть файл: {error_msg}", None
        
        try:
            # Сохраняем в нужном формате
            # Форматы: 32 = PDF, 24 = PPTX, 1 = PPT, 35 = ODP
            presentation.SaveAs(FileName=output_file_path, FileFormat=file_format)
            logger.info(f"Презентация успешно конвертирована через PowerPoint: {output_file_path}")
            
            # Проверяем существование файла с поддержкой Unicode
            if _check_file_exists_unicode(output_file_path):
                return True, "Презентация успешно конвертирована через PowerPoint", output_file_path
            else:
                return False, "Файл не был создан", None
        except (OSError, RuntimeError, AttributeError, PermissionError) as e:
            error_msg = str(e)
            logger.error(f"Ошибка выполнения при сохранении презентации: {error_msg}")
            return False, f"Ошибка при сохранении: {error_msg}", None
        except (ValueError, TypeError, KeyError, IndexError) as e:
            error_msg = str(e)
            logger.error(f"Ошибка данных при сохранении презентации: {error_msg}")
            return False, f"Ошибка данных при сохранении: {error_msg}", None
        except (MemoryError, RecursionError) as e:
            error_msg = str(e)
            logger.error(f"Ошибка памяти/рекурсии при сохранении презентации: {error_msg}", exc_info=True)
            return False, f"Ошибка памяти/рекурсии при сохранении: {error_msg}", None
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            error_msg = str(e)
            logger.error(f"Критическая ошибка при сохранении презентации: {error_msg}", exc_info=True)
            return False, f"Критическая ошибка при сохранении: {error_msg}", None
        finally:
            # Закрываем презентацию
            if presentation:
                try:
                    presentation.Close()
                except:
                    pass
                presentation = None
            
            # Закрываем приложение
            if powerpoint:
                try:
                    powerpoint.Quit()
                except:
                    pass
                powerpoint = None
            
            # Освобождаем COM
            if com_initialized and pythoncom_module:
                pythoncom_module.CoUninitialize()
                com_initialized = False
                
    except (OSError, RuntimeError, AttributeError, PermissionError) as e:
        logger.error(f"Ошибка выполнения при конвертации презентации через PowerPoint {file_path}: {e}", exc_info=True)
        error_msg = str(e)
        if "PowerPoint.Application" in error_msg or "COM" in error_msg:
            return False, "Не удалось использовать Microsoft PowerPoint. Убедитесь, что PowerPoint установлен и доступен.", None
        return False, f"Ошибка: {error_msg}", None
    except (ValueError, TypeError, KeyError, IndexError) as e:
        logger.error(f"Ошибка данных при конвертации презентации через PowerPoint {file_path}: {e}", exc_info=True)
        error_msg = str(e)
        if "PowerPoint.Application" in error_msg or "COM" in error_msg:
            return False, "Не удалось использовать Microsoft PowerPoint. Убедитесь, что PowerPoint установлен и доступен.", None
        return False, f"Ошибка данных: {error_msg}", None
    except (MemoryError, RecursionError) as e:
        logger.error(f"Ошибка памяти/рекурсии при конвертации презентации через PowerPoint {file_path}: {e}", exc_info=True)
        error_msg = str(e)
        if "PowerPoint.Application" in error_msg or "COM" in error_msg:
            return False, "Не удалось использовать Microsoft PowerPoint. Убедитесь, что PowerPoint установлен и доступен.", None
        return False, f"Ошибка памяти/рекурсии: {error_msg}", None
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        logger.error(f"Критическая ошибка при конвертации презентации через PowerPoint {file_path}: {e}", exc_info=True)
        error_msg = str(e)
        if "PowerPoint.Application" in error_msg or "COM" in error_msg:
            return False, "Не удалось использовать Microsoft PowerPoint. Убедитесь, что PowerPoint установлен и доступен.", None
        return False, f"Неожиданная ошибка: {error_msg}", None
    finally:
        # Убеждаемся, что все закрыто
        if presentation:
            try:
                presentation.Close()
            except:
                pass
        if powerpoint:
            try:
                powerpoint.Quit()
            except:
                pass
        if com_initialized and pythoncom_module:
            try:
                pythoncom_module.CoUninitialize()
            except:
                pass
    
    return False, "Не удалось конвертировать презентацию", None


def convert_presentation(
    file_path: str,
    output_path: str,
    target_ext: str,
    win32com,
    comtypes,
    convert_with_libreoffice
) -> Tuple[bool, str, Optional[str]]:
    """Универсальная конвертация презентаций.
    
    Args:
        file_path: Путь к исходному файлу
        target_ext: Целевое расширение
        output_path: Путь для сохранения
        win32com: Модуль win32com (или None)
        comtypes: Модуль comtypes (или None)
        convert_with_libreoffice: Функция конвертации через LibreOffice
        
    Returns:
        Tuple[успех, сообщение, путь к выходному файлу]
    """
    source_ext = os.path.splitext(file_path)[1].lower()
    
    # Определяем формат для PowerPoint
    # Форматы PowerPoint: 32 = PDF, 24 = PPTX, 1 = PPT, 35 = ODP
    powerpoint_format_map = {
        '.pdf': 32,   # PDF
        '.pptx': 24,  # PPTX
        '.ppt': 1,    # PPT
        '.odp': 35,   # ODP
    }
    
    powerpoint_format = powerpoint_format_map.get(target_ext.lower())
    
    # Пробуем через PowerPoint COM (если доступен и формат поддерживается)
    if sys.platform == 'win32' and (win32com or comtypes) and powerpoint_format is not None:
        if source_ext in ('.pptx', '.ppt'):
            result = convert_pptx_with_powerpoint_com(
                file_path, output_path, powerpoint_format,
                win32com, comtypes
            )
            if result[0]:
                return result
    
    # Пробуем через LibreOffice (универсальный метод)
    result = convert_with_libreoffice(file_path, output_path, target_ext)
    if result[0]:
        return result
    
    # Если оба метода не сработали, возвращаем ошибку
    error_msg = f"Не удалось конвертировать {source_ext} в {target_ext}"
    if powerpoint_format is not None:
        error_msg += ". LibreOffice и Microsoft PowerPoint недоступны или не поддерживают этот формат"
    else:
        error_msg += ". LibreOffice недоступен"
    
    return False, error_msg, None


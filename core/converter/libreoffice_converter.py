"""Модуль конвертации через LibreOffice.

Содержит функции для конвертации файлов через LibreOffice:
- Проверка доступности LibreOffice
- Конвертация различных форматов документов
"""

import logging
import os
import shutil
import subprocess
import sys
from typing import Optional, Tuple

# Импорт утилит безопасности
try:
    from utils.security_utils import (
        sanitize_path_for_subprocess,
        validate_path_for_subprocess
    )
except ImportError:
    # Fallback если утилиты недоступны
    def sanitize_path_for_subprocess(path: str) -> Optional[str]:
        try:
            return os.path.abspath(os.path.normpath(path))
        except (OSError, ValueError):
            return None
    
    def validate_path_for_subprocess(path: str, must_exist: bool = True, must_be_file: bool = False) -> Tuple[bool, Optional[str]]:
        if not os.path.exists(path) and must_exist:
            return False, "Путь не существует"
        if must_be_file and not os.path.isfile(path):
            return False, "Путь не является файлом"
        return True, None

logger = logging.getLogger(__name__)




def convert_with_libreoffice(
    file_path: str,
    output_path: str,
    target_ext: str
) -> Tuple[bool, str, Optional[str]]:
    """Конвертация файлов через LibreOffice.
    
    Args:
        file_path: Путь к исходному файлу
        output_path: Путь для сохранения
        target_ext: Целевое расширение (с точкой)
        
    Returns:
        Кортеж (успех, сообщение, путь к выходному файлу)
    """
    try:
        # Находим путь к soffice
        soffice_path = None
        if sys.platform == 'win32':
            # Проверяем стандартные пути
            possible_paths = [
                r'C:\Program Files\LibreOffice\program\soffice.exe',
                r'C:\Program Files (x86)\LibreOffice\program\soffice.exe',
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    soffice_path = path
                    break
            # Если не нашли, проверяем через PATH
            if not soffice_path:
                soffice_path = shutil.which('soffice.exe')
        else:
            soffice_path = shutil.which('soffice')
        
        if not soffice_path:
            return False, "LibreOffice не найден в системе", None
        
        # Определяем формат для LibreOffice
        format_map = {
            '.pdf': 'pdf',
            '.docx': 'docx',
            '.doc': 'doc',
            '.odt': 'odt',
            '.odp': 'odp',
            '.pptx': 'pptx',
            '.ppt': 'ppt',
            '.txt': 'txt',
            '.rtf': 'rtf',
            '.html': 'html',
            '.htm': 'html'
        }
        
        output_format = format_map.get(target_ext.lower())
        if not output_format:
            return False, f"Неподдерживаемый целевой формат для LibreOffice: {target_ext}", None
        
        # Валидируем и нормализуем пути
        validated_file_path = sanitize_path_for_subprocess(file_path)
        if not validated_file_path:
            return False, "Небезопасный путь к исходному файлу", None
        
        validated_soffice = sanitize_path_for_subprocess(soffice_path)
        if not validated_soffice:
            return False, "Небезопасный путь к LibreOffice", None
        
        file_path = validated_file_path
        soffice_path = validated_soffice
        
        output_dir = os.path.dirname(output_path)
        output_filename = os.path.basename(output_path)
        
        # Валидируем выходную директорию
        if output_dir:
            validated_output_dir = sanitize_path_for_subprocess(output_dir)
            if not validated_output_dir:
                return False, "Небезопасный путь к выходной директории", None
            output_dir = validated_output_dir
            
            # Создаем директорию для выходного файла, если её нет
            try:
                os.makedirs(output_dir, exist_ok=True)
            except (OSError, PermissionError) as e:
                return False, f"Не удалось создать директорию для выходного файла: {e}", None
        
        # Валидация путей перед использованием в subprocess
        try:
            from utils.security_utils import validate_path_for_subprocess
            # Валидируем входной файл
            is_safe_input, error_msg_input = validate_path_for_subprocess(file_path, must_exist=True, must_be_file=True)
            if not is_safe_input:
                return False, f"Небезопасный путь к входному файлу: {error_msg_input}", None
            
            # Валидируем путь к LibreOffice
            is_safe_soffice, error_msg_soffice = validate_path_for_subprocess(soffice_path, must_exist=True, must_be_file=True)
            if not is_safe_soffice:
                return False, f"Небезопасный путь к LibreOffice: {error_msg_soffice}", None
            
            # Валидируем выходную директорию
            is_safe_output_dir, error_msg_output = validate_path_for_subprocess(output_dir, must_exist=False, must_be_file=False)
            if not is_safe_output_dir:
                return False, f"Небезопасный путь к выходной директории: {error_msg_output}", None
        except ImportError:
            # Если security_utils недоступен, продолжаем без валидации (fallback)
            logger.warning("Модуль security_utils недоступен, валидация путей пропущена")
        
        # Формируем команду для LibreOffice
        cmd = [
            soffice_path,
            '--headless',
            '--convert-to', output_format,
            '--outdir', output_dir,
            file_path
        ]
        
        logger.info(f"Запуск LibreOffice для конвертации: {' '.join(cmd)}")
        
        # Запускаем конвертацию
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(soffice_path) if soffice_path else None,
                check=False  # Не выбрасываем исключение при ненулевом коде возврата
            )
        except subprocess.TimeoutExpired:
            return False, "Таймаут при конвертации через LibreOffice", None
        except (OSError, ValueError) as e:
            logger.error(f"Ошибка запуска subprocess для LibreOffice: {e}", exc_info=True)
            return False, f"Ошибка запуска конвертации: {str(e)}", None
        
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout or "Неизвестная ошибка"
            logger.error(f"Ошибка конвертации через LibreOffice: {error_msg}")
            return False, f"Ошибка конвертации через LibreOffice: {error_msg[:200]}", None
        
        # LibreOffice сохраняет файл с тем же именем, но с новым расширением
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        expected_output = os.path.join(output_dir, base_name + target_ext)
        
        # Если ожидаемый файл не найден, ищем файлы с похожим именем
        if not os.path.exists(expected_output):
            if os.path.exists(output_dir):
                for file in os.listdir(output_dir):
                    if file.startswith(base_name) and file.endswith(target_ext):
                        expected_output = os.path.join(output_dir, file)
                        break
        
        # Если файл все еще не найден, пробуем использовать указанный output_path
        if not os.path.exists(expected_output):
            if os.path.exists(output_path):
                expected_output = output_path
            else:
                return False, f"Файл не был создан: {expected_output}", None
        
        # Если нужно переименовать файл
        if expected_output != output_path:
            try:
                if os.path.exists(output_path):
                    os.remove(output_path)
                shutil.move(expected_output, output_path)
            except (OSError, PermissionError, shutil.Error) as e:
                logger.warning(f"Не удалось переименовать файл: {e}, используем созданный файл")
                output_path = expected_output
        
        return True, "Файл успешно конвертирован через LibreOffice", output_path
        
    except (OSError, PermissionError, ValueError) as e:
        logger.error(f"Ошибка при конвертации через LibreOffice {file_path}: {e}", exc_info=True)
        return False, f"Ошибка: {str(e)}", None


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
        
        # Нормализуем пути
        file_path = os.path.abspath(file_path)
        output_dir = os.path.dirname(output_path)
        output_filename = os.path.basename(output_path)
        
        # Создаем директорию для выходного файла, если её нет
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
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
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=os.path.dirname(soffice_path) if soffice_path else None
        )
        
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
            except Exception as e:
                logger.warning(f"Не удалось переименовать файл: {e}, используем созданный файл")
                output_path = expected_output
        
        return True, "Файл успешно конвертирован через LibreOffice", output_path
        
    except subprocess.TimeoutExpired:
        return False, "Таймаут при конвертации через LibreOffice", None
    except Exception as e:
        logger.error(f"Ошибка при конвертации через LibreOffice {file_path}: {e}", exc_info=True)
        return False, f"Ошибка: {str(e)}", None


"""Модуль конвертации аудио и видео файлов.

Содержит функции для конвертации аудио и видео через ffmpeg.
"""

import logging
import os
import subprocess
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def get_ffmpeg_path() -> Optional[str]:
    """Получение пути к исполняемому файлу ffmpeg.
    
    Сначала проверяет локальную версию в папке проекта, затем системную.
    
    Returns:
        Путь к ffmpeg.exe или None если не найден
    """
    # Получаем корневую папку проекта (предполагаем, что мы в core/converter/)
    current_file = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    
    # Проверяем локальную версию в tools/ffmpeg/bin/
    local_ffmpeg = os.path.join(project_root, 'tools', 'ffmpeg', 'bin', 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg
    
    # Если локальная версия не найдена, возвращаем None (будет использоваться системная)
    return None


def check_ffmpeg_installed() -> bool:
    """Проверка, установлен ли ffmpeg в системе или в проекте.
    
    Returns:
        True если ffmpeg доступен, False иначе
    """
    # Проверяем локальную версию
    local_ffmpeg = get_ffmpeg_path()
    if local_ffmpeg and os.path.exists(local_ffmpeg):
        try:
            result = subprocess.run(
                [local_ffmpeg, '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
            pass
    
    # Проверяем системную версию
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return False


def convert_audio_video(
    file_path: str,
    output_path: str,
    target_ext: str
) -> Tuple[bool, str, Optional[str]]:
    """Конвертация аудио или видео файла через ffmpeg.
    
    Args:
        file_path: Путь к исходному файлу
        output_path: Путь для сохранения результата
        target_ext: Целевое расширение (например, '.mp3', '.mp4')
        
    Returns:
        Tuple[успех, сообщение, путь к выходному файлу]
    """
    try:
        # Получаем путь к ffmpeg (локальный или системный)
        ffmpeg_path = get_ffmpeg_path()
        if not ffmpeg_path:
            ffmpeg_path = 'ffmpeg'  # Используем системную версию
        
        # Проверяем, установлен ли ffmpeg
        if not check_ffmpeg_installed():
            return False, "ffmpeg не установлен. Установите ffmpeg для конвертации аудио/видео файлов.", None
        
        # Нормализуем пути
        file_path = os.path.abspath(file_path)
        output_path = os.path.abspath(output_path)
        
        # Создаем директорию для выходного файла, если её нет
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Строим команду ffmpeg
        # -i: входной файл
        # -y: перезаписывать выходной файл без запроса
        # -loglevel error: показывать только ошибки (для уменьшения вывода)
        cmd = [
            ffmpeg_path,
            '-i', file_path,
            '-y',  # Перезаписывать без запроса
            '-loglevel', 'error',  # Минимальный вывод
            output_path
        ]
        
        # Запускаем ffmpeg
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=300  # Таймаут 5 минут
        )
        
        # Проверяем результат
        if result.returncode == 0:
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True, "Конвертация завершена успешно", output_path
            else:
                return False, "Файл создан, но пуст", None
        else:
            error_msg = result.stderr.decode('utf-8', errors='ignore') if result.stderr else "Неизвестная ошибка"
            return False, f"Ошибка ffmpeg: {error_msg[:200]}", None
            
    except subprocess.TimeoutExpired:
        return False, "Превышено время ожидания конвертации (5 минут)", None
    except Exception as e:
        logger.error(f"Ошибка при конвертации аудио/видео {file_path}: {e}", exc_info=True)
        return False, f"Ошибка конвертации: {str(e)}", None


def get_ffmpeg_codec_for_format(target_ext: str) -> Optional[str]:
    """Получение кодека ffmpeg для целевого формата.
    
    Args:
        target_ext: Целевое расширение
        
    Returns:
        Название кодека или None
    """
    codec_map = {
        # Аудио кодек
        '.mp3': 'libmp3lame',
        '.aac': 'aac',
        '.ogg': 'libvorbis',
        '.wav': 'pcm_s16le',
        '.flac': 'flac',
        '.wma': 'wmav2',
        '.m4a': 'aac',
        # Видео кодеки
        '.mp4': 'libx264',
        '.avi': 'libx264',
        '.mkv': 'libx264',
        '.mov': 'libx264',
        '.webm': 'libvpx-vp9',
        '.flv': 'flv',
    }
    return codec_map.get(target_ext.lower())


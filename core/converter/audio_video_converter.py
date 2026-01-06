"""Модуль конвертации аудио и видео файлов.

Содержит функции для конвертации аудио и видео через ffmpeg.
"""

import logging
import os
import subprocess
from typing import Optional, Tuple

# Импорт утилит безопасности
try:
    from utils.security_utils import (
        sanitize_path_for_subprocess,
        validate_path_for_subprocess,
        _check_file_exists_unicode
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
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        except (OSError, ValueError, RuntimeError) as e:
            logger.debug(f"Ошибка проверки локального ffmpeg: {e}")
            pass
        except (subprocess.SubprocessError, AttributeError) as e:
            logger.debug(f"Ошибка subprocess/атрибутов при проверке локального ffmpeg: {e}")
            pass
        except (MemoryError, RecursionError) as e:

            # Ошибки памяти/рекурсии

            pass

        # Финальный catch для неожиданных исключений (критично для стабильности)

        except BaseException as e:

            if isinstance(e, (KeyboardInterrupt, SystemExit)):

                raise
            logger.warning(f"Неожиданная ошибка при проверке локального ffmpeg: {e}", exc_info=True)
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
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    except (OSError, ValueError, RuntimeError) as e:
        logger.debug(f"Ошибка проверки системного ffmpeg: {e}")
        return False
    except (subprocess.SubprocessError, AttributeError) as e:
        logger.debug(f"Ошибка subprocess/атрибутов при проверке системного ffmpeg: {e}")
        return False
    except (MemoryError, RecursionError) as e:

        # Ошибки памяти/рекурсии

        pass

    # Финальный catch для неожиданных исключений (критично для стабильности)

    except BaseException as e:

        if isinstance(e, (KeyboardInterrupt, SystemExit)):

            raise
        logger.warning(f"Неожиданная ошибка при проверке системного ffmpeg: {e}", exc_info=True)
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
        
        # Валидируем и нормализуем пути с поддержкой Unicode (кириллица)
        # Сначала проверяем существование файла с полной поддержкой Unicode
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
        
        if not _check_file_exists_unicode(file_path):
            logger.warning(f"Файл не существует перед валидацией: {file_path}")
            return False, f"Файл не найден: {os.path.basename(file_path)}", None
        
        validated_file_path = sanitize_path_for_subprocess(file_path)
        if not validated_file_path:
            # Если валидация не прошла, но файл существует, используем исходный путь
            # Это может быть проблема с валидацией Unicode путей
            logger.warning(f"Валидация пути не прошла, но файл существует: {file_path}")
            # Используем исходный путь, но проверяем его безопасность базовыми методами
            if _check_file_exists_unicode(file_path):
                validated_file_path = os.path.abspath(os.path.normpath(file_path))
            else:
                return False, "Небезопасный путь к исходному файлу", None
        
        # Для выходного файла не проверяем существование (файл еще не создан)
        validated_output_path = sanitize_path_for_subprocess(output_path, check_existence=False)
        if not validated_output_path:
            # Если нормализация не удалась, пробуем просто нормализовать путь
            try:
                validated_output_path = os.path.abspath(os.path.normpath(output_path))
            except (OSError, ValueError):
                return False, "Небезопасный путь к выходному файлу", None
        
        file_path = validated_file_path
        output_path = validated_output_path
        
        # Валидируем путь к ffmpeg
        if ffmpeg_path != 'ffmpeg':  # Системная версия уже проверена
            validated_ffmpeg = sanitize_path_for_subprocess(ffmpeg_path)
            if not validated_ffmpeg:
                return False, "Небезопасный путь к ffmpeg", None
            ffmpeg_path = validated_ffmpeg
        
        # Создаем директорию для выходного файла, если её нет
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
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
            
            # Валидируем путь к ffmpeg
            is_safe_ffmpeg, error_msg_ffmpeg = validate_path_for_subprocess(ffmpeg_path, must_exist=True, must_be_file=True)
            if not is_safe_ffmpeg:
                return False, f"Небезопасный путь к ffmpeg: {error_msg_ffmpeg}", None
            
            # Валидируем выходной путь (может не существовать)
            output_dir = os.path.dirname(output_path)
            if output_dir:
                is_safe_output_dir, error_msg_output = validate_path_for_subprocess(output_dir, must_exist=False, must_be_file=False)
                if not is_safe_output_dir:
                    return False, f"Небезопасный путь к выходной директории: {error_msg_output}", None
        except ImportError:
            # Если security_utils недоступен, продолжаем без валидации (fallback)
            logger.warning("Модуль security_utils недоступен, валидация путей пропущена")
        
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
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=300,  # Таймаут 5 минут
                check=False  # Не выбрасываем исключение при ненулевом коде возврата
            )
        except subprocess.TimeoutExpired:
            return False, "Превышено время ожидания конвертации (5 минут)", None
        except (OSError, ValueError) as e:
            logger.error(f"Ошибка запуска subprocess для ffmpeg: {e}", exc_info=True)
            return False, f"Ошибка запуска конвертации: {str(e)}", None
        
        # Проверяем результат с поддержкой Unicode (кириллица в путях)
        if result.returncode == 0:
            # Используем функцию с поддержкой Unicode для проверки существования
            if _check_file_exists_unicode(output_path):
                try:
                    # Проверяем размер файла
                    file_size = os.path.getsize(output_path)
                    if file_size > 0:
                        return True, "Конвертация завершена успешно", output_path
                    else:
                        return False, "Файл создан, но пуст", None
                except (OSError, UnicodeEncodeError, UnicodeDecodeError) as e:
                    # Если не удалось проверить размер, но файл существует - считаем успехом
                    logger.debug(f"Не удалось проверить размер файла {output_path}: {e}")
                    return True, "Конвертация завершена успешно", output_path
            else:
                return False, "Файл не был создан после конвертации", None
        else:
            error_msg = result.stderr.decode('utf-8', errors='ignore') if result.stderr else "Неизвестная ошибка"
            return False, f"Ошибка ffmpeg: {error_msg[:200]}", None
            
    except (OSError, PermissionError, ValueError) as e:
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


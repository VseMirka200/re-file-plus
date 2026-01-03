#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Скрипт для установки всех необходимых библиотек для Ре-Файл+.

Запустите этот скрипт двойным кликом для установки всех зависимостей.
Версия .pyw - без консоли (для Windows).
"""

import os
import subprocess
import sys
import urllib.request
import zipfile
import shutil

# Кодировка для Windows консоли
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
    except (OSError, AttributeError, RuntimeError):
        pass
    except (MemoryError, RecursionError):
        # Ошибки памяти/рекурсии
        pass
    except BaseException:
        # Финальный catch для неожиданных исключений
        pass

def print_header(text):
    """Печать заголовка."""
    print("\n" + "=" * 50)
    print(f"  {text}")
    print("=" * 50 + "\n")

def check_python():
    """Проверка наличия Python."""
    print("[Проверка] Python версия:", sys.version.split()[0])
    if sys.version_info < (3, 7):
        print("[ОШИБКА] Требуется Python 3.7 или выше!")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)

def upgrade_pip():
    """Обновление pip."""
    print("[1/4] Обновление pip...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            check=False,
            capture_output=True
        )
        print("  ✓ pip обновлен")
    except (subprocess.SubprocessError, OSError, FileNotFoundError) as e:
        print(f"  ⚠ Ошибка выполнения при обновлении pip: {e}")
    except (MemoryError, RecursionError) as e:
        # Ошибки памяти/рекурсии
        print(f"  ⚠ Ошибка памяти/рекурсии при обновлении pip: {e}")
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        print(f"  ⚠ Неожиданная ошибка при обновлении pip: {e}")

def install_ffmpeg_to_project():
    """Установка FFmpeg в папку проекта."""
    print("\n[FFmpeg] Начало установки...")
    
    # Определяем пути
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tools_dir = os.path.join(script_dir, "tools")
    ffmpeg_dir = os.path.join(tools_dir, "ffmpeg")
    bin_dir = os.path.join(ffmpeg_dir, "bin")
    zip_path = os.path.join(ffmpeg_dir, "ffmpeg.zip")
    
    # Проверяем, не установлен ли уже FFmpeg
    ffmpeg_exe = os.path.join(bin_dir, "ffmpeg.exe")
    if os.path.exists(ffmpeg_exe):
        print("  ✓ FFmpeg уже установлен в проекте")
        return
    
    try:
        # Создаем папки
        os.makedirs(bin_dir, exist_ok=True)
        
        # URL для скачивания FFmpeg (статическая сборка для Windows)
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        
        print(f"  ⬇ Скачивание FFmpeg...")
        print(f"     URL: {ffmpeg_url}")
        
        # Скачиваем архив
        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100)
            print(f"\r     Прогресс: {percent:.1f}%", end='', flush=True)
        
        urllib.request.urlretrieve(ffmpeg_url, zip_path, show_progress)
        print()  # Новая строка после прогресса
        
        if not os.path.exists(zip_path) or os.path.getsize(zip_path) < 1000:
            print("  ✗ Ошибка: архив не скачан или поврежден")
            return
        
        print(f"  📦 Распаковка архива...")
        
        # Распаковываем архив
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(ffmpeg_dir)
        
        # Ищем ffmpeg.exe в распакованных файлах
        ffmpeg_exe_found = None
        for root, dirs, files in os.walk(ffmpeg_dir):
            if 'ffmpeg.exe' in files:
                ffmpeg_exe_found = os.path.join(root, 'ffmpeg.exe')
                break
        
        if not ffmpeg_exe_found:
            print("  ✗ Ошибка: ffmpeg.exe не найден в архиве")
            return
        
        # Копируем ffmpeg.exe и ffprobe.exe в bin/
        ffprobe_exe_found = ffmpeg_exe_found.replace('ffmpeg.exe', 'ffprobe.exe')
        
        shutil.copy2(ffmpeg_exe_found, bin_dir)
        print(f"  ✓ Скопирован ffmpeg.exe")
        
        if os.path.exists(ffprobe_exe_found):
            shutil.copy2(ffprobe_exe_found, bin_dir)
            print(f"  ✓ Скопирован ffprobe.exe")
        
        # Удаляем архив и временные файлы
        try:
            os.remove(zip_path)
            # Удаляем распакованную папку (оставляем только bin/)
            for item in os.listdir(ffmpeg_dir):
                item_path = os.path.join(ffmpeg_dir, item)
                if item != 'bin' and os.path.isdir(item_path):
                    shutil.rmtree(item_path, ignore_errors=True)
                elif item != 'bin' and item != 'ffmpeg.zip':
                    try:
                        os.remove(item_path)
                    except (OSError, PermissionError):
                        pass
                    except (MemoryError, RecursionError):
                        # Ошибки памяти/рекурсии
                        pass
                    except BaseException:
                        # Финальный catch для неожиданных исключений
                        pass
        except (OSError, PermissionError, IOError) as e:
            print(f"  ⚠ Ошибка доступа при очистке временных файлов: {e}")
        except (MemoryError, RecursionError) as e:
            # Ошибки памяти/рекурсии
            print(f"  ⚠ Ошибка памяти/рекурсии при очистке временных файлов: {e}")
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            print(f"  ⚠ Неожиданная ошибка при очистке временных файлов: {e}")
        
        # Проверяем, что всё работает
        try:
            result = subprocess.run(
                [ffmpeg_exe, '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5
            )
            if result.returncode == 0:
                print(f"  ✓ FFmpeg успешно установлен в {bin_dir}")
            else:
                print(f"  ⚠ FFmpeg установлен, но проверка не прошла")
        except (subprocess.SubprocessError, subprocess.TimeoutExpired) as e:
            print(f"  ⚠ FFmpeg установлен, но проверка не выполнена (ошибка subprocess): {e}")
        except (OSError, FileNotFoundError) as e:
            print(f"  ⚠ FFmpeg установлен, но проверка не выполнена (ошибка доступа): {e}")
        except (MemoryError, RecursionError) as e:
            # Ошибки памяти/рекурсии
            print(f"  ⚠ FFmpeg установлен, но проверка не выполнена (ошибка памяти/рекурсии): {e}")
        except BaseException as e:
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                raise
            print(f"  ⚠ FFmpeg установлен, но проверка не выполнена: {e}")
    
    except urllib.error.URLError as e:
        print(f"  ✗ Ошибка скачивания: {e}")
        print(f"     Проверьте подключение к интернету")
    except zipfile.BadZipFile:
        print(f"  ✗ Ошибка: архив поврежден или не является ZIP файлом")
    except (OSError, PermissionError, IOError) as e:
        print(f"  ✗ Ошибка доступа при установке FFmpeg: {e}")
        import traceback
        traceback.print_exc()
    except (ValueError, TypeError) as e:
        print(f"  ✗ Ошибка данных при установке FFmpeg: {e}")
        import traceback
        traceback.print_exc()
    except (MemoryError, RecursionError) as e:
        # Ошибки памяти/рекурсии
        print(f"  ✗ Ошибка памяти/рекурсии при установке FFmpeg: {e}")
        import traceback
        traceback.print_exc()
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        print(f"  ✗ Неожиданная ошибка установки FFmpeg: {e}")
        import traceback
        traceback.print_exc()


def install_package(package, description=""):
    """Установка пакета."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print(f"  ✓ {description or package}")
            return True
        else:
            error_msg = result.stderr[:200] if result.stderr else result.stdout[:200]
            print(f"  ✗ {description or package}: {error_msg}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ {description or package}: таймаут")
        return False
    except (OSError, FileNotFoundError) as e:
        print(f"  ✗ {description or package}: ошибка доступа - {e}")
        return False
    except (MemoryError, RecursionError) as e:
        # Ошибки памяти/рекурсии
        print(f"  ✗ {description or package}: ошибка памяти/рекурсии - {e}")
        return False
    except BaseException as e:
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        print(f"  ✗ {description or package}: {e}")
        return False

def main():
    """Главная функция."""
    print_header("Установка библиотек для Ре-Файл+")
    
    # Проверка Python
    check_python()
    
    # Обновление pip
    upgrade_pip()
    
    # Обязательные библиотеки
    print("\n[2/4] Установка обязательных библиотек...")
    required = [
        ("Pillow>=9.0.0", "Pillow (работа с изображениями)"),
        ("tkinterdnd2>=0.4.0", "tkinterdnd2 (drag and drop)"),
    ]
    
    required_failed = []
    for package, desc in required:
        if not install_package(package, desc):
            required_failed.append(desc)
    
    if required_failed:
        print(f"\n[ОШИБКА] Не удалось установить обязательные библиотеки:")
        for lib in required_failed:
            print(f"  - {lib}")
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
    
    # Опциональные библиотеки
    print("\n[3/4] Установка опциональных библиотек...")
    optional = [
        ("pypdf>=3.0.0", "pypdf (работа с PDF)"),
        ("PyMuPDF>=1.23.0", "PyMuPDF (работа с PDF)"),
        ("python-docx>=0.8.11", "python-docx (работа с DOCX)"),
    ]
    
    for package, desc in optional:
        install_package(package, desc)
    
    # Windows-специфичные библиотеки
    if sys.platform == 'win32':
        print("\n[4/4] Установка Windows-специфичных библиотек...")
        windows_packages = [
            ("pywin32>=300", "pywin32 (COM для Word)"),
            ("comtypes>=1.1.0", "comtypes (COM для Word)"),
            ("docx2pdf>=0.1.8", "docx2pdf (конвертация DOCX)"),
            ("pdf2docx>=0.5.0", "pdf2docx (конвертация PDF)"),
        ]
        
        for package, desc in windows_packages:
            install_package(package, desc)
    
    # Установка FFmpeg (для конвертации аудио/видео)
    print_header("Установка FFmpeg (опционально)")
    print("FFmpeg необходим для конвертации аудио и видео файлов.")
    install_ffmpeg = input("Установить FFmpeg в папку проекта? (y/n, по умолчанию n): ").strip().lower()
    
    if install_ffmpeg in ('y', 'yes', 'д', 'да', 'у', 'установить'):
        install_ffmpeg_to_project()
    else:
        print("  ⏭ Пропущено")
    
    # Итоги
    print_header("Установка завершена!")
    print("Все необходимые библиотеки установлены.")
    print("Теперь можно запускать приложение Ре-Файл+.")
    print("\n" + "=" * 50)
    
    # Пауза перед закрытием
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[ОТМЕНЕНО] Установка прервана пользователем.")
        sys.exit(1)
    except (OSError, PermissionError, IOError) as e:
        print(f"\n[ОШИБКА] Критическая ошибка доступа: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
    except (ValueError, TypeError, AttributeError) as e:
        print(f"\n[ОШИБКА] Критическая ошибка данных: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
    except (MemoryError, RecursionError) as e:
        # Ошибки памяти/рекурсии
        print(f"\n[ОШИБКА] Критическая ошибка памяти/рекурсии: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
        sys.exit(1)
    except BaseException as e:
        # Финальный catch для неожиданных исключений (критично для стабильности)
        if isinstance(e, (KeyboardInterrupt, SystemExit)):
            raise
        print(f"\n[ОШИБКА] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
        sys.exit(1)


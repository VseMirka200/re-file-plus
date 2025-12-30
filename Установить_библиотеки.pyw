#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Скрипт для установки всех необходимых библиотек для Ре-Файл+.

Запустите этот скрипт двойным кликом для установки всех зависимостей.
Версия .pyw - без консоли (для Windows).
"""

import os
import subprocess
import sys

# Кодировка для Windows консоли
if sys.platform == 'win32':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
    except Exception:
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
    except Exception as e:
        print(f"  ⚠ Не удалось обновить pip: {e}")

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
    except Exception as e:
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
    except Exception as e:
        print(f"\n[ОШИБКА] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("\nНажмите Enter для выхода...")
        sys.exit(1)


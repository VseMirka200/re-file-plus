"""Модуль конвертации изображений.

Содержит функции для конвертации:
- Изображений в различные форматы изображений
- Изображений в PDF
- PDF в изображения
"""

import io
import logging
import os
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def convert_pdf_to_image(
    file_path: str,
    output_path: str,
    target_ext: str,
    quality: int,
    fitz_module,
    Image_module,
    supported_image_formats: dict
) -> Tuple[bool, str, Optional[str]]:
    """Конвертация PDF в изображение.
    
    Args:
        file_path: Путь к PDF файлу
        output_path: Путь для сохранения изображения
        target_ext: Расширение целевого формата (например, '.png', '.jpg')
        quality: Качество для JPEG (1-100)
        fitz_module: Модуль PyMuPDF (fitz)
        Image_module: Модуль Pillow (PIL.Image)
        supported_image_formats: Словарь поддерживаемых форматов изображений
        
    Returns:
        Tuple[успех, сообщение, путь к выходному файлу]
    """
    if not fitz_module:
        return False, "PyMuPDF не установлен. Установите: pip install PyMuPDF", None
    
    if not Image_module:
        return False, "Pillow не установлен", None
    
    try:
        # Открываем PDF
        pdf_document = fitz_module.open(file_path)
        
        # Проверяем наличие страниц
        num_pages = len(pdf_document)
        if num_pages == 0:
            pdf_document.close()
            return False, "PDF файл не содержит страниц", None
        
        # Определяем формат для сохранения
        format_name = supported_image_formats.get(target_ext, 'PNG')
        
        # Параметры сохранения
        save_kwargs = {}
        if format_name == 'JPEG':
            save_kwargs['quality'] = quality
            save_kwargs['optimize'] = True
        elif format_name == 'PNG':
            save_kwargs['optimize'] = True
        elif format_name == 'WEBP':
            save_kwargs['quality'] = quality
            save_kwargs['method'] = 6
        
        # Используем матрицу для увеличения разрешения (zoom = 2.0 для лучшего качества)
        zoom = 2.0
        mat = fitz_module.Matrix(zoom, zoom)
        
        # Конвертируем все страницы
        output_files = []
        base_name = os.path.splitext(output_path)[0]
        base_dir = os.path.dirname(output_path) or os.path.dirname(file_path)
        
        # Определяем имя папки на основе исходного файла (для уникальности)
        source_base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_folder = None
        
        # Если несколько страниц, создаем структурированную папку
        if num_pages > 1:
            # Создаем структуру: base_dir/Конвертированные/[имя_файла]/
            converted_base = os.path.join(base_dir, "Конвертированные")
            folder_name = source_base_name
            output_folder = os.path.join(converted_base, folder_name)
            
            # Если папка уже существует, добавляем суффикс для уникальности
            counter = 1
            original_folder = output_folder
            max_attempts = 1000  # Защита от бесконечного цикла
            while os.path.exists(output_folder) and counter < max_attempts:
                output_folder = os.path.join(converted_base, f"{folder_name}_{counter:03d}")
                counter += 1
            
            if counter >= max_attempts:
                return False, "Не удалось создать уникальную папку для сохранения страниц", None
            
            # Создаем папку (включая родительскую "Конвертированные")
            try:
                os.makedirs(output_folder, exist_ok=True)
                # Проверяем, что папка действительно создана
                if not os.path.exists(output_folder):
                    return False, f"Не удалось создать папку: {output_folder}", None
            except (OSError, PermissionError) as e:
                return False, f"Ошибка при создании папки: {str(e)}", None
        
        for page_num in range(num_pages):
            pix = None
            img = None
            try:
                # Получаем страницу
                page = pdf_document[page_num]
                
                # Конвертируем страницу в изображение
                pix = page.get_pixmap(matrix=mat)
                
                # Конвертируем в PIL Image
                img_data = pix.tobytes("png")
                img = Image_module.open(io.BytesIO(img_data))
                
                # Подготовка изображения для сохранения
                if format_name == 'JPEG':
                    # Конвертируем в RGB для JPEG
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                
                # Определяем путь для сохранения страницы
                if num_pages == 1:
                    # Если одна страница, используем исходный путь
                    page_output_path = output_path
                else:
                    # Если несколько страниц, сохраняем в папку с номером страницы
                    page_filename = f"страница_{page_num + 1:03d}{target_ext}"
                    page_output_path = os.path.join(output_folder, page_filename)
                
                # Сохраняем изображение
                img.save(page_output_path, format=format_name, **save_kwargs)
                output_files.append(page_output_path)
            finally:
                # Освобождаем память после обработки каждой страницы
                if pix is not None:
                    pix = None
                if img is not None:
                    img.close()
                    img = None
        
        # Закрываем PDF
        pdf_document.close()
        
        # Формируем сообщение
        if num_pages == 1:
            message = "PDF успешно конвертирован в изображение"
            return_path = output_path
        else:
            folder_display_name = os.path.basename(output_folder)
            message = f"PDF успешно конвертирован: {num_pages} страниц сохранено в папку '{folder_display_name}'"
            return_path = output_folder  # Возвращаем путь к папке
        
        return True, message, return_path
        
    except Exception as e:
        logger.error(f"Ошибка при конвертации PDF в изображение {file_path}: {e}", exc_info=True)
        return False, f"Ошибка конвертации PDF: {str(e)}", None


def convert_image_to_pdf(
    file_path: str,
    output_path: str,
    quality: int,
    fitz_module,
    Image_module
) -> Tuple[bool, str, Optional[str]]:
    """Конвертация изображения в PDF.
    
    Args:
        file_path: Путь к изображению
        output_path: Путь для сохранения PDF
        quality: Качество для JPEG (1-100), используется для оптимизации изображения перед вставкой в PDF
        fitz_module: Модуль PyMuPDF (fitz)
        Image_module: Модуль Pillow (PIL.Image)
        
    Returns:
        Tuple[успех, сообщение, путь к выходному файлу]
    """
    if not fitz_module:
        return False, "PyMuPDF не установлен. Установите: pip install PyMuPDF", None
    
    if not Image_module:
        return False, "Pillow не установлен", None
    
    try:
        # Открываем изображение через Pillow
        with Image_module.open(file_path) as img:
            # Конвертируем в RGB если нужно
            if img.mode in ('RGBA', 'LA', 'P'):
                # Создаем белый фон для прозрачных изображений
                background = Image_module.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Получаем размеры изображения
            width, height = img.size
            
            # Создаем новый PDF документ
            pdf_document = fitz_module.open()  # Создаем пустой PDF
            
            # Создаем страницу с размерами изображения (в точках, 1 точка = 1/72 дюйма)
            # Конвертируем пиксели в точки (используем DPI = 72, стандарт для PDF)
            dpi = 72.0
            page_width = width * 72.0 / dpi
            page_height = height * 72.0 / dpi
            
            # Создаем страницу
            page = pdf_document.new_page(width=page_width, height=page_height)
            
            # Конвертируем изображение в байты для вставки в PDF
            # Сохраняем во временный буфер
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_data = img_buffer.getvalue()
            img_buffer.close()
            
            # Вставляем изображение на страницу
            # Используем rect для размещения изображения на всей странице
            rect = fitz_module.Rect(0, 0, page_width, page_height)
            page.insert_image(rect, stream=img_data)
            
            # Сохраняем PDF
            pdf_document.save(output_path)
            pdf_document.close()
            
            return True, "Изображение успешно конвертировано в PDF", output_path
            
    except Exception as e:
        logger.error(f"Ошибка при конвертации изображения в PDF {file_path}: {e}", exc_info=True)
        return False, f"Ошибка конвертации: {str(e)}", None


def convert_image_to_image(
    file_path: str,
    output_path: str,
    target_ext: str,
    quality: int,
    Image_module,
    supported_image_formats: dict
) -> Tuple[bool, str, Optional[str]]:
    """Конвертация изображения в другой формат изображения.
    
    Args:
        file_path: Путь к исходному изображению
        output_path: Путь для сохранения
        target_ext: Расширение целевого формата (например, '.png', '.jpg')
        quality: Качество для JPEG (1-100)
        Image_module: Модуль Pillow (PIL.Image)
        supported_image_formats: Словарь поддерживаемых форматов изображений
        
    Returns:
        Tuple[успех, сообщение, путь к выходному файлу]
    """
    if not Image_module:
        return False, "Pillow не установлен", None
    
    try:
        # Открываем изображение
        with Image_module.open(file_path) as img:
            # Конвертируем в RGB для форматов, которые не поддерживают прозрачность
            if target_ext in ('.jpg', '.jpeg', '.bmp') and img.mode in ('RGBA', 'LA', 'P'):
                # Создаем белый фон
                background = Image_module.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img)
                img = background
            elif img.mode == 'P' and target_ext not in ('.png', '.gif', '.webp'):
                # Конвертируем палитровые изображения
                img = img.convert('RGB')
            
            # Параметры сохранения
            save_kwargs = {}
            format_name = supported_image_formats.get(target_ext, 'PNG')
            
            # Обработка специальных форматов
            if format_name == 'JPEG2000':
                format_name = 'JPEG2000'
            elif format_name == 'HEIC' or format_name == 'HEIF':
                # Pillow может не поддерживать HEIC/HEIF напрямую
                # Конвертируем в PNG как fallback
                format_name = 'PNG'
                if not output_path.endswith('.png'):
                    output_path = os.path.splitext(output_path)[0] + '.png'
            elif format_name == 'AVIF':
                # Pillow может не поддерживать AVIF напрямую
                # Конвертируем в PNG как fallback
                format_name = 'PNG'
                if not output_path.endswith('.png'):
                    output_path = os.path.splitext(output_path)[0] + '.png'
            
            if format_name == 'JPEG':
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
                if img.mode != 'RGB':
                    img = img.convert('RGB')
            elif format_name == 'PNG':
                save_kwargs['optimize'] = True
            elif format_name == 'WEBP':
                save_kwargs['quality'] = quality
                save_kwargs['method'] = 6
            elif format_name == 'GIF':
                # Для GIF можно использовать optimize для уменьшения размера (low quality)
                if quality < 50:  # Low quality
                    save_kwargs['optimize'] = True
                    # Конвертируем в палитровый режим с ограниченной палитрой для меньшего размера
                    if img.mode not in ('P', 'L'):
                        # Конвертируем в RGB, затем в палитровый с ограниченной палитрой
                        if img.mode in ('RGBA', 'LA'):
                            # Для прозрачности используем палитровый режим
                            img = img.convert('P', palette=Image_module.ADAPTIVE, colors=128)
                        else:
                            img = img.convert('RGB').convert('P', palette=Image_module.ADAPTIVE, colors=128)
                else:
                    save_kwargs['optimize'] = True
                    # GIF поддерживает только палитровые изображения или RGB
                    if img.mode not in ('P', 'RGB', 'RGBA', 'L', 'LA'):
                        img = img.convert('RGB')
                    elif img.mode in ('RGBA', 'LA'):
                        # Конвертируем RGBA/LA в палитровый для GIF
                        img = img.convert('P', palette=Image_module.ADAPTIVE)
            elif format_name == 'TIFF':
                save_kwargs['compression'] = 'tiff_lzw'  # Сжатие для TIFF
            elif format_name == 'BMP':
                # BMP не поддерживает сжатие, но можно оптимизировать режим
                if img.mode not in ('RGB', 'RGBA', 'L', 'P'):
                    img = img.convert('RGB')
            elif format_name == 'ICO':
                # ICO требует определенных размеров, но Pillow обработает это автоматически
                pass
            elif format_name == 'JPEG2000':
                save_kwargs['quality'] = quality
            
            # Сохраняем в новом формате
            try:
                img.save(output_path, format=format_name, **save_kwargs)
            except Exception as e:
                # Если формат не поддерживается, пробуем PNG
                if format_name not in ('PNG', 'JPEG'):
                    format_name = 'PNG'
                    output_path = os.path.splitext(output_path)[0] + '.png'
                    img.save(output_path, format='PNG', optimize=True)
                    logger.warning(f"Формат {target_ext} не поддерживается, сохранено как PNG")
                else:
                    raise
        
        return True, "Файл успешно конвертирован", output_path
        
    except Exception as e:
        logger.error(f"Ошибка при конвертации изображения {file_path}: {e}", exc_info=True)
        return False, f"Ошибка конвертации: {str(e)}", None

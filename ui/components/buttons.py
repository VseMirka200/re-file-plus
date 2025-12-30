"""Модуль для создания переиспользуемых UI компонентов (кнопки).

Предоставляет статические методы для создания стандартизированных
элементов интерфейса с единым стилем оформления.
"""

import logging
import tkinter as tk
import tkinter.messagebox as mb
from typing import Callable, Optional, Tuple

from .tooltip import ToolTip

logger = logging.getLogger(__name__)


class UIComponents:
    """Класс для создания переиспользуемых UI компонентов.
    
    Предоставляет статические методы для создания стандартизированных
    элементов интерфейса с единым стилем оформления.
    """
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Конвертация hex в RGB.
        
        Args:
            hex_color: Цвет в формате hex (например, "#FF0000")
            
        Returns:
            Кортеж (R, G, B) с значениями от 0 до 255
        """
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    @staticmethod
    def create_rounded_button(
        parent,
        text: str,
        command: Callable,
        bg_color: str,
        fg_color: str = 'white',
        font: Tuple[str, int, str] = ('Robot', 10, 'bold'),
        padx: int = 16,
        pady: int = 10,
        active_bg: Optional[str] = None,
        active_fg: str = 'white',
        width: Optional[int] = None,
        expand: bool = True,
        tooltip: Optional[str] = None
    ) -> tk.Frame:
        """Создание кнопки с закругленными углами через Canvas.
        
        Args:
            parent: Родительский виджет
            text: Текст кнопки
            command: Функция-обработчик клика
            bg_color: Цвет фона
            fg_color: Цвет текста
            font: Шрифт (семейство, размер, стиль)
            padx: Горизонтальный отступ
            pady: Вертикальный отступ
            active_bg: Цвет фона при наведении
            active_fg: Цвет текста при наведении
            width: Ширина кнопки
            expand: Растягивать ли кнопку
            
        Returns:
            Фрейм с кнопкой
        """
        if active_bg is None:
            active_bg = bg_color
        
        # Проверка, что command передан
        if command is None:
            command = lambda: None
        
        # Фрейм для кнопки
        btn_frame = tk.Frame(parent, bg=parent.cget('bg'))
        
        # Вычисляем ширину текста для компактных кнопок
        if not expand and width is None:
            temp_label = tk.Label(parent, text=text, font=font)
            temp_label.update_idletasks()
            text_width = temp_label.winfo_reqwidth()
            temp_label.destroy()
            width = text_width + padx * 2 + 10
        
        # Canvas для закругленного фона
        canvas_height = pady * 2 + 16
        canvas = tk.Canvas(
            btn_frame, 
            highlightthickness=0, 
            borderwidth=0,
            bg=parent.cget('bg'), 
            height=canvas_height,
            cursor='hand2'
        )
        
        if expand:
            canvas.pack(fill=tk.BOTH, expand=True)
        else:
            if width:
                canvas.config(width=width)
                btn_frame.config(width=width)
            canvas.pack(fill=tk.NONE, expand=False)
        
        # Сохраняем параметры
        canvas.btn_text = text
        canvas.btn_command = command
        # Проверяем, что команда передана
        if command is None:
            logger.warning("Команда кнопки не передана!")
        elif not callable(command):
            logger.warning(f"Команда кнопки не является вызываемой: {type(command)}")
        canvas.btn_bg = bg_color
        canvas.btn_fg = fg_color
        canvas.btn_active_bg = active_bg
        canvas.btn_active_fg = active_fg
        canvas.btn_font = font
        canvas.btn_state = 'normal'
        canvas.btn_width = width
        canvas.btn_expand = expand
        
        # Флаг для предотвращения бесконечных вызовов
        canvas._drawing = False
        canvas._pending_draw = None
        canvas._click_processing = False  # Флаг для предотвращения двойных кликов
        
        # Определяем обработчики событий сначала
        def on_click(e=None):
            # Защита от двойных кликов
            if canvas._click_processing:
                return
            canvas._click_processing = True
            try:
                # Проверяем, что команда существует и вызываем её
                if hasattr(canvas, 'btn_command') and canvas.btn_command:
                    # Вызываем команду без аргументов
                    if callable(canvas.btn_command):
                        canvas.btn_command()
                    else:
                        # Показываем ошибку пользователю
                        try:
                            mb.showerror("Ошибка", "Команда кнопки не является вызываемой функцией")
                        except Exception:
                            pass
                else:
                    # Показываем ошибку пользователю
                    try:
                        mb.showerror("Ошибка", "Команда кнопки не найдена")
                    except Exception:
                        pass
            except Exception as ex:
                # Логируем ошибку в файл, так как консоль может быть недоступна
                logger.error(f"Ошибка при нажатии кнопки: {ex}", exc_info=True)
                # Также показываем сообщение пользователю
                try:
                    mb.showerror("Ошибка", f"Ошибка при выполнении команды кнопки:\n{ex}")
                except Exception:
                    pass
            finally:
                # Сбрасываем флаг после небольшой задержки (300мс)
                canvas.after(300, lambda: setattr(canvas, '_click_processing', False))
        
        def on_enter(e):
            if canvas.btn_state != 'active':
                canvas.btn_state = 'active'
                draw_button('active')
        
        def on_leave(e):
            if canvas.btn_state != 'normal':
                canvas.btn_state = 'normal'
                draw_button('normal')
        
        def on_configure(e):
            if not canvas.btn_expand and canvas.btn_width:
                if canvas.winfo_width() != canvas.btn_width:
                    canvas.config(width=canvas.btn_width)
                if btn_frame.winfo_width() != canvas.btn_width:
                    btn_frame.config(width=canvas.btn_width)
            draw_button(canvas.btn_state)
        
        def draw_button(state: str = 'normal'):
            # Защита от одновременных вызовов
            if canvas._drawing:
                return
            
            # Отменяем предыдущий отложенный вызов, если есть
            if canvas._pending_draw:
                try:
                    canvas.after_cancel(canvas._pending_draw)
                except (tk.TclError, ValueError):
                    pass
                canvas._pending_draw = None
            
            canvas._drawing = True
            try:
                canvas.delete('all')
                if canvas.btn_expand:
                    w = canvas.winfo_width()
                else:
                    w = canvas.btn_width if canvas.btn_width else canvas.winfo_width()
                h = canvas.winfo_height()
                
                if w <= 1 or h <= 1:
                    # Отложенный вызов с ограничением попыток
                    canvas._pending_draw = canvas.after(50, lambda: draw_button(state))
                    return
                
                if canvas.btn_expand and w < 50:
                    w = 50
                
                radius = 8
                color = canvas.btn_active_bg if state == 'active' else canvas.btn_bg
                text_color = canvas.btn_active_fg if state == 'active' else canvas.btn_fg
                
                # Конвертируем цвет в hex для Canvas
                if isinstance(color, tuple):
                    color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                elif isinstance(color, str) and color.startswith('#'):
                    color_hex = color
                else:
                    # Если цвет не распознан, используем значение по умолчанию
                    try:
                        # Пробуем преобразовать в строку и использовать как есть
                        color_hex = str(color) if color else '#6366F1'
                        if not color_hex.startswith('#'):
                            color_hex = '#6366F1'
                    except Exception:
                        color_hex = '#6366F1'
                
                # Рисуем закругленный прямоугольник с тегом для привязки событий
                tag = 'button_item'
                canvas.create_arc(0, 0, radius*2, radius*2, start=90, extent=90, 
                                fill=color_hex, outline=color_hex, tags=tag)
                canvas.create_arc(w-radius*2, 0, w, radius*2, start=0, extent=90, 
                                fill=color_hex, outline=color_hex, tags=tag)
                canvas.create_arc(0, h-radius*2, radius*2, h, start=180, extent=90, 
                                fill=color_hex, outline=color_hex, tags=tag)
                canvas.create_arc(w-radius*2, h-radius*2, w, h, start=270, extent=90, 
                                fill=color_hex, outline=color_hex, tags=tag)
                canvas.create_rectangle(radius, 0, w-radius, h, fill=color_hex, outline=color_hex, tags=tag)
                canvas.create_rectangle(0, radius, w, h-radius, fill=color_hex, outline=color_hex, tags=tag)
                
                canvas.create_text(w//2, h//2, text=canvas.btn_text, 
                                 fill=text_color, font=canvas.btn_font, width=max(w-20, 50), tags=tag)
                
                # Привязываем события клика к элементам через тег
                # Это важно, чтобы клики на текст и фигуры тоже обрабатывались
                # Используем только Button-1, чтобы избежать двойных вызовов
                # Убираем старые привязки перед добавлением новых
                try:
                    canvas.tag_unbind(tag, '<Button-1>')
                except (tk.TclError, AttributeError):
                    pass
                try:
                    canvas.tag_bind(tag, '<Button-1>', on_click)
                except Exception:
                    pass
            finally:
                canvas._drawing = False
        
        # Привязка событий мыши к canvas
        # Важно: привязываем только к canvas, чтобы избежать двойных вызовов
        # Убираем старую привязку перед добавлением новой
        try:
            canvas.unbind('<Button-1>')
        except (tk.TclError, AttributeError):
            pass
        canvas.bind('<Button-1>', on_click)
        canvas.bind('<Enter>', on_enter)
        canvas.bind('<Leave>', on_leave)
        canvas.bind('<Configure>', on_configure)
        
        # Убеждаемся, что canvas может получать события
        canvas.update_idletasks()
        
        # Привязываем события после первой отрисовки
        canvas.after(50, lambda: draw_button('normal'))
        
        # Добавляем tooltip с названием кнопки (используем tooltip если указан, иначе text)
        tooltip_text = tooltip if tooltip is not None else text
        ToolTip(canvas, text=tooltip_text)
        ToolTip(btn_frame, text=tooltip_text)
        
        return btn_frame
    
    @staticmethod
    def create_square_icon_button(
        parent,
        icon: str,
        command: Callable,
        bg_color: str = '#667EEA',
        fg_color: str = 'white',
        size: int = 40,
        active_bg: Optional[str] = None,
        tooltip: Optional[str] = None
    ) -> tk.Frame:
        """Создание квадратной кнопки со значком.
        
        Args:
            parent: Родительский виджет
            icon: Текст значка (например, "+", "-", "?", "✓")
            command: Функция-обработчик клика
            bg_color: Цвет фона
            fg_color: Цвет текста/значка
            size: Размер кнопки в пикселях (ширина и высота)
            active_bg: Цвет фона при наведении
            
        Returns:
            Frame с кнопкой внутри
        """
        if active_bg is None:
            active_bg = bg_color
        
        # Создаем Frame с фиксированными размерами для квадратной кнопки
        btn_frame = tk.Frame(parent, bg=parent.cget('bg'), width=size, height=size)
        btn_frame.grid_propagate(False)  # Запрещаем изменение размера фрейма при использовании grid
        btn_frame.pack_propagate(False)  # Запрещаем изменение размера фрейма при использовании pack
        
        # Используем Canvas для точного центрирования иконки
        canvas = tk.Canvas(
            btn_frame,
            highlightthickness=0,
            borderwidth=0,
            bg=bg_color,
            width=size,
            height=size,
            cursor='hand2'
        )
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Сохраняем параметры
        canvas.btn_icon = icon
        canvas.btn_command = command
        canvas.btn_bg = bg_color
        canvas.btn_fg = fg_color
        canvas.btn_active_bg = active_bg
        canvas.btn_size = size
        canvas.btn_state = 'normal'
        
        def on_click(e=None):
            if hasattr(canvas, 'btn_command') and canvas.btn_command and callable(canvas.btn_command):
                try:
                    canvas.btn_command()
                except Exception as ex:
                    logger.error(f"Ошибка при нажатии кнопки: {ex}", exc_info=True)
        
        def on_enter(e):
            if canvas.btn_state != 'active':
                canvas.btn_state = 'active'
                draw_button('active')
        
        def on_leave(e):
            if canvas.btn_state != 'normal':
                canvas.btn_state = 'normal'
                draw_button('normal')
        
        def draw_button(state: str = 'normal'):
            canvas.delete('all')
            # Получаем актуальные размеры canvas
            try:
                w = canvas.winfo_width()
                h = canvas.winfo_height()
                if w <= 1 or h <= 1:
                    w = canvas.btn_size
                    h = canvas.btn_size
            except (tk.TclError, AttributeError):
                w = canvas.btn_size
                h = canvas.btn_size
            
            if w <= 1 or h <= 1:
                return
            
            color = canvas.btn_active_bg if state == 'active' else canvas.btn_bg
            text_color = canvas.btn_fg
            
            # Конвертируем цвет в hex
            if isinstance(color, tuple):
                color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
            elif isinstance(color, str) and color.startswith('#'):
                color_hex = color
            else:
                color_hex = str(color) if color else '#6366F1'
                if not color_hex.startswith('#'):
                    color_hex = '#6366F1'
            
            # Рисуем прямоугольник (квадратную кнопку)
            canvas.create_rectangle(0, 0, w, h, fill=color_hex, outline=color_hex, tags='button_item')
            
            # Центрируем иконку точно по центру (anchor='center' центрирует текст относительно точки)
            # Используем точные координаты центра
            center_x = w / 2.0
            center_y = h / 2.0
            # Для лупы и дискеты немного смещаем вверх для лучшего визуального восприятия
            if canvas.btn_icon == "🔍" or canvas.btn_icon == "💾":
                center_y = h / 2.0 - 2
            # Для корзинки смещаем правее и выше
            if canvas.btn_icon == "🗑️":
                center_x = w / 2.0 + 13
                center_y = h / 2.0 - 2
            # Для эмодзи используем anchor='center' без justify, чтобы обеспечить точное центрирование
            # Используем шрифт, который хорошо поддерживает эмодзи
            canvas.create_text(center_x, center_y, text=canvas.btn_icon, 
                             fill=text_color, font=('Arial', 14), 
                             anchor='center', tags='button_item')
            
            # Привязываем события
            try:
                canvas.tag_unbind('button_item', '<Button-1>')
            except (tk.TclError, AttributeError):
                pass
            try:
                canvas.tag_bind('button_item', '<Button-1>', on_click)
            except Exception:
                pass
        
        # Привязка событий
        canvas.bind('<Button-1>', on_click)
        canvas.bind('<Enter>', on_enter)
        canvas.bind('<Leave>', on_leave)
        canvas.bind('<Configure>', lambda e: draw_button(canvas.btn_state))
        
        # Первая отрисовка
        canvas.after(50, lambda: draw_button('normal'))
        
        # Добавляем tooltip с названием кнопки
        if tooltip is not None:
            tooltip_text = tooltip
        else:
            # Для квадратных кнопок создаем понятное название на основе иконки
            tooltip_text = icon
            icon_to_text = {
                '?': 'Справка',
                '✓': 'Применить',
                '+': 'Добавить',
                '-': 'Очистить',
                '➖': 'Удалить',
                '🗑️': 'Удалить',
                '▶': 'Начать',
                '▶️': 'Начать',
                '💾': 'Сохранить',
                '👁': 'Предпросмотр',
                '👀': 'Предпросмотр',
                '⏸️': 'Пауза',
                '⏹️': 'Остановить'
            }
            if icon in icon_to_text:
                tooltip_text = icon_to_text[icon]
            elif len(icon) > 1:
                # Если иконка содержит текст (например, "➕ Добавить"), используем его
                tooltip_text = icon
        
        ToolTip(canvas, text=tooltip_text)
        ToolTip(btn_frame, text=tooltip_text)
        
        return btn_frame
    
    @staticmethod
    def create_rounded_icon_button(
        parent,
        icon: str,
        command: Callable,
        bg_color: str = '#667EEA',
        fg_color: str = 'white',
        size: int = 40,
        active_bg: Optional[str] = None,
        tooltip: Optional[str] = None,
        radius: int = 8
    ) -> tk.Frame:
        """Создание округлой кнопки со значком (иконкой).
        
        Args:
            parent: Родительский виджет
            icon: Текст значка (например, "+", "-", "?", "✓", "💾", "👀")
            command: Функция-обработчик клика
            bg_color: Цвет фона
            fg_color: Цвет текста/значка
            size: Размер кнопки в пикселях (ширина и высота)
            active_bg: Цвет фона при наведении
            tooltip: Текст подсказки
            radius: Радиус закругления углов
            
        Returns:
            Frame с кнопкой внутри
        """
        if active_bg is None:
            active_bg = bg_color
        
        # Фрейм для кнопки
        btn_frame = tk.Frame(parent, bg=parent.cget('bg'), width=size, height=size)
        btn_frame.grid_propagate(False)
        btn_frame.pack_propagate(False)
        
        # Canvas для закругленного фона
        canvas = tk.Canvas(
            btn_frame,
            highlightthickness=0,
            borderwidth=0,
            bg=parent.cget('bg'),
            width=size,
            height=size,
            cursor='hand2'
        )
        canvas.pack(fill=tk.BOTH, expand=True)
        
        # Сохраняем параметры
        canvas.btn_icon = icon
        canvas.btn_command = command
        canvas.btn_bg = bg_color
        canvas.btn_fg = fg_color
        canvas.btn_active_bg = active_bg
        canvas.btn_size = size
        canvas.btn_radius = radius
        canvas.btn_state = 'normal'
        
        # Флаг для предотвращения бесконечных вызовов
        canvas._drawing = False
        
        def on_click(e=None):
            if hasattr(canvas, 'btn_command') and canvas.btn_command and callable(canvas.btn_command):
                try:
                    canvas.btn_command()
                except Exception as ex:
                    logger.error(f"Ошибка при нажатии кнопки: {ex}", exc_info=True)
        
        def on_enter(e):
            if canvas.btn_state != 'active':
                canvas.btn_state = 'active'
                draw_button('active')
        
        def on_leave(e):
            if canvas.btn_state != 'normal':
                canvas.btn_state = 'normal'
                draw_button('normal')
        
        def draw_button(state: str = 'normal'):
            if canvas._drawing:
                return
            
            canvas._drawing = True
            try:
                canvas.delete('all')
                w = canvas.btn_size
                h = canvas.btn_size
                
                if w <= 1 or h <= 1:
                    return
                
                r = canvas.btn_radius
                color = canvas.btn_active_bg if state == 'active' else canvas.btn_bg
                text_color = canvas.btn_fg
                
                # Конвертируем цвет в hex
                if isinstance(color, tuple):
                    color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                elif isinstance(color, str) and color.startswith('#'):
                    color_hex = color
                else:
                    color_hex = str(color) if color else '#6366F1'
                    if not color_hex.startswith('#'):
                        color_hex = '#6366F1'
                
                # Рисуем закругленный прямоугольник
                tag = 'button_item'
                # Верхние углы
                canvas.create_arc(0, 0, r*2, r*2, start=90, extent=90, 
                                fill=color_hex, outline=color_hex, tags=tag)
                canvas.create_arc(w-r*2, 0, w, r*2, start=0, extent=90, 
                                fill=color_hex, outline=color_hex, tags=tag)
                # Нижние углы
                canvas.create_arc(0, h-r*2, r*2, h, start=180, extent=90, 
                                fill=color_hex, outline=color_hex, tags=tag)
                canvas.create_arc(w-r*2, h-r*2, w, h, start=270, extent=90, 
                                fill=color_hex, outline=color_hex, tags=tag)
                # Прямоугольники для заполнения
                canvas.create_rectangle(r, 0, w-r, h, fill=color_hex, outline=color_hex, tags=tag)
                canvas.create_rectangle(0, r, w, h-r, fill=color_hex, outline=color_hex, tags=tag)
                
                # Центрируем иконку
                canvas.create_text(w//2, h//2, text=canvas.btn_icon, 
                                 fill=text_color, font=('Arial', 12, 'bold'), 
                                 anchor='center', tags=tag)
                
                # Привязываем события
                try:
                    canvas.tag_unbind(tag, '<Button-1>')
                except (tk.TclError, AttributeError):
                    pass
                try:
                    canvas.tag_bind(tag, '<Button-1>', on_click)
                except Exception:
                    pass
            finally:
                canvas._drawing = False
        
        # Привязка событий
        canvas.bind('<Button-1>', on_click)
        canvas.bind('<Enter>', on_enter)
        canvas.bind('<Leave>', on_leave)
        canvas.bind('<Configure>', lambda e: draw_button(canvas.btn_state))
        
        # Первая отрисовка
        canvas.after(50, lambda: draw_button('normal'))
        
        # Tooltip
        if tooltip is not None:
            tooltip_text = tooltip
        else:
            tooltip_text = icon
            icon_to_text = {
                '?': 'Справка',
                '✓': 'Применить',
                '+': 'Добавить',
                '-': 'Очистить',
                '💾': 'Сохранить',
                '👀': 'Предпросмотр',
                '🗑️': 'Удалить'
            }
            if icon in icon_to_text:
                tooltip_text = icon_to_text[icon]
        
        ToolTip(canvas, text=tooltip_text)
        ToolTip(btn_frame, text=tooltip_text)
        
        return btn_frame
    
    @staticmethod
    def create_rounded_top_tab_button(
        parent,
        text: str,
        command: Callable,
        bg_color: str,
        fg_color: str = '#1A202C',
        font: Tuple[str, int, str] = ('Robot', 11, 'bold'),
        padx: int = 10,
        pady: int = 1,
        active_bg: Optional[str] = None,
        active_fg: str = 'white',
        radius: int = 8
    ) -> tk.Frame:
        """Создание кнопки вкладки с закругленными только верхними углами через Canvas"""
        
        # Фрейм для кнопки
        btn_frame = tk.Frame(parent, bg=parent.cget('bg'))
        
        # Вычисляем минимальную ширину на основе текста
        temp_label = tk.Label(parent, text=text, font=font)
        temp_label.update_idletasks()
        text_width = temp_label.winfo_reqwidth()
        temp_label.destroy()
        min_width = text_width + padx * 2
        
        # Canvas для закругленного фона (только верхние углы)
        canvas_height = pady * 2 + 20  # Высота с учетом отступов
        canvas = tk.Canvas(
            btn_frame, 
            highlightthickness=0, 
            borderwidth=0,
            bg=parent.cget('bg'), 
            height=canvas_height,
            width=min_width,
            cursor='hand2'
        )
        canvas.pack(fill=tk.NONE, expand=False)
        
        # Сохраняем параметры
        canvas.btn_text = text
        canvas.btn_command = command
        canvas.btn_bg = bg_color
        canvas.btn_fg = fg_color
        canvas.btn_active_bg = active_bg if active_bg else bg_color
        canvas.btn_active_fg = active_fg
        canvas.btn_font = font
        canvas.btn_state = 'normal'
        canvas.btn_padx = padx
        canvas.btn_radius = radius
        
        # Флаг для предотвращения бесконечных вызовов
        canvas._drawing = False
        
        def on_click(e=None):
            if canvas.btn_command:
                canvas.btn_command()
        
        def on_enter(e):
            if canvas.btn_state != 'active':
                canvas.btn_state = 'active'
                draw_tab_button('active')
        
        def on_leave(e):
            if canvas.btn_state != 'normal':
                canvas.btn_state = 'normal'
                draw_tab_button('normal')
        
        def on_configure(e):
            draw_tab_button(canvas.btn_state)
        
        def draw_tab_button(state: str = 'normal'):
            if canvas._drawing:
                return
            canvas._drawing = True
            try:
                canvas.delete('all')
                w = canvas.winfo_width()
                h = canvas.winfo_height()
                
                if w <= 1 or h <= 1:
                    canvas.after(50, lambda: draw_tab_button(state))
                    return
                
                color = canvas.btn_active_bg if state == 'active' else canvas.btn_bg
                text_color = canvas.btn_active_fg if state == 'active' else canvas.btn_fg
                
                # Конвертируем цвет в hex для Canvas
                if isinstance(color, tuple):
                    color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                else:
                    color_hex = color
                
                # Рисуем только верхние закругленные углы
                r = canvas.btn_radius
                
                # Верхний левый угол (arc)
                canvas.create_arc(0, 0, r*2, r*2, start=90, extent=90, 
                                fill=color_hex, outline=color_hex)
                
                # Верхний правый угол (arc)
                canvas.create_arc(w-r*2, 0, w, r*2, start=0, extent=90, 
                                fill=color_hex, outline=color_hex)
                
                # Основной прямоугольник (заполняет всю область, включая верх)
                canvas.create_rectangle(0, r, w, h, fill=color_hex, outline=color_hex)
                canvas.create_rectangle(r, 0, w-r, h, fill=color_hex, outline=color_hex)
                
                # Текст
                canvas.create_text(w//2, h//2, text=canvas.btn_text, 
                                 fill=text_color, font=canvas.btn_font, tags=('text',))
                
            finally:
                canvas._drawing = False
        
        # Сохраняем функцию перерисовки в canvas для внешнего доступа
        canvas.draw_button = draw_tab_button
        
        canvas.bind('<Button-1>', on_click)
        canvas.bind('<Enter>', on_enter)
        canvas.bind('<Leave>', on_leave)
        canvas.bind('<Configure>', on_configure)
        
        # Первоначальная отрисовка
        canvas.after_idle(lambda: draw_tab_button('normal'))
        
        return btn_frame


"""Модуль для UI компонентов, стилей и утилит работы с окнами.

Объединяет:
- UI компоненты и стили (UIComponents, StyleManager)
- Утилиты для работы с окнами (set_window_icon, bind_mousewheel, setup_window_resize_handler)
- Менеджер тем (ThemeManager)
"""

import os
import sys
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Tuple, Dict

# Попытка импортировать PIL для работы с иконками
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Попытка импортировать ctypes для Windows API (для установки иконки в панели задач)
if sys.platform == 'win32':
    try:
        import ctypes
        from ctypes import wintypes
        HAS_CTYPES = True
    except ImportError:
        HAS_CTYPES = False
else:
    HAS_CTYPES = False

# Константы для прокрутки мыши
MOUSEWHEEL_DELTA_DIVISOR = 120  # Делитель для нормализации прокрутки в Windows
LINUX_SCROLL_UP = 4  # Код прокрутки вверх для Linux
LINUX_SCROLL_DOWN = 5  # Код прокрутки вниз для Linux


class ToolTip:
    """Класс для создания подсказок при наведении на виджеты."""
    
    def __init__(self, widget, text='', delay=500):
        """
        Инициализация tooltip.
        
        Args:
            widget: Виджет, для которого создается подсказка
            text: Текст подсказки
            delay: Задержка перед показом подсказки (в миллисекундах)
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        
        # Привязываем события
        self.widget.bind('<Enter>', self.enter)
        self.widget.bind('<Leave>', self.leave)
        self.widget.bind('<ButtonPress>', self.leave)
    
    def enter(self, event=None):
        """Показ подсказки при наведении."""
        self.schedule()
    
    def leave(self, event=None):
        """Скрытие подсказки при уходе курсора."""
        self.unschedule()
        self.hidetip()
    
    def schedule(self):
        """Планирование показа подсказки."""
        self.unschedule()
        self.id = self.widget.after(self.delay, self.showtip)
    
    def unschedule(self):
        """Отмена показа подсказки."""
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)
    
    def showtip(self, event=None):
        """Показ подсказки."""
        if self.tipwindow or not self.text:
            return
        
        # Получаем координаты виджета
        try:
            # Для Canvas виджетов используем winfo_rootx/y
            if isinstance(self.widget, tk.Canvas):
                x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
                y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            else:
                # Для обычных виджетов
                x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
                y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        except (tk.TclError, AttributeError):
            # Если не удалось получить координаты, используем позицию курсора
            try:
                x = self.widget.winfo_pointerx() + 10
                y = self.widget.winfo_pointery() + 10
            except (tk.TclError, AttributeError):
                x = 100
                y = 100
        
        # Создаем окно подсказки
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry("+%d+%d" % (x, y))
        
        # Стилизуем подсказку
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                        background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                        font=('Robot', 9))
        label.pack(ipadx=4, ipady=2)
        
        # Центрируем подсказку относительно виджета
        try:
            tw.update_idletasks()
            tw_width = tw.winfo_width()
            x = x - tw_width // 2
            tw.wm_geometry("+%d+%d" % (x, y))
        except (tk.TclError, AttributeError):
            pass
    
    def hidetip(self):
        """Скрытие подсказки."""
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()


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
            def empty_command():
                pass
            command = empty_command
        
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
            import logging
            logging.getLogger(__name__).warning("Команда кнопки не передана!")
        elif not callable(command):
            import logging
            logging.getLogger(__name__).warning(f"Команда кнопки не является вызываемой: {type(command)}")
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
                            import tkinter.messagebox as mb
                            mb.showerror("Ошибка", "Команда кнопки не является вызываемой функцией")
                        except Exception:
                            pass
                else:
                    # Показываем ошибку пользователю
                    try:
                        import tkinter.messagebox as mb
                        mb.showerror("Ошибка", "Команда кнопки не найдена")
                    except Exception:
                        pass
            except Exception as ex:
                # Логируем ошибку в файл, так как консоль может быть недоступна
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Ошибка при нажатии кнопки: {ex}", exc_info=True)
                # Также показываем сообщение пользователю
                try:
                    import tkinter.messagebox as mb
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
                    import logging
                    logging.getLogger(__name__).error(f"Ошибка при нажатии кнопки: {ex}", exc_info=True)
        
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
        # Если tooltip указан явно, используем его, иначе создаем на основе иконки
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
                '🗑️': 'Очистить',
                '▶': 'Начать',
                '▶️': 'Начать',
                '💾': 'Сохранить',
                '👁': 'Предпросмотр',
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
                    import logging
                    logging.getLogger(__name__).error(f"Ошибка при нажатии кнопки: {ex}", exc_info=True)
        
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


class StyleManager:
    """Класс для управления стилями интерфейса."""
    
    def __init__(self):
        """Инициализация менеджера стилей."""
        self.style = ttk.Style()
        self.colors = self._get_color_scheme()
        self._setup_theme()
        self._setup_styles()
    
    def _get_color_scheme(self) -> dict:
        """Получение цветовой схемы."""
        return {
            'primary': '#667EEA',
            'primary_hover': '#5568D3',
            'primary_light': '#818CF8',
            'primary_dark': '#4C51BF',
            'success': '#10B981',
            'success_hover': '#059669',
            'danger': '#EF4444',
            'danger_hover': '#DC2626',
            'warning': '#F59E0B',
            'warning_hover': '#D97706',
            'info': '#3B82F6',
            'info_hover': '#2563EB',
            'secondary': '#6B7280',
            'secondary_hover': '#4B5563',
            'bg_main': '#FFFFFF',
            'bg_card': '#FFFFFF',  # Оставлено для совместимости, но не используется
            'bg_secondary': '#FFFFFF',  # Изменено на bg_main для единого фона
            'bg_hover': '#F7FAFC',
            'bg_input': '#FFFFFF',
            'bg_elevated': '#FFFFFF',
            'border': '#E2E8F0',
            'border_focus': '#667EEA',
            'border_light': '#F1F5F9',
            'text_primary': '#1A202C',
            'text_secondary': '#4A5568',
            'text_muted': '#718096',
            'header_bg': '#FFFFFF',
            'header_text': '#1A202C',
            'accent': '#9F7AEA',
            'shadow': 'rgba(0,0,0,0.08)',
            'shadow_lg': 'rgba(0,0,0,0.12)',
            'shadow_xl': 'rgba(0,0,0,0.16)',
            'glow': 'rgba(102, 126, 234, 0.4)',
            'gradient_start': '#667EEA',
            'gradient_end': '#764BA2'
        }
    
    def _setup_theme(self):
        """Настройка темы."""
        try:
            self.style.theme_use('vista')
        except Exception:
            try:
                self.style.theme_use('clam')
            except Exception:
                pass
    
    def _setup_styles(self):
        """Настройка стилей виджетов."""
        # Стиль для основных кнопок
        self.style.configure('Primary.TButton', 
                           background=self.colors['primary'],
                           foreground='white',
                           font=('Robot', 10, 'bold'),
                           padding=(16, 10),
                           borderwidth=0,
                           focuscolor='none',
                           relief='flat',
                           anchor='center')
        self.style.map('Primary.TButton',
                     background=[('active', self.colors['primary_hover']), 
                               ('pressed', self.colors['primary_dark']),
                               ('disabled', '#94A3B8')],
                     foreground=[('active', 'white'), 
                              ('pressed', 'white'),
                              ('disabled', '#E2E8F0')],
                     relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Стиль для кнопок успеха
        self.style.configure('Success.TButton',
                           background=self.colors['success'],
                           foreground='white',
                           font=('Robot', 9, 'bold'),
                           padding=(10, 6),
                           borderwidth=0,
                           focuscolor='none',
                           relief='flat',
                           anchor='center')
        self.style.map('Success.TButton',
                     background=[('active', self.colors['success_hover']), 
                               ('pressed', '#047857'),
                               ('disabled', '#94A3B8')],
                     foreground=[('active', 'white'), 
                              ('pressed', 'white'),
                              ('disabled', '#E2E8F0')],
                     relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Стиль для кнопок опасности
        self.style.configure('Danger.TButton',
                           background=self.colors['danger'],
                           foreground='white',
                           font=('Robot', 9, 'bold'),
                           padding=(10, 6),
                           borderwidth=0,
                           focuscolor='none',
                           relief='flat',
                           anchor='center')
        self.style.map('Danger.TButton',
                     background=[('active', self.colors['danger_hover']), 
                               ('pressed', '#B91C1C'),
                               ('disabled', '#94A3B8')],
                     foreground=[('active', 'white'), 
                              ('pressed', 'white'),
                              ('disabled', '#E2E8F0')],
                     relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Стиль для обычных кнопок
        self.style.configure('TButton',
                           font=('Robot', 9, 'bold'),
                           padding=(10, 6),
                           borderwidth=0,
                           relief='flat',
                           background='#F59E0B',
                           foreground='white',
                           anchor='center')
        self.style.map('TButton',
                     background=[('active', '#D97706'), 
                               ('pressed', '#B45309'),
                               ('disabled', '#94A3B8')],
                     foreground=[('active', 'white'),
                              ('pressed', 'white'),
                              ('disabled', '#E2E8F0')],
                     relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Стиль для вторичных кнопок
        self.style.configure('Secondary.TButton',
                           font=('Robot', 9, 'bold'),
                           padding=(10, 6),
                           borderwidth=0,
                           relief='flat',
                           background='#818CF8',
                           foreground='white',
                           anchor='center')
        self.style.map('Secondary.TButton',
                     background=[('active', '#6366F1'), 
                               ('pressed', '#4F46E5'),
                               ('disabled', '#94A3B8')],
                     foreground=[('active', 'white'),
                              ('pressed', 'white'),
                              ('disabled', '#E2E8F0')],
                     relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Стиль для предупреждающих кнопок
        self.style.configure('Warning.TButton',
                           font=('Robot', 9, 'bold'),
                           padding=(10, 6),
                           borderwidth=0,
                           relief='flat',
                           background='#F59E0B',
                           foreground='white',
                           anchor='center')
        self.style.map('Warning.TButton',
                     background=[('active', '#D97706'), 
                               ('pressed', '#B45309'),
                               ('disabled', '#94A3B8')],
                     foreground=[('active', 'white'),
                              ('pressed', 'white'),
                              ('disabled', '#E2E8F0')],
                     relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Стиль для LabelFrame
        self.style.configure('Card.TLabelframe', 
                           background=self.colors['bg_main'],
                           borderwidth=0,
                           relief='flat',
                           bordercolor=self.colors['border'],
                           padding=24)
        self.style.configure('Card.TLabelframe.Label',
                           background=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           font=('Robot', 11, 'bold'),
                           padding=(0, 0, 0, 12))
        
        # Стиль для PanedWindow
        self.style.configure('TPanedwindow',
                           background=self.colors['bg_main'])
        self.style.configure('TPanedwindow.Sash',
                           sashthickness=6,
                           sashrelief='flat',
                           sashpad=0)
        self.style.map('TPanedwindow.Sash',
                     background=[('hover', self.colors['primary_light']),
                               ('active', self.colors['primary'])])
        
        # Стиль для меток
        self.style.configure('TLabel',
                           background=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           font=('Robot', 9))
        
        # Стиль для Frame
        self.style.configure('TFrame',
                           background=self.colors['bg_main'])
        
        # Стиль для Notebook
        self.style.configure('TNotebook',
                           background=self.colors['bg_main'],
                           borderwidth=0)
        self.style.configure('TNotebook.Tab',
                           padding=(20, 8),  # Уменьшено с 12 до 8 (на 1/3)
                           font=('Robot', 10, 'bold'),
                           background=self.colors['bg_main'],
                           foreground='#000000')  # Черный цвет шрифта
        self.style.map('TNotebook.Tab',
                     background=[('selected', self.colors['bg_main']),  # Убрана подсветка выбранной вкладки
                               ('active', self.colors['bg_hover'])],
                     foreground=[('selected', '#000000'),  # Черный цвет для выбранной вкладки
                               ('active', '#000000')],  # Черный цвет для активной вкладки
                     expand=[('selected', [1, 1, 1, 0])])
        
        # Стиль для Radiobutton
        self.style.configure('TRadiobutton',
                           background=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           font=('Robot', 11),
                           selectcolor='white')
        
        # Стиль для Checkbutton
        self.style.configure('TCheckbutton',
                           background=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           font=('Robot', 11),
                           selectcolor='white')
        
        # Стиль для Entry
        self.style.configure('TEntry',
                           fieldbackground=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           borderwidth=2,
                           relief='flat',
                           padding=10,
                           font=('Robot', 10))
        self.style.map('TEntry',
                     bordercolor=[('focus', self.colors['border_focus']),
                                ('!focus', self.colors['border'])],
                     lightcolor=[('focus', self.colors['border_focus']),
                               ('!focus', self.colors['border'])],
                     darkcolor=[('focus', self.colors['border_focus']),
                              ('!focus', self.colors['border'])])
        
        # Стиль для Combobox
        self.style.configure('TCombobox',
                           fieldbackground=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           borderwidth=2,
                           relief='flat',
                           padding=10,
                           font=('Robot', 11))
        self.style.map('TCombobox',
                     bordercolor=[('focus', self.colors['border_focus']),
                                ('!focus', self.colors['border'])],
                     selectbackground=[('focus', self.colors['bg_main'])],
                     selectforeground=[('focus', self.colors['text_primary'])])
        
        # Стиль для Treeview
        self.style.configure('Custom.Treeview',
                           rowheight=30,
                           font=('Robot', 10),
                           background=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           fieldbackground=self.colors['bg_main'],
                           borderwidth=0)
        self.style.configure('Custom.Treeview.Heading',
                           font=('Robot', 10, 'bold'),
                           background=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           borderwidth=0,
                           relief='flat',
                           padding=(12, 10))
        self.style.map('Custom.Treeview.Heading',
                     background=[('active', self.colors['bg_hover'])])
        self.style.map('Custom.Treeview',
                     background=[('selected', self.colors['primary'])],
                     foreground=[('selected', 'white')])


# ============================================================================
# УТИЛИТЫ ДЛЯ РАБОТЫ С ОКНАМИ (из window_utils.py)
# ============================================================================

def load_image_icon(
    icon_name: str,
    size: Optional[Tuple[int, int]] = None,
    icons_list: Optional[list] = None
) -> Optional[tk.PhotoImage]:
    """Загрузка иконки из папки materials/icon.
    
    Универсальная функция для загрузки изображений иконок с автоматическим
    определением формата (PNG, ICO) и опциональным изменением размера.
    
    Args:
        icon_name: Имя файла иконки (например, "Логотип.png" или "ВКонтакте.png")
        size: Кортеж (width, height) для изменения размера. Если None, размер не изменяется.
        icons_list: Список для сохранения ссылки на изображение (предотвращает удаление GC).
    
    Returns:
        PhotoImage объект или None если загрузка не удалась.
    """
    if not HAS_PIL:
        return None
    
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Пробуем разные варианты путей
        possible_paths = [
            os.path.join(base_dir, "materials", "icon", icon_name),
            os.path.join(base_dir, "materials", "icon", icon_name.replace('.png', '.ico')),
            os.path.join(base_dir, "materials", "icon", icon_name.replace('.ico', '.png')),
        ]
        
        image_path = None
        for path in possible_paths:
            if os.path.exists(path):
                image_path = path
                break
        
        if not image_path:
            return None
        
        img = Image.open(image_path)
        
        # Изменяем размер если указан
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        
        photo = ImageTk.PhotoImage(img)
        
        # Сохраняем ссылку если передан список
        if icons_list is not None:
            icons_list.append(photo)
        
        return photo
    except Exception:
        return None


# Глобальный словарь для отслеживания установленных иконок (чтобы не устанавливать повторно)
_icon_set_flags = {}

def set_window_icon(window: tk.Tk, icon_photos_list: Optional[list] = None) -> None:
    """Установка иконки приложения для окна и панели задач.
    
    Пытается загрузить иконку из файлов icon.ico (приоритет), Логотип.ico или Логотип.png.
    Использует iconbitmap для Windows (лучше всего для панели задач) и
    iconphoto для кроссплатформенной поддержки.
    Также использует Windows API для более надежной установки иконки в панели задач.
    
    Args:
        window: Окно Tkinter для установки иконки
        icon_photos_list: Список для хранения ссылок на изображения (опционально).
                         Необходим для предотвращения удаления изображений сборщиком мусора.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Инициализируем флаг для отслеживания установки иконки
    window_id = id(window)
    if window_id not in _icon_set_flags:
        _icon_set_flags[window_id] = {'icon_set': False, 'api_set': False}
    
    # Проверяем, была ли иконка уже установлена для этого окна
    if _icon_set_flags[window_id].get('icon_set', False):
        # Иконка уже установлена, пропускаем (но разрешаем одну повторную попытку через API)
        if _icon_set_flags[window_id].get('api_set', False):
            return  # Полностью пропускаем
        # Разрешаем только установку через Windows API (если еще не была установлена)
        if sys.platform != 'win32' or not HAS_CTYPES:
            return
    
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # Приоритет: icon.ico -> Логотип.ico -> Логотип.png
        # Сначала пробуем использовать .ico файл для Windows (лучше всего для панели задач)
        ico_path = os.path.join(base_dir, "materials", "icon", "icon.ico")
        if not os.path.exists(ico_path):
            ico_path = os.path.join(base_dir, "materials", "icon", "Логотип.ico")
        ico_path = os.path.normpath(ico_path)
        
        if os.path.exists(ico_path):
            try:
                # Преобразуем в абсолютный путь для надежности
                ico_path = os.path.abspath(ico_path)
                
                # iconbitmap устанавливает иконку для окна и панели задач в Windows
                # Это самый надежный способ для панели задач
                if not _icon_set_flags[window_id]['icon_set']:
                    try:
                        window.iconbitmap(ico_path)
                        _icon_set_flags[window_id]['icon_set'] = True
                        logger.info(f"Иконка установлена через iconbitmap: {ico_path}")
                    except Exception as iconbitmap_error:
                        logger.debug(f"iconbitmap не сработал: {iconbitmap_error}, пробуем через PIL")
                        # Если iconbitmap не работает, пробуем через PIL
                        if HAS_PIL:
                            try:
                                img = Image.open(ico_path)
                                photo = ImageTk.PhotoImage(img)
                                window.iconphoto(True, photo)
                                if icon_photos_list is not None:
                                    icon_photos_list.append(photo)
                                _icon_set_flags[window_id]['icon_set'] = True
                                logger.info(f"Иконка установлена через PIL из ICO: {ico_path}")
                            except Exception:
                                pass
                
                # Используем Windows API для установки иконки в панели задач и процесса
                # Это критически важно для отображения иконки в панели задач и диспетчере задач Windows
                if sys.platform == 'win32' and HAS_CTYPES and not _icon_set_flags[window_id]['api_set']:
                    def set_taskbar_icon():
                        """Установка иконки в панели задач и процесса через Windows API"""
                        # Проверяем, не была ли уже установлена иконка через API
                        if _icon_set_flags.get(window_id, {}).get('api_set', False):
                            return
                        try:
                            # Ждем полной инициализации окна
                            window.update_idletasks()
                            window.update()
                            
                            # Получаем HWND окна - правильный способ для Tkinter
                            hwnd = None
                            try:
                                # Метод 1: В Tkinter winfo_id() возвращает HWND напрямую для Windows
                                widget_id = window.winfo_id()
                                
                                # Проверяем, что это валидный HWND (должен быть > 0)
                                if widget_id and widget_id > 0:
                                    # В Tkinter для Windows winfo_id() может вернуть HWND окна или виджета
                                    # Проверяем, является ли это окном верхнего уровня
                                    window_style = ctypes.windll.user32.GetWindowLongW(widget_id, -16)  # GWL_STYLE
                                    # WS_OVERLAPPEDWINDOW = 0x00CF0000, проверяем что это окно
                                    if window_style & 0x80000000:  # WS_POPUP или WS_OVERLAPPED
                                        hwnd = widget_id
                                    else:
                                        # Если это виджет, получаем родительское окно
                                        parent_hwnd = ctypes.windll.user32.GetParent(widget_id)
                                        if parent_hwnd and parent_hwnd != 0:
                                            hwnd = parent_hwnd
                                        else:
                                            # Пробуем получить окно через GetAncestor
                                            hwnd = ctypes.windll.user32.GetAncestor(widget_id, 2)  # GA_ROOT
                                
                                # Метод 2: Если не получили, пробуем найти окно по заголовку
                                if not hwnd or hwnd == 0:
                                    window_title = window.title()
                                    if window_title:
                                        hwnd = ctypes.windll.user32.FindWindowW(None, window_title)
                                        # Проверяем, что это действительно наше окно
                                        if hwnd:
                                            buffer = ctypes.create_unicode_buffer(256)
                                            ctypes.windll.user32.GetWindowTextW(hwnd, buffer, 256)
                                            if buffer.value != window_title:
                                                hwnd = 0
                                
                                # Метод 3: Пробуем через GetForegroundWindow (если окно активно)
                                if not hwnd or hwnd == 0:
                                    fg_hwnd = ctypes.windll.user32.GetForegroundWindow()
                                    if fg_hwnd and fg_hwnd != 0:
                                        # Проверяем, что это наше окно по заголовку
                                        window_title = window.title()
                                        if window_title:
                                            buffer = ctypes.create_unicode_buffer(256)
                                            ctypes.windll.user32.GetWindowTextW(fg_hwnd, buffer, 256)
                                            if buffer.value == window_title:
                                                hwnd = fg_hwnd
                                
                                # Метод 4: Последняя попытка - через класс окна Tkinter
                                if not hwnd or hwnd == 0:
                                    # Ищем окно по классу TkTopLevel (класс окон Tkinter)
                                    hwnd = ctypes.windll.user32.FindWindowW("TkTopLevel", None)
                                    
                            except Exception as hwnd_error:
                                logger.debug(f"Ошибка получения HWND: {hwnd_error}")
                                hwnd = None
                            
                            if hwnd and hwnd != 0:
                                # Загружаем иконку через LoadImage для меню Пуск и панели задач
                                # IMAGE_ICON = 1, LR_LOADFROMFILE = 0x0010
                                ico_path_unicode = str(ico_path)
                                
                                # Константы для LoadImage
                                IMAGE_ICON = 1
                                LR_LOADFROMFILE = 0x0010
                                LR_DEFAULTSIZE = 0x0040
                                
                                # Загружаем иконки разных размеров для процесса
                                # Для меню Пуск нужны размеры: 16x16, 32x32, 48x48
                                hicon_16 = ctypes.windll.user32.LoadImageW(
                                    None,  # hInst = None для загрузки из файла
                                    ico_path_unicode,
                                    IMAGE_ICON,
                                    16, 16,
                                    LR_LOADFROMFILE
                                )
                                hicon_32 = ctypes.windll.user32.LoadImageW(
                                    None,
                                    ico_path_unicode,
                                    IMAGE_ICON,
                                    32, 32,
                                    LR_LOADFROMFILE
                                )
                                hicon_48 = ctypes.windll.user32.LoadImageW(
                                    None,
                                    ico_path_unicode,
                                    IMAGE_ICON,
                                    48, 48,
                                    LR_LOADFROMFILE
                                )
                                
                                # Если не удалось загрузить с конкретными размерами, пробуем без указания размеров
                                # (Windows выберет подходящий размер из файла)
                                if not hicon_16:
                                    hicon_16 = ctypes.windll.user32.LoadImageW(
                                        None, ico_path_unicode, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
                                    )
                                if not hicon_32:
                                    hicon_32 = ctypes.windll.user32.LoadImageW(
                                        None, ico_path_unicode, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
                                    )
                                if not hicon_48:
                                    hicon_48 = ctypes.windll.user32.LoadImageW(
                                        None, ico_path_unicode, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE
                                    )
                                
                                # Используем 16x16 как маленькую иконку, 32x32 как большую
                                hicon_small = hicon_16 if hicon_16 else hicon_32
                                hicon_big = hicon_32 if hicon_32 else hicon_48
                                
                                if hicon_small or hicon_big:
                                    # Устанавливаем иконку для окна (WM_SETICON)
                                    # WM_SETICON = 0x0080, ICON_SMALL = 0, ICON_BIG = 1
                                    icon_set_success = False
                                    if hicon_small:
                                        ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon_small)  # ICON_SMALL
                                        icon_set_success = True
                                    if hicon_big:
                                        ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon_big)  # ICON_BIG
                                        icon_set_success = True
                                    
                                    # КРИТИЧНО: Устанавливаем иконку класса окна для процесса
                                    # Это влияет на отображение иконки в диспетчере задач, панели задач и меню Пуск
                                    try:
                                        # GCL_HICONSM = -34 (маленькая иконка класса, 16x16)
                                        # GCL_HICON = -14 (большая иконка класса, 32x32)
                                        # SetClassLongPtrW устанавливает иконку для всего класса окон
                                        
                                        # Определяем правильную функцию для установки иконки класса
                                        if sys.maxsize > 2**32:  # 64-bit
                                            SetClassLongPtr = ctypes.windll.user32.SetClassLongPtrW
                                        else:  # 32-bit
                                            SetClassLongPtr = ctypes.windll.user32.SetClassLongW
                                        
                                        # Устанавливаем маленькую иконку класса (для меню Пуск и панели задач)
                                        if hicon_small:
                                            old_small = SetClassLongPtr(hwnd, -34, hicon_small)  # GCL_HICONSM
                                            if old_small:
                                                # Освобождаем старую иконку, если она была
                                                try:
                                                    ctypes.windll.user32.DestroyIcon(old_small)
                                                except (OSError, AttributeError, ctypes.ArgumentError):
                                                    pass
                                        
                                        # Устанавливаем большую иконку класса (для панели задач)
                                        if hicon_big:
                                            old_big = SetClassLongPtr(hwnd, -14, hicon_big)  # GCL_HICON
                                            if old_big:
                                                # Освобождаем старую иконку, если она была
                                                try:
                                                    ctypes.windll.user32.DestroyIcon(old_big)
                                                except (OSError, AttributeError, ctypes.ArgumentError):
                                                    pass
                                        
                                        # Также устанавливаем иконку 48x48 для меню Пуск (если доступна)
                                        if hicon_48:
                                            # Пробуем установить через SendMessage для больших иконок
                                            try:
                                                # WM_SETICON с ICON_BIG = 1 для больших иконок
                                                ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon_48)
                                            except (OSError, AttributeError, ctypes.ArgumentError):
                                                pass
                                        
                                        # Устанавливаем флаг, что иконка установлена через API
                                        _icon_set_flags[window_id]['api_set'] = True
                                        if icon_set_success:
                                            logger.info(f"Иконка установлена для окна, процесса и меню Пуск: {ico_path}")
                                    except Exception as class_error:
                                        logger.debug(f"Ошибка установки иконки класса: {class_error}")
                                    
                                    # Принудительно обновляем окно и панель задач
                                    ctypes.windll.user32.InvalidateRect(hwnd, None, True)
                                    ctypes.windll.user32.UpdateWindow(hwnd)
                                    
                                    # Обновляем панель задач и меню Пуск через Shell API
                                    try:
                                        # SHCNE_ASSOCCHANGED = 0x08000000 - обновление ассоциаций файлов
                                        # SHCNE_UPDATEITEM = 0x00002000 - обновление элемента
                                        # SHCNF_IDLIST = 0x0000 - флаг для IDList
                                        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
                                        # Дополнительное обновление для меню Пуск
                                        ctypes.windll.shell32.SHChangeNotify(0x00002000, 0x0000, None, None)
                                    except (OSError, AttributeError, ctypes.ArgumentError):
                                        pass
                                    
                                    # Дополнительно: принудительно обновляем иконку процесса
                                    # Это важно для меню Пуск в Windows 10/11
                                    try:
                                        # Получаем PID процесса
                                        process_id = ctypes.c_ulong()
                                        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
                                        
                                        # Обновляем иконку процесса через shell32
                                        # Это помогает Windows правильно отобразить иконку в меню Пуск
                                        if process_id.value:
                                            # Используем SHGetFileInfo для получения информации об иконке
                                            # Это обновит кэш иконок Windows
                                            try:
                                                SHGFI_ICON = 0x000000100
                                                SHGFI_LARGEICON = 0x000000000
                                                file_info = ctypes.create_string_buffer(ctypes.sizeof(ctypes.c_void_p) * 2 + 260)
                                                ctypes.windll.shell32.SHGetFileInfoW(
                                                    ico_path_unicode,
                                                    0,
                                                    file_info,
                                                    ctypes.sizeof(file_info),
                                                    SHGFI_ICON | SHGFI_LARGEICON
                                                )
                                            except (OSError, AttributeError, ctypes.ArgumentError):
                                                pass
                                    except (OSError, AttributeError, ctypes.ArgumentError):
                                        pass
                        except Exception as api_error:
                            logger.debug(f"Ошибка установки иконки через Windows API: {api_error}")
                    
                    # Устанавливаем иконку сразу и с одной задержкой для надежности
                    set_taskbar_icon()
                    window.after(500, set_taskbar_icon)  # Одна повторная попытка через 500мс
                
                # Принудительно обновляем окно для применения иконки
                window.update_idletasks()
                window.update()
                return
            except Exception as e:
                logger.debug(f"Не удалось установить иконку через iconbitmap: {e}")
        
        # Если .ico не найден или не сработал, используем PNG иконку (если еще не использовали)
        png_path = os.path.join(base_dir, "materials", "icon", "Логотип.png")
        png_path = os.path.normpath(png_path)
        
        if os.path.exists(png_path):
            if HAS_PIL:
                try:
                    png_path = os.path.abspath(png_path)
                    img = Image.open(png_path)
                    # Для панели задач лучше использовать иконку по умолчанию (True)
                    photo = ImageTk.PhotoImage(img)
                    window.iconphoto(True, photo)  # True = установить как иконку по умолчанию для всех окон
                    if icon_photos_list is not None:
                        icon_photos_list.append(photo)
                    # Принудительно обновляем окно для применения иконки
                    window.update_idletasks()
                    window.update()
                    logger.info(f"Иконка установлена через PNG (fallback): {png_path}")
                except Exception as e:
                    logger.debug(f"Не удалось установить PNG иконку через PIL: {e}")
            else:
                    try:
                        png_path = os.path.abspath(png_path)
                        photo = tk.PhotoImage(file=png_path)
                        window.iconphoto(True, photo)  # True = установить как иконку по умолчанию
                        if icon_photos_list is not None:
                            icon_photos_list.append(photo)
                        # Принудительно обновляем окно для применения иконки
                        window.update_idletasks()
                        window.update()
                    except Exception as e:
                        logger.debug(f"Не удалось установить PNG иконку: {e}")
    except Exception as e:
        logger.debug(f"Не удалось установить иконку: {e}")


def bind_mousewheel(widget: tk.Widget, canvas: Optional[tk.Canvas] = None) -> None:
    """Привязка прокрутки колесом мыши к виджету.
    
    Args:
        widget: Виджет для привязки прокрутки
        canvas: Опциональный Canvas для прокрутки
    """
    def on_mousewheel(event):
        """Обработчик прокрутки для Windows и macOS."""
        scroll_amount = int(-1 * (event.delta / MOUSEWHEEL_DELTA_DIVISOR))
        target = canvas if canvas else widget
        if hasattr(target, 'yview_scroll'):
            target.yview_scroll(scroll_amount, "units")
    
    def on_mousewheel_linux(event):
        """Обработчик прокрутки для Linux."""
        target = canvas if canvas else widget
        if hasattr(target, 'yview_scroll'):
            if event.num == LINUX_SCROLL_UP:
                target.yview_scroll(-1, "units")
            elif event.num == LINUX_SCROLL_DOWN:
                target.yview_scroll(1, "units")
    
    # Windows и macOS
    widget.bind("<MouseWheel>", on_mousewheel)
    # Linux
    widget.bind("<Button-4>", on_mousewheel_linux)
    widget.bind("<Button-5>", on_mousewheel_linux)
    
    # Привязка к дочерним виджетам
    def bind_to_children(parent):
        """Рекурсивная привязка прокрутки к дочерним виджетам."""
        for child in parent.winfo_children():
            try:
                child.bind("<MouseWheel>", on_mousewheel)
                child.bind("<Button-4>", on_mousewheel_linux)
                child.bind("<Button-5>", on_mousewheel_linux)
                bind_to_children(child)
            except (AttributeError, tk.TclError):
                pass
    
    bind_to_children(widget)


def setup_window_resize_handler(window: tk.Toplevel, canvas: Optional[tk.Canvas] = None, 
                                canvas_window: Optional[int] = None) -> None:
    """Настройка обработчика изменения размера для окна с canvas.
    
    Args:
        window: Окно для обработки изменения размера
        canvas: Canvas виджет (опционально)
        canvas_window: ID окна canvas (опционально)
    """
    def on_resize(event):
        if canvas and canvas_window is not None:
            try:
                canvas_width = window.winfo_width() - 20
                canvas.itemconfig(canvas_window, width=max(canvas_width, 100))
            except (AttributeError, tk.TclError):
                pass
    
    window.bind('<Configure>', on_resize)


# ============================================================================
# МЕНЕДЖЕР ТЕМ (из theme_manager.py)
# ============================================================================

class ThemeManager:
    """Класс для управления темами интерфейса."""
    
    LIGHT_THEME = {
        'primary': '#667EEA',
        'primary_hover': '#5568D3',
        'primary_light': '#818CF8',
        'primary_dark': '#4C51BF',
        'success': '#10B981',
        'success_hover': '#059669',
        'danger': '#EF4444',
        'danger_hover': '#DC2626',
        'warning': '#F59E0B',
        'warning_hover': '#D97706',
        'info': '#3B82F6',
        'info_hover': '#2563EB',
        'secondary': '#6B7280',
        'secondary_hover': '#4B5563',
        'bg_main': '#FFFFFF',
        'bg_card': '#FFFFFF',  # Оставлено для совместимости, но не используется
        'bg_secondary': '#FFFFFF',  # Изменено на bg_main для единого фона
        'bg_hover': '#F7FAFC',
        'bg_input': '#FFFFFF',
        'bg_elevated': '#FFFFFF',
        'border': '#E2E8F0',
        'border_focus': '#667EEA',
        'border_light': '#F1F5F9',
        'text_primary': '#1A202C',
        'text_secondary': '#4A5568',
        'text_muted': '#718096',
        'header_bg': '#FFFFFF',
        'header_text': '#1A202C',
        'accent': '#9F7AEA',
        'shadow': 'rgba(0,0,0,0.08)',
        'shadow_lg': 'rgba(0,0,0,0.12)',
        'shadow_xl': 'rgba(0,0,0,0.16)',
        'glow': 'rgba(102, 126, 234, 0.4)',
        'gradient_start': '#667EEA',
        'gradient_end': '#764BA2'
    }
    
    DARK_THEME = {
        'primary': '#667EEA',
        'primary_hover': '#5568D3',
        'primary_light': '#818CF8',
        'primary_dark': '#4C51BF',
        'success': '#10B981',
        'success_hover': '#059669',
        'danger': '#EF4444',
        'danger_hover': '#DC2626',
        'warning': '#F59E0B',
        'warning_hover': '#D97706',
        'info': '#3B82F6',
        'info_hover': '#2563EB',
        'secondary': '#9CA3AF',
        'secondary_hover': '#6B7280',
        'bg_main': '#1A202C',
        'bg_card': '#1A202C',  # Изменено на bg_main для единого фона
        'bg_secondary': '#1A202C',  # Изменено на bg_main для единого фона
        'bg_hover': '#374151',
        'bg_input': '#4A5568',
        'bg_elevated': '#2D3748',
        'border': '#4A5568',
        'border_focus': '#667EEA',
        'border_light': '#718096',
        'text_primary': '#F7FAFC',
        'text_secondary': '#CBD5E0',
        'text_muted': '#A0AEC0',
        'header_bg': '#2D3748',
        'header_text': '#F7FAFC',
        'accent': '#9F7AEA',
        'shadow': 'rgba(0,0,0,0.3)',
        'shadow_lg': 'rgba(0,0,0,0.4)',
        'shadow_xl': 'rgba(0,0,0,0.5)',
        'glow': 'rgba(102, 126, 234, 0.4)',
        'gradient_start': '#667EEA',
        'gradient_end': '#764BA2'
    }
    
    def __init__(self, theme: str = 'light'):
        """Инициализация менеджера тем.
        
        Args:
            theme: Название темы ('light' или 'dark')
        """
        self.current_theme = theme
        self.colors = self.get_theme_colors(theme)
    
    def get_theme_colors(self, theme: str) -> Dict[str, str]:
        """Получение цветов темы.
        
        Args:
            theme: Название темы
            
        Returns:
            Словарь с цветами
        """
        if theme == 'dark':
            return self.DARK_THEME.copy()
        return self.LIGHT_THEME.copy()
    
    def set_theme(self, theme: str) -> None:
        """Установка темы.
        
        Args:
            theme: Название темы ('light' или 'dark')
        """
        self.current_theme = theme
        self.colors = self.get_theme_colors(theme)
    
    def toggle_theme(self) -> str:
        """Переключение темы.
        
        Returns:
            Название новой темы
        """
        if self.current_theme == 'light':
            self.set_theme('dark')
            return 'dark'
        else:
            self.set_theme('light')
            return 'light'


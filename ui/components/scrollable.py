"""Модуль для создания переиспользуемых прокручиваемых компонентов.

Содержит фабрики для создания Canvas+Scrollbar комбинаций
и других часто используемых UI паттернов.
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk

logger = logging.getLogger(__name__)


class ScrollableFrame:
    """Переиспользуемый компонент для создания прокручиваемого контента.
    
    Создает Canvas с Scrollbar и внутренний Frame для размещения контента.
    Автоматически обрабатывает:
    - Изменение размера контента
    - Прокрутку колесом мыши
    - Динамическое показ/скрытие scrollbar
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        bg_color: str,
        orientation: str = 'vertical',
        auto_scrollbar: bool = True,
        bind_mousewheel_func: Optional[Callable] = None
    ):
        """Инициализация прокручиваемого фрейма.
        
        Args:
            parent: Родительский виджет
            bg_color: Цвет фона
            orientation: Ориентация scrollbar ('vertical' или 'horizontal')
            auto_scrollbar: Автоматически показывать/скрывать scrollbar
            bind_mousewheel_func: Функция для привязки прокрутки мыши
        """
        self.parent = parent
        self.bg_color = bg_color
        self.orientation = orientation
        self.auto_scrollbar = auto_scrollbar
        self.bind_mousewheel_func = bind_mousewheel_func
        
        # Создаем контейнер для canvas и scrollbar
        self.container = tk.Frame(parent, bg=bg_color)
        
        # Создаем Canvas
        self.canvas = tk.Canvas(
            self.container,
            bg=bg_color,
            highlightthickness=0
        )
        
        # Создаем Scrollbar
        if orientation == 'vertical':
            self.scrollbar = ttk.Scrollbar(
                self.container,
                orient="vertical",
                command=self.canvas.yview
            )
            self.canvas.configure(yscrollcommand=self._on_scroll)
        else:
            self.scrollbar = ttk.Scrollbar(
                self.container,
                orient="horizontal",
                command=self.canvas.xview
            )
            self.canvas.configure(xscrollcommand=self._on_scroll)
        
        # Создаем прокручиваемый Frame
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg_color)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )
        
        # Привязываем события
        self._setup_events()
        
        # Изначально скрываем scrollbar если auto_scrollbar=True
        if self.auto_scrollbar:
            self.scrollbar.pack_forget()
    
    def _setup_events(self) -> None:
        """Настройка событий для автоматической прокрутки."""
        # Обновление scrollregion при изменении размера контента
        def on_scrollable_configure(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            if self.auto_scrollbar:
                self._update_scrollbar_visibility()
        
        self.scrollable_frame.bind("<Configure>", on_scrollable_configure)
        
        # Обновление ширины canvas_window при изменении размера canvas
        def on_canvas_configure(event):
            if event.widget == self.canvas:
                try:
                    canvas_width = event.width
                    if canvas_width > 1:
                        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
                    if self.auto_scrollbar:
                        self.canvas.after(10, self._update_scrollbar_visibility)
                except (AttributeError, tk.TclError):
                    pass
        
        self.canvas.bind('<Configure>', on_canvas_configure)
        
        # Привязка прокрутки мыши
        if self.bind_mousewheel_func:
            self.bind_mousewheel_func(self.canvas, self.canvas)
            self.bind_mousewheel_func(self.scrollable_frame, self.canvas)
        else:
            # Базовая привязка прокрутки
            def on_mousewheel(event):
                if self.orientation == 'vertical':
                    scroll_amount = int(-1 * (event.delta / 120))
                    self.canvas.yview_scroll(scroll_amount, "units")
                else:
                    scroll_amount = int(-1 * (event.delta / 120))
                    self.canvas.xview_scroll(scroll_amount, "units")
            
            self.canvas.bind("<MouseWheel>", on_mousewheel)
    
    def _on_scroll(self, *args) -> None:
        """Обработчик прокрутки."""
        if self.orientation == 'vertical':
            self.scrollbar.set(*args)
        else:
            self.scrollbar.set(*args)
    
    def _update_scrollbar_visibility(self) -> None:
        """Обновление видимости scrollbar в зависимости от размера контента."""
        try:
            self.canvas.update_idletasks()
            bbox = self.canvas.bbox("all")
            
            if not bbox:
                if self.scrollbar.winfo_manager() != '':
                    self.scrollbar.pack_forget()
                return
            
            if self.orientation == 'vertical':
                canvas_height = self.canvas.winfo_height()
                content_height = bbox[3] - bbox[1]
                needs_scroll = content_height > canvas_height and canvas_height > 1
            else:
                canvas_width = self.canvas.winfo_width()
                content_width = bbox[2] - bbox[0]
                needs_scroll = content_width > canvas_width and canvas_width > 1
            
            if needs_scroll:
                if self.scrollbar.winfo_manager() == '':
                    if self.orientation == 'vertical':
                        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                    else:
                        self.scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            else:
                if self.scrollbar.winfo_manager() != '':
                    self.scrollbar.pack_forget()
        except (tk.TclError, AttributeError) as e:
            logger.debug(f"Ошибка при обновлении видимости scrollbar: {e}")
    
    def pack(self, **kwargs) -> None:
        """Упаковка контейнера."""
        self.container.pack(**kwargs)
        if self.orientation == 'vertical':
            self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        else:
            self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
    def grid(self, **kwargs) -> None:
        """Размещение контейнера через grid."""
        self.container.grid(**kwargs)
        if self.orientation == 'vertical':
            self.canvas.grid(row=0, column=0, sticky="nsew")
            self.scrollbar.grid(row=0, column=1, sticky="ns")
        else:
            self.canvas.grid(row=0, column=0, sticky="nsew")
            self.scrollbar.grid(row=1, column=0, sticky="ew")
        
        self.container.columnconfigure(0, weight=1)
        if self.orientation == 'vertical':
            self.container.rowconfigure(0, weight=1)
        else:
            self.container.rowconfigure(0, weight=1)
            self.container.rowconfigure(1, weight=0)
    
    def update_scroll_region(self) -> None:
        """Обновление области прокрутки."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        if self.auto_scrollbar:
            self._update_scrollbar_visibility()


def create_scrollable_frame(
    parent: tk.Widget,
    bg_color: str,
    orientation: str = 'vertical',
    auto_scrollbar: bool = True,
    bind_mousewheel_func: Optional[Callable] = None
) -> Tuple[tk.Frame, ScrollableFrame]:
    """Фабрика для создания прокручиваемого фрейма.
    
    Args:
        parent: Родительский виджет
        bg_color: Цвет фона
        orientation: Ориентация scrollbar
        auto_scrollbar: Автоматически показывать/скрывать scrollbar
        bind_mousewheel_func: Функция для привязки прокрутки мыши
    
    Returns:
        Tuple[scrollable_frame, scrollable_component]:
        - scrollable_frame: Frame для размещения контента
        - scrollable_component: Объект ScrollableFrame для управления
    """
    scrollable = ScrollableFrame(
        parent,
        bg_color,
        orientation,
        auto_scrollbar,
        bind_mousewheel_func
    )
    return scrollable.scrollable_frame, scrollable


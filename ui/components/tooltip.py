"""Модуль для создания подсказок при наведении на виджеты."""

import tkinter as tk


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


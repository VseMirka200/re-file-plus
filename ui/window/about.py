"""Модуль для создания вкладки 'О программе'."""

import tkinter as tk
from tkinter import ttk


class MainWindowAbout:
    """Класс для создания вкладки 'О программе'."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def create_about_tab_content(self, parent):
        """Создание содержимого вкладки 'О программе'.
        
        Args:
            parent: Родительский контейнер (Frame)
        """
        from ui.about_tab import AboutTab
        
        # Создаем Canvas для прокрутки
        canvas = tk.Canvas(parent, bg=self.app.colors['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.app.colors['bg_main'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def on_canvas_configure(event):
            if event.widget == canvas:
                try:
                    canvas_width = event.width
                    canvas.itemconfig(canvas_window, width=canvas_width)
                    # Обновляем wraplength для текста в about_tab
                    scrollable_frame.update_idletasks()
                except (AttributeError, tk.TclError):
                    pass
        
        canvas.bind('<Configure>', on_canvas_configure)
        def on_window_configure(event):
            if event.widget == parent:
                try:
                    canvas_width = parent.winfo_width() - scrollbar.winfo_width() - 4
                    canvas.itemconfig(canvas_window, width=max(canvas_width, 100))
                    # Обновляем wraplength для текста в about_tab
                    scrollable_frame.update_idletasks()
                except (AttributeError, tk.TclError):
                    pass
        
        parent.bind('<Configure>', on_window_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Привязка прокрутки колесом мыши
        self.app.bind_mousewheel(canvas, canvas)
        self.app.bind_mousewheel(scrollable_frame, canvas)
        
        # Создаем AboutTab и используем его метод для создания содержимого
        about_tab_handler = AboutTab(
            None,  # notebook не нужен, так как мы используем Frame
            self.app.colors,
            self.app.bind_mousewheel,
            self.app._icon_photos
        )
        
        # Вызываем метод для создания содержимого на Frame
        about_tab_handler.create_content(scrollable_frame)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)


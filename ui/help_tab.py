"""Модуль для создания вкладки 'Справка'.

Отображает информацию о том, как использовать программу.
"""

import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)


class HelpTab:
    """Класс для создания и управления вкладкой 'Справка'."""
    
    def __init__(self, notebook, colors, bind_mousewheel_func):
        """Инициализация вкладки 'Справка'.
        
        Args:
            notebook: Notebook виджет для добавления вкладки
            colors: Словарь с цветами интерфейса
            bind_mousewheel_func: Функция для привязки прокрутки колесом мыши
        """
        self.notebook = notebook
        self.colors = colors
        self.bind_mousewheel = bind_mousewheel_func
    
    def create_tab(self):
        """Создание вкладки справки"""
        help_tab = tk.Frame(self.notebook, bg=self.colors['bg_main'])
        help_tab.columnconfigure(0, weight=1)
        help_tab.rowconfigure(0, weight=1)
        self.notebook.add(help_tab, text="Справка")
        
        # Содержимое справки с прокруткой
        canvas = tk.Canvas(help_tab, bg=self.colors['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(help_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg_main'])
        
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
                except (AttributeError, tk.TclError):
                    pass
        
        canvas.bind('<Configure>', on_canvas_configure)
        def on_window_configure(event):
            if event.widget == help_tab:
                try:
                    canvas_width = help_tab.winfo_width() - scrollbar.winfo_width() - 4
                    canvas.itemconfig(canvas_window, width=max(canvas_width, 100))
                except (AttributeError, tk.TclError):
                    pass
        
        help_tab.bind('<Configure>', on_window_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Привязка прокрутки колесом мыши
        self.bind_mousewheel(canvas, canvas)
        self.bind_mousewheel(scrollable_frame, canvas)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        help_tab.rowconfigure(0, weight=1)
        help_tab.columnconfigure(0, weight=1)
        
        content_frame = scrollable_frame
        content_frame.columnconfigure(0, weight=1)
        scrollable_frame.configure(padx=20, pady=20)
        
        # Основные возможности - карточка
        features_card = ttk.LabelFrame(content_frame, text="Основные возможности", 
                                      style='Card.TLabelframe', padding=20)
        features_card.pack(fill=tk.X, pady=(10, 20))
        
        features_content = tk.Frame(features_card, bg=self.colors['bg_card'])
        features_content.pack(fill=tk.BOTH, expand=True)
        
        features_text = """• Переименование файлов по шаблонам с поддержкой метаданных (EXIF, ID3, документы Office и др.)
• Предпросмотр изменений перед применением
• Удобный интерфейс с поддержкой Drag & Drop для быстрого добавления файлов
• Перестановка файлов в списке простым перетаскиванием
• Конвертация файлов между различными форматами
• Сортировка и организация файлов
• Гибкая настройка методов переименования
• Сохранение и загрузка шаблонов переименования"""
        
        features_label = tk.Label(features_content, 
                                 text=features_text,
                                 font=('Robot', 10),
                                 bg=self.colors['bg_card'], 
                                 fg=self.colors['text_primary'],
                                 justify=tk.LEFT,
                                 anchor=tk.NW)
        features_label.pack(anchor=tk.NW, fill=tk.X)
        
        # Использование - карточка
        usage_card = ttk.LabelFrame(content_frame, text="Как использовать", 
                                    style='Card.TLabelframe', padding=20)
        usage_card.pack(fill=tk.X, pady=(10, 20))
        
        usage_content = tk.Frame(usage_card, bg=self.colors['bg_card'])
        usage_content.pack(fill=tk.BOTH, expand=True)
        
        usage_text = """1. Добавьте файлы в список:
   - Перетащите файлы из проводника в окно программы
   - Или используйте кнопки "Добавить файлы" / "Добавить папку"
   
2. Настройте методы переименования:
   - Выберите метод из списка (Новое имя, Префикс, Суффикс и т.д.)
   - Настройте параметры метода
   - Добавьте дополнительные методы при необходимости
   
3. Просмотрите результат:
   - В колонке "Новое имя" отображается предпросмотр результата
   - Проверьте, что все файлы будут переименованы правильно
   
4. Начните переименование:
   - Нажмите кнопку "Начать переименование"
   - Дождитесь завершения операции"""
        
        usage_label = tk.Label(usage_content, 
                              text=usage_text,
                              font=('Robot', 10),
                              bg=self.colors['bg_card'], 
                              fg=self.colors['text_primary'],
                              justify=tk.LEFT,
                              anchor=tk.NW)
        usage_label.pack(anchor=tk.NW, fill=tk.X)
        
        # Горячие клавиши - карточка
        shortcuts_card = ttk.LabelFrame(content_frame, text="Горячие клавиши", 
                                        style='Card.TLabelframe', padding=20)
        shortcuts_card.pack(fill=tk.X, pady=(10, 20))
        
        shortcuts_content = tk.Frame(shortcuts_card, bg=self.colors['bg_card'])
        shortcuts_content.pack(fill=tk.BOTH, expand=True)
        
        shortcuts_text = """Ctrl+Shift+A - Добавить файлы
Ctrl+O - Добавить папку
Ctrl+Z - Отменить переименование
Ctrl+Y / Ctrl+Shift+Z - Повторить переименование
Delete - Удалить выбранные файлы из списка
Ctrl+F - Фокус на поле поиска
F5 - Обновить список файлов
Ctrl+R - Применить методы переименования
Ctrl+S - Сохранить шаблон"""
        
        shortcuts_label = tk.Label(shortcuts_content, 
                                  text=shortcuts_text,
                                  font=('Robot', 10),
                                  bg=self.colors['bg_card'], 
                                  fg=self.colors['text_primary'],
                                  justify=tk.LEFT,
                                  anchor=tk.NW)
        shortcuts_label.pack(anchor=tk.NW, fill=tk.X)


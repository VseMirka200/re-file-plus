"""Модуль для окна руководства по шаблонам."""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

logger = logging.getLogger(__name__)


class TemplatesGuide:
    """Класс для управления окном руководства по шаблонам."""
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def show_templates_guide(self):
        """Показ окна руководства по шаблонам с возможностью копирования"""
        # Проверяем, не открыто ли уже окно руководства
        if hasattr(self.app, '_templates_guide_window'):
            try:
                if self.app._templates_guide_window.winfo_exists():
                    # Окно уже открыто, просто поднимаем его на передний план
                    self.app._templates_guide_window.lift()
                    self.app._templates_guide_window.focus_force()
                    return
            except (tk.TclError, AttributeError):
                # Окно было закрыто, но ссылка осталась
                pass
        
        guide_window = tk.Toplevel(self.app.root)
        guide_window.title("Руководство по шаблонам")
        guide_window.geometry("800x700")
        guide_window.configure(bg=self.app.colors['bg_main'])
        guide_window.transient(self.app.root)
        
        # Сохраняем ссылку на окно
        self.app._templates_guide_window = guide_window
        
        # Флаг для предотвращения двойного закрытия
        _closing = [False]
        
        # Обработчик закрытия по Escape и кнопке X
        def on_close(event=None):
            if _closing[0]:
                return
            _closing[0] = True
            try:
                if guide_window.winfo_exists():
                    guide_window.destroy()
                # Удаляем ссылку на окно после закрытия
                if hasattr(self.app, '_templates_guide_window'):
                    del self.app._templates_guide_window
            except (tk.TclError, AttributeError):
                # Удаляем ссылку даже при ошибке
                if hasattr(self.app, '_templates_guide_window'):
                    try:
                        del self.app._templates_guide_window
                    except:
                        pass
        
        guide_window.bind('<Escape>', on_close)
        guide_window.protocol("WM_DELETE_WINDOW", on_close)
        guide_window.focus_set()
        
        try:
            from ui.ui_components import set_window_icon
            set_window_icon(guide_window, self.app._icon_photos)
        except (AttributeError, tk.TclError, OSError, RuntimeError, TypeError):
            pass
        except (MemoryError, RecursionError):
            pass
        # Финальный catch для неожиданных исключений (критично для стабильности)
        except BaseException:
            pass
        
        # Заголовок
        header = tk.Label(
            guide_window,
            text="Руководство по шаблонам переименования",
            font=('Robot', 14, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        header.pack(pady=(15, 10))
        
        # Контейнер с прокруткой
        canvas = tk.Canvas(guide_window, bg=self.app.colors['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(guide_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.app.colors['bg_main'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def on_canvas_configure(event):
            canvas_width = event.width
            canvas.itemconfig(canvas_window, width=canvas_width)
        
        canvas.bind('<Configure>', on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Функция для создания кликабельного блока с переменной
        def create_variable_block(parent, var_name, description, category=""):
            """Создание блока с переменной, которую можно скопировать"""
            var_frame = tk.Frame(parent, bg=self.app.colors['bg_main'], relief=tk.SOLID, borderwidth=1)
            var_frame.pack(fill=tk.X, padx=10, pady=2)
            
            # Внутренний фрейм для содержимого
            inner_frame = tk.Frame(var_frame, bg=self.app.colors['bg_main'])
            inner_frame.pack(fill=tk.X, padx=8, pady=6)
            
            # Переменная (кликабельная для копирования)
            var_label = tk.Label(
                inner_frame,
                text=var_name,
                font=('Courier New', 11, 'bold'),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['primary'],
                cursor="hand2"
            )
            var_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Описание
            desc_label = tk.Label(
                inner_frame,
                text=description,
                font=('Robot', 10),
                bg=self.app.colors['bg_main'],
                fg=self.app.colors['text_primary'],
                anchor='w'
            )
            desc_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Функция копирования
            def copy_var(e=None):
                guide_window.clipboard_clear()
                guide_window.clipboard_append(var_name)
                guide_window.update()
                # Визуальная обратная связь
                var_label.config(fg=self.app.colors['success'])
                guide_window.after(200, lambda: var_label.config(fg=self.app.colors['primary']))
            
            var_label.bind("<Button-1>", copy_var)
            inner_frame.bind("<Button-1>", copy_var)
            desc_label.bind("<Button-1>", copy_var)
            var_frame.bind("<Button-1>", copy_var)
            
            # Изменение курсора при наведении
            for widget in [var_label, inner_frame, desc_label, var_frame]:
                widget.bind("<Enter>", lambda e, w=var_label: w.config(fg=self.app.colors['primary_hover']))
                widget.bind("<Leave>", lambda e, w=var_label: w.config(fg=self.app.colors['primary']))
        
        # Основные переменные
        basic_label = tk.Label(
            scrollable_frame,
            text="Основные переменные:",
            font=('Robot', 12, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        basic_label.pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        basic_vars = [
            ("{name}", "исходное имя файла (без расширения)"),
            ("{ext}", "расширение файла"),
            ("{n}", "порядковый номер файла (использует настройки по умолчанию из 'Настройки' → 'Настройки нумерации')"),
            ("{n:10}", "номер файла с указанным начальным номером (например: {n:10} начнется с 10, 11, 12...)"),
            ("{n:1:3}", "номер файла с начальным номером и количеством ведущих нулей (например: {n:1:3} → 001, 002, 003...)"),
            ("{filename}", "полное имя файла (с расширением)"),
            ("{dirname}", "имя папки, содержащей файл"),
            ("{format}", "формат файла (расширение без точки, заглавными)")
        ]
        
        for var, desc in basic_vars:
            create_variable_block(scrollable_frame, var, desc)
        
        # Даты и время
        date_label = tk.Label(
            scrollable_frame,
            text="Даты и время:",
            font=('Robot', 12, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        date_label.pack(anchor=tk.W, padx=10, pady=(15, 5))
        
        date_vars = [
            ("{date_created}", "дата создания (YYYY-MM-DD)"),
            ("{date_modified}", "дата изменения (YYYY-MM-DD)"),
            ("{date_created_time}", "дата и время создания (YYYY-MM-DD_HH-MM-SS)"),
            ("{date_modified_time}", "дата и время изменения (YYYY-MM-DD_HH-MM-SS)"),
            ("{year}", "год создания"),
            ("{month}", "месяц создания (01-12)"),
            ("{day}", "день создания (01-31)"),
            ("{hour}", "час создания (00-23)"),
            ("{minute}", "минута создания (00-59)"),
            ("{second}", "секунда создания (00-59)")
        ]
        
        for var, desc in date_vars:
            create_variable_block(scrollable_frame, var, desc)
        
        # Метаданные изображений
        image_label = tk.Label(
            scrollable_frame,
            text="Метаданные изображений:",
            font=('Robot', 12, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        image_label.pack(anchor=tk.W, padx=10, pady=(15, 5))
        
        image_vars = [
            ("{width}", "ширина изображения"),
            ("{height}", "высота изображения"),
            ("{width}x{height}", "размеры изображения (например, 1920x1080)"),
            ("{camera}", "модель камеры (из EXIF)"),
            ("{iso}", "ISO (из EXIF)"),
            ("{focal_length}", "фокусное расстояние (из EXIF)"),
            ("{aperture}", "диафрагма (из EXIF)"),
            ("{exposure_time}", "выдержка (из EXIF)")
        ]
        
        for var, desc in image_vars:
            create_variable_block(scrollable_frame, var, desc)
        
        # Общие
        general_label = tk.Label(
            scrollable_frame,
            text="Общие:",
            font=('Robot', 12, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        general_label.pack(anchor=tk.W, padx=10, pady=(15, 5))
        
        general_vars = [
            ("{file_size}", "размер файла (B, KB, MB, GB)")
        ]
        
        for var, desc in general_vars:
            create_variable_block(scrollable_frame, var, desc)
        
        # Сохранение шаблона
        save_template_label = tk.Label(
            scrollable_frame,
            text="Сохранить свой шаблон:",
            font=('Robot', 12, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        save_template_label.pack(anchor=tk.W, padx=10, pady=(15, 5))
        
        save_template_frame = tk.Frame(scrollable_frame, bg=self.app.colors['bg_main'], relief=tk.SOLID, borderwidth=1)
        save_template_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        save_template_inner = tk.Frame(save_template_frame, bg=self.app.colors['bg_main'])
        save_template_inner.pack(fill=tk.X, padx=12, pady=10)
        
        # Поле ввода шаблона
        template_entry_frame = tk.Frame(save_template_inner, bg=self.app.colors['bg_main'])
        template_entry_frame.pack(fill=tk.X, pady=(0, 8))
        
        template_entry_label = tk.Label(
            template_entry_frame,
            text="Шаблон:",
            font=('Robot', 10),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary']
        )
        template_entry_label.pack(side=tk.LEFT, padx=(0, 5))
        
        template_entry_var = tk.StringVar()
        template_entry = tk.Entry(
            template_entry_frame,
            textvariable=template_entry_var,
            font=('Courier New', 10),
            bg='white',
            fg=self.app.colors['text_primary'],
            relief=tk.SOLID,
            borderwidth=1
        )
        template_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Кнопка сохранения
        def save_template_from_guide():
            template = template_entry_var.get().strip()
            if not template:
                messagebox.showwarning("Предупреждение", "Введите шаблон для сохранения")
                return
            
            # Запрашиваем имя для шаблона
            template_name = simpledialog.askstring(
                "Сохранить шаблон",
                "Введите имя для шаблона:",
                initialvalue=template[:30] if len(template) > 30 else template
            )
            
            if template_name:
                template_name = template_name.strip()
                if template_name:
                    # Получаем начальный номер из настроек
                    start_number = self.app.settings_manager.get('numbering_start_number', '1')
                    
                    # Получаем количество нулей из настроек
                    zeros_count = self.app.settings_manager.get('numbering_zeros_count', '0')
                    
                    # Сохраняем шаблон
                    if not hasattr(self.app, 'saved_templates'):
                        self.app.saved_templates = {}
                    
                    self.app.saved_templates[template_name] = {
                        'template': template,
                        'start_number': start_number,
                        'zeros_count': zeros_count
                    }
                    
                    # Обновляем в менеджере шаблонов
                    if hasattr(self.app, 'templates_manager'):
                        self.app.templates_manager.templates = self.app.saved_templates
                        self.app.save_templates()
                        self.app.templates_manager.save_templates(self.app.saved_templates)
                    
                    self.app.log(f"Шаблон '{template_name}' сохранен")
                    messagebox.showinfo("Успех", f"Шаблон '{template_name}' успешно сохранен!")
                    # Очищаем поле ввода
                    template_entry_var.set("")
        
        save_btn = self.app.create_rounded_button(
            template_entry_frame,
            "💾 Сохранить",
            save_template_from_guide,
            bg_color=self.app.colors['primary'],
            fg_color='white',
            font=('Robot', 9, 'bold'),
            padx=12,
            pady=6,
            active_bg=self.app.colors['primary_hover'],
            expand=False
        )
        save_btn.pack(side=tk.LEFT)
        
        # Подсказка
        hint_label = tk.Label(
            scrollable_frame,
            text="💡 Подсказка: Кликните на любую переменную, чтобы скопировать её в буфер обмена. Введите свой шаблон выше и сохраните его.",
            font=('Robot', 9, 'italic'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_secondary']
        )
        hint_label.pack(anchor=tk.W, padx=10, pady=(15, 10))
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


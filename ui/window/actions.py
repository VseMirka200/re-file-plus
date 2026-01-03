"""Модуль для создания содержимого действий (переименование, конвертация)."""

import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)


class MainWindowActions:
    """Класс для создания содержимого действий главного окна.
    
    Отвечает за создание и управление содержимым для различных действий:
    - Переименование файлов (re-file операции)
    - Конвертация файлов
    - Настройки методов переименования
    
    Управляет переключением между различными панелями действий
    и созданием соответствующих UI компонентов.
    """
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения (ReFilePlusApp)
        """
        self.app = app
    
    def on_action_changed(self, action: str) -> None:
        """Обработка изменения выбранного действия.
        
        Args:
            action: Название действия ("Переименовать", "Конвертировать")
        """
        # Убеждаемся, что мы находимся во вкладке "Файлы"
        # Если мы не во вкладке "Файлы", ничего не делаем
        if not hasattr(self.app, 'current_tab') or self.app.current_tab != "files":
            return
        
        # Используем action_content_frame для размещения содержимого действий
        parent = self.app.action_content_frame if hasattr(self.app, 'action_content_frame') else None
        if not parent:
            return
        
        # Скрываем текущее содержимое действий
        for key in ["re_file", "convert"]:
            if key in self.app.tab_contents and self.app.tab_contents[key]:
                frame = self.app.tab_contents[key]
                # Проверяем, что это не сам parent и frame существует
                if frame != parent:
                    try:
                        if frame.winfo_exists():
                            frame.grid_remove()
                    except (tk.TclError, AttributeError):
                        # Frame уже уничтожен, удаляем из словаря
                        self.app.tab_contents[key] = None
        
        if action == "Переименовать":
            if "re_file" not in self.app.tab_contents or self.app.tab_contents["re_file"] is None:
                self.create_re_file_action_content(parent)
            frame = self.app.tab_contents.get("re_file")
            if frame:
                try:
                    if frame.winfo_exists():
                        frame.grid(row=0, column=0, sticky="ew")
                    else:
                        # Frame уничтожен, создаем заново
                        self.create_re_file_action_content(parent)
                        self.app.tab_contents["re_file"].grid(row=0, column=0, sticky="ew")
                except (tk.TclError, AttributeError):
                    # Frame не существует, создаем заново
                    self.create_re_file_action_content(parent)
                    self.app.tab_contents["re_file"].grid(row=0, column=0, sticky="ew")
            # Обновляем колонки для переименования
            self.app.root.after(100, lambda act="re_file": self.app.main_window_handler.update_tree_columns_for_action(act))
    
    def create_re_file_action_content(self, parent) -> None:
        """Создание содержимого для действия 'Переименовать' в одну линию.
        
        Args:
            parent: Родительский контейнер (action_content_frame)
        """
        # Удаляем старый frame, если он существует
        if "re_file" in self.app.tab_contents and self.app.tab_contents["re_file"]:
            old_frame = self.app.tab_contents["re_file"]
            try:
                if old_frame.winfo_exists():
                    old_frame.destroy()
            except (tk.TclError, AttributeError):
                pass
        
        # Создаем Frame для содержимого действия переименования
        re_file_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        re_file_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        # Настраиваем веса колонок для правильного растяжения
        re_file_frame.columnconfigure(1, weight=1)  # Поле шаблона растягивается
        
        # Сохраняем ссылку
        self.app.tab_contents["re_file"] = re_file_frame
        
        # Метка "Шаблон:" слева от поля
        template_label = tk.Label(
            re_file_frame,
            text="Шаблон:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        template_label.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=0)
        
        # Поле ввода шаблона (простое Entry без выпадающего списка)
        if not hasattr(self.app, 'new_name_template'):
            self.app.new_name_template = tk.StringVar()
        
        # Frame для Entry с фиксированной высотой 28px (как у кнопок)
        template_entry_frame = tk.Frame(re_file_frame, bg=self.app.colors['bg_main'], height=28)
        template_entry_frame.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        template_entry_frame.grid_propagate(False)
        template_entry_frame.pack_propagate(False)
        
        # Поле ввода шаблона (используем обычный Entry вместо ttk для лучшей видимости)
        template_entry = tk.Entry(
            template_entry_frame,
            textvariable=self.app.new_name_template,
            width=30,
            font=('Robot', 9),
            bg='white',
            fg=self.app.colors['text_primary'],
            relief=tk.SOLID,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=self.app.colors['border'],
            highlightcolor=self.app.colors['border_focus']
        )
        template_entry.pack(fill=tk.BOTH, expand=True)
        
        # Функции для работы с буфером обмена (для контекстного меню)
        def on_copy(event=None):
            try:
                text = template_entry.selection_get()
                if text:
                    self.app.root.clipboard_clear()
                    self.app.root.clipboard_append(text)
            except tk.TclError:
                pass
        
        def on_paste(event=None):
            try:
                # Удаляем выделенный текст перед вставкой, если есть
                try:
                    if template_entry.selection_present():
                        template_entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
                except tk.TclError:
                    pass
                # Используем root.clipboard_get() для более надежного получения данных из буфера обмена
                text = self.app.root.clipboard_get()
                if text:
                    template_entry.insert(tk.INSERT, text)
                    # После вставки применяем шаблон
                    if hasattr(self.app, '_apply_template_immediate'):
                        self.app.root.after(50, self.app._apply_template_immediate)
            except (tk.TclError, Exception) as e:
                logger.debug(f"Ошибка при вставке: {e}")
                pass
        
        def on_cut(event=None):
            try:
                text = template_entry.selection_get()
                if text:
                    self.app.root.clipboard_clear()
                    self.app.root.clipboard_append(text)
                    template_entry.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
        
        def on_select_all(event=None):
            template_entry.selection_range(0, tk.END)
            template_entry.icursor(tk.END)
        
        # В Tkinter Entry виджеты поддерживают стандартные горячие клавиши по умолчанию
        # Но мы переопределяем их для использования наших функций, которые работают с контекстным меню
        def handle_copy(event):
            on_copy()
            return "break"
        
        def handle_paste(event):
            nonlocal _is_paste_operation
            _is_paste_operation = True
            on_paste()
            # Возвращаем "break" чтобы предотвратить дальнейшую обработку события
            # и стандартную вставку Tkinter
            return "break"
        
        def handle_cut(event):
            on_cut()
            return "break"
        
        def handle_select_all(event):
            on_select_all()
            return "break"
        
        # Привязка горячих клавиш напрямую к этому виджету
        template_entry.bind('<Control-c>', handle_copy)
        template_entry.bind('<Control-C>', handle_copy)
        template_entry.bind('<Control-v>', handle_paste)
        template_entry.bind('<Control-V>', handle_paste)
        template_entry.bind('<Control-x>', handle_cut)
        template_entry.bind('<Control-X>', handle_cut)
        template_entry.bind('<Control-a>', handle_select_all)
        template_entry.bind('<Control-A>', handle_select_all)
        
        # Привязка правой кнопки мыши для контекстного меню
        def show_context_menu(event):
            """Показ контекстного меню для копирования/вставки"""
            try:
                # Устанавливаем фокус на поле ввода
                template_entry.focus_set()
                
                context_menu = tk.Menu(template_entry, tearoff=0)
                
                # Проверяем, есть ли выделенный текст
                try:
                    template_entry.selection_get()
                    has_selection = True
                except tk.TclError:
                    has_selection = False
                
                if has_selection:
                    context_menu.add_command(label="Копировать  Ctrl+C", command=lambda: on_copy(None))
                    context_menu.add_command(label="Вырезать  Ctrl+X", command=lambda: on_cut(None))
                else:
                    context_menu.add_command(label="Копировать  Ctrl+C", command=lambda: on_copy(None), state='disabled')
                    context_menu.add_command(label="Вырезать  Ctrl+X", command=lambda: on_cut(None), state='disabled')
                
                context_menu.add_command(label="Вставить  Ctrl+V", command=lambda: on_paste(None))
                context_menu.add_separator()
                context_menu.add_command(label="Выделить всё  Ctrl+A", command=lambda: on_select_all(None))
                
                try:
                    context_menu.tk_popup(event.x_root, event.y_root)
                finally:
                    context_menu.grab_release()
            except (tk.TclError, RuntimeError, AttributeError):
                # Игнорируем ошибки контекстного меню (не критично)
                pass
        
        template_entry.bind('<Button-3>', show_context_menu)  # Правая кнопка мыши (Windows/Linux)
        template_entry.bind('<Button-2>', show_context_menu)  # Средняя кнопка (для совместимости)
        
        # Флаг для отслеживания операций вставки/копирования/вырезания
        _is_paste_operation = False
        
        # Привязка обработчика изменения шаблона в поле ввода
        # Используем KeyRelease и проверяем, что это не горячие клавиши
        def on_template_entry_change(event=None):
            nonlocal _is_paste_operation
            if event is None:
                return
            # Если это была операция вставки, пропускаем обработку
            if _is_paste_operation:
                _is_paste_operation = False
                # Но все равно применяем шаблон после вставки
                if hasattr(self.app, '_apply_template_immediate'):
                    self.app.root.after(50, self.app._apply_template_immediate)
                return
            # Пропускаем горячие клавиши Ctrl+C, Ctrl+V, Ctrl+X, Ctrl+A
            # Проверяем как через state, так и через keysym для надежности
            key = event.keysym.lower()
            # Проверяем, нажата ли Control (0x4) или это комбинация клавиш
            if event.state & 0x4:  # Control key pressed
                if key in ('c', 'v', 'x', 'a', 'control_l', 'control_r'):
                    return
            # Также проверяем комбинации напрямую через keysym
            if key in ('control-c', 'control-v', 'control-x', 'control-a'):
                return
            # Применяем шаблон сразу же с минимальной задержкой для стабильности
            if hasattr(self.app, '_apply_template_immediate'):
                # Используем небольшую задержку (50 мс) для предотвращения проблем при быстром вводе
                self.app.root.after(50, self.app._apply_template_immediate)
        template_entry.bind('<KeyRelease>', on_template_entry_change)
        
        # Также применяем шаблон при потере фокуса (принудительно)
        def on_template_focus_out(event=None):
            if hasattr(self.app, '_apply_template_immediate'):
                # Принудительно применяем шаблон при потере фокуса, чтобы убедиться, что он применен
                self.app._apply_template_immediate(force=True)
        template_entry.bind('<FocusOut>', on_template_focus_out)
        
        # Кнопка руководства по шаблонам "?" (квадратная)
        btn_guide = self.app.create_square_icon_button(
            re_file_frame,
            "?",
            self.app.main_window_handler.show_templates_guide,
            bg_color=self.app.colors['info'],
            size=28,
            active_bg=self.app.colors['info_hover']
        )
        btn_guide.grid(row=0, column=2, padx=(0, 5), pady=0, sticky="n")
        self.app.templates_btn_guide = btn_guide
        
        # Кнопка "Применить" (квадратная, со значком галочки)
        btn_start = self.app.create_square_icon_button(
            re_file_frame,
            "✓",
            self.app.start_re_file,
            bg_color=self.app.colors['success'],
            size=28,
            active_bg=self.app.colors['success_hover']
        )
        btn_start.grid(row=0, column=4, padx=(0, 0), pady=0, sticky="n")
        self.app.rename_btn_start = btn_start
    
    def create_convert_action_content(self, parent) -> None:
        """Создание содержимого для действия 'Конвертировать'.
        
        Args:
            parent: Родительский контейнер (action_content_frame)
        """
        # Удаляем старый frame, если он существует
        if "convert" in self.app.tab_contents and self.app.tab_contents["convert"]:
            old_frame = self.app.tab_contents["convert"]
            try:
                if old_frame.winfo_exists():
                    old_frame.destroy()
            except (tk.TclError, AttributeError):
                pass
        
        # Создаем Frame для содержимого действия конвертации
        convert_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        convert_frame.grid(row=0, column=1, sticky="ew", padx=0, pady=0)
        convert_frame.columnconfigure(3, weight=1)  # Поле формата растягивается
        
        # Сохраняем ссылку на frame
        self.app.tab_contents["convert"] = convert_frame
        
        # Метка "Тип:"
        type_label = tk.Label(
            convert_frame,
            text="Тип:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        type_label.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=5)
        
        # Frame для Combobox с фиксированной высотой 40px (как у кнопок)
        filter_combo_frame = tk.Frame(convert_frame, bg=self.app.colors['bg_main'], height=40)
        filter_combo_frame.grid(row=0, column=1, sticky="ew", padx=(0, 5), pady=5)
        filter_combo_frame.grid_propagate(False)
        
        # Выпадающее меню с типами файлов
        filter_var = tk.StringVar(value="Все")
        filter_combo = ttk.Combobox(
            filter_combo_frame,
            textvariable=filter_var,
            values=["Все", "Изображения", "Документы", "Презентации"],
            state='readonly',
            width=12,
            font=('Robot', 9)
        )
        # Настраиваем стиль для поля "Тип" с увеличенным padding для высоты 40px
        self.app.style.configure('Tall.TCombobox',
                                 fieldbackground=self.app.colors['bg_main'],
                                 foreground=self.app.colors['text_primary'],
                                 borderwidth=1,
                                 relief='solid',
                                 padding=(5, 5),
                                 font=('Robot', 9))
        self.app.style.map('Tall.TCombobox',
                          bordercolor=[('focus', self.app.colors['border_focus']),
                                     ('!focus', self.app.colors['border'])],
                          selectbackground=[('focus', self.app.colors['bg_main'])],
                          selectforeground=[('focus', self.app.colors['text_primary'])])
        filter_combo.configure(style='Tall.TCombobox')
        # Заполняем весь Frame без отступов для правильной высоты 40px
        filter_combo.pack(expand=True, fill=tk.BOTH)
        self.app.converter_filter_var = filter_var
        self.app.converter_filter_combo = filter_combo
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.app.converter_tab_handler.filter_converter_files_by_type() if hasattr(self.app, 'converter_tab_handler') else None)
        
        # Метка "Формат:"
        format_label = tk.Label(
            convert_frame,
            text="Формат:",
            font=('Robot', 9, 'bold'),
            bg=self.app.colors['bg_main'],
            fg=self.app.colors['text_primary'],
            anchor='w'
        )
        format_label.grid(row=0, column=2, sticky="w", padx=(0, 5), pady=5)
        
        # Frame для Combobox формата с фиксированной высотой 28px (как у кнопок)
        format_combo_frame = tk.Frame(convert_frame, bg=self.app.colors['bg_main'], height=28)
        format_combo_frame.grid(row=0, column=3, sticky="ew", padx=(0, 5), pady=5)
        format_combo_frame.grid_propagate(False)
        format_combo_frame.pack_propagate(False)
        convert_frame.columnconfigure(3, weight=1)  # Поле формата растягивается
        
        # Выпадающее меню с форматами
        formats = self.app.file_converter.get_supported_formats() if hasattr(self.app, 'file_converter') else []
        format_var = tk.StringVar(value=formats[0] if formats else '.png')
        format_combo = ttk.Combobox(
            format_combo_frame,
            textvariable=format_var,
            values=formats,
            state='readonly',
            width=15,
            font=('Robot', 9)
        )
        # Заполняем весь Frame без отступов для правильной высоты 28px
        format_combo.pack(fill=tk.BOTH, expand=True)
        self.app.converter_format_var = format_var
        self.app.converter_format_combo = format_combo
        
        # Кнопка "Начать конвертацию" (квадратная, со значком галочки)
        def start_convert():
            if hasattr(self.app, 'converter_tab_handler'):
                self.app.converter_tab_handler.convert_files()
        
        btn_start = self.app.create_square_icon_button(
            convert_frame,
            "✓",
            start_convert,
            bg_color=self.app.colors['success'],
            size=28,
            active_bg=self.app.colors['success_hover']
        )
        btn_start.grid(row=0, column=5, padx=(0, 0), pady=5)
    
    def create_rename_tab_content(self, parent) -> None:
        """Создание содержимого вкладки переименования (только правая панель с методами).
        
        Args:
            parent: Родительский контейнер (action_content_frame)
        """
        # Создаем Frame для содержимого вкладки переименования (только правая панель)
        re_file_frame = tk.Frame(parent, bg=self.app.colors['bg_main'])
        re_file_frame.grid(row=0, column=0, sticky="nsew")
        re_file_frame.columnconfigure(0, weight=1)
        re_file_frame.rowconfigure(0, weight=1)
        
        # Сохраняем ссылку
        self.app.tab_contents["re_file"] = re_file_frame
        
        # Правая панель (только методы)
        right_panel = ttk.LabelFrame(
            re_file_frame,
            text="Методы переименования",
            style='Card.TLabelframe',
            padding=(6, 12, 6, 12)
        )
        right_panel.grid(row=0, column=0, sticky="nsew", padx=(2, 0), pady=(20, 20))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        # Сохраняем ссылку на панель
        self.app.right_panel = right_panel
        
        # Внутренний Frame для содержимого
        methods_frame = tk.Frame(right_panel, bg=self.app.colors['bg_main'])
        self.app.methods_frame = methods_frame
        methods_frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        methods_frame.columnconfigure(0, weight=1)
        methods_frame.rowconfigure(1, weight=1)
        
        # Устанавливаем метод "Новое имя" по умолчанию
        self.app.method_var = tk.StringVar()
        self.app.method_var.set("Новое имя")
        
        # Область настроек метода с прокруткой
        settings_container = tk.Frame(methods_frame, bg=self.app.colors['bg_main'])
        settings_container.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        settings_container.columnconfigure(0, weight=1)
        settings_container.rowconfigure(0, weight=1)
        
        # Canvas для прокрутки настроек
        settings_canvas = tk.Canvas(settings_container, bg=self.app.colors['bg_main'], 
                                    highlightthickness=0)
        settings_scrollbar = ttk.Scrollbar(settings_container, orient="vertical", 
                                           command=settings_canvas.yview)
        scrollable_frame = tk.Frame(settings_canvas, bg=self.app.colors['bg_main'])
        
        # Флаг для предотвращения бесконечных циклов
        _updating_scroll = False
        _needs_scrolling_settings = True
        
        def update_scroll_region():
            """Обновление области прокрутки и видимости скроллбара"""
            nonlocal _updating_scroll, _needs_scrolling_settings
            if _updating_scroll:
                return
            _updating_scroll = True
            try:
                settings_canvas.update_idletasks()
                bbox = settings_canvas.bbox("all")
                if bbox:
                    canvas_height = settings_canvas.winfo_height()
                    if canvas_height > 1:
                        content_height = bbox[3] - bbox[1]
                        if content_height <= canvas_height + 2:
                            settings_canvas.configure(scrollregion=(0, 0, bbox[2], canvas_height))
                            settings_canvas.yview_moveto(0)
                            _needs_scrolling_settings = False
                            try:
                                if settings_scrollbar.winfo_viewable():
                                    settings_scrollbar.grid_remove()
                            except (tk.TclError, AttributeError):
                                pass
                        else:
                            settings_canvas.configure(scrollregion=bbox)
                            _needs_scrolling_settings = True
                            try:
                                if not settings_scrollbar.winfo_viewable():
                                    settings_scrollbar.grid(row=0, column=1, sticky="ns")
                            except (tk.TclError, AttributeError):
                                pass
                            self.app.main_window_handler.update_scrollbar_visibility(settings_canvas, settings_scrollbar, 'vertical')
                else:
                    settings_scrollbar.grid_remove()
            except (AttributeError, tk.TclError):
                pass
            finally:
                _updating_scroll = False
        
        def on_frame_configure(event):
            self.app.root.after_idle(update_scroll_region)
        
        scrollable_frame.bind("<Configure>", on_frame_configure)
        
        settings_canvas_window = settings_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        def on_canvas_configure(event):
            if event.widget == settings_canvas:
                try:
                    canvas_width = event.width
                    if canvas_width > 1:
                        settings_canvas.itemconfig(settings_canvas_window, width=canvas_width)
                    self.app.root.after_idle(update_scroll_region)
                except (AttributeError, tk.TclError):
                    pass
        
        settings_canvas.bind('<Configure>', on_canvas_configure)
        
        def on_scroll(*args):
            settings_scrollbar.set(*args)
        
        settings_canvas.configure(yscrollcommand=on_scroll)
        
        # Сохраняем функцию обновления для использования извне
        self.app.update_scroll_region = update_scroll_region
        
        # Сохраняем ссылки для обновления размеров
        self.app.settings_canvas = settings_canvas
        self.app.settings_canvas_window = settings_canvas_window
        
        # Кастомная функция прокрутки
        def on_mousewheel_settings(event):
            if not _needs_scrolling_settings:
                return
            scroll_amount = int(-1 * (event.delta / 120))
            settings_canvas.yview_scroll(scroll_amount, "units")
        
        def on_mousewheel_linux_settings(event):
            if not _needs_scrolling_settings:
                return
            if event.num == 4:
                settings_canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                settings_canvas.yview_scroll(1, "units")
        
        settings_canvas.bind("<MouseWheel>", on_mousewheel_settings)
        settings_canvas.bind("<Button-4>", on_mousewheel_linux_settings)
        settings_canvas.bind("<Button-5>", on_mousewheel_linux_settings)
        
        def bind_to_children_settings(parent):
            for child in parent.winfo_children():
                try:
                    child.bind("<MouseWheel>", on_mousewheel_settings)
                    child.bind("<Button-4>", on_mousewheel_linux_settings)
                    child.bind("<Button-5>", on_mousewheel_linux_settings)
                    bind_to_children_settings(child)
                except (AttributeError, tk.TclError):
                    pass
        
        bind_to_children_settings(scrollable_frame)
        
        settings_canvas.grid(row=0, column=0, sticky="nsew")
        settings_scrollbar.grid(row=0, column=1, sticky="ns")
        
        self.app.settings_frame = scrollable_frame
        
        # Объединенная группа кнопок
        self.app.method_buttons_frame = tk.Frame(methods_frame, bg=self.app.colors['bg_main'])
        self.app.method_buttons_frame.pack(fill=tk.X, pady=(0, 0))
        
        # Кнопка "Применить"
        btn_start_rename = self.app.create_rounded_button(
            self.app.method_buttons_frame, "✓ Применить", self.app.start_re_file,
            self.app.colors['success'], 'white',
            font=('Robot', 9, 'bold'), padx=6, pady=8,
            active_bg=self.app.colors['success_hover'], expand=True)
        btn_start_rename.pack(fill=tk.X, pady=(6, 0))
        
        # Скрытый listbox для внутреннего использования методов
        self.app.methods_listbox = tk.Listbox(methods_frame, height=0)
        self.app.methods_listbox.pack_forget()
        
        # Создаем log_text для логирования
        self.app.logger.set_log_widget(None)
        
        # Инициализация первого метода (Новое имя)
        self.app.on_method_selected()
        
        # Создание вкладок для сортировки и настроек (в старой структуре с Notebook)
        # Создаем скрытый Notebook для этих вкладок (они работают в старой структуре)
        hidden_notebook_frame = tk.Frame(self.app.root)
        hidden_notebook_frame.pack_forget()  # Скрываем, но создаем для обратной совместимости
        
        if not hasattr(self.app, 'main_notebook'):
            self.app.main_notebook = ttk.Notebook(hidden_notebook_frame)
            self.app.main_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Создаем вкладки для сортировки и настроек
        self.app.sorter_tab_handler.create_tab()
        self.app.settings_tab_handler.create_tab()


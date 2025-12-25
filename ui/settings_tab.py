"""Модуль для вкладки настроек.

Обеспечивает интерфейс для управления настройками приложения:
автоприменение, резервные копии, шрифты, контекстное меню и другие параметры.
"""

import logging
import os
import subprocess
import sys

import tkinter as tk
from tkinter import messagebox, ttk

logger = logging.getLogger(__name__)


class SettingsTab:
    """Класс для управления вкладкой настроек."""
    
    def __init__(self, app) -> None:
        """Инициализация вкладки настроек.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
    
    def create_tab(self):
        """Создание вкладки настроек на главном экране"""
        settings_tab = tk.Frame(self.app.main_notebook, bg=self.app.colors['bg_main'])
        settings_tab.columnconfigure(0, weight=1)
        settings_tab.rowconfigure(0, weight=1)
        self.app.main_notebook.add(settings_tab, text="Настройки")
        
        # Используем общий метод для создания содержимого
        self.create_tab_content(settings_tab)
    
    def create_tab_for_notebook(self, notebook):
        """Создание вкладки настроек для отдельного notebook"""
        # Фрейм для вкладки настроек
        settings_tab = tk.Frame(notebook, bg=self.app.colors['bg_card'])
        settings_tab.columnconfigure(0, weight=1)
        settings_tab.rowconfigure(0, weight=1)
        notebook.add(settings_tab, text="Настройки")
        
        # Используем общий метод для создания содержимого
        self.create_tab_content(settings_tab)
    
    def create_tab_content(self, settings_tab):
        """Создание содержимого вкладки настроек (используется и в главном окне, и в отдельном)"""
        # Определяем цвет фона в зависимости от того, где используется
        try:
            bg_color = settings_tab.cget('bg')
        except (tk.TclError, AttributeError):
            bg_color = self.app.colors['bg_main']
        # Содержимое настроек с прокруткой
        canvas = tk.Canvas(settings_tab, bg=bg_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(settings_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=bg_color)
        
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
            if event.widget == settings_tab:
                try:
                    canvas_width = settings_tab.winfo_width() - scrollbar.winfo_width() - 4
                    canvas.itemconfig(canvas_window, width=max(canvas_width, 100))
                except (AttributeError, tk.TclError):
                    pass
        
        settings_tab.bind('<Configure>', on_window_configure)
        
        # Функция для автоматического управления видимостью скроллбара
        def update_settings_scrollbar_visibility():
            """Обновление видимости скроллбара в настройках"""
            try:
                canvas.update_idletasks()
                bbox = canvas.bbox("all")
                if bbox:
                    canvas_height = canvas.winfo_height()
                    if canvas_height > 1:
                        content_height = bbox[3] - bbox[1]
                        # Если содержимое помещается, скрываем скроллбар
                        if content_height <= canvas_height + 2:
                            canvas.configure(scrollregion=(0, 0, bbox[2], canvas_height))
                            canvas.yview_moveto(0)
                            try:
                                if scrollbar.winfo_viewable():
                                    scrollbar.grid_remove()
                            except (tk.TclError, AttributeError):
                                pass
                        else:
                            canvas.configure(scrollregion=bbox)
                            try:
                                if not scrollbar.winfo_viewable():
                                    scrollbar.grid(row=0, column=1, sticky="ns")
                            except (tk.TclError, AttributeError):
                                pass
            except (tk.TclError, AttributeError):
                pass
        
        def on_settings_scroll(*args):
            scrollbar.set(*args)
            self.app.root.after(10, update_settings_scrollbar_visibility)
        
        canvas.configure(yscrollcommand=on_settings_scroll)
        
        # Обновляем scrollregion при изменении содержимого
        def on_scrollable_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            self.app.root.after(10, update_settings_scrollbar_visibility)
        
        scrollable_frame.bind("<Configure>", on_scrollable_configure)
        
        # Привязка прокрутки колесом мыши
        self.app.bind_mousewheel(canvas, canvas)
        self.app.bind_mousewheel(scrollable_frame, canvas)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        settings_tab.rowconfigure(0, weight=1)
        settings_tab.columnconfigure(0, weight=1)
        
        # Первоначальная проверка видимости скроллбара
        self.app.root.after(100, update_settings_scrollbar_visibility)
        
        content_frame = scrollable_frame
        content_frame.columnconfigure(0, weight=1)
        scrollable_frame.configure(padx=20, pady=20)
        
        # Заголовок убран - настройки начинаются сразу с секций
        
        # Функция для создания сворачиваемой секции
        def create_collapsible_frame(parent, title, default_expanded=False):
            """Создание сворачиваемой секции"""
            # Основной контейнер
            container = tk.Frame(parent, bg=bg_color)
            container.pack(fill=tk.X, pady=(0, 10))
            
            # Заголовок с кнопкой сворачивания
            header_frame = tk.Frame(container, bg=self.app.colors['bg_card'], cursor='hand2')
            header_frame.pack(fill=tk.X)
            
            # Индикатор сворачивания
            indicator = "▼" if default_expanded else "▶"
            indicator_label = tk.Label(header_frame, text=indicator, 
                                     font=('Robot', 12), 
                                     bg=self.app.colors['bg_card'],
                                     fg=self.app.colors['text_primary'])
            indicator_label.pack(side=tk.LEFT, padx=(10, 10))
            
            # Заголовок секции
            title_label = tk.Label(header_frame, text=title,
                                  font=('Robot', 12, 'bold'),
                                  bg=self.app.colors['bg_card'],
                                  fg=self.app.colors['text_primary'])
            title_label.pack(side=tk.LEFT)
            
            # Контент секции
            content_frame = ttk.LabelFrame(container, text="", 
                                          style='Card.TLabelframe', padding=20)
            is_expanded = default_expanded
            
            def toggle():
                nonlocal is_expanded
                is_expanded = not is_expanded
                if is_expanded:
                    content_frame.pack(fill=tk.BOTH, expand=True)
                    indicator_label.config(text="▼")
                else:
                    content_frame.pack_forget()
                    indicator_label.config(text="▶")
            
            if default_expanded:
                content_frame.pack(fill=tk.BOTH, expand=True)
            else:
                content_frame.pack_forget()
            
            # Привязка клика к заголовку
            header_frame.bind("<Button-1>", lambda e: toggle())
            indicator_label.bind("<Button-1>", lambda e: toggle())
            title_label.bind("<Button-1>", lambda e: toggle())
            
            return content_frame
        
        # Секция: Контекстное меню Windows
        if sys.platform == 'win32':
            context_menu_frame = create_collapsible_frame(content_frame, "Контекстное меню Windows", default_expanded=False)
            
            context_menu_info_label = tk.Label(context_menu_frame,
                                             text="Добавление пункта 'Добавить в конвертер Ре-Файл+' в контекстное меню Windows. "
                                                  "Позволяет быстро добавлять файлы в конвертер прямо из Проводника.",
                                             font=('Robot', 9),
                                             bg=self.app.colors['bg_card'],
                                             fg=self.app.colors['text_secondary'],
                                             wraplength=600,
                                             justify=tk.LEFT)
            context_menu_info_label.pack(anchor=tk.W, pady=(0, 15))
            
            # Импортируем менеджер контекстного меню
            try:
                from utils.context_menu import ContextMenuManager
                context_menu_manager = ContextMenuManager()
                
                # Фрейм для статуса и кнопок
                context_menu_controls = tk.Frame(context_menu_frame, bg=self.app.colors['bg_card'])
                context_menu_controls.pack(fill=tk.X, pady=(0, 10))
                
                # Статус установки
                status_label = tk.Label(context_menu_controls,
                                       text="Статус: Проверка...",
                                       font=('Robot', 9),
                                       bg=self.app.colors['bg_card'],
                                       fg=self.app.colors['text_primary'])
                status_label.pack(side=tk.LEFT, padx=(0, 15))
                
                # Кнопка установки
                def install_context_menu():
                    """Установка контекстного меню"""
                    success, message = context_menu_manager.install()
                    if success:
                        messagebox.showinfo("Успех", message)
                    else:
                        messagebox.showerror("Ошибка", message)
                    update_context_menu_status()
                
                install_btn = self.app.create_rounded_button(
                    context_menu_controls, "Установить", install_context_menu,
                    self.app.colors['primary'], 'white',
                    font=('Robot', 9), padx=15, pady=8,
                    active_bg=self.app.colors['primary_hover'])
                install_btn.pack(side=tk.LEFT, padx=(0, 10))
                
                # Кнопка удаления
                def uninstall_context_menu():
                    """Удаление контекстного меню"""
                    success, message = context_menu_manager.uninstall()
                    if success:
                        messagebox.showinfo("Успех", message)
                    else:
                        messagebox.showerror("Ошибка", message)
                    update_context_menu_status()
                
                uninstall_btn = self.app.create_rounded_button(
                    context_menu_controls, "Удалить", uninstall_context_menu,
                    self.app.colors['danger'], 'white',
                    font=('Robot', 9), padx=15, pady=8,
                    active_bg=self.app.colors['danger_hover'])
                uninstall_btn.pack(side=tk.LEFT)
                
                def update_context_menu_status():
                    """Обновление статуса контекстного меню"""
                    if context_menu_manager.is_installed():
                        status_label.config(text="Статус: ✓ Установлено", fg='green')
                        # Для rounded_button изменяем команду и визуальный вид
                        try:
                            # Получаем canvas из фрейма кнопки
                            install_canvas = install_btn.winfo_children()[0] if install_btn.winfo_children() else None
                            uninstall_canvas = uninstall_btn.winfo_children()[0] if uninstall_btn.winfo_children() else None
                            
                            # Делаем кнопку установки неактивной
                            if install_canvas:
                                install_canvas.btn_command = lambda: None  # Пустая команда
                                install_canvas.config(cursor='arrow')
                            
                            # Делаем кнопку удаления активной
                            if uninstall_canvas:
                                uninstall_canvas.btn_command = uninstall_context_menu
                                uninstall_canvas.config(cursor='hand2')
                        except Exception:
                            pass
                    else:
                        status_label.config(text="Статус: ✗ Не установлено", fg='gray')
                        # Обратное состояние
                        try:
                            install_canvas = install_btn.winfo_children()[0] if install_btn.winfo_children() else None
                            uninstall_canvas = uninstall_btn.winfo_children()[0] if uninstall_btn.winfo_children() else None
                            
                            # Делаем кнопку установки активной
                            if install_canvas:
                                install_canvas.btn_command = install_context_menu
                                install_canvas.config(cursor='hand2')
                            
                            # Делаем кнопку удаления неактивной
                            if uninstall_canvas:
                                uninstall_canvas.btn_command = lambda: None  # Пустая команда
                                uninstall_canvas.config(cursor='arrow')
                        except Exception:
                            pass
                
                # Обновляем статус при создании
                update_context_menu_status()
            
            except ImportError as e:
                error_label = tk.Label(context_menu_frame,
                                      text=f"Не удалось загрузить модуль контекстного меню: {e}",
                                      font=('Robot', 9),
                                      bg=self.app.colors['bg_card'],
                                      fg='red',
                                      wraplength=600,
                                      justify=tk.LEFT)
                error_label.pack(anchor=tk.W, pady=(0, 15))
        
        # Управление ярлыками (сворачиваемая секция)
        shortcuts_frame = create_collapsible_frame(content_frame, "Ярлыки", default_expanded=False)
        
        shortcuts_buttons_frame = tk.Frame(shortcuts_frame, bg=self.app.colors['bg_card'])
        shortcuts_buttons_frame.pack(fill=tk.X)
        shortcuts_buttons_frame.columnconfigure(0, weight=1)
        shortcuts_buttons_frame.columnconfigure(1, weight=1)
        
        def get_icon_path():
            """Получение пути к файлу иконки приложения"""
            app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            # Приоритет: icon.ico -> Логотип.ico
            icon_path = os.path.join(app_dir, "materials", "icon", "icon.ico")
            if not os.path.exists(icon_path):
                icon_path = os.path.join(app_dir, "materials", "icon", "Логотип.ico")
            if os.path.exists(icon_path):
                return os.path.abspath(icon_path)
            return None
        
        def create_desktop_shortcut():
            """Создание ярлыка на рабочем столе"""
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                desktop = shell.SpecialFolders("Desktop")
                shortcut_path = os.path.join(desktop, "Ре-Файл+.lnk")
                shortcut = shell.CreateShortCut(shortcut_path)
                # Определяем путь к основному файлу запуска
                app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                launch_file = os.path.join(app_dir, "file_renamer.py")
                if not os.path.exists(launch_file):
                    launch_file = os.path.join(app_dir, "Запуск.pyw")
                shortcut.Targetpath = sys.executable
                shortcut.Arguments = f'"{launch_file}"'
                shortcut.WorkingDirectory = app_dir
                
                # Устанавливаем иконку для ярлыка
                icon_path = get_icon_path()
                if icon_path:
                    # IconLocation принимает путь к файлу и индекс иконки (0 - первая иконка)
                    shortcut.IconLocation = f"{icon_path},0"
                
                shortcut.save()
                messagebox.showinfo("Успех", "Ярлык на рабочем столе создан")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать ярлык: {e}")
        
        def delete_desktop_shortcut():
            """Удаление ярлыка с рабочего стола"""
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                desktop = shell.SpecialFolders("Desktop")
                shortcut_path = os.path.join(desktop, "Ре-Файл+.lnk")
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    messagebox.showinfo("Успех", "Ярлык с рабочего стола удален")
                else:
                    messagebox.showinfo("Информация", "Ярлык на рабочем столе не найден")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить ярлык: {e}")
        
        def create_start_menu_shortcut():
            """Создание или обновление ярлыка в меню Пуск с иконкой"""
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                start_menu = shell.SpecialFolders("StartMenu")
                shortcut_path = os.path.join(start_menu, "Programs", "Ре-Файл+.lnk")
                os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)
                
                # Создаем или открываем существующий ярлык
                shortcut = shell.CreateShortCut(shortcut_path)
                
                # Определяем путь к основному файлу запуска
                app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                launch_file = os.path.join(app_dir, "file_renamer.py")
                if not os.path.exists(launch_file):
                    launch_file = os.path.join(app_dir, "Запуск.pyw")
                
                # Устанавливаем параметры ярлыка
                shortcut.Targetpath = sys.executable
                shortcut.Arguments = f'"{launch_file}"'
                shortcut.WorkingDirectory = app_dir
                
                # Устанавливаем иконку для ярлыка (важно для меню Пуск)
                icon_path = get_icon_path()
                if icon_path:
                    # IconLocation принимает путь к файлу и индекс иконки (0 - первая иконка)
                    # Формат: "путь_к_файлу,индекс"
                    shortcut.IconLocation = f"{icon_path},0"
                else:
                    # Если иконка не найдена, используем иконку из исполняемого файла Python
                    # Это запасной вариант
                    shortcut.IconLocation = f"{sys.executable},0"
                
                # Сохраняем ярлык
                shortcut.save()
                
                # Принудительно обновляем кэш иконок Windows для меню Пуск
                try:
                    import ctypes
                    # SHCNE_ASSOCCHANGED - обновление ассоциаций файлов
                    # SHCNE_UPDATEITEM - обновление элемента
                    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
                    ctypes.windll.shell32.SHChangeNotify(0x00002000, 0x0000, None, None)
                except:
                    pass
                
                if os.path.exists(shortcut_path):
                    messagebox.showinfo("Успех", "Ярлык в меню Пуск создан/обновлен с иконкой")
                else:
                    messagebox.showinfo("Успех", "Ярлык в меню Пуск создан")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось создать ярлык: {e}")
        
        def update_existing_shortcuts():
            """Обновление иконки существующих ярлыков в меню Пуск и на рабочем столе"""
            updated_count = 0
            icon_path = get_icon_path()
            
            if not icon_path:
                messagebox.showwarning("Предупреждение", "Файл иконки не найден")
                return
            
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                
                # Обновляем ярлык в меню Пуск
                try:
                    start_menu = shell.SpecialFolders("StartMenu")
                    shortcut_path = os.path.join(start_menu, "Programs", "Ре-Файл+.lnk")
                    if os.path.exists(shortcut_path):
                        shortcut = shell.CreateShortCut(shortcut_path)
                        shortcut.IconLocation = f"{icon_path},0"
                        shortcut.save()
                        updated_count += 1
                except Exception as e:
                    logger.debug(f"Не удалось обновить ярлык в меню Пуск: {e}")
                
                # Обновляем ярлык на рабочем столе
                try:
                    desktop = shell.SpecialFolders("Desktop")
                    shortcut_path = os.path.join(desktop, "Ре-Файл+.lnk")
                    if os.path.exists(shortcut_path):
                        shortcut = shell.CreateShortCut(shortcut_path)
                        shortcut.IconLocation = f"{icon_path},0"
                        shortcut.save()
                        updated_count += 1
                except Exception as e:
                    logger.debug(f"Не удалось обновить ярлык на рабочем столе: {e}")
                
                # Обновляем кэш иконок Windows
                try:
                    import ctypes
                    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
                    ctypes.windll.shell32.SHChangeNotify(0x00002000, 0x0000, None, None)
                except:
                    pass
                
                if updated_count > 0:
                    messagebox.showinfo("Успех", f"Обновлено ярлыков: {updated_count}")
                else:
                    messagebox.showinfo("Информация", "Ярлыки не найдены для обновления")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить ярлыки: {e}")
        
        def delete_start_menu_shortcut():
            """Удаление ярлыка из меню Пуск"""
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                start_menu = shell.SpecialFolders("StartMenu")
                shortcut_path = os.path.join(start_menu, "Programs", "Ре-Файл+.lnk")
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    messagebox.showinfo("Успех", "Ярлык из меню Пуск удален")
                else:
                    messagebox.showinfo("Информация", "Ярлык в меню Пуск не найден")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить ярлык: {e}")
        
        btn_create_desktop = self.app.create_rounded_button(
            shortcuts_buttons_frame, "Создать ярлык на рабочем столе", create_desktop_shortcut,
            self.app.colors['success'], 'white',
            font=('Robot', 9, 'bold'), padx=8, pady=6,
            active_bg=self.app.colors['success_hover'], expand=True)
        btn_create_desktop.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        btn_delete_desktop = self.app.create_rounded_button(
            shortcuts_buttons_frame, "Удалить ярлык с рабочего стола", delete_desktop_shortcut,
            self.app.colors['danger'], 'white',
            font=('Robot', 9, 'bold'), padx=8, pady=6,
            active_bg=self.app.colors['danger_hover'], expand=True)
        btn_delete_desktop.grid(row=0, column=1, sticky="ew")
        
        btn_create_start = self.app.create_rounded_button(
            shortcuts_buttons_frame, "Создать ярлык в меню Пуск", create_start_menu_shortcut,
            self.app.colors['success'], 'white',
            font=('Robot', 9, 'bold'), padx=8, pady=6,
            active_bg=self.app.colors['success_hover'], expand=True)
        btn_create_start.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(5, 0))
        
        btn_delete_start = self.app.create_rounded_button(
            shortcuts_buttons_frame, "Удалить ярлык из меню Пуск", delete_start_menu_shortcut,
            self.app.colors['danger'], 'white',
            font=('Robot', 9, 'bold'), padx=8, pady=6,
            active_bg=self.app.colors['danger_hover'], expand=True)
        btn_delete_start.grid(row=1, column=1, sticky="ew", pady=(5, 0))
        
        # Кнопка для обновления иконок существующих ярлыков
        btn_update_icons = self.app.create_rounded_button(
            shortcuts_buttons_frame, "Обновить иконки ярлыков", update_existing_shortcuts,
            self.app.colors['info'], 'white',
            font=('Robot', 9, 'bold'), padx=8, pady=6,
            active_bg=self.app.colors['info_hover'], expand=True)
        btn_update_icons.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        
        # Секция: Поведение программы (сворачиваемая секция)
        behavior_frame = create_collapsible_frame(content_frame, "Поведение программы", default_expanded=False)
        
        # Настройка удаления файлов после операций
        remove_files_var = tk.BooleanVar(value=self.app.settings_manager.get('remove_files_after_operation', False))
        
        def on_remove_files_change():
            """Обработчик изменения настройки удаления файлов"""
            self.app.settings_manager.set('remove_files_after_operation', remove_files_var.get())
            self.app.settings_manager.save_settings()
        
        remove_files_check = tk.Checkbutton(
            behavior_frame,
            text="Удалять файлы из списка после успешного переименования или конвертации",
            variable=remove_files_var,
            command=on_remove_files_change,
            bg=self.app.colors['bg_card'],
            fg=self.app.colors['text_primary'],
            font=('Robot', 9),
            anchor='w',
            activebackground=self.app.colors['bg_card'],
            activeforeground=self.app.colors['text_primary']
        )
        remove_files_check.pack(anchor=tk.W, fill=tk.X, pady=(0, 10))
        
        remove_files_info = tk.Label(
            behavior_frame,
            text="Если включено, файлы будут автоматически удаляться из списка после успешного выполнения операции.",
            font=('Robot', 8),
            bg=self.app.colors['bg_card'],
            fg=self.app.colors['text_secondary'],
            wraplength=600,
            justify=tk.LEFT,
            anchor='w'
        )
        remove_files_info.pack(anchor=tk.W, fill=tk.X, pady=(0, 15))
        
        # Сохраняем ссылку на переменную для использования в других модулях
        self.app.remove_files_after_operation_var = remove_files_var
        
        # Секция: Логи (сворачиваемая секция)
        logs_frame = create_collapsible_frame(content_frame, "Логи", default_expanded=False)
        
        logs_info_label = tk.Label(logs_frame,
                                 text="Просмотр и управление логами программы. Все действия записываются в файл лога.",
                                 font=('Robot', 9),
                                 bg=self.app.colors['bg_card'],
                                 fg=self.app.colors['text_secondary'],
                                 wraplength=600,
                                 justify=tk.LEFT)
        logs_info_label.pack(anchor=tk.W, pady=(0, 15))
        
        logs_buttons_frame = tk.Frame(logs_frame, bg=self.app.colors['bg_card'])
        logs_buttons_frame.pack(fill=tk.X)
        logs_buttons_frame.columnconfigure(0, weight=1)
        
        def open_logs():
            """Открытие файла логов"""
            try:
                # Импорт функции работы с путями
                try:
                    from infrastructure.system.paths import get_log_file_path
                except ImportError:
                    # Fallback на старый импорт
                    from config.constants import get_log_file_path
                log_file_path = get_log_file_path()
                
                if os.path.exists(log_file_path):
                    # Открываем файл в системном редакторе по умолчанию (безопасно)
                    if sys.platform == 'win32':
                        os.startfile(log_file_path)
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', log_file_path], check=False)
                    else:
                        subprocess.run(['xdg-open', log_file_path], check=False)
                    logger.info(f"Открыт файл логов: {log_file_path}")
                else:
                    messagebox.showinfo("Информация", "Файл логов еще не создан")
            except Exception as e:
                logger.error(f"Ошибка при открытии логов: {e}", exc_info=True)
                messagebox.showerror("Ошибка", f"Не удалось открыть файл логов: {e}")
        
        btn_open_logs = self.app.create_rounded_button(
            logs_buttons_frame, "Открыть файл логов", open_logs,
            self.app.colors['primary'], 'white',
            font=('Robot', 9, 'bold'), padx=8, pady=6,
            active_bg=self.app.colors['primary_hover'], expand=True)
        btn_open_logs.pack(fill=tk.X)
    
    def load_settings(self):
        """Загрузка настроек из файла"""
        return self.app.settings_manager.load_settings()
    
    def save_settings(self, settings_dict):
        """Сохранение настроек в файл"""
        return self.app.settings_manager.save_settings(settings_dict)

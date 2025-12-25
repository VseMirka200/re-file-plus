"""Модуль для управления шаблонами переименования.

Обеспечивает сохранение, загрузку и применение шаблонов имен файлов
с поддержкой метаданных и переменных.
"""

import json
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from ui.ui_components import set_window_icon

logger = logging.getLogger(__name__)


class TemplatesManager:
    """Класс для управления шаблонами переименования."""
    
    def __init__(self, app):
        """Инициализация менеджера шаблонов.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
        self._template_change_timer = None
    
    def save_template_quick(self):
        """Быстрое сохранение шаблона (Ctrl+S)"""
        self.save_current_template()
    
    def save_current_template(self):
        """Сохранение текущего шаблона"""
        if not hasattr(self.app, 'new_name_template'):
            return
        
        template = self.app.new_name_template.get().strip()
        if not template:
            messagebox.showwarning("Предупреждение", "Введите шаблон для сохранения")
            return
        
        # Запрашиваем имя для шаблона
        template_name = simpledialog.askstring(
            "Сохранить шаблон",
            "Введите имя для шаблона:",
            initialvalue=template[:30]  # Предлагаем первые 30 символов
        )
        
        if template_name:
            template_name = template_name.strip()
            if template_name:
                # Получаем начальный номер, если есть
                start_number = "1"
                if hasattr(self.app, 'new_name_start_number'):
                    start_number = self.app.new_name_start_number.get().strip() or "1"
                
                # Сохраняем шаблон
                self.app.saved_templates[template_name] = {
                    'template': template,
                    'start_number': start_number
                }
                # Обновляем в менеджере шаблонов
                self.app.templates_manager.templates = self.app.saved_templates
                self.app.save_templates()
                # Автосохранение шаблонов
                self.app.templates_manager.save_templates(self.app.saved_templates)
                self.app.log(f"Шаблон '{template_name}' сохранен")
                messagebox.showinfo("Успех", f"Шаблон '{template_name}' успешно сохранен!")
    
    def load_templates_from_file(self):
        """Загрузка шаблонов из файла"""
        try:
            # Открываем диалог выбора файла
            file_path = filedialog.askopenfilename(
                title="Выберите файл с шаблонами",
                filetypes=[
                    ("JSON файлы", "*.json"),
                    ("Все файлы", "*.*")
                ],
                defaultextension=".json"
            )
            
            if not file_path:
                return
            
            # Загружаем шаблоны из файла
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_templates = json.load(f)
            
            if not isinstance(loaded_templates, dict):
                messagebox.showerror("Ошибка", "Неверный формат файла шаблонов")
                return
            
            if not loaded_templates:
                messagebox.showwarning("Предупреждение", "Файл не содержит шаблонов")
                return
            
            # Подсчитываем количество шаблонов для добавления
            new_templates = {}
            existing_count = 0
            added_count = 0
            
            for template_name, template_data in loaded_templates.items():
                # Проверяем формат шаблона
                if isinstance(template_data, dict):
                    if 'template' not in template_data:
                        continue
                elif isinstance(template_data, str):
                    # Совместимость: преобразуем старый формат (строка) в новый (словарь)
                    template_data = {'template': template_data, 'start_number': '1'}
                else:
                    continue
                
                # Если шаблон с таким именем уже существует, добавляем суффикс
                original_name = template_name
                counter = 1
                while template_name in self.app.saved_templates:
                    template_name = f"{original_name} ({counter})"
                    counter += 1
                    existing_count += 1
                
                new_templates[template_name] = template_data
                added_count += 1
            
            if not new_templates:
                messagebox.showwarning("Предупреждение", "Не удалось загрузить ни одного шаблона из файла")
                return
            
            # Объединяем с существующими шаблонами
            self.app.saved_templates.update(new_templates)
            
            # Сохраняем обновленные шаблоны
            self.app.templates_manager.templates = self.app.saved_templates
            self.app.save_templates()
            self.app.templates_manager.save_templates(self.app.saved_templates)
            
            # Показываем результат
            message = f"Загружено шаблонов: {added_count}"
            if existing_count > 0:
                message += f"\nПереименовано из-за совпадений: {existing_count}"
            messagebox.showinfo("Успех", message)
            self.app.log(f"Загружено {added_count} шаблонов из файла: {file_path}")
            
        except json.JSONDecodeError:
            messagebox.showerror("Ошибка", "Неверный формат JSON файла")
        except FileNotFoundError:
            messagebox.showerror("Ошибка", "Файл не найден")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить шаблоны:\n{e}")
            self.app.log(f"Ошибка загрузки шаблонов: {e}")
    
    def show_saved_templates(self):
        """Показать окно с сохраненными шаблонами"""
        try:
            # Обновляем список шаблонов из менеджера
            self.app.saved_templates = self.app.templates_manager.templates
            
            # Создание окна выбора шаблона
            template_window = tk.Toplevel(self.app.root)
            template_window.title("Сохраненные шаблоны")
            template_window.geometry("600x500")
            template_window.transient(self.app.root)  # Делаем окно модальным относительно главного
            template_window.grab_set()  # Захватываем фокус
            
            # Установка иконки
            try:
                set_window_icon(template_window, self.app._icon_photos)
            except Exception:
                pass
            
            # Настройка фона окна
            template_window.configure(bg=self.app.colors['bg_main'])
            
            # Заголовок
            header_frame = tk.Frame(template_window, bg=self.app.colors['bg_main'])
            header_frame.pack(fill=tk.X, padx=10, pady=10)
            
            title_label = tk.Label(header_frame, text="Сохраненные шаблоны", 
                                  font=('Robot', 14, 'bold'),
                                  bg=self.app.colors['bg_main'], fg=self.app.colors['text_primary'])
            title_label.pack(anchor=tk.W)
            
            # Список шаблонов
            list_frame = tk.Frame(template_window, bg=self.app.colors['bg_main'])
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                font=('Robot', 10),
                                bg='white', fg='black',
                                selectbackground=self.app.colors['primary'],
                                selectforeground='white',
                                relief=tk.SOLID,
                                borderwidth=1)
            scrollbar.config(command=listbox.yview)
            
            # Функция для обновления списка шаблонов
            def refresh_template_list():
                listbox.delete(0, tk.END)
                template_keys = sorted(self.app.saved_templates.keys())
                for template_name in template_keys:
                    template_data = self.app.saved_templates[template_name]
                    if isinstance(template_data, dict):
                        template = template_data.get('template', '')
                    else:
                        template = str(template_data)
                    display_text = f"{template_name} → {template}"
                    listbox.insert(tk.END, display_text)
            
            # Заполняем список шаблонов
            refresh_template_list()
            
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Автоматическое управление видимостью скроллбара
            def update_saved_template_scrollbar(*args):
                self.app.update_scrollbar_visibility(listbox, scrollbar, 'vertical')
            
            def on_template_configure(e):
                template_window.after_idle(update_saved_template_scrollbar)
            
            listbox.bind('<Configure>', on_template_configure)
            template_window.after(100, update_saved_template_scrollbar)
            
            # Убеждаемся, что окно видимо
            template_window.update()
            template_window.deiconify()  # Показываем окно, если оно было скрыто
            
            # Кнопки
            btn_frame = tk.Frame(template_window, bg=self.app.colors['bg_main'])
            btn_frame.pack(fill=tk.X, padx=10, pady=10)
            btn_frame.columnconfigure(0, weight=1)
            btn_frame.columnconfigure(1, weight=1)
            btn_frame.columnconfigure(2, weight=1)
            btn_frame.columnconfigure(3, weight=1)
            btn_frame.columnconfigure(4, weight=1)
            btn_frame.columnconfigure(5, weight=1)
            
            def apply_template():
                selection = listbox.curselection()
                if selection:
                    template_name = sorted(self.app.saved_templates.keys())[selection[0]]
                    template_data = self.app.saved_templates[template_name]
                    template = template_data['template']
                    start_number = template_data.get('start_number', '1')
                    
                    # Применяем шаблон
                    self.app.new_name_template.delete(0, tk.END)
                    self.app.new_name_template.insert(0, template)
                    
                    if hasattr(self.app, 'new_name_start_number'):
                        self.app.new_name_start_number.delete(0, tk.END)
                        self.app.new_name_start_number.insert(0, start_number)
                    
                    template_window.destroy()
                    self.app.log(f"Применен сохраненный шаблон: {template_name}")
                    # Применяем шаблон
                    self.apply_template_quick(auto=True)
            
            def delete_template():
                selection = listbox.curselection()
                if selection:
                    template_name = sorted(self.app.saved_templates.keys())[selection[0]]
                    if messagebox.askyesno("Подтверждение", f"Удалить шаблон '{template_name}'?"):
                        del self.app.saved_templates[template_name]
                        # Обновляем в менеджере шаблонов
                        self.app.templates_manager.templates = self.app.saved_templates
                        self.app.save_templates()
                        # Автосохранение шаблонов
                        self.app.templates_manager.save_templates(self.app.saved_templates)
                        listbox.delete(selection[0])
                        self.app.log(f"Шаблон '{template_name}' удален")
                        if not self.app.saved_templates:
                            template_window.destroy()
                            messagebox.showinfo("Информация", "Все шаблоны удалены")
            
            btn_apply = self.app.create_rounded_button(
                btn_frame, "Применить", apply_template,
                self.app.colors['success'], 'white',
                font=('Robot', 9, 'bold'), padx=10, pady=6,
                active_bg=self.app.colors['success_hover'])
            btn_apply.grid(row=0, column=0, sticky="ew", padx=(0, 5))
            
            def export_templates():
                """Выгрузка сохраненных шаблонов в JSON файл"""
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    title="Сохранить шаблоны"
                )
                
                if file_path:
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(self.app.saved_templates, f, ensure_ascii=False, indent=2)
                        messagebox.showinfo("Успех", f"Шаблоны успешно сохранены в:\n{file_path}")
                        self.app.log(f"Шаблоны выгружены в: {file_path}")
                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Не удалось сохранить шаблоны:\n{e}")
                        self.app.log(f"Ошибка выгрузки шаблонов: {e}")
            
            btn_delete = self.app.create_rounded_button(
                btn_frame, "Удалить", delete_template,
                self.app.colors['danger'], 'white',
                font=('Robot', 9, 'bold'), padx=10, pady=6,
                active_bg=self.app.colors['danger_hover'])
            btn_delete.grid(row=0, column=1, sticky="ew", padx=(0, 5))
            
            btn_export = self.app.create_rounded_button(
                btn_frame, "Выгрузить", export_templates,
                self.app.colors['primary'], 'white',
                font=('Robot', 9, 'bold'), padx=10, pady=6,
                active_bg=self.app.colors['primary_hover'])
            btn_export.grid(row=0, column=2, sticky="ew", padx=(0, 5))
            
            def load_templates_and_refresh():
                """Загрузка шаблонов с обновлением списка в окне"""
                # Вызываем метод загрузки
                self.load_templates_from_file()
                
                # Обновляем список шаблонов в окне
                self.app.saved_templates = self.app.templates_manager.templates
                
                # Обновляем listbox
                refresh_template_list()
                
                # Обновляем скроллбар
                template_window.after_idle(update_saved_template_scrollbar)
            
            btn_load = self.app.create_rounded_button(
                btn_frame, "Загрузить", load_templates_and_refresh,
                '#3B82F6', 'white',
                font=('Robot', 9, 'bold'), padx=10, pady=6,
                active_bg='#2563EB')
            btn_load.grid(row=0, column=3, sticky="ew", padx=(0, 5))
            
            btn_close = self.app.create_rounded_button(
                btn_frame, "Закрыть", template_window.destroy,
                '#818CF8', 'white',
                font=('Robot', 9, 'bold'), padx=10, pady=6,
                active_bg='#6366F1')
            btn_close.grid(row=0, column=4, sticky="ew")
            
            # Двойной клик для применения
            listbox.bind('<Double-Button-1>', lambda e: apply_template())
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть окно сохраненных шаблонов:\n{e}")
            self.app.log(f"Ошибка открытия сохраненных шаблонов: {e}")
    
    def _apply_template_immediate(self):
        """Немедленное применение шаблона (при потере фокуса)"""
        if hasattr(self.app, 'new_name_template'):
            template = self.app.new_name_template.get().strip()
            if template:
                try:
                    self.apply_template_quick(auto=True)
                except Exception as e:
                    # Логируем ошибки, но не показываем пользователю при автоматическом применении
                    try:
                        if hasattr(self.app, 'log'):
                            self.app.log(f"Ошибка при применении шаблона: {e}")
                    except Exception as log_error:
                        logger.debug(f"Не удалось залогировать ошибку применения шаблона: {log_error}")
    
    def _apply_template_delayed(self):
        """Отложенное применение шаблона (используется для автоматического применения при вводе)"""
        # Сбрасываем таймер
        self._template_change_timer = None
        if hasattr(self.app, 'new_name_template'):
            template = self.app.new_name_template.get().strip()
            if template:
                try:
                    # Применяем шаблон
                    self.apply_template_quick(auto=True)
                    # Убеждаемся, что таблица обновлена
                    if hasattr(self.app, 'refresh_treeview'):
                        self.app.refresh_treeview()
                except Exception as e:
                    # Логируем ошибки, но не показываем пользователю при автоматическом применении
                    try:
                        if hasattr(self.app, 'log'):
                            self.app.log(f"Ошибка при автоматическом применении шаблона: {e}")
                    except Exception as log_error:
                        logger.debug(f"Не удалось залогировать ошибку применения шаблона: {log_error}")
    
    def apply_template_quick(self, auto=False):
        """Быстрое применение шаблона: добавление метода и применение"""
        from core.rename_methods import NewNameMethod
        
        template = self.app.new_name_template.get().strip()
        
        if not template:
            if not auto:
                messagebox.showwarning(
                    "Предупреждение",
                    "Введите шаблон или выберите из быстрых шаблонов"
                )
            return
        
        try:
            # Удаляем старый метод "Новое имя", если он есть
            methods_to_remove = []
            for i, method in enumerate(self.app.methods_manager.get_methods()):
                if isinstance(method, NewNameMethod):
                    methods_to_remove.append(i)
            
            # Удаляем в обратном порядке, чтобы индексы не сбились
            for i in reversed(methods_to_remove):
                self.app.methods_manager.remove_method(i)
                if i < self.app.methods_listbox.size():
                    self.app.methods_listbox.delete(i)
            
            # Создаем новый метод используя общий метод
            method = self.app._create_new_name_method(template)
            
            # Добавляем метод
            self.app.methods_manager.add_method(method)
            self.app.methods_listbox.insert(tk.END, "Новое имя")
            
            if not auto:
                self.app.log(f"Добавлен метод: Новое имя (шаблон: {template})")
            
            # Автоматически применяем метод
            if self.app.files:
                # Применяем методы и принудительно обновляем таблицу
                self.app.apply_methods()
                # Полностью обновляем таблицу для отображения изменений
                self.app.refresh_treeview()
                # Принудительно обновляем отображение
                self.app.root.update_idletasks()
            
            if not auto:
                messagebox.showinfo(
                    "Готово",
                    f"Шаблон '{template}' применен!\n"
                    f"Проверьте предпросмотр в таблице."
                )
            
        except Exception as e:
            if not auto:
                messagebox.showerror("Ошибка", f"Не удалось применить шаблон: {e}")
            else:
                # Используем try-except для логирования, так как log может быть не инициализирован
                try:
                    self.app.log(f"Ошибка при применении шаблона: {e}")
                except Exception as log_error:
                    logger.debug(f"Не удалось залогировать ошибку применения шаблона: {log_error}")

"""Модуль для обработки изменения размера окна и управления колонками."""

import logging
import tkinter as tk
from tkinter import ttk

logger = logging.getLogger(__name__)


class MainWindowResize:
    """Класс для управления изменением размеров главного окна.
    
    Отвечает за:
    - Динамическое изменение размеров колонок Treeview при изменении размера окна
    - Автоматическое управление видимостью scrollbar в зависимости от содержимого
    - Адаптация UI элементов к изменению размеров окна
    
    Обеспечивает корректное отображение содержимого при любых размерах окна.
    """
    
    def __init__(self, app):
        """Инициализация.
        
        Args:
            app: Экземпляр главного приложения
        """
        self.app = app
    
    def update_tree_columns_for_action(self, action: str) -> None:
        """Обновление колонок таблицы в зависимости от выбранного действия.

        Args:
            action: Название действия ('rename', 'convert')
        """
        if not hasattr(self.app, 'tree') or not self.app.tree:
            return
        
        try:
            current_columns = list(self.app.tree['columns'])
            
            # Используем три колонки: "Имя файла", "Новое имя" и "Путь"
            required_columns = ("files", "new_name", "path")
            if current_columns != list(required_columns):
                self.app.tree['columns'] = required_columns
                # Настраиваем заголовки
                self.app.tree.heading("files", text="Имя файла", command=lambda: self.app.file_list_manager.sort_column("files"))
                self.app.tree.heading("new_name", text="Новое имя", command=lambda: self.app.file_list_manager.sort_column("new_name"))
                self.app.tree.heading("path", text="Путь", command=lambda: self.app.file_list_manager.sort_column("path"))
                # Настраиваем колонки (равной ширины)
                list_frame_width = self.app.list_frame.winfo_width() if hasattr(self.app, 'list_frame') else 900
                column_width = max(int(list_frame_width / 3), 200)
                self.app.tree.column("files", width=column_width, anchor='w', minwidth=150, stretch=tk.YES)
                self.app.tree.column("new_name", width=column_width, anchor='w', minwidth=150, stretch=tk.YES)
                self.app.tree.column("path", width=column_width, anchor='w', minwidth=200, stretch=tk.YES)
            
            # Вызываем обновление размеров
            self.app.root.after(100, self.update_tree_columns)
        except (tk.TclError, AttributeError) as e:
            logger.debug(f"Ошибка обновления колонок для действия {action}: {e}")
    
    def update_tree_columns(self) -> None:
        """Обновление размеров колонок таблицы в соответствии с размером окна."""
        has_list_frame = hasattr(self.app, 'list_frame')
        has_tree = hasattr(self.app, 'tree')
        if has_list_frame and has_tree and self.app.list_frame and self.app.tree:
            try:
                # Определяем активную вкладку
                current_tab = getattr(self.app, 'current_tab', 'files')
                
                list_frame_width = self.app.list_frame.winfo_width()
                if list_frame_width > 100:
                    if current_tab == 'convert':
                        # Для конвертера: только "Имя файла" и "Путь" (без "Новое имя")
                        column_width = max(int(list_frame_width / 2), 200)
                        
                        # Скрываем колонку "new_name" для конвертера
                        self.app.tree.column("new_name", width=0, minwidth=0, stretch=tk.NO)
                        self.app.tree.heading("new_name", text="")
                        
                        self.app.tree.column(
                            "files",
                            width=column_width,
                            minwidth=200,
                            stretch=tk.YES
                        )
                        self.app.tree.column(
                            "path",
                            width=column_width,
                            minwidth=200,
                            stretch=tk.YES
                        )
                    else:
                        # Для переименовщика: все три колонки
                        column_width = max(int(list_frame_width / 3), 150)
                        
                        # Показываем колонку "new_name" для переименовщика
                        self.app.tree.heading("new_name", text="Новое имя", command=lambda: self.app.file_list_manager.sort_column("new_name"))
                        self.app.tree.column("new_name", width=column_width, minwidth=150, stretch=tk.YES)
                        
                        self.app.tree.column(
                            "files",
                            width=column_width,
                            minwidth=150,
                            stretch=tk.YES
                        )
                        self.app.tree.column(
                            "path",
                            width=column_width,
                            minwidth=200,
                            stretch=tk.YES
                        )
                    
                    if hasattr(self.app, 'tree_scrollbar_x'):
                        self.app.root.after_idle(lambda: self.update_scrollbar_visibility(
                            self.app.tree, self.app.tree_scrollbar_x, 'horizontal'))
            except Exception as e:
                logger.debug(f"Ошибка обновления колонок таблицы: {e}")
    
    def update_scrollbar_visibility(
        self, widget, scrollbar, orientation: str = 'vertical'
    ) -> None:
        """Автоматическое управление видимостью скроллбара.
        
        Args:
            widget: Виджет (Treeview, Listbox, Text, Canvas)
            scrollbar: Скроллбар для управления
            orientation: Ориентация ('vertical' или 'horizontal')
        """
        try:
            if isinstance(widget, ttk.Treeview):
                items = widget.get_children()
                if not items:
                    scrollbar.grid_remove()
                    return
                
                widget.update_idletasks()
                if orientation == 'vertical':
                    widget_height = widget.winfo_height()
                    item_height = 20
                    visible_items = max(1, widget_height // item_height) if widget_height > 0 else 1
                    needs_scroll = len(items) > visible_items
                else:
                    widget_width = widget.winfo_width()
                    if widget_width > 0:
                        total_width = 0
                        for col in widget['columns']:
                            col_width = widget.column(col, 'width')
                            if col_width:
                                total_width += col_width
                        try:
                            tree_col_width = widget.column('#0', 'width')
                            if tree_col_width:
                                total_width += tree_col_width
                        except (tk.TclError, AttributeError):
                            pass
                        needs_scroll = total_width > widget_width
                    else:
                        needs_scroll = False
                
            elif isinstance(widget, tk.Listbox):
                count = widget.size()
                widget.update_idletasks()
                widget_height = widget.winfo_height()
                if widget_height > 0:
                    item_height = widget.bbox(0)[3] - widget.bbox(0)[1] if count > 0 and widget.bbox(0) else 20
                    visible_items = max(1, widget_height // item_height) if item_height > 0 else 1
                    needs_scroll = count > visible_items
                else:
                    needs_scroll = count > 0
            
            elif isinstance(widget, tk.Text):
                widget.update_idletasks()
                widget_height = widget.winfo_height()
                if widget_height > 0:
                    line_height = widget.dlineinfo('1.0')
                    if line_height:
                        line_height = line_height[3]
                        visible_lines = max(1, widget_height // line_height) if line_height > 0 else 1
                        total_lines = int(widget.index('end-1c').split('.')[0])
                        needs_scroll = total_lines > visible_lines
                    else:
                        needs_scroll = False
                else:
                    needs_scroll = False
            
            elif isinstance(widget, tk.Canvas):
                widget.update_idletasks()
                bbox = widget.bbox("all")
                if bbox:
                    if orientation == 'vertical':
                        canvas_height = widget.winfo_height()
                        content_height = bbox[3] - bbox[1]
                        needs_scroll = content_height > canvas_height and canvas_height > 1
                    else:
                        canvas_width = widget.winfo_width()
                        content_width = bbox[2] - bbox[0]
                        needs_scroll = content_width > canvas_width and canvas_width > 1
                else:
                    needs_scroll = False
            else:
                return
            
            # Показываем или скрываем скроллбар
            if needs_scroll:
                if scrollbar.winfo_manager() == '':
                    if hasattr(scrollbar, '_grid_info'):
                        scrollbar.grid(**scrollbar._grid_info)
                    elif hasattr(scrollbar, '_pack_info'):
                        scrollbar.pack(**scrollbar._pack_info)
                else:
                    try:
                        scrollbar.grid()
                    except tk.TclError:
                        try:
                            scrollbar.pack()
                        except tk.TclError as e:
                            logger.debug(f"Не удалось показать скроллбар: {e}")
            else:
                try:
                    grid_info = scrollbar.grid_info()
                    if grid_info:
                        scrollbar._grid_info = grid_info
                        scrollbar.grid_remove()
                except tk.TclError:
                    try:
                        pack_info = scrollbar.pack_info()
                        if pack_info:
                            scrollbar._pack_info = pack_info
                            scrollbar.pack_forget()
                    except tk.TclError as e:
                        logger.debug(f"Не удалось скрыть скроллбар: {e}")
        except (AttributeError, tk.TclError, ValueError):
            pass
    
    def on_window_resize(self, event=None) -> None:
        """Обработчик изменения размера окна для адаптивного масштабирования."""
        if event and event.widget == self.app.root:
            if hasattr(self.app, 'list_frame') and self.app.list_frame:
                try:
                    self.app.root.after(50, self.update_tree_columns)
                    self.app.root.after(200, self.update_tree_columns)
                except (AttributeError, tk.TclError):
                    pass


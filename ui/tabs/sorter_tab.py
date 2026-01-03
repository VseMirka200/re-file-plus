"""Модуль для вкладки сортировки файлов.

Обеспечивает интерфейс для сортировки файлов по различным критериям:
дата создания, размер, расширение и другие параметры.

ВНИМАНИЕ: Этот модуль теперь является координатором.
Основная логика перенесена в ui/sorter/.
"""

import logging

# Локальные импорты
from ui.sorter.ui import SorterUI
from ui.sorter.folder import SorterFolder
from ui.sorter.filters import SorterFilters
from ui.sorter.sorting import SorterSorting

logger = logging.getLogger(__name__)


class SorterTab:
    """Класс для управления вкладкой сортировки файлов.
    
    Теперь является координатором, делегирующим работу подмодулям.
    """
    
    def __init__(self, app):
        """Инициализация вкладки сортировки.
        
        Args:
            app: Экземпляр главного приложения (для доступа к методам и данным)
        """
        self.app = app
        # Инициализируем подмодули
        self.ui = SorterUI(app)
        self.folder = SorterFolder(app)
        self.filters = SorterFilters(app)
        self.sorting = SorterSorting(app)
    
    def create_tab(self):
        """Создание вкладки сортировки файлов (делегируется ui)."""
        return self.ui.create_tab()
    
    def create_tab_content(self, parent):
        """Создание содержимого вкладки сортировки (делегируется ui).
        
        Args:
            parent: Родительский контейнер для размещения содержимого
        """
        return self.ui.create_tab_content(parent)
    
    def browse_sorter_folder(self):
        """Выбор папки для сортировки (делегируется folder)."""
        return self.folder.browse_sorter_folder()
    
    def add_sorter_filter(self):
        """Добавление нового правила фильтрации (делегируется filters)."""
        return self.filters.add_sorter_filter()
    
    def refresh_filters_display(self):
        """Обновление отображения фильтров (делегируется filters)."""
        return self.filters.refresh_filters_display()
    
    def toggle_filter(self, index):
        """Включение/выключение фильтра (делегируется filters)."""
        return self.filters.toggle_filter(index)
    
    def delete_filter(self, index):
        """Удаление фильтра (делегируется filters)."""
        return self.filters.delete_filter(index)
    
    def add_default_filters(self):
        """Добавление фильтров по умолчанию (делегируется filters)."""
        return self.filters.add_default_filters()
    
    def save_sorter_filters(self):
        """Сохранение фильтров в настройки (делегируется filters)."""
        return self.filters.save_sorter_filters()
    
    def load_sorter_filters(self):
        """Загрузка фильтров из настроек (делегируется filters)."""
        return self.filters.load_sorter_filters()
    
    def preview_file_sorting(self):
        """Предпросмотр сортировки файлов (делегируется sorting)."""
        return self.sorting.preview_file_sorting()
    
    def start_file_sorting(self):
        """Запуск сортировки файлов (делегируется sorting)."""
        return self.sorting.start_file_sorting()
    
    def sort_files_thread(self, folder_path, filters):
        """Поток для сортировки файлов (делегируется sorting)."""
        return self.sorting.sort_files_thread(folder_path, filters)
    
    def file_matches_filter(self, file_path, filter_data):
        """Проверка, соответствует ли файл фильтру (делегируется sorting)."""
        return self.sorting.file_matches_filter(file_path, filter_data)

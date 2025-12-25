"""Модуль для создания вкладки 'О программе'.

Отображает информацию о программе, разработчиках и используемых библиотеках.
"""

import logging
import os
import sys
import tkinter as tk
from tkinter import ttk

# Опциональные импорты
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

logger = logging.getLogger(__name__)


class AboutTab:
    """Класс для создания и управления вкладкой 'О программе'."""
    
    def __init__(self, notebook, colors, bind_mousewheel_func, icon_photos_list):
        """Инициализация вкладки 'О программе'.
        
        Args:
            notebook: Notebook виджет для добавления вкладки
            colors: Словарь с цветами интерфейса
            bind_mousewheel_func: Функция для привязки прокрутки колесом мыши
            icon_photos_list: Список для хранения ссылок на изображения
        """
        self.notebook = notebook
        self.colors = colors
        self.bind_mousewheel = bind_mousewheel_func
        self.icon_photos_list = icon_photos_list
        self._about_icons = []
    
    def create_tab(self):
        """Создание вкладки о программе на главном экране"""
        about_tab = tk.Frame(self.notebook, bg=self.colors['bg_main'])
        about_tab.columnconfigure(0, weight=1)
        about_tab.rowconfigure(0, weight=1)
        self.notebook.add(about_tab, text="О программе")
        
        # Содержимое о программе с прокруткой
        canvas = tk.Canvas(about_tab, bg=self.colors['bg_main'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(about_tab, orient="vertical", command=canvas.yview)
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
            if event.widget == about_tab:
                try:
                    canvas_width = about_tab.winfo_width() - scrollbar.winfo_width() - 4
                    canvas.itemconfig(canvas_window, width=max(canvas_width, 100))
                except (AttributeError, tk.TclError):
                    pass
        
        about_tab.bind('<Configure>', on_window_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Привязка прокрутки колесом мыши
        self.bind_mousewheel(canvas, canvas)
        self.bind_mousewheel(scrollable_frame, canvas)
        
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        about_tab.rowconfigure(0, weight=1)
        about_tab.columnconfigure(0, weight=1)
        
        content_frame = scrollable_frame
        content_frame.columnconfigure(0, weight=1)
        scrollable_frame.configure(padx=20, pady=20)
        
        # Описание программы - карточка
        about_card = ttk.LabelFrame(content_frame, text="О программе", 
                                    style='Card.TLabelframe', padding=20)
        about_card.pack(fill=tk.X, pady=(10, 20))
        
        # Контейнер для двух столбцов (изображение, описание)
        about_content_frame = tk.Frame(about_card, bg=self.colors['bg_card'])
        about_content_frame.pack(fill=tk.BOTH, expand=True)
        about_content_frame.columnconfigure(0, weight=0)  # Левый столбец (изображение) - фиксированная ширина
        about_content_frame.columnconfigure(1, weight=1)  # Средний столбец (описание) - растягивается
        about_content_frame.rowconfigure(0, weight=1)  # Растягиваем строку по высоте
        
        # Левый столбец: контейнер для изображения, названия и версии
        left_container = tk.Frame(about_content_frame, bg=self.colors['bg_card'])
        left_container.grid(row=0, column=0, sticky="nsew", padx=(0, 20))
        
        # Внутренний контейнер для центрирования содержимого по вертикали
        left_inner = tk.Frame(left_container, bg=self.colors['bg_card'])
        left_inner.pack(expand=True, fill=tk.BOTH)
        
        # Изображение программы с рамкой
        image_frame = tk.Frame(left_inner, bg=self.colors['bg_card'], 
                               highlightbackground=self.colors['border'],
                               highlightthickness=1,
                               relief=tk.FLAT)
        image_frame.pack(anchor=tk.CENTER, pady=(0, 15), padx=5)
        
        # Получаем версию программы из констант
        try:
            from config.constants import APP_VERSION
        except ImportError:
            APP_VERSION = "1.0.0"
        
        try:
            # Используем существующий логотип приложения
            # Приоритет: icon.ico -> Логотип.ico -> Логотип.png
            possible_paths = [
                os.path.join(os.path.dirname(__file__), "..", "materials", "icon", "icon.ico"),
                os.path.join(os.path.dirname(__file__), "..", "materials", "icon", "Логотип.ico"),
                os.path.join(os.path.dirname(__file__), "..", "materials", "icon", "Логотип.png"),
            ]
            image_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    image_path = path
                    logger.debug(f"Найдено изображение приложения: {path}")
                    break
            
            if image_path and HAS_PIL:
                img = Image.open(image_path)
                img = img.resize((150, 150), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self._about_icons.append(photo)
                self.icon_photos_list.append(photo)  # Сохраняем в общий список
                image_label = tk.Label(image_frame, image=photo, bg=self.colors['bg_card'])
                image_label.pack(anchor=tk.CENTER)
            elif not HAS_PIL:
                logger.warning("PIL (Pillow) не установлен, изображение приложения не может быть загружено")
            else:
                logger.warning(f"Изображение приложения не найдено. Проверенные пути: {possible_paths}")
        except Exception as e:
            logger.error(f"Ошибка загрузки изображения приложения: {e}", exc_info=True)
        
        # Название программы под изображением
        app_name_label = tk.Label(left_inner,
                                 text="Ре-Файл+",
                                 font=('Robot', 22, 'bold'),
                                 bg=self.colors['bg_card'],
                                 fg=self.colors['primary'])
        app_name_label.pack(anchor=tk.CENTER, pady=(0, 8))
        
        # Версия программы под названием
        version_label = tk.Label(left_inner,
                                text=f"Версия {APP_VERSION}",
                                font=('Robot', 9),
                                bg=self.colors['bg_card'],
                                fg=self.colors['text_secondary'])
        version_label.pack(anchor=tk.CENTER)
        
        # Средний столбец: описание программы
        desc_frame = tk.Frame(about_content_frame, bg=self.colors['bg_card'])
        desc_frame.grid(row=0, column=1, sticky="nsew")
        
        desc_text = """Ре-Файл+ - это мощная и удобная программа для массового переименования файлов. 

Программа предоставляет широкий набор инструментов для работы с именами файлов: 
переименование по различным шаблонам, поддержка метаданных (EXIF, ID3 и др.), 
предпросмотр изменений перед применением, удобный интерфейс с поддержкой Drag & Drop, 
возможность перестановки файлов в списке и многое другое.

Программа поможет вам быстро и эффективно организовать ваши файлы."""
        
        desc_label = tk.Label(desc_frame, 
                              text=desc_text,
                              font=('Robot', 10),
                              bg=self.colors['bg_card'], 
                              fg=self.colors['text_primary'],
                              justify=tk.LEFT,
                              anchor=tk.NW,
                              wraplength=500)
        desc_label.pack(anchor=tk.NW)
        
        # Карточка с используемыми библиотеками
        self._create_libraries_card(content_frame)
        
        # Разработчики - карточка
        self._create_developers_card(content_frame)
        
        # Социальные сети - карточка
        self._create_social_card(content_frame)
        
        # GitHub - карточка
        self._create_github_card(content_frame)
        
        # Контакты разработчиков - карточка
        self._create_contact_card(content_frame)
        
        # Поддержка проекта - карточка
        self._create_support_card(content_frame)
    
    def _create_libraries_card(self, parent):
        """Создание карточки с используемыми библиотеками и ссылками на скачивание"""
        libraries_card = ttk.LabelFrame(parent, text="Используемые библиотеки", 
                                        style='Card.TLabelframe', padding=20)
        libraries_card.pack(fill=tk.X, pady=(0, 20))
        
        # Список библиотек
        required_libs = ['Pillow', 'tkinterdnd2']
        optional_libs = ['python-docx', 'mutagen', 'openpyxl', 'python-pptx', 'pypdf', 'PyPDF2', 'pydub', 'moviepy']
        windows_libs = ['pywin32', 'comtypes', 'docx2pdf', 'pdf2docx'] if sys.platform == 'win32' else []
        
        # Стандартные библиотеки Python (без ссылок, так как встроены)
        standard_libs = ['Python 3', 'Tkinter', 'os', 'sys', 'subprocess', 'threading', 'logging', 'json', 're', 'pathlib']
        
        # Словарь ссылок на библиотеки (PyPI и документация Python)
        library_links = {
            # Стандартные библиотеки Python
            'Python 3': 'https://www.python.org/downloads/',
            'Tkinter': 'https://docs.python.org/3/library/tkinter.html',
            'os': 'https://docs.python.org/3/library/os.html',
            'sys': 'https://docs.python.org/3/library/sys.html',
            'subprocess': 'https://docs.python.org/3/library/subprocess.html',
            'threading': 'https://docs.python.org/3/library/threading.html',
            'logging': 'https://docs.python.org/3/library/logging.html',
            'json': 'https://docs.python.org/3/library/json.html',
            're': 'https://docs.python.org/3/library/re.html',
            'pathlib': 'https://docs.python.org/3/library/pathlib.html',
            # Внешние библиотеки
            'Pillow': 'https://pypi.org/project/Pillow/',
            'tkinterdnd2': 'https://pypi.org/project/tkinterdnd2/',
            'python-docx': 'https://pypi.org/project/python-docx/',
            'mutagen': 'https://pypi.org/project/mutagen/',
            'openpyxl': 'https://pypi.org/project/openpyxl/',
            'python-pptx': 'https://pypi.org/project/python-pptx/',
            'pypdf': 'https://pypi.org/project/pypdf/',
            'PyPDF2': 'https://pypi.org/project/PyPDF2/',
            'pydub': 'https://pypi.org/project/pydub/',
            'moviepy': 'https://pypi.org/project/moviepy/',
            'pywin32': 'https://pypi.org/project/pywin32/',
            'comtypes': 'https://pypi.org/project/comtypes/',
            'docx2pdf': 'https://pypi.org/project/docx2pdf/',
            'pdf2docx': 'https://pypi.org/project/pdf2docx/',
        }
        
        # Объединяем все библиотеки в один общий список
        all_libraries = []
        all_libraries.extend(standard_libs)
        all_libraries.extend(required_libs)
        all_libraries.extend(optional_libs)
        if windows_libs:
            all_libraries.extend(windows_libs)
        
        # Разделяем библиотеки на 5 столбцов
        total_libs = len(all_libraries)
        items_per_column = (total_libs + 4) // 5  # Округляем вверх
        column1_libs = all_libraries[:items_per_column]
        column2_libs = all_libraries[items_per_column:items_per_column * 2]
        column3_libs = all_libraries[items_per_column * 2:items_per_column * 3]
        column4_libs = all_libraries[items_per_column * 3:items_per_column * 4]
        column5_libs = all_libraries[items_per_column * 4:]
        
        # Контейнер для пяти столбцов библиотек
        libraries_columns_frame = tk.Frame(libraries_card, bg=self.colors['bg_card'])
        libraries_columns_frame.pack(anchor=tk.NW, fill=tk.X)
        
        # Функция для создания столбца библиотек
        def create_library_column(parent_frame, libs_list, padx_right=15):
            column_frame = tk.Frame(parent_frame, bg=self.colors['bg_card'])
            column_frame.pack(side=tk.LEFT, anchor=tk.NW, padx=(0, padx_right))
            
            for lib in libs_list:
                lib_frame = tk.Frame(column_frame, bg=self.colors['bg_card'])
                lib_frame.pack(anchor=tk.W, pady=2)
                
                bullet_label = tk.Label(lib_frame,
                                       text="•",
                                       font=('Robot', 9),
                                       bg=self.colors['bg_card'],
                                       fg=self.colors['text_primary'])
                bullet_label.pack(side=tk.LEFT, padx=(0, 5))
                
                # Если есть ссылка, делаем библиотеку кликабельной
                if lib in library_links:
                    lib_url = library_links[lib]
                    def make_open_url(url):
                        def open_url(event):
                            import webbrowser
                            webbrowser.open(url)
                        return open_url
                    
                    lib_label = tk.Label(lib_frame,
                                       text=lib,
                                       font=('Robot', 9),
                                       bg=self.colors['bg_card'],
                                       fg=self.colors['primary'],
                                       cursor='hand2',
                                       underline=0)
                    lib_label.pack(side=tk.LEFT)
                    lib_label.bind("<Button-1>", make_open_url(lib_url))
                else:
                    # Библиотеки без ссылок
                    lib_label = tk.Label(lib_frame,
                                       text=lib,
                                       font=('Robot', 9),
                                       bg=self.colors['bg_card'],
                                       fg=self.colors['text_primary'])
                    lib_label.pack(side=tk.LEFT)
        
        # Создаем 5 столбцов
        create_library_column(libraries_columns_frame, column1_libs, padx_right=15)
        create_library_column(libraries_columns_frame, column2_libs, padx_right=15)
        create_library_column(libraries_columns_frame, column3_libs, padx_right=15)
        create_library_column(libraries_columns_frame, column4_libs, padx_right=15)
        create_library_column(libraries_columns_frame, column5_libs, padx_right=0)
    
    def _create_developers_card(self, parent):
        """Создание карточки с информацией о разработчиках"""
        dev_card = ttk.LabelFrame(parent, text="Команда разработчиков", 
                                  style='Card.TLabelframe', padding=20)
        dev_card.pack(fill=tk.X, pady=(0, 20))
        
        # Ведущий разработчик
        lead_dev_frame = tk.Frame(dev_card, bg=self.colors['bg_card'])
        lead_dev_frame.pack(anchor=tk.W, pady=(0, 8))
        
        def open_lead_dev_profile(event):
            import webbrowser
            webbrowser.open("https://github.com/VseMirka200")
        
        lead_dev_prefix = tk.Label(lead_dev_frame, 
                            text="Ведущий разработчик: ",
                            font=('Robot', 10),
                            bg=self.colors['bg_card'], 
                            fg=self.colors['text_primary'],
                            justify=tk.LEFT)
        lead_dev_prefix.pack(side=tk.LEFT)
        
        lead_dev_name = tk.Label(lead_dev_frame, 
                            text="VseMirka200",
                            font=('Robot', 10),
                            bg=self.colors['bg_card'], 
                            fg=self.colors['primary'],
                            cursor='hand2',
                            justify=tk.LEFT)
        lead_dev_name.pack(side=tk.LEFT, padx=(0, 0))
        lead_dev_name.bind("<Button-1>", open_lead_dev_profile)
        
        # Разработчик
        dev_frame = tk.Frame(dev_card, bg=self.colors['bg_card'])
        dev_frame.pack(anchor=tk.W)
        
        def open_dev_profile(event):
            import webbrowser
            webbrowser.open("https://github.com/ZipFile45")
        
        dev_prefix = tk.Label(dev_frame, 
                            text="Разработчик: ",
                            font=('Robot', 10),
                            bg=self.colors['bg_card'], 
                            fg=self.colors['text_primary'],
                            justify=tk.LEFT)
        dev_prefix.pack(side=tk.LEFT)
        
        dev_name_label = tk.Label(dev_frame, 
                                 text="ZipFile45",
                                 font=('Robot', 10),
                                 bg=self.colors['bg_card'], 
                                 fg=self.colors['primary'],
                                 cursor='hand2',
                                 justify=tk.LEFT)
        dev_name_label.pack(side=tk.LEFT, padx=(0, 0))
        dev_name_label.bind("<Button-1>", open_dev_profile)
    
    def _create_social_card(self, parent):
        """Создание карточки с нашими сообществами"""
        social_card = ttk.LabelFrame(parent, text="Наши сообщества", 
                                     style='Card.TLabelframe', padding=20)
        social_card.pack(fill=tk.X, pady=(0, 20))
        
        def open_vk_social(event):
            import webbrowser
            webbrowser.open("https://vk.com/urban_solution")
        
        vk_frame = tk.Frame(social_card, bg=self.colors['bg_card'])
        vk_frame.pack(anchor=tk.W, fill=tk.X, pady=(0, 3))
        
        try:
            vk_icon_path = os.path.join(os.path.dirname(__file__), "..", "materials", "icon", "ВКонтакте.png")
            if os.path.exists(vk_icon_path) and HAS_PIL:
                vk_img = Image.open(vk_icon_path)
                vk_img = vk_img.resize((24, 24), Image.Resampling.LANCZOS)
                vk_photo = ImageTk.PhotoImage(vk_img)
                self._about_icons.append(vk_photo)
                self.icon_photos_list.append(vk_photo)
                vk_icon_label = tk.Label(vk_frame, image=vk_photo, bg=self.colors['bg_card'], cursor='hand2')
                vk_icon_label.pack(side=tk.LEFT, padx=(0, 8))
                vk_icon_label.bind("<Button-1>", open_vk_social)
        except Exception as e:
            logger.error(f"Ошибка загрузки иконки VK: {e}", exc_info=True)
        
        vk_label = tk.Label(vk_frame, 
                           text="Группа ВКонтакте",
                           font=('Robot', 10),
                           bg=self.colors['bg_card'], 
                           fg=self.colors['primary'],
                           cursor='hand2',
                           justify=tk.LEFT)
        vk_label.pack(side=tk.LEFT)
        vk_label.bind("<Button-1>", open_vk_social)
        
        def open_tg_channel(event):
            import webbrowser
            webbrowser.open("https://t.me/+n1JeH5DS-HQ2NjYy")
        
        tg_frame = tk.Frame(social_card, bg=self.colors['bg_card'])
        tg_frame.pack(anchor=tk.W, fill=tk.X)
        
        try:
            tg_icon_path = os.path.join(os.path.dirname(__file__), "..", "materials", "icon", "Telegram.png")
            if os.path.exists(tg_icon_path) and HAS_PIL:
                tg_img = Image.open(tg_icon_path)
                tg_img = tg_img.resize((24, 24), Image.Resampling.LANCZOS)
                tg_photo = ImageTk.PhotoImage(tg_img)
                self._about_icons.append(tg_photo)
                self.icon_photos_list.append(tg_photo)
                tg_icon_label = tk.Label(tg_frame, image=tg_photo, bg=self.colors['bg_card'], cursor='hand2')
                tg_icon_label.pack(side=tk.LEFT, padx=(0, 8))
                tg_icon_label.bind("<Button-1>", open_tg_channel)
        except Exception as e:
            logger.error(f"Ошибка загрузки иконки Telegram: {e}", exc_info=True)
        
        tg_label = tk.Label(tg_frame, 
                           text="Телеграм-канал",
                           font=('Robot', 10),
                           bg=self.colors['bg_card'], 
                           fg=self.colors['primary'],
                           cursor='hand2',
                           justify=tk.LEFT)
        tg_label.pack(side=tk.LEFT)
        tg_label.bind("<Button-1>", open_tg_channel)
    
    def _create_github_card(self, parent):
        """Создание карточки с GitHub"""
        github_card = ttk.LabelFrame(parent, text="Посмотреть код", 
                                     style='Card.TLabelframe', padding=20)
        github_card.pack(fill=tk.X, pady=(0, 20))
        
        def open_github(event):
            import webbrowser
            webbrowser.open("https://github.com/VseMirka200/nazovi")
        
        github_frame = tk.Frame(github_card, bg=self.colors['bg_card'])
        github_frame.pack(anchor=tk.W, fill=tk.X)
        
        try:
            github_icon_path = os.path.join(os.path.dirname(__file__), "..", "materials", "icon", "GitHUB.png")
            if os.path.exists(github_icon_path) and HAS_PIL:
                github_img = Image.open(github_icon_path)
                github_img = github_img.resize((24, 24), Image.Resampling.LANCZOS)
                github_photo = ImageTk.PhotoImage(github_img)
                self._about_icons.append(github_photo)
                self.icon_photos_list.append(github_photo)
                github_icon_label = tk.Label(github_frame, image=github_photo, bg=self.colors['bg_card'], cursor='hand2')
                github_icon_label.pack(side=tk.LEFT, padx=(0, 8))
                github_icon_label.bind("<Button-1>", open_github)
        except Exception as e:
            logger.error(f"Ошибка загрузки иконки GitHub: {e}", exc_info=True)
        
        github_label = tk.Label(github_frame, 
                               text="GitHub",
                               font=('Robot', 10),
                               bg=self.colors['bg_card'], 
                               fg=self.colors['primary'],
                               cursor='hand2',
                               justify=tk.LEFT)
        github_label.pack(side=tk.LEFT)
        github_label.bind("<Button-1>", open_github)
    
    def _create_contact_card(self, parent):
        """Создание карточки с контактами"""
        contact_card = ttk.LabelFrame(parent, text="Связаться с разработчиками", 
                                      style='Card.TLabelframe', padding=20)
        contact_card.pack(fill=tk.X, pady=(0, 20))
        
        def open_email(event):
            import webbrowser
            webbrowser.open("mailto:urban-solution@ya.ru")
        
        contact_frame = tk.Frame(contact_card, bg=self.colors['bg_card'])
        contact_frame.pack(anchor=tk.W, fill=tk.X)
        
        email_icon_label = tk.Label(contact_frame, 
                                    text="📧",
                                    font=('Robot', 10),
                                    bg=self.colors['bg_card'],
                                    fg=self.colors['primary'])
        email_icon_label.pack(side=tk.LEFT, padx=(0, 4))
        
        contact_label = tk.Label(contact_frame, 
                                text="urban-solution@ya.ru",
                                font=('Robot', 10),
                                bg=self.colors['bg_card'], 
                                fg=self.colors['primary'],
                                cursor='hand2',
                                justify=tk.LEFT)
        contact_label.pack(side=tk.LEFT)
        contact_label.bind("<Button-1>", open_email)
    
    def _create_support_card(self, parent):
        """Создание карточки с информацией о поддержке проекта"""
        support_card = ttk.LabelFrame(parent, text="Поддержать проект", 
                                     style='Card.TLabelframe', padding=20)
        support_card.pack(fill=tk.X, pady=(0, 20))
        
        # Первый параграф
        desc_text1 = "Если вам нравится эта программа и она помогает вам в работе,\nвы можете поддержать её развитие!"
        
        desc_label1 = tk.Label(support_card, 
                             text=desc_text1,
                             font=('Robot', 10),
                             bg=self.colors['bg_card'], 
                             fg=self.colors['text_primary'],
                             justify=tk.LEFT,
                             anchor=tk.W)
        desc_label1.pack(anchor=tk.W, fill=tk.X, pady=(0, 8))
        
        # Заголовок списка
        support_heading = tk.Label(support_card, 
                                  text="Ваша поддержка поможет:",
                                  font=('Robot', 10),
                                  bg=self.colors['bg_card'], 
                                  fg=self.colors['text_primary'],
                                  justify=tk.LEFT,
                                  anchor=tk.W)
        support_heading.pack(anchor=tk.W, fill=tk.X, pady=(0, 3))
        
        # Маркированный список
        support_list = """- Добавлять новые функции
- Улучшать существующие возможности
- Исправлять ошибки
- Поддерживать проект активным"""
        
        support_list_label = tk.Label(support_card, 
                                     text=support_list,
                                     font=('Robot', 10),
                                     bg=self.colors['bg_card'], 
                                     fg=self.colors['text_primary'],
                                     justify=tk.LEFT,
                                     anchor=tk.W)
        support_list_label.pack(anchor=tk.W, fill=tk.X, pady=(0, 12))
        
        # Ссылка на донат
        def open_donation(event):
            import webbrowser
            webbrowser.open("https://pay.cloudtips.ru/p/1fa22ea5")
        
        donation_label = tk.Label(support_card, 
                                 text="Поддержать проект",
                                 font=('Robot', 10),
                                 bg=self.colors['bg_card'], 
                                 fg=self.colors['primary'],
                                 cursor='hand2',
                                 justify=tk.LEFT)
        donation_label.pack(anchor=tk.W, pady=(8, 0))
        donation_label.bind("<Button-1>", open_donation)


class SupportTab:
    """Класс для создания и управления вкладкой 'Поддержка'.
    
    Объединен с AboutTab, так как оба создают информационные вкладки.
    """
    
    def __init__(self, notebook, colors):
        """Инициализация вкладки 'Поддержка'.
        
        Args:
            notebook: Notebook виджет для добавления вкладки
            colors: Словарь с цветами интерфейса
        """
        self.notebook = notebook
        self.colors = colors
    
    def create_tab(self):
        """Создание вкладки поддержки на главном экране"""
        support_tab = tk.Frame(self.notebook, bg=self.colors['bg_main'])
        support_tab.columnconfigure(0, weight=1)
        support_tab.rowconfigure(0, weight=1)
        self.notebook.add(support_tab, text="Поддержка")
        
        # Содержимое поддержки без скроллбара
        content_frame = tk.Frame(support_tab, bg=self.colors['bg_main'])
        content_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        content_frame.columnconfigure(0, weight=1)
        support_tab.rowconfigure(0, weight=1)
        support_tab.columnconfigure(0, weight=1)
        
        # Описание - карточка
        desc_card = ttk.LabelFrame(content_frame, text="Поддержать проект", 
                                   style='Card.TLabelframe', padding=20)
        desc_card.pack(fill=tk.X, pady=(10, 20))
        
        # Первый параграф
        desc_text1 = "Если вам нравится эта программа и она помогает вам в работе,\nвы можете поддержать её развитие!"
        
        desc_label1 = tk.Label(desc_card, 
                               text=desc_text1,
                               font=('Robot', 10),
                               bg=self.colors['bg_card'], 
                               fg=self.colors['text_primary'],
                               justify=tk.LEFT,
                               anchor=tk.W)
        desc_label1.pack(anchor=tk.W, fill=tk.X, pady=(0, 8))
        
        # Заголовок списка
        support_heading = tk.Label(desc_card, 
                                  text="Ваша поддержка поможет:",
                                  font=('Robot', 10),
                                  bg=self.colors['bg_card'], 
                                  fg=self.colors['text_primary'],
                                  justify=tk.LEFT,
                                  anchor=tk.W)
        support_heading.pack(anchor=tk.W, fill=tk.X, pady=(0, 3))
        
        # Маркированный список
        support_list = """- Добавлять новые функции
- Улучшать существующие возможности
- Исправлять ошибки
- Поддерживать проект активным"""
        
        support_list_label = tk.Label(desc_card, 
                                     text=support_list,
                                     font=('Robot', 10),
                                     bg=self.colors['bg_card'], 
                                     fg=self.colors['text_primary'],
                                     justify=tk.LEFT,
                                     anchor=tk.W)
        support_list_label.pack(anchor=tk.W, fill=tk.X, pady=(0, 12))
        
        # Ссылка на донат
        def open_donation(event):
            import webbrowser
            webbrowser.open("https://pay.cloudtips.ru/p/1fa22ea5")
        
        donation_label = tk.Label(desc_card, 
                                 text="Поддержать проект",
                                 font=('Robot', 10),
                                 bg=self.colors['bg_card'], 
                                 fg=self.colors['primary'],
                                 cursor='hand2',
                                 justify=tk.LEFT)
        donation_label.pack(anchor=tk.W, pady=(8, 0))
        donation_label.bind("<Button-1>", open_donation)

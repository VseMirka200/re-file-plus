"""Модуль для управления стилями интерфейса."""

from tkinter import ttk


class StyleManager:
    """Класс для управления стилями интерфейса."""
    
    def __init__(self):
        """Инициализация менеджера стилей."""
        self.style = ttk.Style()
        self.colors = self._get_color_scheme()
        self._setup_theme()
        self._setup_styles()
    
    def _get_color_scheme(self) -> dict:
        """Получение цветовой схемы."""
        return {
            'primary': '#667EEA',
            'primary_hover': '#5568D3',
            'primary_light': '#818CF8',
            'primary_dark': '#4C51BF',
            'success': '#10B981',
            'success_hover': '#059669',
            'danger': '#EF4444',
            'danger_hover': '#DC2626',
            'warning': '#F59E0B',
            'warning_hover': '#D97706',
            'info': '#3B82F6',
            'info_hover': '#2563EB',
            'secondary': '#6B7280',
            'secondary_hover': '#4B5563',
            'bg_main': '#FFFFFF',
            'bg_card': '#FFFFFF',
            'bg_secondary': '#FFFFFF',  # Изменено на bg_main для единого фона
            'bg_hover': '#F7FAFC',
            'bg_input': '#FFFFFF',
            'bg_elevated': '#FFFFFF',
            'border': '#E2E8F0',
            'border_focus': '#667EEA',
            'border_light': '#F1F5F9',
            'text_primary': '#1A202C',
            'text_secondary': '#4A5568',
            'text_muted': '#718096',
            'header_bg': '#FFFFFF',
            'header_text': '#1A202C',
            'accent': '#9F7AEA',
            'shadow': 'rgba(0,0,0,0.08)',
            'shadow_lg': 'rgba(0,0,0,0.12)',
            'shadow_xl': 'rgba(0,0,0,0.16)',
            'glow': 'rgba(102, 126, 234, 0.4)',
            'gradient_start': '#667EEA',
            'gradient_end': '#764BA2'
        }
    
    def _setup_theme(self):
        """Настройка темы."""
        try:
            self.style.theme_use('vista')
        except Exception:
            try:
                self.style.theme_use('clam')
            except Exception:
                pass
    
    def _setup_styles(self):
        """Настройка стилей виджетов."""
        # Стиль для основных кнопок
        self.style.configure('Primary.TButton', 
                           background=self.colors['primary'],
                           foreground='white',
                           font=('Robot', 10, 'bold'),
                           padding=(16, 10),
                           borderwidth=0,
                           focuscolor='none',
                           relief='flat',
                           anchor='center')
        self.style.map('Primary.TButton',
                     background=[('active', self.colors['primary_hover']), 
                               ('pressed', self.colors['primary_dark']),
                               ('disabled', '#94A3B8')],
                     foreground=[('active', 'white'), 
                              ('pressed', 'white'),
                              ('disabled', '#E2E8F0')],
                     relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Стиль для кнопок успеха
        self.style.configure('Success.TButton',
                           background=self.colors['success'],
                           foreground='white',
                           font=('Robot', 9, 'bold'),
                           padding=(10, 6),
                           borderwidth=0,
                           focuscolor='none',
                           relief='flat',
                           anchor='center')
        self.style.map('Success.TButton',
                     background=[('active', self.colors['success_hover']), 
                               ('pressed', '#047857'),
                               ('disabled', '#94A3B8')],
                     foreground=[('active', 'white'), 
                              ('pressed', 'white'),
                              ('disabled', '#E2E8F0')],
                     relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Стиль для кнопок опасности
        self.style.configure('Danger.TButton',
                           background=self.colors['danger'],
                           foreground='white',
                           font=('Robot', 9, 'bold'),
                           padding=(10, 6),
                           borderwidth=0,
                           focuscolor='none',
                           relief='flat',
                           anchor='center')
        self.style.map('Danger.TButton',
                     background=[('active', self.colors['danger_hover']), 
                               ('pressed', '#B91C1C'),
                               ('disabled', '#94A3B8')],
                     foreground=[('active', 'white'), 
                              ('pressed', 'white'),
                              ('disabled', '#E2E8F0')],
                     relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Стиль для обычных кнопок
        self.style.configure('TButton',
                           font=('Robot', 9, 'bold'),
                           padding=(10, 6),
                           borderwidth=0,
                           relief='flat',
                           background='#F59E0B',
                           foreground='white',
                           anchor='center')
        self.style.map('TButton',
                     background=[('active', '#D97706'), 
                               ('pressed', '#B45309'),
                               ('disabled', '#94A3B8')],
                     foreground=[('active', 'white'),
                              ('pressed', 'white'),
                              ('disabled', '#E2E8F0')],
                     relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Стиль для вторичных кнопок
        self.style.configure('Secondary.TButton',
                           font=('Robot', 9, 'bold'),
                           padding=(10, 6),
                           borderwidth=0,
                           relief='flat',
                           background='#818CF8',
                           foreground='white',
                           anchor='center')
        self.style.map('Secondary.TButton',
                     background=[('active', '#6366F1'), 
                               ('pressed', '#4F46E5'),
                               ('disabled', '#94A3B8')],
                     foreground=[('active', 'white'),
                              ('pressed', 'white'),
                              ('disabled', '#E2E8F0')],
                     relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Стиль для предупреждающих кнопок
        self.style.configure('Warning.TButton',
                           font=('Robot', 9, 'bold'),
                           padding=(10, 6),
                           borderwidth=0,
                           relief='flat',
                           background='#F59E0B',
                           foreground='white',
                           anchor='center')
        self.style.map('Warning.TButton',
                     background=[('active', '#D97706'), 
                               ('pressed', '#B45309'),
                               ('disabled', '#94A3B8')],
                     foreground=[('active', 'white'),
                              ('pressed', 'white'),
                              ('disabled', '#E2E8F0')],
                     relief=[('pressed', 'sunken'), ('!pressed', 'flat')])
        
        # Стиль для LabelFrame
        self.style.configure('Card.TLabelframe', 
                           background=self.colors['bg_main'],
                           borderwidth=0,
                           relief='flat',
                           bordercolor=self.colors['border'],
                           padding=24)
        self.style.configure('Card.TLabelframe.Label',
                           background=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           font=('Robot', 11, 'bold'),
                           padding=(0, 0, 0, 12))
        
        # Стиль для PanedWindow
        self.style.configure('TPanedwindow',
                           background=self.colors['bg_main'])
        self.style.configure('TPanedwindow.Sash',
                           sashthickness=6,
                           sashrelief='flat',
                           sashpad=0)
        self.style.map('TPanedwindow.Sash',
                     background=[('hover', self.colors['primary_light']),
                               ('active', self.colors['primary'])])
        
        # Стиль для меток
        self.style.configure('TLabel',
                           background=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           font=('Robot', 9))
        
        # Стиль для Frame
        self.style.configure('TFrame',
                           background=self.colors['bg_main'])
        
        # Стиль для Notebook
        self.style.configure('TNotebook',
                           background=self.colors['bg_main'],
                           borderwidth=0)
        self.style.configure('TNotebook.Tab',
                           padding=(20, 8),  # Уменьшено с 12 до 8 (на 1/3)
                           font=('Robot', 10, 'bold'),
                           background=self.colors['bg_main'],
                           foreground='#000000')  # Черный цвет шрифта
        self.style.map('TNotebook.Tab',
                     background=[('selected', self.colors['bg_main']),  # Убрана подсветка выбранной вкладки
                               ('active', self.colors['bg_hover'])],
                     foreground=[('selected', '#000000'),  # Черный цвет для выбранной вкладки
                               ('active', '#000000')],  # Черный цвет для активной вкладки
                     expand=[('selected', [1, 1, 1, 0])])
        
        # Стиль для Radiobutton
        self.style.configure('TRadiobutton',
                           background=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           font=('Robot', 11),
                           selectcolor='white')
        
        # Стиль для Checkbutton
        self.style.configure('TCheckbutton',
                           background=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           font=('Robot', 11),
                           selectcolor='white')
        
        # Стиль для Entry
        self.style.configure('TEntry',
                           fieldbackground=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           borderwidth=2,
                           relief='flat',
                           padding=10,
                           font=('Robot', 10))
        self.style.map('TEntry',
                     bordercolor=[('focus', self.colors['border_focus']),
                                ('!focus', self.colors['border'])],
                     lightcolor=[('focus', self.colors['border_focus']),
                               ('!focus', self.colors['border'])],
                     darkcolor=[('focus', self.colors['border_focus']),
                              ('!focus', self.colors['border'])])
        
        # Стиль для Combobox
        self.style.configure('TCombobox',
                           fieldbackground=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           borderwidth=2,
                           relief='flat',
                           padding=10,
                           font=('Robot', 11))
        self.style.map('TCombobox',
                     bordercolor=[('focus', self.colors['border_focus']),
                                ('!focus', self.colors['border'])],
                     selectbackground=[('focus', self.colors['bg_main'])],
                     selectforeground=[('focus', self.colors['text_primary'])])
        
        # Стиль для Treeview
        self.style.configure('Custom.Treeview',
                           rowheight=30,
                           font=('Robot', 10),
                           background=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           fieldbackground=self.colors['bg_main'],
                           borderwidth=0)
        self.style.configure('Custom.Treeview.Heading',
                           font=('Robot', 10, 'bold'),
                           background=self.colors['bg_main'],
                           foreground=self.colors['text_primary'],
                           borderwidth=0,
                           relief='flat',
                           padding=(12, 10))
        self.style.map('Custom.Treeview.Heading',
                     background=[('active', self.colors['bg_hover'])])
        self.style.map('Custom.Treeview',
                     background=[('selected', self.colors['primary'])],
                     foreground=[('selected', 'white')])


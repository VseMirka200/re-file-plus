"""Обработчики горячих клавиш приложения."""

import logging

logger = logging.getLogger(__name__)


class HotkeysHandler:
    """Класс для управления горячими клавишами приложения."""
    
    def __init__(self, root, app) -> None:
        self.root = root
        self.app = app
        self.setup_hotkeys()
    
    def setup_hotkeys(self) -> None:
        """Настройка горячих клавиш."""
        self.root.bind('<Control-Shift-A>', lambda e: self.app.add_files())
        self.root.bind('<Control-z>', lambda e: self.app.undo_re_file())
        self.root.bind('<Control-y>', lambda e: self.app.redo_re_file())
        self.root.bind('<Control-Shift-Z>', lambda e: self.app.redo_re_file())
        self.root.bind('<Delete>', lambda e: self.app.delete_selected())
        self.root.bind('<Control-o>', lambda e: self.app.add_folder())
        self.root.bind('<Control-s>', lambda e: self.app.save_template_quick())
        self.root.bind('<Control-f>', lambda e: self.app.focus_search())
        self.root.bind('<F5>', lambda e: self.app.refresh_treeview())
        self.root.bind('<Control-r>', lambda e: self.app.apply_methods())


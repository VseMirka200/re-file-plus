"""Модуль для создания переиспользуемых карточек (cards).

Содержит фабрики для создания карточек в едином стиле.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Tuple, Callable


def create_card(
    parent: tk.Widget,
    title: str,
    style: str = 'Card.TLabelframe',
    padding: int = 20,
    padx: int = 20,
    pady: Tuple[int, int] = (10, 10),
    fill: str = tk.X,
    expand: bool = False
) -> ttk.LabelFrame:
    """Создание карточки в едином стиле.
    
    Args:
        parent: Родительский виджет
        title: Заголовок карточки
        style: Стиль карточки (по умолчанию 'Card.TLabelframe')
        padding: Внутренний отступ карточки
        padx: Горизонтальный отступ от родителя
        pady: Вертикальный отступ от родителя (кортеж из двух значений)
        fill: Направление заполнения (tk.X, tk.Y, tk.BOTH)
        expand: Растягивать ли карточку
    
    Returns:
        ttk.LabelFrame: Созданная карточка
    """
    card = ttk.LabelFrame(
        parent,
        text=title,
        style=style,
        padding=padding
    )
    
    pack_kwargs = {'fill': fill, 'padx': padx, 'pady': pady}
    if expand:
        pack_kwargs['expand'] = True
    
    card.pack(**pack_kwargs)
    
    return card


def create_card_with_content(
    parent: tk.Widget,
    title: str,
    content_creator: Callable[[ttk.LabelFrame], None],
    style: str = 'Card.TLabelframe',
    padding: int = 20,
    padx: int = 20,
    pady: Tuple[int, int] = (10, 10),
    fill: str = tk.X,
    expand: bool = False
) -> ttk.LabelFrame:
    """Создание карточки с содержимым.
    
    Args:
        parent: Родительский виджет
        title: Заголовок карточки
        content_creator: Функция для создания содержимого карточки
                        Принимает card как аргумент
        style: Стиль карточки
        padding: Внутренний отступ карточки
        padx: Горизонтальный отступ от родителя
        pady: Вертикальный отступ от родителя
        fill: Направление заполнения
        expand: Растягивать ли карточку
    
    Returns:
        ttk.LabelFrame: Созданная карточка
    """
    card = create_card(
        parent,
        title,
        style,
        padding,
        padx,
        pady,
        fill,
        expand
    )
    
    if content_creator:
        content_creator(card)
    
    return card


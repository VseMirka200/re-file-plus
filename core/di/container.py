"""Контейнер для Dependency Injection."""

import logging
from typing import Any, Dict, Optional, Type, TypeVar, Callable

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DIContainer:
    """Простой контейнер для Dependency Injection."""
    
    def __init__(self):
        """Инициализация контейнера."""
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
    
    def register(
        self,
        service_type: Type[T],
        instance: Optional[T] = None,
        factory: Optional[Callable[[], T]] = None,
        singleton: bool = True
    ) -> None:
        """Регистрация сервиса.
        
        Args:
            service_type: Тип сервиса (класс)
            instance: Готовый экземпляр (опционально)
            factory: Фабрика для создания экземпляра (опционально)
            singleton: Создавать ли один экземпляр на все запросы
        """
        service_name = service_type.__name__
        
        if instance is not None:
            self._services[service_name] = instance
            if singleton:
                self._singletons[service_name] = instance
        elif factory is not None:
            self._factories[service_name] = factory
        else:
            # Регистрируем класс для создания экземпляров
            self._factories[service_name] = lambda: service_type()
    
    def get(self, service_type: Type[T]) -> T:
        """Получение экземпляра сервиса.
        
        Args:
            service_type: Тип сервиса
            
        Returns:
            Экземпляр сервиса
            
        Raises:
            ValueError: Если сервис не зарегистрирован
        """
        service_name = service_type.__name__
        
        # Проверяем синглтоны
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        # Проверяем готовые экземпляры
        if service_name in self._services:
            instance = self._services[service_name]
            if service_name in self._singletons:
                self._singletons[service_name] = instance
            return instance
        
        # Создаем через фабрику
        if service_name in self._factories:
            instance = self._factories[service_name]()
            if service_name in self._singletons:
                self._singletons[service_name] = instance
            return instance
        
        raise ValueError(f"Сервис {service_name} не зарегистрирован")
    
    def has(self, service_type: Type[T]) -> bool:
        """Проверка наличия сервиса.
        
        Args:
            service_type: Тип сервиса
            
        Returns:
            True если сервис зарегистрирован
        """
        service_name = service_type.__name__
        return (service_name in self._services or
                service_name in self._factories or
                service_name in self._singletons)
    
    def clear(self) -> None:
        """Очистка контейнера."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()


# Глобальный контейнер по умолчанию
_default_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """Получение глобального контейнера.
    
    Returns:
        Глобальный контейнер
    """
    global _default_container
    if _default_container is None:
        _default_container = DIContainer()
    return _default_container


def set_container(container: DIContainer) -> None:
    """Установка глобального контейнера.
    
    Args:
        container: Контейнер для установки
    """
    global _default_container
    _default_container = container


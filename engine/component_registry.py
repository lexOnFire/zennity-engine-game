from __future__ import annotations

from typing import Any, Optional, Type

from engine.core.component import Component
from engine.core.component_registry import component_registry


class ComponentRegistry:
    """Compatibility facade for scripts that use engine.component_registry."""

    @classmethod
    def register(cls, component_class: Type[Component], alias: Optional[str] = None) -> Type[Component]:
        component_registry.register(component_class)
        if alias:
            component_registry.register(component_class, alias)
        return component_class

    @classmethod
    def component(cls, _cls: Optional[Type[Component]] = None, *, alias: Optional[str] = None):
        def _decorator(klass: Type[Component]) -> Type[Component]:
            return cls.register(klass, alias=alias)
        if _cls is not None:
            return _decorator(_cls)
        return _decorator

    @classmethod
    def resolve(cls, name: str) -> Type[Component]:
        component_class = component_registry.resolve(name)
        if component_class is None:
            raise KeyError(f"Componente '{name}' não registrado.")
        return component_class

    @classmethod
    def get(cls, name: str, default=None):
        return component_registry.resolve(name) or default

    @classmethod
    def create(cls, name: str, **kwargs: Any) -> Component:
        return cls.resolve(name)(**kwargs)

    @classmethod
    def all_names(cls) -> list[str]:
        return list(component_registry.registered_types())

    @classmethod
    def all_classes(cls) -> list[type[Component]]:
        return list(component_registry.available_components())

    @classmethod
    def clear(cls) -> None:
        component_registry._types.clear()

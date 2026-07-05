from __future__ import annotations

from typing import Type

from engine.core.component import Component


class ComponentRegistry:
    """Registro central para tipos de Component serializaveis."""

    def __init__(self) -> None:
        self._types: dict[str, Type[Component]] = {}

    def register(self, component_type: Type[Component], name: str | None = None) -> Type[Component]:
        key = name or getattr(component_type, "component_type", component_type.__name__)
        self._types[str(key)] = component_type
        self._types[component_type.__name__] = component_type
        return component_type

    def resolve(self, name: str) -> Type[Component] | None:
        return self._types.get(str(name))

    def create(self, data: dict) -> Component:
        component_type = self.resolve(str(data.get("type", "")))
        if component_type is None:
            component_type = Component
        if hasattr(component_type, "deserialize"):
            return component_type.deserialize(data)
        return component_type()

    def registered_types(self) -> tuple[str, ...]:
        return tuple(sorted(self._types))

    def available_components(self) -> tuple[type[Component], ...]:
        seen: set[type[Component]] = set()
        components: list[type[Component]] = []
        for component_type in self._types.values():
            if component_type in seen:
                continue
            seen.add(component_type)
            components.append(component_type)
        return tuple(
            sorted(
                components,
                key=lambda item: str(getattr(item, "component_type", item.__name__)),
            )
        )


component_registry = ComponentRegistry()


def register_component(component_type: Type[Component], name: str | None = None) -> Type[Component]:
    return component_registry.register(component_type, name)


from engine.core.component import Transform
from engine.graphics.camera import Camera
from engine.audio import AudioSource, AudioListener
from engine.animation.animator import Animator
from engine.ui.runtime_components import Canvas, LabelComponent, ImageComponent, ButtonComponent

component_registry.register(Component)
component_registry.register(Transform)
component_registry.register(Camera)
component_registry.register(AudioSource)
component_registry.register(AudioListener)
component_registry.register(Animator)
component_registry.register(Canvas)
component_registry.register(LabelComponent)
component_registry.register(ImageComponent)
component_registry.register(ButtonComponent)

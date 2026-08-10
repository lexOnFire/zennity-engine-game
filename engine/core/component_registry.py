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
            try:
                return component_type.deserialize(data)
            except TypeError:
                component = component_type()
                component.deserialize(data)
                return component
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
from engine.graphics.material_property_animator import MaterialPropertyAnimator
from engine.audio import AudioSource, AudioListener
from engine.animation.animator import Animator
from engine.animation.animation_controller import AnimationController
from engine.ui.runtime_components import (
    Canvas, LabelComponent, ImageComponent, InfiniteBackground, ButtonComponent,
    ProgressBarComponent,
)
from engine.ui.ui_binder import UIBinder
from engine.ui.dialogue_manager import DialogueManager
from engine.tilemap import Tilemap, TilemapRenderer
from engine.components.script_component import ScriptComponent
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider, CircleCollider


component_registry.register(Component)
component_registry.register(Transform)
component_registry.register(Camera)
component_registry.register(MaterialPropertyAnimator)
component_registry.register(AudioSource)
component_registry.register(AudioListener)
component_registry.register(Animator)
component_registry.register(AnimationController)
component_registry.register(Canvas)
# BUG FIX: real project scenes (RPG_Showcase.zscene, TestGame_Showcase.zscene)
# serialize the HUD root component as type "UICanvas", but only "Canvas" was
# ever registered — "UICanvas" resolved to nothing and silently degraded to a
# bare Component on load. Register the same class under both names.
component_registry.register(Canvas, "UICanvas")
component_registry.register(LabelComponent)
component_registry.register(ImageComponent)
component_registry.register(InfiniteBackground)
component_registry.register(InfiniteBackground, "Infinite Background")
component_registry.register(ButtonComponent)
# BUG FIX: NebulaDefensePro.zscene saves "ProgressBar" components, which had
# no matching class anywhere in engine.ui.runtime_components and was never
# registered — see ProgressBarComponent in runtime_components.py.
component_registry.register(ProgressBarComponent)
component_registry.register(UIBinder)
component_registry.register(DialogueManager)
component_registry.register(Tilemap)
component_registry.register(TilemapRenderer)
component_registry.register(ScriptComponent, "Script")
component_registry.register(RigidBody)
component_registry.register(BoxCollider)
component_registry.register(CircleCollider)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from engine.core.component import Component, Transform
from engine.core.component_registry import ComponentRegistry, component_registry


@dataclass
class AddComponentCommand:
    """Adiciona um Component em um GameObject usando o ComponentRegistry."""

    game_object: Any
    component_type: str
    registry: ComponentRegistry = component_registry
    component: Component | None = None

    @property
    def description(self) -> str:
        return f"Add Component {self.component_type}"

    def execute(self) -> None:
        component_class = self.registry.resolve(self.component_type)
        if component_class is None:
            raise ValueError(f"Unknown component type: {self.component_type}")
        if component_class is Transform or getattr(component_class, "required", False):
            raise ValueError(f"Component cannot be added manually: {self.component_type}")
        existing = self.game_object.get_component(component_class)
        if getattr(component_class, "unique", False) and existing is not None and existing is not self.component:
            raise ValueError(f"Component already exists: {self.component_type}")
        if self.component is None:
            self.component = self.registry.create({"type": self.component_type})
        self.game_object.add_component(self.component)

    def undo(self) -> None:
        if self.component is not None and self.component in self.game_object.components:
            self.game_object.remove_component(self.component)


@dataclass
class RemoveComponentCommand:
    """Remove um Component opcional e restaura a mesma instancia no undo."""

    game_object: Any
    component: Component
    index: int | None = None

    @property
    def description(self) -> str:
        return f"Remove Component {getattr(self.component, 'type_name', type(self.component).__name__)}"

    def execute(self) -> None:
        if self.component is getattr(self.game_object, "transform", None) or getattr(self.component, "required", False):
            raise ValueError("Required components cannot be removed")
        if self.component in self.game_object.components:
            self.index = self.game_object.components.index(self.component)
            self.game_object.remove_component(self.component)

    def undo(self) -> None:
        if self.component not in self.game_object.components:
            self.game_object.insert_component(self.component, self.index)

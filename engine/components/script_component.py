from __future__ import annotations

from typing import Any

from engine.core.component import Component


class ScriptComponent(Component):
    """Referencia leve para script de comportamento anexado ao GameObject."""

    component_type = "Script"

    def __init__(self, script_path: str = "") -> None:
        super().__init__()
        self.script_path = script_path

    def serialize_properties(self) -> dict[str, Any]:
        return {"script_path": self.script_path}

    def deserialize_properties(self, data: dict[str, Any]) -> None:
        self.script_path = str(data.get("script_path", ""))


from engine.core.component_registry import register_component

register_component(ScriptComponent)
register_component(ScriptComponent, "ScriptComponent")

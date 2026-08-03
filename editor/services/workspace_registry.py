"""Central registry for opening Phase 1 editor workspaces."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget


@dataclass(frozen=True)
class WorkspaceDefinition:
    workspace_id: str
    module_path: str
    class_name: str
    attr_name: str
    graph_tool_id: str = ""


class WorkspaceRegistry:
    """Creates and reuses editor workspace windows from a single registry."""

    def __init__(self, host: Any, definitions: list[WorkspaceDefinition] | None = None) -> None:
        self.host = host
        self.definitions = {item.workspace_id: item for item in definitions or default_workspace_definitions()}

    def open(self, workspace_id: str) -> Any:
        if workspace_id == "animation":
            return self._open_animation()
        definition = self.definitions[workspace_id]
        widget = self.open_dynamic(
            definition.module_path,
            definition.class_name,
            definition.attr_name,
        )
        if definition.graph_tool_id and hasattr(widget, "open_graph_tool"):
            widget.open_graph_tool(definition.graph_tool_id)
        return widget

    def open_dynamic(self, module_path: str, class_name: str, attr_name: str) -> Any:
        dock_attr = f"_dock_{attr_name}"
        dock_widget = getattr(self.host, dock_attr, None)
        if dock_widget is None:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            dock_widget = cls(self.host)
            setattr(self.host, dock_attr, dock_widget)
            if isinstance(dock_widget, QDockWidget):
                self.host.addDockWidget(Qt.RightDockWidgetArea, dock_widget)
            if hasattr(dock_widget, "configure_independent_window"):
                dock_widget.configure_independent_window()
        self._show_widget(dock_widget)
        return dock_widget

    def _open_animation(self) -> Any:
        handler = getattr(self.host, "_show_animation_window", None)
        if callable(handler):
            handler()
            return getattr(self.host, "animation_window", None)
        animation_window = getattr(self.host, "animation_window", None)
        if animation_window is not None:
            self._show_widget(animation_window)
            return animation_window
        definition = self.definitions["animation_studio"]
        return self.open_dynamic(definition.module_path, definition.class_name, definition.attr_name)

    @staticmethod
    def _show_widget(widget: Any) -> None:
        widget.show()
        widget.raise_()
        widget.activateWindow()


def default_workspace_definitions() -> list[WorkspaceDefinition]:
    return [
        WorkspaceDefinition(
            "logic",
            "editor.visual_scripting.visual_scripting_dock",
            "VisualScriptingEditorDock",
            "visual_scripting",
            "logic_graph",
        ),
        WorkspaceDefinition(
            "behavior_tree",
            "editor.visual_scripting.visual_scripting_dock",
            "VisualScriptingEditorDock",
            "visual_scripting",
            "behavior_tree",
        ),
        WorkspaceDefinition(
            "dialogue",
            "editor.visual_scripting.visual_scripting_dock",
            "VisualScriptingEditorDock",
            "visual_scripting",
            "dialogue",
        ),
        WorkspaceDefinition(
            "material_graph",
            "editor.visual_scripting.visual_scripting_dock",
            "VisualScriptingEditorDock",
            "visual_scripting",
            "material_graph",
        ),
        WorkspaceDefinition(
            "ui_builder",
            "editor.ui_builder.ui_builder_dock",
            "UIBuilderDock",
            "ui_builder",
        ),
        WorkspaceDefinition(
            "animation_studio",
            "editor.animation_studio.animation_studio_dock",
            "AnimationStudioDock",
            "animation_studio",
        ),
    ]

"""Tool selection, viewport utility shortcuts and ToolManager synchronization."""
from __future__ import annotations

from typing import Any

from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QApplication, QWidget

from editor.runtime.tool_manager import EditorTool
from editor.services.shortcut_service import ShortcutService


class ToolController:
    """Owns Phase 1 editor tool state and its keyboard shortcuts."""

    TOOL_SHORTCUTS = {
        EditorTool.SELECT: "Q",
        EditorTool.MOVE: "W",
        EditorTool.ROTATE: "E",
        EditorTool.SCALE: "R",
    }
    SCENE_EDIT_COMMANDS = (
        "edit.duplicate",
        "edit.undo",
        "edit.redo",
        "edit.delete",
    )

    def __init__(self, host: Any) -> None:
        self.host = host
        self.shortcut_service = ShortcutService(host)
        self._application: QApplication | None = None

    def configure(self) -> None:
        h = self.host
        group = QActionGroup(h)
        group.setExclusive(True)
        h._tool_actions = {}
        h._tool_shortcuts = []
        action_bound_commands: set[str] = set()

        for action in h.findChildren(QAction):
            label = action.toolTip() if action.toolTip() else action.text()
            tool = self._tool_from_label(label)
            if tool is None:
                continue
            action.setCheckable(True)
            self.shortcut_service.bind_action(action, self.TOOL_SHORTCUTS[tool])
            action.setChecked(tool == h.editor_context.tools.active_tool)
            group.addAction(action)
            h._tool_actions[tool.value] = action
            action_bound_commands.add(f"tool.{tool.value}")
            action.triggered.connect(
                lambda checked=False, next_tool=tool: checked
                and self.activate_tool(next_tool)
            )

        h.editor_context.tools.subscribe(self._sync_tool_action)
        fallback_bindings = (
            binding
            for binding in ShortcutService.STANDARD_BINDINGS
            if binding.command_id not in action_bound_commands
        )
        self.shortcut_service.register(
            fallback_bindings,
            {
                "tool.select": lambda: self.activate_tool(EditorTool.SELECT),
                "tool.move": lambda: self.activate_tool(EditorTool.MOVE),
                "tool.rotate": lambda: self.activate_tool(EditorTool.ROTATE),
                "tool.scale": lambda: self.activate_tool(EditorTool.SCALE),
                "edit.duplicate": lambda: h._selected_name is not None
                and h._scene_objects.duplicate_selected(),
                "edit.undo": h._undo,
                "edit.redo": h._redo,
                "edit.delete": lambda: h._selected_name is not None
                and h._scene_objects.delete(h._selected_name),
                "viewport.focus_selected": self.focus_selected,
                "viewport.toggle_grid": self.toggle_grid,
            },
        )
        h._tool_shortcuts.extend(self.shortcut_service.shortcuts)
        h._tool_action_group = group
        application = QApplication.instance()
        if application is not None:
            self._application = application
            application.focusChanged.connect(self._sync_edit_shortcut_scope)
            self._sync_edit_shortcut_scope(None, application.focusWidget())
        self._sync_tool_action(h.editor_context.tools.active_tool)

    def activate_tool(self, tool: EditorTool | str) -> None:
        h = self.host
        next_tool = tool if isinstance(tool, EditorTool) else EditorTool(str(tool))
        h.editor_context.tools.set_active_tool(next_tool)
        h._viewport_commands.set_tool(next_tool)
        selected = getattr(h, "_selected_name", None)
        if selected in getattr(h, "_objects_by_name", {}):
            h._scene_controller.select(selected)

    def focus_selected(self) -> None:
        self.host._viewport_commands.focus_selected()

    def toggle_grid(self) -> None:
        self.host._viewport_commands.toggle_grid()

    def disconnect(self) -> None:
        if self._application is None:
            return
        try:
            self._application.focusChanged.disconnect(self._sync_edit_shortcut_scope)
        except (RuntimeError, TypeError):
            pass
        self._application = None

    def _sync_edit_shortcut_scope(
        self, _previous: QWidget | None, current: QWidget | None
    ) -> None:
        enabled = self._scene_shortcuts_allowed(current)
        for command_id in self.SCENE_EDIT_COMMANDS:
            shortcut = self.shortcut_service.shortcut_for(command_id)
            if shortcut is not None:
                shortcut.setEnabled(enabled)

    def _scene_shortcuts_allowed(self, widget: QWidget | None) -> bool:
        if widget is None:
            return True
        window = widget.window()
        if window is not self.host:
            return False
        current: QWidget | None = widget
        while current is not None:
            marker = f"{type(current).__name__} {current.objectName()}".lower()
            if "graph" in marker or "nodecanvas" in marker:
                return False
            current = current.parentWidget()
        return True

    def _sync_tool_action(self, tool: EditorTool) -> None:
        action = self.host._tool_actions.get(tool.value)
        if action is not None and not action.isChecked():
            action.setChecked(True)

    @staticmethod
    def _tool_from_label(label: str) -> EditorTool | None:
        normalized = str(label).strip().lower()
        try:
            tool = EditorTool(normalized)
        except ValueError:
            return None
        return tool if tool in ToolController.TOOL_SHORTCUTS else None

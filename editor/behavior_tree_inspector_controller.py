"""BehaviorTreeInspectorController — owns the Behavior Tree Inspector card.

Responsibilities:
  - pick()         → open a file dialog filtered to .zbehavior, link to the object
  - open_editor()  → switch the Visual Scripting dock to the Behavior Tree tab
                      and load the linked file
  - unlink()       → remove 'behavior' dict from the selected object
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QInputDialog

from editor.widgets.logic_asset_picker import LogicAssetPickerDialog


class BehaviorTreeInspectorController:
    """Owns Behavior Tree card interactions for the isolated editor."""

    BEHAVIOR_FILTER = "Behavior Tree (*.zbehavior);;Todos os arquivos (*.*)"

    def __init__(self, host: Any, project_root: Path | None = None) -> None:
        self.host = host
        self.project_root = (project_root or Path.cwd()).resolve()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _selected(self) -> tuple[str, dict[str, Any]] | None:
        return self.host._selection.selected_scene_object()

    def _behaviors_root(self) -> Path:
        """Return (creating if needed) Assets/Behaviors/ relative to project root."""
        root = self.project_root / "Assets" / "Behaviors"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _clean_path(self, path: Path) -> str:
        """Return a project-relative posix path, or absolute as fallback."""
        try:
            return path.resolve().relative_to(self.project_root).as_posix()
        except ValueError:
            return path.as_posix()

    # ── public API ───────────────────────────────────────────────────────────

    def pick(self) -> None:
        """Open the project asset browser and link the chosen Behavior Tree."""
        selected = self._selected()
        if selected is None:
            return
        name, obj = selected
        picker = LogicAssetPickerDialog(self.project_root, "behavior", self.host)
        if not picker.exec() or not picker.selected_path:
            return
        path = self.project_root / picker.selected_path
        if not path.is_file():
            self.host._log("WARNING", f"Behavior Tree não encontrada: {picker.selected_path}")
            return
        self._link(name, obj, path)

    def create_new(self) -> None:
        """Create a blank Behavior Tree asset and link it to the selected object."""
        selected = self._selected()
        if selected is None:
            return
        name, obj = selected
        suggested = f"{name}Behavior"
        asset_name, accepted = QInputDialog.getText(
            self.host, "Criar Behavior Tree", "Nome do asset:", text=suggested
        )
        if not accepted:
            return
        safe_name = re.sub(r"[^A-Za-z0-9_-]+", "_", asset_name.strip()).strip("_")
        if not safe_name:
            return
        path = self._behaviors_root() / f"{safe_name}.zbehavior"
        suffix = 2
        while path.exists():
            path = self._behaviors_root() / f"{safe_name}_{suffix}.zbehavior"
            suffix += 1
        payload = {
            "format": "zennity.generic_graph",
            "version": 1,
            "category": "Behavior Tree",
            "nodes": [],
            "edges": [],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self._link(name, obj, path)

    def _link(self, name: str, obj: dict[str, Any], path: Path) -> None:
        """Link a .zbehavior file to an object and refresh the inspector."""
        h = self.host
        h._record_history()
        clean_path = self._clean_path(path)
        obj["behavior"] = {
            "controller_path": clean_path,
            "auto_start": False,
        }
        self._set_workspace_path(clean_path)
        h._selection.publish_scene()
        h._selection.refresh_inspector(name)
        # Also open the file in the Behavior Tree editor tab right away.
        self._open_in_editor(path)
        h._log("INFO", f"Behavior Tree vinculada em '{name}': {clean_path}")

    def _set_workspace_path(self, path: str | None) -> None:
        h = self.host
        document = h._scene_document
        if not isinstance(document, dict):
            document = {
                "format_version": 2,
                "scene_name": Path(h._current_scene_path).stem if h._current_scene_path else "Untitled",
                "engine_version": "Zennity 1.0.1",
                "blackboard": {"variables": {}},
                "objects": [],
            }
            h._scene_document = document
        workspace = document.setdefault("visual_logic_workspace", {})
        if not isinstance(workspace, dict):
            workspace = {}
            document["visual_logic_workspace"] = workspace
        if path:
            workspace["behavior_tree"] = str(path)
        else:
            workspace.pop("behavior_tree", None)
        dock = getattr(h, "_dock_visual_scripting", None)
        if dock is not None:
            dock._scene_workspace_signature = ()
            if hasattr(dock, "sync_from_host"):
                dock.sync_from_host()

    def open_editor(self) -> None:
        """Switch the Visual Scripting dock to the Behavior Tree tab."""
        selected = self._selected()
        if selected is None:
            return
        _, obj = selected
        behavior = obj.get("behavior") if isinstance(obj.get("behavior"), dict) else None
        controller_path = str((behavior or {}).get("controller_path", ""))
        if not controller_path:
            return
        path = Path(controller_path)
        path = path if path.is_absolute() else self.project_root / path
        self._open_in_editor(path)

    def _open_in_editor(self, path: Path) -> None:
        """Load the file in the Behavior Tree editor tab via the orchestrator."""
        h = self.host
        dock_vs = getattr(h, "_dock_visual_scripting", None)
        if dock_vs is None:
            logic_controller = getattr(h, "_logic_workspace_controller", None)
            if logic_controller is not None:
                logic_controller.show()
            dock_vs = getattr(h, "_dock_visual_scripting", None)
        if dock_vs is not None:
            bt_editor = getattr(dock_vs, "behavior_tree_editor", None)
            callback = (
                getattr(bt_editor, "open_asset", None)
                or getattr(bt_editor, "load_document", None)
            )
            if callback is not None and path.is_file() and callback(path):
                dock_vs.open_graph_tool("behavior_tree")
                dock_vs.show()
                dock_vs.raise_()
                return
        orchestrator = getattr(h, "bridge_orchestrator", None)
        if orchestrator is not None:
            try:
                orchestrator.open_behavior_tree(path=str(path))
                orchestrator.activate_behavior_tree()
                return
            except Exception:
                pass
        h._log("WARNING", f"Não foi possível abrir o Behavior Tree Editor: {path}")

    def unlink(self) -> None:
        """Remove the behavior dict from the selected object."""
        selected = self._selected()
        if selected is None:
            return
        name, obj = selected
        if "behavior" not in obj:
            return
        h = self.host
        h._record_history()
        obj.pop("behavior", None)
        replacement = next(
            (
                str(value["behavior"].get("controller_path", ""))
                for other_name, value in h._objects_by_name.items()
                if other_name != name and isinstance(value.get("behavior"), dict)
                and value["behavior"].get("controller_path")
            ),
            "",
        )
        self._set_workspace_path(replacement or None)
        h._selection.publish_scene()
        h._selection.refresh_inspector(name)
        h._log("INFO", f"Behavior Tree desvinculada de '{name}'")

    # ── static helpers for asset discovery ───────────────────────────────────

    @staticmethod
    def available_behavior_trees(project_root: Path | None = None) -> list[str]:
        """Return all .zbehavior files under the project, sorted."""
        root = (project_root or Path.cwd()).resolve()
        result: list[str] = []
        for path in root.rglob("*.zbehavior"):
            try:
                result.append(path.resolve().relative_to(root).as_posix())
            except ValueError:
                result.append(str(path).replace("\\", "/"))
        return sorted(result, key=str.lower)

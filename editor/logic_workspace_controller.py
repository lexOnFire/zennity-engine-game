"""Visual-logic asset, binding and editor-window orchestration."""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QMessageBox

from editor.controllers.logic_binding_controller import LogicBindingController
from editor.widgets.logic_graph_picker import LogicGraphPickerDialog
from engine.logic.graph_asset import load_logic_graph, validate_logic_graph


class LogicWorkspaceController:
    """Owns the visual-logic workspace and scene-object bindings."""

    def __init__(self, host: Any, project_root: Path | None = None) -> None:
        self.host = host
        self.project_root = (project_root or Path.cwd()).resolve()
        self.bindings = LogicBindingController(host, self.project_root)
        self._connected = False

    def connect(self) -> bool:
        if self._connected:
            return False
        h = self.host
        h.logic_workspace.message.connect(h._log)
        h.logic_workspace.asset_changed.connect(h._asset_browser.refresh)
        h.logic_workspace.debug_command.connect(self.send_debug_command)
        h.logic_workspace.play_requested.connect(
            lambda: h._editor_commands.dispatch({"type": "play"})
        )
        h.logic_workspace.stop_requested.connect(
            lambda: h._editor_commands.dispatch({"type": "stop"})
        )
        self._connected = True
        return True

    def send_debug_command(self, command: str) -> None:
        h = self.host
        path = h.logic_workspace.current_path
        if path is None:
            h._log("WARNING", "Abra ou salve um Logic Graph antes de depurar")
            return
        graph = h.logic_workspace.graph_data()
        try:
            graph_path = path.resolve().relative_to(self.project_root).as_posix()
        except (OSError, ValueError):
            graph_path = str(path)
        h._commands.put({
            "type": "logic_debug_command",
            "command": str(command),
            "graph": graph_path,
            "breakpoints": list(graph.get("debug", {}).get("breakpoints", [])),
            "breakpoint_conditions": dict(
                graph.get("debug", {}).get("breakpoint_conditions", {})
            ),
            "watches": list(graph.get("debug", {}).get("watches", [])),
            "variables": deepcopy(graph.get("variables", {})),
        })

    def show(self, *, preferred_path: Path | None = None) -> None:
        h = self.host
        selected = h._selected_name if h._selected_name in h._objects_by_name else None
        if selected is not None:
            bindings = self.graphs_for_object(selected)
            context_path = preferred_path or (bindings[0][0] if bindings else None)
            if not h.logic_workspace.open_for_object(selected, context_path):
                return
            source = context_path.name if context_path is not None else "novo rascunho"
            h.statusBar().showMessage(f"Lógica Visual: {selected} • {source}")
        elif preferred_path is not None:
            if not h.logic_workspace.open_asset(preferred_path):
                return
        else:
            assets = self.assets()
            if assets and h.logic_workspace.current_path is None:
                fallback_path, _graph = max(
                    assets,
                    key=lambda entry: (
                        str(entry[1].get("target", {}).get("value", ""))
                        in h._objects_by_name,
                        len(entry[1].get("nodes", [])),
                    ),
                )
                if not h.logic_workspace.open_asset(fallback_path):
                    return
                h.statusBar().showMessage(
                    f"Lógica Visual: {fallback_path.name} • selecione um objeto para vincular"
                )
            else:
                h.statusBar().showMessage(
                    "Selecione um objeto na Hierarchy para definir o alvo da lógica"
                )
        registry = getattr(h, "_workspace_registry", None)
        if registry is not None:
            dock = registry.open("logic")
        else:
            h._show_visual_tool_dock(
                "editor.visual_scripting.visual_scripting_dock",
                "VisualScriptingEditorDock",
                "visual_scripting",
            )
            dock = getattr(h, "_dock_visual_scripting", None)
        if dock is not None and hasattr(dock, "sync_from_host"):
            self._attach_graph_hub_bridges(dock)
            dock.setWindowTitle(
                f"⚡ Visual Scripting Editor 2.0"
                f"{f' — {selected}' if selected else ''}"
            )
            dock.sync_from_host()
        h._log("INFO", f"Editor de Lógica Visual aberto{f' para {selected}' if selected else ''}")

    def _attach_graph_hub_bridges(self, dock: Any) -> None:
        h = self.host
        if getattr(h, "_graph_hub_bridges_attached", False):
            return
        orchestrator = getattr(h, "bridge_orchestrator", None)
        if orchestrator is None:
            return
        orchestrator.visual_scripting.attach_dock(dock)
        orchestrator.behavior_tree.attach_dock(dock.graph_tool_adapter("behavior_tree"))
        orchestrator.dialogue.attach_dock(dock.graph_tool_adapter("dialogue"))
        orchestrator.material_graph.attach_dock(dock.graph_tool_adapter("material_graph"))
        h._graph_hub_bridges_attached = True

    def assets(self) -> list[tuple[Path, dict]]:
        return self.bindings.assets()

    def graphs_for_object(self, object_name: str) -> list[tuple[Path, dict]]:
        return self.bindings.graphs_for_object(object_name)

    def save_binding(self, path: Path, graph: dict) -> None:
        self.bindings.save_binding(path, graph)

    def choose_component(self) -> None:
        h = self.host
        if h._selected_name not in h._objects_by_name:
            return
        assets = self.assets()
        if not assets:
            h.statusBar().showMessage("Nenhum Logic Graph disponível; use Criar novo")
            self.create_for_selected()
            return
        picker = LogicGraphPickerDialog(assets, h)
        if picker.exec() and picker.selected_path is not None:
            self.bindings.bind_existing_to_object(picker.selected_path, h._selected_name)
            h._component_expanded["logic"] = True
            h._log("INFO", f"{picker.selected_path.name} vinculado a {h._selected_name}")

    def create_for_selected(self) -> None:
        h = self.host
        if h._selected_name not in h._objects_by_name:
            return
        path = self.bindings.create_for_object(h._selected_name)
        h._component_expanded["logic"] = True
        self.show(preferred_path=path)
        h._log("INFO", f"Logic Graph criado para {h._selected_name}: {path.name}")

    def selected_path(self) -> Path | None:
        value = self.host.logic_graph_combo.currentData()
        return Path(str(value)).resolve() if value else None

    def open_selected(self) -> None:
        path = self.selected_path()
        if path is not None and path.is_file():
            self.show(preferred_path=path)

    def detach_selected(self) -> None:
        path = self.selected_path()
        if path is None or not path.is_file():
            return
        self.bindings.detach(path)
        self.host._log("INFO", f"Logic Graph desvinculado: {path.name}")

    def remove_all(self) -> None:
        h = self.host
        if h._selected_name not in h._objects_by_name:
            return
        bindings = self.graphs_for_object(h._selected_name)
        if not bindings:
            return
        answer = QMessageBox.question(
            h,
            "Desvincular lógica",
            f"Desvincular {len(bindings)} Logic Graph(s) de {h._selected_name}? Os arquivos serão preservados.",
        )
        if answer != QMessageBox.Yes:
            return
        self.bindings.detach_all_for_object(h._selected_name)
        h._log("INFO", f"Lógica Visual desvinculada de {h._selected_name}")

    def update_summary(self) -> None:
        h = self.host
        path = self.selected_path()
        if path is None or not path.is_file():
            h.logic_summary_label.setText("Nenhum Logic Graph selecionado.")
            h.logic_open_button.setEnabled(False)
            h.logic_unlink_button.setEnabled(False)
            return
        try:
            graph = load_logic_graph(path)
            events = [
                node.get("title", "Evento")
                for node in graph.get("nodes", [])
                if str(node.get("type", "")).startswith("event_")
            ]
            issues = validate_logic_graph(graph)
            errors = sum(issue.get("level") == "error" for issue in issues)
            summary = f"{len(graph.get('nodes', []))} blocos • {len(events)} eventos"
            if events:
                summary += f"\n{', '.join(str(event) for event in events[:3])}"
            summary += f"\n{'Pronto para executar' if not errors else f'{errors} erro(s) de validação'}"
            h.logic_summary_label.setText(summary)
            h.logic_open_button.setEnabled(True)
            h.logic_unlink_button.setEnabled(True)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            h.logic_summary_label.setText(f"Asset inválido: {exc}")

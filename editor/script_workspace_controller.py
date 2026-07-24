"""Script asset and scene-binding orchestration for the isolated editor."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog

from editor.script_templates import build_isolated_script_template, inspect_script_contract


class ScriptWorkspaceController:
    """Owns script discovery, asset creation and object bindings."""

    def __init__(self, host: Any, project_root: Path | None = None) -> None:
        self.host = host
        self.project_root = (project_root or Path.cwd()).resolve()

    def attach(self, object_name: str, path: Path) -> None:
        h = self.host
        if h._play_session.is_running:
            return
        path = Path(path)
        if object_name not in h._objects_by_name or path.suffix.lower() != ".py":
            return
        resolved = path.resolve()
        try:
            script_path = resolved.relative_to(self.project_root).as_posix()
        except ValueError:
            script_path = str(resolved)
        obj = h._objects_by_name[object_name]
        if script_path in obj.get("scripts", []):
            h.statusBar().showMessage(f"Script já anexado: {path.name}")
            return
        compatible, reason = inspect_script_contract(path)
        if not compatible:
            h._log(
                "WARNING",
                f"Script anexado, mas incompatível com Play isolado: {path.name}: {reason}",
            )
        h._record_history()
        obj.setdefault("scripts", []).append(script_path)
        h._component_expanded[f"script:{script_path}"] = True
        self._publish_and_refresh(object_name)
        h._log("INFO", f"Script anexado em {object_name}: {script_path}")

    def available_scripts(self) -> list[Path]:
        scripts_dir = self.project_root / "Assets" / "Scripts"
        if not scripts_dir.exists():
            return []
        return sorted(path for path in scripts_dir.glob("*.py") if path.name != "__init__.py")

    def change(self, old_path: str, new_path: str) -> None:
        h = self.host
        if h._selected_name not in h._objects_by_name or not new_path or old_path == new_path:
            return
        h._record_history()
        scripts = h._objects_by_name[h._selected_name].get("scripts", [])
        if old_path in scripts:
            scripts[scripts.index(old_path)] = new_path
        else:
            scripts.append(new_path)
        self._publish_and_refresh(h._selected_name)
        h._log("INFO", f"Script alterado de {Path(old_path).name} para {Path(new_path).name}")

    def remove(self, script_path: str) -> None:
        h = self.host
        if h._selected_name not in h._objects_by_name:
            return
        h._record_history()
        obj = h._objects_by_name[h._selected_name]
        scripts = obj.get("scripts", [])
        if script_path in scripts:
            scripts.remove(script_path)
        if not scripts:
            obj.pop("scripts", None)
        self._publish_and_refresh(h._selected_name)
        h._log("INFO", f"Script removido: {Path(script_path).name}")

    def update_property(self, script_path: str, key: str, value: float | bool | str) -> None:
        h = self.host
        if h._updating_inspector or h._selected_name not in h._objects_by_name:
            return
        properties = h._objects_by_name[h._selected_name].setdefault(
            "script_properties", {}
        ).setdefault(script_path, {})
        if properties.get(key) == value:
            return
        h._record_history()
        properties[key] = value
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        h._log("INFO", f"{h._selected_name}: '{key}' = {value} em {Path(script_path).name}")

    def remove_all(self) -> None:
        h = self.host
        if h._selected_name not in h._objects_by_name:
            return
        h._record_history()
        h._objects_by_name[h._selected_name].pop("scripts", None)
        self._publish_and_refresh(h._selected_name)
        h._log("INFO", f"Todos os scripts removidos de {h._selected_name}")

    def create_asset(self) -> None:
        h = self.host
        if h._selected_name not in h._objects_by_name:
            h.statusBar().showMessage("Selecione um objeto antes de criar o script")
            return
        default_path = self.project_root / "Assets" / "Scripts" / "new_script.py"
        filename, _ = QFileDialog.getSaveFileName(
            h, "Criar Script", str(default_path), "Python Script (*.py)"
        )
        if not filename:
            return
        path = Path(filename)
        if path.suffix.lower() != ".py":
            path = path.with_suffix(".py")
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(build_isolated_script_template(path.stem), encoding="utf-8")
        h._refresh_assets()
        self.attach(h._selected_name, path)
        self.edit_path(path)

    def edit_selected(self) -> None:
        h = self.host
        if h._selected_name not in h._objects_by_name:
            return
        scripts = h._objects_by_name[h._selected_name].get("scripts", [])
        if not scripts:
            h.statusBar().showMessage("Nenhum script anexado para editar")
            return
        self.edit_path(Path(scripts[0]))

    def edit_path(self, path: Path) -> None:
        path = Path(path)
        if not path.is_absolute():
            path = self.project_root / path
        if not path.exists():
            self.host.statusBar().showMessage(f"Script não encontrado: {path}")
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve()))):
            self.host.statusBar().showMessage(
                f"Não foi possível abrir o editor para {path.name}"
            )

    def _publish_and_refresh(self, object_name: str) -> None:
        h = self.host
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        h._scene_controller.select(object_name)
        h._selected_name = object_name
        h._update_inspector(object_name)

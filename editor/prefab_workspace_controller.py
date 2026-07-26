"""Prefab library and scene-instantiation orchestration for the editor."""
from __future__ import annotations

import json
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from PySide6.QtWidgets import QInputDialog, QMenu, QMessageBox, QTreeWidgetItem

from engine.prefabs.prefab_asset import (
    apply_exposed_properties,
    create_prefab_variant,
    load_prefab_asset,
    resolve_prefab_parameters,
)


class PrefabWorkspaceController:
    """Owns prefab persistence, browsing, variants and scene insertion."""

    def __init__(self, host: Any, project_root: Path | None = None) -> None:
        self.host = host
        self.project_root = (project_root or Path.cwd()).resolve()

    @property
    def directory(self) -> Path:
        return self.project_root / "Assets" / "Prefabs"

    def refresh(self) -> None:
        h = self.host
        h.prefab_tree.clear()
        root = QTreeWidgetItem(["📦 Prefabs"])
        h.prefab_tree.addTopLevelItem(root)
        self.directory.mkdir(parents=True, exist_ok=True)
        for path in sorted(self.directory.rglob("*.zprefab"), key=lambda item: str(item).lower()):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                variant = bool(payload.get("base_prefab")) if isinstance(payload, dict) else False
            except (OSError, json.JSONDecodeError):
                variant = False
            item = QTreeWidgetItem([("↳ " if variant else "🧩 ") + path.stem])
            item.setToolTip(0, str(path))
            root.addChild(item)
        root.setExpanded(True)

    @staticmethod
    def build_payload(obj: Mapping[str, Any], name: str) -> dict[str, Any]:
        prefab_object = deepcopy(dict(obj))
        prefab_object.pop("id", None)
        exposed = [
            {"name": "width", "label": "Largura", "type": "number", "default": float(prefab_object.get("w", 64.0)), "target": "w"},
            {"name": "height", "label": "Altura", "type": "number", "default": float(prefab_object.get("h", 64.0)), "target": "h"},
            {"name": "color", "label": "Cor", "type": "color", "default": prefab_object.get("color", "#ffffff"), "target": "color"},
            {"name": "image", "label": "Imagem", "type": "image", "default": prefab_object.get("texture", ""), "target": "texture"},
            {"name": "tag", "label": "Tag", "type": "text", "default": prefab_object.get("tag", "Untagged"), "target": "tag"},
            {"name": "layer", "label": "Layer", "type": "text", "default": prefab_object.get("layer", "Default"), "target": "layer"},
        ]
        return {
            "format_version": 2,
            "prefab_name": name,
            "object": prefab_object,
            "exposed_properties": exposed,
        }

    def save_selected(self) -> None:
        h = self.host
        if h._selected_name not in h._objects_by_name:
            return
        name, accepted = QInputDialog.getText(
            h, "Criar Prefab", "Nome do Prefab:", text=h._selected_name
        )
        name = "".join(char for char in name.strip() if char.isalnum() or char in "-_ ")
        if not accepted or not name:
            return
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{name}.zprefab"
        payload = self.build_payload(h._objects_by_name[h._selected_name], name)
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        self.refresh()
        h._refresh_assets()
        h._log("INFO", f"Prefab criado: {path.name}")

    def instantiate_item(self, item: QTreeWidgetItem) -> None:
        path_value = item.toolTip(0)
        if path_value:
            self.instantiate(Path(path_value))

    def instantiate(self, path: Path) -> None:
        h = self.host
        try:
            payload = load_prefab_asset(path, self.project_root)
            prefab_object = deepcopy(payload["object"])
            definitions = payload.get("exposed_properties", [])
            apply_exposed_properties(
                prefab_object,
                definitions,
                resolve_prefab_parameters(definitions, {}),
            )
            if any(key in prefab_object for key in ("transform", "visual", "components")):
                raise ValueError("use o Play Mode para instanciar este formato legado")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            h._log("ERROR", f"Falha ao abrir Prefab: {exc}")
            return
        h._record_history()
        obj = deepcopy(prefab_object)
        obj["id"] = str(uuid.uuid4())
        obj["name"] = h._unique_name(
            str(obj.get("name") or payload.get("prefab_name") or "Prefab")
        )
        obj["x"] = float(obj.get("x", 0.0)) + 16.0
        obj["y"] = float(obj.get("y", 0.0)) + 16.0
        h._scene_snapshot.append(obj)
        h._objects_by_name[obj["name"]] = obj
        h._selected_name = obj["name"]
        h._refresh_hierarchy()
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        h._scene_controller.select(obj["name"])
        h._update_inspector(obj["name"])
        h._log("INFO", f"Prefab adicionado: {obj['name']}")

    def open_menu(self, position) -> None:
        h = self.host
        item = h.prefab_tree.itemAt(position)
        path_value = item.toolTip(0) if item is not None else ""
        if not path_value or not Path(path_value).is_file():
            return
        menu = QMenu(h)
        instantiate = menu.addAction("Adicionar à cena")
        variant = menu.addAction("Criar variante...")
        menu.addSeparator()
        unpack = menu.addAction("Desempacotar instância (Unpack)")
        unpack.setToolTip("Remove a relação de prefab do objeto selecionado na cena, preservando seus valores atuais.")
        instantiate.triggered.connect(lambda _checked=False: self.instantiate_item(item))
        variant.triggered.connect(
            lambda _checked=False: self.create_variant(Path(path_value))
        )
        unpack.triggered.connect(lambda _checked=False: self.unpack_selected_instance())
        menu.exec(h.prefab_tree.viewport().mapToGlobal(position))

    def create_variant(self, base_path: Path) -> None:
        h = self.host
        name, accepted = QInputDialog.getText(
            h,
            "Criar variante de Prefab",
            "Nome da variante:",
            text=f"{base_path.stem}Variant",
        )
        safe = "".join(char for char in name.strip() if char.isalnum() or char in "-_ ")
        if not accepted or not safe:
            return
        target = base_path.parent / f"{safe}.zprefab"
        if target.exists() and QMessageBox.question(
            h, "Substituir variante", f"{target.name} já existe. Substituir?"
        ) != QMessageBox.Yes:
            return
        try:
            create_prefab_variant(base_path, target, project_root=self.project_root)
        except (OSError, ValueError) as exc:
            h._log("ERROR", f"Falha ao criar variante: {exc}")
            return
        self.refresh()
        h._refresh_assets()
        h._log("INFO", f"Variante criada: {target.name} → {base_path.name}")

    def unpack_selected_instance(self) -> None:
        """Desvincula o objeto atualmente selecionado na cena de seu prefab."""
        from engine.prefabs.prefab_serializer import unpack_prefab
        h = self.host
        selected = getattr(h, "_selected_name", None)
        if not selected:
            return
        obj = getattr(h, "_objects_by_name", {}).get(selected)
        if obj is None:
            return
        # Suporte ao model MVVM (GameObject) e ao model dict do viewport antigo
        if hasattr(obj, "prefab_uuid"):
            unpack_prefab(obj)
        else:
            obj.pop("prefab_uuid", None)
            obj.pop("prefab_source", None)
        h._log("INFO", f"Prefab desempacotado: {selected}")
        # Atualiza a hierarchy para remover o badge 🔷
        if hasattr(h, "_refresh_hierarchy"):
            h._refresh_hierarchy()


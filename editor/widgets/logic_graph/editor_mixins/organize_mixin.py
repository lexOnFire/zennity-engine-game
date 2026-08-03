"""Layout/organization actions for the Logic Graph canvas (groups, comments,
auto-layout, alignment). Extracted from LogicGraphPropertiesMixin to keep that
class under the release size budget (tests/editor/test_logic_graph_class_boundaries.py) --
purely mechanical move, no behavior change.
"""
from __future__ import annotations

import uuid

from PySide6.QtWidgets import QInputDialog

from editor.widgets.logic_graph.items import LogicNodeItem


class LogicGraphOrganizeMixin:
    def add_group(self) -> None:
        center = self.view.mapToScene(self.view.viewport().rect().center())
        data = {
            "id": uuid.uuid4().hex,
            "title": "Novo grupo",
            "position": [center.x() - 230.0, center.y() - 140.0],
            "size": [460.0, 280.0],
            "color": "#35506b",
        }
        self.graph.setdefault("editor", {}).setdefault("groups", []).append(data)
        self.scene.clearSelection()
        self._create_group_item(data).setSelected(True)
        self.mark_dirty()
        self.minimap.refresh()

    def add_comment(self) -> None:
        center = self.view.mapToScene(self.view.viewport().rect().center())
        text_value, accepted = QInputDialog.getMultiLineText(self, "Novo comentário", "Texto", "Explique esta parte do grafo")
        if not accepted:
            return
        data = {
            "id": uuid.uuid4().hex,
            "text": text_value,
            "position": [center.x() - 130.0, center.y() - 40.0],
            "width": 260.0,
            "color": "#6b5b2f",
        }
        self.graph.setdefault("editor", {}).setdefault("comments", []).append(data)
        self.scene.clearSelection()
        self._create_comment_item(data).setSelected(True)
        self.mark_dirty()
        self.minimap.refresh()

    def organize_graph(self) -> None:
        """Organiza o fluxo em colunas estáveis sem alterar a lógica."""
        if not self.graph.get("nodes"):
            return
        node_ids = [str(node["id"]) for node in self.graph["nodes"]]
        incoming = {node_id: 0 for node_id in node_ids}
        outgoing: dict[str, list[str]] = {node_id: [] for node_id in node_ids}
        for edge in self.graph.get("edges", []):
            source = str(edge.get("from_node", ""))
            target = str(edge.get("to_node", ""))
            if source in outgoing and target in incoming:
                outgoing[source].append(target)
                incoming[target] += 1
        queue = [node_id for node_id in node_ids if incoming[node_id] == 0]
        levels = {node_id: 0 for node_id in queue}
        visited: list[str] = []
        while queue:
            node_id = queue.pop(0)
            visited.append(node_id)
            for target in outgoing[node_id]:
                levels[target] = max(levels.get(target, 0), levels[node_id] + 1)
                incoming[target] -= 1
                if incoming[target] == 0:
                    queue.append(target)
        for node_id in node_ids:
            if node_id not in visited:
                levels[node_id] = max(levels.values(), default=0) + 1
        rows: dict[int, list[str]] = {}
        for node_id in node_ids:
            rows.setdefault(levels.get(node_id, 0), []).append(node_id)
        for level, ids in sorted(rows.items()):
            for row, node_id in enumerate(ids):
                self.node_items[node_id].setPos(80.0 + level * 290.0, 80.0 + row * 170.0)
        self.refresh_connections()
        self.mark_dirty()
        self.fit_graph()
        self.message.emit("INFO", "Grafo organizado por ordem de execução")

    def align_selected(self) -> None:
        selected = [item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)]
        if len(selected) < 2:
            self.message.emit("WARNING", "Selecione dois ou mais blocos para alinhar")
            return
        x = min(item.pos().x() for item in selected)
        for item in selected:
            item.setPos(x, item.pos().y())
        self.mark_dirty()

    def distribute_selected(self) -> None:
        selected = sorted(
            (item for item in self.scene.selectedItems() if isinstance(item, LogicNodeItem)),
            key=lambda item: item.pos().y(),
        )
        if len(selected) < 3:
            self.message.emit("WARNING", "Selecione três ou mais blocos para distribuir")
            return
        top, bottom = selected[0].pos().y(), selected[-1].pos().y()
        spacing = (bottom - top) / (len(selected) - 1)
        for index, item in enumerate(selected):
            item.setPos(item.pos().x(), top + index * spacing)
        self.mark_dirty()

"""Layout and comment helper functions for LogicGraph CanvasMixin."""
from __future__ import annotations
import uuid
from typing import Any
from editor.widgets.logic_graph.items import LogicNodeItem, LogicCommentItem


def add_comment_box(mixin: Any) -> None:
    selected_nodes = [item for item in mixin.scene.selectedItems() if isinstance(item, LogicNodeItem)]
    if selected_nodes:
        min_x = min(item.pos().x() for item in selected_nodes) - 20.0
        min_y = min(item.pos().y() for item in selected_nodes) - 40.0
        max_x = max(item.pos().x() + item.width for item in selected_nodes) + 20.0
        max_y = max(item.pos().y() + item.height for item in selected_nodes) + 20.0
        width = max(260.0, max_x - min_x)
        height = max(120.0, max_y - min_y)
        pos = [min_x, min_y]
    else:
        center = mixin.view.mapToScene(mixin.view.viewport().rect().center())
        pos = [center.x() - 130.0, center.y() - 60.0]
        width, height = 260.0, 120.0

    comment_data = {
        "id": uuid.uuid4().hex,
        "text": "Lógica do Jogo / Comentário",
        "position": pos,
        "width": width,
        "height": height,
        "color": "#1e3a5f",
    }
    mixin.graph.setdefault("comments", []).append(comment_data)
    item = LogicCommentItem(mixin, comment_data)
    mixin.scene.addItem(item)
    mixin.comment_items[comment_data["id"]] = item
    mixin.mark_dirty()
    mixin.message.emit("INFO", "Caixa de comentário criada (Atalho: C)")


def auto_arrange_nodes(mixin: Any) -> None:
    nodes = mixin.graph.get("nodes", [])
    if not nodes:
        return
    edges = mixin.graph.get("edges", [])
    graph_map: dict[str, list[str]] = {}
    for edge in edges:
        graph_map.setdefault(edge["from_node"], []).append(edge["to_node"])

    start_nodes = [n for n in nodes if str(n.get("type", "")).startswith("event_") or not any(e["to_node"] == n["id"] for e in edges)]
    visited = set()
    columns: list[list[dict]] = []

    current_layer = start_nodes or nodes[:1]
    while current_layer:
        columns.append(current_layer)
        for n in current_layer:
            visited.add(n["id"])
        next_layer = []
        for n in current_layer:
            for target_id in graph_map.get(n["id"], []):
                if target_id not in visited:
                    target_node = next((item for item in nodes if item["id"] == target_id), None)
                    if target_node and target_node not in next_layer:
                        next_layer.append(target_node)
        current_layer = next_layer

    unvisited = [n for n in nodes if n["id"] not in visited]
    if unvisited:
        columns.append(unvisited)

    start_x, start_y = 100.0, 100.0
    col_width = 300.0
    row_height = 180.0

    for col_idx, col_nodes in enumerate(columns):
        for row_idx, node in enumerate(col_nodes):
            x = start_x + col_idx * col_width
            y = start_y + row_idx * row_height
            node["position"] = [x, y]
            if node["id"] in mixin.node_items:
                mixin.node_items[node["id"]].setPos(x, y)

    mixin.refresh_connections()
    mixin.mark_dirty()
    mixin.message.emit("INFO", "Grafo re-organizado com sucesso (Auto-Layout Shift+F)")

"""Bidirectional Debug Bridge — Conecta Viewport e Grafo de forma simétrica e bidirecional.

Permite que a depuração funcione nos dois sentidos:
  1. Graph -> Viewport: Selecionar nó 'Move()' destaca o objeto afetado na Viewport, desenha a seta de velocidade e o collider.
  2. Viewport -> Graph: Clicar no objeto na Viewport destaca automaticamente o nó de movimento responsável no Grafo, acende a conexão ativa e posiciona a máquina de estados.
"""
from __future__ import annotations

from typing import Any, Optional
from editor.core.event_bus import EventBus


class BidirectionalDebugBridge:
    """Orquestra a sincronização de depuração bidirecional entre Grafo, Viewport e Inspector."""

    _instance: Optional[BidirectionalDebugBridge] = None

    def __init__(self) -> None:
        self._current_selected_node: Any = None
        self._current_selected_object: Any = None
        self._node_to_object_map: dict[str, Any] = {}
        self._object_to_node_map: dict[str, str] = {}

    @classmethod
    def instance(cls) -> BidirectionalDebugBridge:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register_binding(self, node_id: str, game_object: Any) -> None:
        """Associa um nó do grafo ao objeto de jogo que ele controla."""
        obj_id = getattr(game_object, "id", str(id(game_object)))
        self._node_to_object_map[str(node_id)] = game_object
        self._object_to_node_map[obj_id] = str(node_id)

    def on_node_selected_in_graph(self, node_id: str, node_name: str, viewport_panel: Any) -> None:
        """Sentido 1: Grafo -> Viewport. Destaca o objeto afetado e seus gizmos específicos."""
        self._current_selected_node = node_id
        game_obj = self._node_to_object_map.get(str(node_id))

        if viewport_panel is not None:
            if game_obj:
                viewport_panel.set_target_object(game_obj)
            viewport_panel.highlight_execution_node(node_id, node_name)

        EventBus.emit("Debug.node_highlighted", node_id=node_id, node_name=node_name)

    def on_object_selected_in_viewport(self, game_object: Any, graph_dock: Any) -> None:
        """Sentido 2: Viewport -> Grafo. Localiza o nó responsável no grafo e o destaca no canvas."""
        self._current_selected_object = game_object
        obj_id = getattr(game_object, "id", str(id(game_object)))
        associated_node_id = self._object_to_node_map.get(obj_id)

        if graph_dock is not None and associated_node_id:
            # Notifica o dock para selecionar o nó no canvas
            if hasattr(graph_dock, "highlight_node_execution"):
                graph_dock.highlight_node_execution(associated_node_id, "ActiveNode")

        EventBus.emit("Debug.object_selected", object=game_object, node_id=associated_node_id)

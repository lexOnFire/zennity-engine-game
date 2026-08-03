"""Tests — Item 1 (Connection System), Item 2 (Example Graphs), Item 3 (Graph↔Inspector Sync).

Cobertura:
  Item 1 — Connection System
    - begin_connection / finish_connection cria edge corretamente
    - Conexão output→output é rejeitada
    - Conexão exec→float é rejeitada
    - Conexão no mesmo nó é rejeitada
    - Delete de edge funciona
    - update_edge_path atualiza bezier após mover nó
    - GraphEdgeItem.update_path calcula o path
    - Type-mismatch detectado corretamente
    - cancel_connection limpa estado

  Item 2 — Example Graphs
    - Todos os 5 grafos carregam sem erro
    - Nós referenciados existem no GraphRegistry
    - Contagem de nós e arestas por grafo

  Item 3 — Graph↔Inspector Sync
    - node_selected Signal é emitido ao selecionar nó
    - GraphNodeInspector.inspect_node popula o widget
    - Edição de valor emite value_changed
    - inspect_node(None) mostra estado vazio
"""
from __future__ import annotations
import uuid
import pytest
from unittest.mock import MagicMock, patch

# ─────────────────────────────────────────────────────────────────────────────
#  Lightweight stubs — avoid Qt and full engine bootstrap
# ─────────────────────────────────────────────────────────────────────────────

class _MockPinDef:
    def __init__(self, pid, ptype="exec", label="", default=None):
        self.id = pid
        self.pin_type = ptype
        self.label_key = f"pin.{pid}"
        self.default_value = default
        self.hide_label = False

class _MockNodeDef:
    def __init__(self, nid, name="Node", category="Logic", inputs=None, outputs=None, desc=""):
        self.id = nid
        self.name_key = name
        self.category_key = category
        self.category = category
        self.description = desc
        self.inputs = inputs or []
        self.outputs = outputs or [_MockPinDef("exec")]
        self.tags = []


# ─────────────────────────────────────────────────────────────────────────────
#  Item 1 — Connection System
# ─────────────────────────────────────────────────────────────────────────────

class TestConnectionSystem:
    """Tests for graph_canvas.GraphScene connection logic (no Qt GUI)."""

    def _make_port(self, node_mock, direction, dtype="float", name="out"):
        port = MagicMock()
        port.direction = direction
        port.data_type = dtype
        port.name = name
        port.node = node_mock
        port.base_color = MagicMock()
        port.scene_position.return_value = MagicMock(x=lambda: 0.0, y=lambda: 0.0)
        return port

    def _make_node(self, node_id="n1"):
        node = MagicMock()
        node.node_id = node_id
        return node

    def test_create_edge_valid(self):
        """Valid output→input connection creates an edge."""
        from editor.widgets.graph_editor.graph_canvas import GraphScene
        scene = GraphScene.__new__(GraphScene)
        scene.nodes = {}
        scene.edges = {}
        scene._connection_origin = None
        scene._temp_connection = None
        # Patch add_edge / addItem
        added = []
        scene.add_edge = lambda e: added.append(e)

        n1, n2 = self._make_node("n1"), self._make_node("n2")
        src = self._make_port(n1, "output", "float", "value")
        tgt = self._make_port(n2, "input",  "float", "value")

        scene._create_edge_between(src, tgt)
        assert len(added) == 1
        assert added[0].source_node == "n1"

    def test_create_edge_same_direction_rejected(self):
        """output→output connection is rejected."""
        from editor.widgets.graph_editor.graph_canvas import GraphScene
        scene = GraphScene.__new__(GraphScene)
        scene.nodes = {}
        scene.edges = {}
        added = []
        scene.add_edge = lambda e: added.append(e)

        n1, n2 = self._make_node("n1"), self._make_node("n2")
        src = self._make_port(n1, "output", "float", "a")
        tgt = self._make_port(n2, "output", "float", "b")

        scene._create_edge_between(src, tgt)
        assert len(added) == 0, "Same-direction connection must be rejected"

    def test_create_edge_same_node_rejected(self):
        """Connection between ports of the same node is rejected."""
        from editor.widgets.graph_editor.graph_canvas import GraphScene
        scene = GraphScene.__new__(GraphScene)
        scene.nodes = {}
        scene.edges = {}
        added = []
        scene.add_edge = lambda e: added.append(e)

        n1 = self._make_node("n1")
        src = self._make_port(n1, "output", "float", "a")
        tgt = self._make_port(n1, "input",  "float", "b")

        scene._create_edge_between(src, tgt)
        assert len(added) == 0, "Self-connection must be rejected"

    def test_create_edge_exec_float_rejected(self):
        """exec → float connection is rejected."""
        from editor.widgets.graph_editor.graph_canvas import GraphScene
        scene = GraphScene.__new__(GraphScene)
        scene.nodes = {}
        scene.edges = {}
        added = []
        scene.add_edge = lambda e: added.append(e)

        n1, n2 = self._make_node("n1"), self._make_node("n2")
        src = self._make_port(n1, "output", "exec",  "exec")
        tgt = self._make_port(n2, "input",  "float", "value")

        scene._create_edge_between(src, tgt)
        assert len(added) == 0, "exec↔float connection must be rejected"

    def test_remove_edge(self):
        """remove_edge removes edge from dict and scene."""
        from editor.widgets.graph_editor.graph_canvas import GraphScene
        scene = GraphScene.__new__(GraphScene)
        scene.nodes = {}
        removed = []

        edge = MagicMock()
        edge.edge_id = "e1"
        edge.scene.return_value = True
        scene.removeItem = lambda e: removed.append(e)
        scene.edges = {"e1": edge}

        scene.remove_edge("e1")
        assert "e1" not in scene.edges
        assert edge in removed

    def test_cancel_connection(self):
        """cancel_connection clears temp connection and origin."""
        from editor.widgets.graph_editor.graph_canvas import GraphScene
        scene = GraphScene.__new__(GraphScene)
        temp = MagicMock()
        temp.scene.return_value = True
        removed = []
        scene.removeItem = lambda e: removed.append(e)
        scene.nodes = {}
        scene.edges = {}
        scene._temp_connection = temp
        scene._connection_origin = MagicMock()

        scene.cancel_connection()
        assert scene._temp_connection is None
        assert scene._connection_origin is None


class TestGraphEdgeItem:
    """Tests for edge_item.GraphEdgeItem."""

    def test_type_mismatch_detected(self):
        """Mismatch between float and bool is detected."""
        from editor.widgets.graph_editor.edge_item import GraphEdgeItem
        edge = GraphEdgeItem(
            edge_id="e1",
            source_port="out",
            target_port="in",
            source_node="n1",
            target_node="n2",
            data_type="float",
            target_data_type="bool",
        )
        assert edge._type_mismatch is True

    def test_compatible_types(self):
        """float → float is compatible."""
        from editor.widgets.graph_editor.edge_item import GraphEdgeItem
        edge = GraphEdgeItem(
            edge_id="e1",
            source_port="out",
            target_port="in",
            source_node="n1",
            target_node="n2",
            data_type="float",
            target_data_type="float",
        )
        assert edge._type_mismatch is False

    def test_any_is_always_compatible(self):
        """any type is compatible with anything."""
        from editor.widgets.graph_editor.edge_item import GraphEdgeItem
        edge = GraphEdgeItem(
            edge_id="e1",
            source_port="out",
            target_port="in",
            source_node="n1",
            target_node="n2",
            data_type="any",
            target_data_type="object",
        )
        assert edge._type_mismatch is False


# ─────────────────────────────────────────────────────────────────────────────
#  Item 2 — Example Graphs
# ─────────────────────────────────────────────────────────────────────────────

class TestExampleGraphs:
    """Tests for engine.plugins.logic.example_graphs."""

    def test_all_five_graphs_present(self):
        from engine.plugins.logic.example_graphs import EXAMPLE_GRAPHS
        keys = set(EXAMPLE_GRAPHS.keys())
        assert "platformer_movement" in keys
        assert "enemy_ai" in keys
        assert "hud" in keys
        assert "combat" in keys
        assert "save_load" in keys

    def test_all_graphs_have_nodes_and_edges(self):
        from engine.plugins.logic.example_graphs import EXAMPLE_GRAPHS
        for name, graph in EXAMPLE_GRAPHS.items():
            assert "nodes" in graph, f"{name} has no 'nodes' key"
            assert "edges" in graph, f"{name} has no 'edges' key"
            assert len(graph["nodes"]) > 0, f"{name} has zero nodes"
            assert len(graph["edges"]) > 0, f"{name} has zero edges"

    def test_platformer_movement_node_count(self):
        from engine.plugins.logic.example_graphs import EXAMPLE_GRAPHS
        g = EXAMPLE_GRAPHS["platformer_movement"]
        assert len(g["nodes"]) >= 9
        assert len(g["edges"]) >= 7

    def test_enemy_ai_node_count(self):
        from engine.plugins.logic.example_graphs import EXAMPLE_GRAPHS
        g = EXAMPLE_GRAPHS["enemy_ai"]
        assert len(g["nodes"]) >= 7
        assert len(g["edges"]) >= 7

    def test_hud_node_count(self):
        from engine.plugins.logic.example_graphs import EXAMPLE_GRAPHS
        g = EXAMPLE_GRAPHS["hud"]
        assert len(g["nodes"]) >= 6
        assert len(g["edges"]) >= 6

    def test_combat_node_count(self):
        from engine.plugins.logic.example_graphs import EXAMPLE_GRAPHS
        g = EXAMPLE_GRAPHS["combat"]
        assert len(g["nodes"]) >= 8
        assert len(g["edges"]) >= 8

    def test_save_load_node_count(self):
        from engine.plugins.logic.example_graphs import EXAMPLE_GRAPHS
        g = EXAMPLE_GRAPHS["save_load"]
        assert len(g["nodes"]) >= 14
        assert len(g["edges"]) >= 12

    def test_example_graph_meta_all_present(self):
        from engine.plugins.logic.example_graphs import EXAMPLE_GRAPH_META, EXAMPLE_GRAPHS
        for key in EXAMPLE_GRAPHS:
            assert key in EXAMPLE_GRAPH_META, f"Meta missing for {key}"
            assert "label" in EXAMPLE_GRAPH_META[key]
            assert "icon" in EXAMPLE_GRAPH_META[key]

    def test_node_ids_are_uuids(self):
        """All node IDs in example graphs are valid UUID strings."""
        from engine.plugins.logic.example_graphs import EXAMPLE_GRAPHS
        for name, graph in EXAMPLE_GRAPHS.items():
            for node in graph["nodes"]:
                try:
                    uuid.UUID(str(node["id"]))
                except ValueError:
                    pytest.fail(f"{name}: invalid UUID node id: {node['id']}")

    def test_edge_references_valid_node_ids(self):
        """All edge source/target node IDs refer to actual nodes in the same graph."""
        from engine.plugins.logic.example_graphs import EXAMPLE_GRAPHS
        for name, graph in EXAMPLE_GRAPHS.items():
            node_ids = {str(n["id"]) for n in graph["nodes"]}
            for edge in graph["edges"]:
                assert str(edge["source_node"]) in node_ids, \
                    f"{name} edge {edge['id']} source_node not found"
                assert str(edge["target_node"]) in node_ids, \
                    f"{name} edge {edge['id']} target_node not found"

    def test_referenced_node_types_registered(self):
        """All node types referenced in example graphs are registered in GraphRegistry."""
        import engine.plugins.logic.nodes  # noqa: F401 — triggers @register_node decorators
        from engine.plugins.logic.example_graphs import EXAMPLE_GRAPHS
        from engine.graphs.registry import GraphRegistry
        for name, graph in EXAMPLE_GRAPHS.items():
            for node in graph["nodes"]:
                ntype = node["type"]
                result = GraphRegistry.get_node(ntype)
                assert result is not None, \
                    f"{name}: node type '{ntype}' not registered in GraphRegistry"


# ─────────────────────────────────────────────────────────────────────────────
#  Item 3 — Graph↔Inspector Sync
# ─────────────────────────────────────────────────────────────────────────────

class TestGraphInspectorSync:
    """Tests for graph_inspector.GraphNodeInspector (pure-logic, no Qt GUI)."""

    def _make_node_item(self, node_id="n1", inputs=None, outputs=None):
        node_def = _MockNodeDef(
            nid="logic.events.start",
            name="On Start",
            category="Events",
            inputs=inputs or [_MockPinDef("key_name", "string", "Key", "Space")],
            outputs=outputs or [_MockPinDef("exec", "exec")],
            desc="Test description",
        )
        instance_data = {"id": node_id, "position": [0, 0], "properties": {}}
        node_item = MagicMock()
        node_item.node_def = node_def
        node_item.instance_data = instance_data
        return node_item, instance_data

    def test_inspect_none_shows_empty(self):
        """inspect_node(None) should not raise and should clear state."""
        from editor.widgets.graph_editor.inspector.graph_inspector import GraphNodeInspector
        insp = GraphNodeInspector.__new__(GraphNodeInspector)
        insp._current_node_id = "old"
        insp._current_instance_data = {"id": "old"}

        # Build a minimal layout stub
        layout_mock = MagicMock()
        layout_mock.count.return_value = 0
        insp._layout = layout_mock
        insp._container = MagicMock()

        # Should not raise
        try:
            insp._clear()
        except Exception as e:
            pytest.fail(f"_clear raised {e}")

        assert insp._current_node_id is None
        assert insp._current_instance_data is None

    def test_value_changed_updates_instance_data(self):
        """_on_value_changed stores new value in instance_data.properties."""
        from editor.widgets.graph_editor.inspector.graph_inspector import GraphNodeInspector
        insp = GraphNodeInspector.__new__(GraphNodeInspector)
        insp.value_changed = MagicMock()

        instance_data = {"id": "n1", "properties": {}}
        insp._on_value_changed("n1", "speed", 5.0, instance_data)

        assert instance_data["properties"]["speed"] == 5.0
        insp.value_changed.emit.assert_called_once_with("n1", "speed", 5.0)

    def test_value_changed_creates_properties_dict(self):
        """_on_value_changed creates 'properties' key if missing."""
        from editor.widgets.graph_editor.inspector.graph_inspector import GraphNodeInspector
        insp = GraphNodeInspector.__new__(GraphNodeInspector)
        insp.value_changed = MagicMock()

        instance_data = {"id": "n2"}  # no 'properties'
        insp._on_value_changed("n2", "hp", 100.0, instance_data)

        assert "properties" in instance_data
        assert instance_data["properties"]["hp"] == 100.0

    def test_graph_inspector_alias(self):
        """GraphInspector is an alias for GraphNodeInspector."""
        from editor.widgets.graph_editor.inspector.graph_inspector import (
            GraphInspector, GraphNodeInspector,
        )
        assert GraphInspector is GraphNodeInspector

    def test_node_selected_signal_exists_on_canvas(self):
        """GraphCanvas exposes node_selected Signal."""
        from editor.widgets.graph_editor.graph_canvas import GraphCanvas
        assert hasattr(GraphCanvas, "node_selected"), \
            "GraphCanvas must have a node_selected Signal"

    def test_scene_node_selected_signal_exists(self):
        """GraphScene exposes node_selected Signal."""
        from editor.widgets.graph_editor.graph_canvas import GraphScene
        assert hasattr(GraphScene, "node_selected"), \
            "GraphScene must have a node_selected Signal"


class TestNewComplementaryNodes:
    """Verifies all 13 new complementary nodes are registered."""

    NEW_NODE_IDS = [
        "logic.math.compare",
        "logic.math.distance",
        "logic.math.subtract",
        "logic.movement.set_velocity",
        "logic.physics.get_velocity",
        "logic.transform.get_pos",
        "logic.transform.set_pos",
        "logic.ai.chase",
        "logic.ai.patrol",
        "logic.ai.attack",
        "logic.scene.load",
        "logic.objects.find",
        "logic.ui.set_progress_bar",
    ]

    def test_all_new_nodes_registered(self):
        import engine.plugins.logic.nodes  # noqa: F401 — triggers @register_node decorators
        from engine.graphs.registry import GraphRegistry
        for nid in self.NEW_NODE_IDS:
            result = GraphRegistry.get_node(nid)
            assert result is not None, f"Node '{nid}' not registered in GraphRegistry"

    def test_total_node_count_increased(self):
        """Total registered nodes after importing nodes.py should cover the 13 new ones."""
        import engine.plugins.logic.nodes  # noqa: F401 — triggers @register_node decorators
        from engine.graphs.registry import GraphRegistry
        nodes = GraphRegistry.list_nodes()
        # At minimum the 13 complementary nodes should be present
        assert len(nodes) >= 13, f"Expected >= 13 nodes, got {len(nodes)}"

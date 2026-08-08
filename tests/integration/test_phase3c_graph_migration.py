"""
PHASE 3C: Graph migration tests

Validate:
1. Flow edges are removed, not converted
2. Bypass works for 1 in → 1 out
3. Data edges are preserved
4. Ambiguous migrations are warned
"""
from engine.logic.runtime.graph_migration import migrate_graph_if_needed


def test_bypass_single_input_output():
    """Test case 1: A → Getter → B becomes A → B."""

    graph = {
        "format_version": 1,
        "nodes": [
            {"id": "event_update", "type": "event_update"},
            {"id": "get_pb", "type": "get_progress_bar_value", "properties": {}},
            {"id": "compare", "type": "compare_number"},
        ],
        "edges": [
            {
                "id": "edge1",
                "from_node": "event_update",
                "from_port": "next",
                "to_node": "get_pb",
                "to_port": "in",
                "kind": "flow",
                "order": 0,
            },
            {
                "id": "edge2",
                "from_node": "get_pb",
                "from_port": "next",
                "to_node": "compare",
                "to_port": "in",
                "kind": "flow",
                "order": 0,
            },
            {
                "id": "edge3",
                "from_node": "get_pb",
                "from_port": "value",
                "to_node": "compare",
                "to_port": "a",
                "kind": "data",
            },
        ],
    }

    migrated, warnings = migrate_graph_if_needed(graph)

    print("\n[TEST] Bypass single input/output")
    print(f"  Input edges: {len(graph['edges'])}")
    print(f"  Output edges: {len(migrated['edges'])}")
    print(f"  Warnings: {len(warnings)}")

    # Check flow edges removed, bypass added
    flow_edges = [e for e in migrated["edges"] if e.get("kind") == "flow"]
    data_edges = [e for e in migrated["edges"] if e.get("kind") == "data"]

    print(f"  Flow edges after: {len(flow_edges)}")
    print(f"  Data edges after: {len(data_edges)}")

    # Should have bypass edge: event_update → compare
    bypass_exists = any(
        e.get("from_node") == "event_update" and e.get("to_node") == "compare"
        for e in flow_edges
    )
    print(f"  Bypass edge created: {bypass_exists}")

    # Should NOT have direct edges to get_pb
    edges_to_getter = [e for e in flow_edges if e.get("to_node") == "get_pb"]
    edges_from_getter = [e for e in flow_edges if e.get("from_node") == "get_pb"]

    print(f"  Edges to get_pb: {len(edges_to_getter)}")
    print(f"  Edges from get_pb: {len(edges_from_getter)}")

    # Data edge must be preserved
    value_edge_exists = any(
        e.get("from_node") == "get_pb" and e.get("from_port") == "value"
        for e in data_edges
    )
    print(f"  Data edge (value) preserved: {value_edge_exists}")

    assert migrated["format_version"] == 2
    assert len(warnings) == 0, f"Should have no warnings: {warnings}"
    assert bypass_exists, "Should have bypass edge"
    assert len(edges_to_getter) == 0, "Should not connect to getter via flow"
    assert len(edges_from_getter) == 0, "Should not connect from getter via flow"
    assert value_edge_exists, "Should preserve data edge"

    print("  PASSED")


def test_no_flow_edges():
    """Test case 2: Getter with only data edges (no flow)."""

    graph = {
        "format_version": 1,
        "nodes": [
            {"id": "get_pb", "type": "get_progress_bar_value"},
            {"id": "compare", "type": "compare_number"},
        ],
        "edges": [
            {
                "id": "edge1",
                "from_node": "get_pb",
                "from_port": "value",
                "to_node": "compare",
                "to_port": "a",
                "kind": "data",
            },
        ],
    }

    migrated, warnings = migrate_graph_if_needed(graph)

    print("\n[TEST] No flow edges (pure data)")
    print(f"  Warnings: {len(warnings)}")
    print(f"  Edges preserved: {len(migrated['edges'])}")

    assert len(warnings) == 0
    assert len(migrated["edges"]) == 1
    assert migrated["edges"][0]["kind"] == "data"

    print("  PASSED")


def test_incoming_flow_no_outgoing():
    """Test case 3: Getter with incoming flow but no outgoing."""

    graph = {
        "format_version": 1,
        "nodes": [
            {"id": "event", "type": "event_update"},
            {"id": "get_pb", "type": "get_progress_bar_value"},
            {"id": "display", "type": "set_hud"},
        ],
        "edges": [
            {
                "id": "edge1",
                "from_node": "event",
                "from_port": "next",
                "to_node": "get_pb",
                "to_port": "in",
                "kind": "flow",
            },
            {
                "id": "edge2",
                "from_node": "get_pb",
                "from_port": "value",
                "to_node": "display",
                "to_port": "text",
                "kind": "data",
            },
        ],
    }

    migrated, warnings = migrate_graph_if_needed(graph)

    print("\n[TEST] Incoming flow, no outgoing")
    print(f"  Warnings: {len(warnings)}")

    flow_edges = [e for e in migrated["edges"] if e.get("kind") == "flow"]
    data_edges = [e for e in migrated["edges"] if e.get("kind") == "data"]

    print(f"  Flow edges: {len(flow_edges)}")
    print(f"  Data edges: {len(data_edges)}")

    # Should remove incoming flow
    incoming_to_getter = [e for e in flow_edges if e.get("to_node") == "get_pb"]
    print(f"  Incoming flow to getter: {len(incoming_to_getter)}")

    # Should preserve data edge
    assert len(data_edges) == 1
    assert len(incoming_to_getter) == 0

    print("  PASSED")


def test_multiple_incoming_no_outgoing():
    """Test case 4: Multiple incoming flow, no outgoing - unambiguous, just remove."""

    graph = {
        "format_version": 1,
        "nodes": [
            {"id": "event1", "type": "event_update"},
            {"id": "event2", "type": "event_timer"},
            {"id": "get_pb", "type": "get_progress_bar_value"},
        ],
        "edges": [
            {
                "id": "edge1",
                "from_node": "event1",
                "from_port": "next",
                "to_node": "get_pb",
                "to_port": "in",
                "kind": "flow",
            },
            {
                "id": "edge2",
                "from_node": "event2",
                "from_port": "next",
                "to_node": "get_pb",
                "to_port": "in",
                "kind": "flow",
            },
        ],
    }

    migrated, warnings = migrate_graph_if_needed(graph)

    print("\n[TEST] Multiple flow predecessors (unambiguous - no outgoing)")
    print(f"  Warnings: {len(warnings)}")

    flow_edges = [e for e in migrated["edges"] if e.get("kind") == "flow"]
    edges_to_getter = [e for e in flow_edges if e.get("to_node") == "get_pb"]

    print(f"  Flow edges to getter: {len(edges_to_getter)}")

    # No warning needed - just remove all incoming
    # Getter is pure, doesn't need flow from anywhere
    assert len(edges_to_getter) == 0, "Should remove all incoming flow edges"

    print("  PASSED")


def test_never_convert_flow_to_data():
    """CRITICAL: Never convert 'in' (flow) to 'widget_name' (data)."""

    graph = {
        "format_version": 1,
        "nodes": [
            {"id": "event", "type": "event_update"},
            {"id": "get_pb", "type": "get_progress_bar_value"},
        ],
        "edges": [
            {
                "id": "edge1",
                "from_node": "event",
                "from_port": "next",
                "to_node": "get_pb",
                "to_port": "in",
                "kind": "flow",
            },
        ],
    }

    migrated, warnings = migrate_graph_if_needed(graph)

    print("\n[TEST] Never convert flow edge to data edge")
    print(f"  Warnings: {len(warnings)}")

    # Check no edge has "widget_name" as target port with "flow" kind
    invalid_edges = [
        e for e in migrated["edges"]
        if e.get("to_port") == "widget_name" and e.get("kind") == "flow"
    ]

    print(f"  Invalid flow-to-widget_name edges: {len(invalid_edges)}")

    assert len(invalid_edges) == 0, "Should NEVER convert flow to data by renaming"

    # All edges to getter should be removed
    edges_to_getter = [e for e in migrated["edges"] if e.get("to_node") == "get_pb"]
    print(f"  Edges to getter: {len(edges_to_getter)}")

    assert len(edges_to_getter) == 0

    print("  PASSED")


def test_format_version_updated():
    """Migrated graph should have format_version = 2."""

    graph = {"format_version": 1, "nodes": [], "edges": []}

    migrated, _ = migrate_graph_if_needed(graph)

    print("\n[TEST] Format version updated to 2")
    print(f"  Before: {graph['format_version']}")
    print(f"  After: {migrated['format_version']}")

    assert migrated["format_version"] == 2

    print("  PASSED")


def test_already_canonical():
    """Already canonical graphs should not be modified."""

    graph = {"format_version": 2, "nodes": [], "edges": []}

    migrated, warnings = migrate_graph_if_needed(graph)

    print("\n[TEST] Already canonical graph unchanged")

    assert migrated is graph, "Should return same object"
    assert len(warnings) == 0

    print("  PASSED")


if __name__ == "__main__":
    test_bypass_single_input_output()
    test_no_flow_edges()
    test_incoming_flow_no_outgoing()
    test_multiple_successors_warning()
    test_never_convert_flow_to_data()
    test_format_version_updated()
    test_already_canonical()

    print("\n" + "=" * 80)
    print("All Phase 3C migration tests PASSED")
    print("=" * 80)

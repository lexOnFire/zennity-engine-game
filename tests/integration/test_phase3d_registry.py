"""
PHASE 3D: Node Definition Registry Tests

Validate canonical registry works correctly with gradual legacy support.
"""
import pytest
from engine.logic.node_definitions.registry import (
    NodeDefinitionRegistry,
    NodeDefinitionConflictError,
    get_registry,
    resolve_node_definition,
)


class MockNodeDefinition:
    """Mock canonical node definition for testing."""

    def __init__(self, node_id: str, inputs=None, outputs=None, pure=False):
        self.id = node_id
        self.inputs = inputs or []
        self.outputs = outputs or []
        self.pure = pure


def test_registry_register_canonical():
    """Test registering canonical definitions."""

    registry = NodeDefinitionRegistry()

    node = MockNodeDefinition("test_node", inputs=[], outputs=[])
    registry.register_canonical(node)

    assert registry.contains("test_node")
    assert registry.get("test_node") == node

    print("[TEST] Register canonical: PASSED")


def test_registry_register_legacy():
    """Test registering legacy definitions."""

    registry = NodeDefinitionRegistry()

    legacy_def = {"id": "legacy_node", "inputs": [], "outputs": []}
    registry.register_legacy("legacy_node", legacy_def)

    assert registry.contains("legacy_node")
    assert registry.get("legacy_node") is not None

    print("[TEST] Register legacy: PASSED")


def test_registry_canonical_takes_precedence():
    """Test that canonical definitions override legacy."""

    registry = NodeDefinitionRegistry()

    # Register legacy first
    legacy_def = {
        "id": "my_node",
        "inputs": [("in", "flow")],
        "outputs": [("next", "flow")],
    }
    registry.register_legacy("my_node", legacy_def)

    # Register canonical
    canonical_node = MockNodeDefinition("my_node", inputs=[], outputs=[])
    registry.register_canonical(canonical_node)

    # Get should return canonical
    result = registry.get("my_node")
    assert result == canonical_node, "Should return canonical, not legacy"

    print("[TEST] Canonical takes precedence: PASSED")


def test_registry_conflict_detection():
    """Test that conflicting definitions are detected."""

    registry = NodeDefinitionRegistry()

    # Register legacy
    legacy_def = {"id": "conflict_node", "inputs": [("a", "text")], "outputs": [("b", "number")]}
    registry.register_legacy("conflict_node", legacy_def)

    # Register conflicting canonical
    canonical_node = MockNodeDefinition(
        "conflict_node",
        inputs=[],  # Different!
        outputs=[],  # Different!
    )
    registry.register_canonical(canonical_node)

    # Should detect conflict
    conflicts = registry.detect_conflicts()
    assert "conflict_node" in conflicts, "Should detect contract mismatch"

    print("[TEST] Conflict detection: PASSED")


def test_registry_stats():
    """Test registry statistics."""

    registry = NodeDefinitionRegistry()

    # Add various nodes
    registry.register_canonical(MockNodeDefinition("can1"))
    registry.register_canonical(MockNodeDefinition("can2"))
    registry.register_legacy("leg1", {"id": "leg1"})
    registry.register_legacy("both", {"id": "both"})
    registry.register_canonical(MockNodeDefinition("both"))

    stats = registry.get_stats()

    print(f"\n[STATS]")
    print(f"  canonical_count: {stats['canonical_count']}")
    print(f"  legacy_count: {stats['legacy_count']}")
    print(f"  overlap_count: {stats['overlap_count']}")
    print(f"  legacy_only_count: {stats['legacy_only_count']}")
    print(f"  canonical_only_count: {stats['canonical_only_count']}")
    print(f"  total_unique: {stats['total_unique']}")

    assert stats["canonical_count"] == 3
    assert stats["legacy_count"] == 2
    assert stats["overlap_count"] == 1
    assert stats["legacy_only_count"] == 1
    assert stats["canonical_only_count"] == 2
    assert stats["total_unique"] == 4

    print("[TEST] Registry stats: PASSED")


def test_registry_all_resolved():
    """Test that all_resolved includes both canonical and adapted legacy."""

    registry = NodeDefinitionRegistry()

    registry.register_canonical(MockNodeDefinition("can1"))
    registry.register_legacy("leg1", {"id": "leg1"})
    registry.register_legacy("both", {"id": "both"})
    registry.register_canonical(MockNodeDefinition("both"))

    resolved = registry.all_resolved()

    assert "can1" in resolved
    assert "leg1" in resolved
    assert "both" in resolved
    assert len(resolved) == 3

    print("[TEST] All resolved: PASSED")


def test_registry_no_silent_override():
    """Test that duplicate canonical registration raises error."""

    registry = NodeDefinitionRegistry()

    node1 = MockNodeDefinition("same_id")
    node2 = MockNodeDefinition("same_id")

    registry.register_canonical(node1)

    # Should raise on second registration
    with pytest.raises(NodeDefinitionConflictError):
        registry.register_canonical(node2)

    print("[TEST] No silent override: PASSED")


def test_registry_allow_override():
    """Test that override flag allows re-registration."""

    registry = NodeDefinitionRegistry()

    node1 = MockNodeDefinition("same_id")
    node2 = MockNodeDefinition("same_id")

    registry.register_canonical(node1)
    registry.register_canonical(node2, allow_override=True)

    result = registry.get("same_id")
    assert result == node2, "Should have the second node"

    print("[TEST] Allow override: PASSED")


def test_singleton_registry():
    """Test that get_registry returns singleton."""

    reg1 = get_registry()
    reg2 = get_registry()

    assert reg1 is reg2, "Should return same instance"

    print("[TEST] Singleton registry: PASSED")


def test_resolve_function():
    """Test the resolve_node_definition convenience function."""

    registry = get_registry()
    registry._canonical.clear()
    registry._legacy.clear()
    registry._adapters.clear()

    registry.register_canonical(MockNodeDefinition("test"))

    result = resolve_node_definition("test")
    assert result is not None

    result_none = resolve_node_definition("nonexistent")
    assert result_none is None

    print("[TEST] Resolve function: PASSED")


if __name__ == "__main__":
    test_registry_register_canonical()
    test_registry_register_legacy()
    test_registry_canonical_takes_precedence()
    test_registry_conflict_detection()
    test_registry_stats()
    test_registry_all_resolved()
    test_registry_no_silent_override()
    test_registry_allow_override()
    test_singleton_registry()
    test_resolve_function()

    print("\n" + "=" * 80)
    print("All Phase 3D registry tests PASSED")
    print("=" * 80)

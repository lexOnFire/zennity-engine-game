"""Unit Tests for Graph Registry."""
import pytest
from engine.graphs.registry.graph_registry import GraphRegistry
from engine.graphs.metadata.node import NodeDefinition

def test_registry_singleton():
    reg1 = GraphRegistry()
    reg2 = GraphRegistry()
    assert reg1 is reg2

def test_node_registration():
    registry = GraphRegistry()
    node_def = NodeDefinition(id="test.node", name="Test Node", category="Test")
    registry.register_node(node_def)
    
    fetched = registry.get_node("test.node")
    assert fetched is not None
    assert fetched.name == "Test Node"

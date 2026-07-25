"""Unit Tests for Metadata Manager with Graph Nodes."""
import pytest
from engine.metadata.manager import MetadataManager
from engine.core.metadata.node import NodeDefinition

def test_metadata_manager_registration():
    manager = MetadataManager()
    node_def = NodeDefinition(id="test.node", name_key="Test Node", category_key="Test")
    manager.register(node_def)
    
    fetched = manager.get(NodeDefinition, "test.node")
    assert fetched is not None
    assert fetched.name_key == "Test Node"
    assert fetched.title_key == "Test Node"
    
def test_metadata_manager_query():
    manager = MetadataManager()
    manager.register(NodeDefinition(id="node1", name_key="Node 1", category_key="A"))
    manager.register(NodeDefinition(id="node2", name_key="Node 2", category_key="B"))
    manager.register(NodeDefinition(id="node3", name_key="Node 3", category_key="A"))
    
    results = manager.query(NodeDefinition, category_key="A")
    assert len(results) == 2
    assert results[0].id == "node1"
    assert results[1].id == "node3"

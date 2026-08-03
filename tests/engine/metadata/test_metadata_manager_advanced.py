import pytest
from engine.core.context import EngineContext
from engine.metadata.manager import MetadataManager
from engine.metadata.core import MetadataDefinition

@pytest.fixture
def manager():
    m = MetadataManager()
    return m

def test_metadata_unregister(manager):
    def1 = MetadataDefinition(id="test1", title_key="Test 1")
    manager.register(def1)
    assert manager.get(MetadataDefinition, "test1") is not None
    manager.unregister(MetadataDefinition, "test1")
    assert manager.get(MetadataDefinition, "test1") is None

def test_metadata_query_advanced(manager):
    def1 = MetadataDefinition(id="test1", title_key="Test 1", tags=["a", "b"], version="1.0")
    def2 = MetadataDefinition(id="test2", title_key="Test 2", tags=["a"], version="2.0")
    manager.register(def1)
    manager.register(def2)
    
    res = manager.query(MetadataDefinition, tags=["a"])
    assert len(res) == 2
    
    res = manager.query(MetadataDefinition, tags=["a", "b"])
    assert len(res) == 1
    assert res[0].id == "test1"
    
    res = manager.query(MetadataDefinition, version="2.0")
    assert len(res) == 1
    assert res[0].id == "test2"
    
def test_metadata_find(manager):
    def1 = MetadataDefinition(id="test1", title_key="Test 1", category_key="CatA")
    manager.register(def1)
    found = manager.find(MetadataDefinition, category_key="CatA")
    assert found is not None
    assert found.id == "test1"
    
def test_metadata_list_ids(manager):
    def1 = MetadataDefinition(id="test1")
    def2 = MetadataDefinition(id="test2")
    manager.register(def1)
    manager.register(def2)
    ids = manager.list_ids(MetadataDefinition)
    assert "test1" in ids
    assert "test2" in ids
    assert len(ids) == 2

def test_metadata_indices(manager):
    def1 = MetadataDefinition(id="test1", category_key="Math", tags=["core"])
    manager.register(def1)
    
    ref1 = (type(def1), def1.id)
    
    assert "Math" in manager._idx_by_category
    assert ref1 in manager._idx_by_category["Math"]
    assert "core" in manager._idx_by_tag
    assert ref1 in manager._idx_by_tag["core"]
    
    # Overwrite removes from old index (mocked by changing and re-registering)
    def1_new = MetadataDefinition(id="test1", category_key="Physics", tags=[])
    manager.register(def1_new)
    assert ref1 not in manager._idx_by_category.get("Math", set())
    assert ref1 in manager._idx_by_category.get("Physics", set())
    assert ref1 not in manager._idx_by_tag.get("core", set())
    
    manager.unregister(MetadataDefinition, "test1")
    assert ref1 not in manager._idx_by_category.get("Physics", set())

import pytest
from pathlib import Path
from engine.assets.asset_handle import AssetHandle
from engine.assets.asset_database import AssetDatabase
from engine.core.services import EngineServices
from engine.core.lifecycle import ServiceScope, ServiceState


def test_asset_handle_validity():
    empty_handle = AssetHandle()
    assert not empty_handle.is_valid()
    assert not bool(empty_handle)

    valid_handle = AssetHandle(guid="12345-abcde")
    assert valid_handle.is_valid()
    assert bool(valid_handle)
    assert str(valid_handle) == "12345-abcde"


def test_asset_database_service_registration(tmp_path):
    services = EngineServices()
    # project_root must be explicit: AssetDatabase falls back to Path.cwd(), and
    # initialize_all() below runs a full scan() that rewrites every .meta it
    # finds.  With the default that scan lands on the repository's own Assets/
    # directory and dirties 314 tracked files -- see
    # tests/architecture/test_repository_mutation_guard.py.
    db = AssetDatabase(tmp_path)

    assert db.scope == ServiceScope.ENGINE
    assert db.state == ServiceState.CREATED
    
    services.register(AssetDatabase, db)
    assert services.has(AssetDatabase)
    assert services.get(AssetDatabase) is db
    
    services.initialize_all()
    assert db.state == ServiceState.RUNNING


def test_asset_database_handle_resolution(tmp_path):
    assets_dir = tmp_path / "Assets"
    assets_dir.mkdir()
    
    (assets_dir / "test_image.png").write_text("dummy", encoding="utf-8")
    
    db = AssetDatabase(project_root=tmp_path)
    db.scan()
    
    info = db.get_asset_by_path("Assets/test_image.png")
    assert info is not None
    
    handle = db.resolve_handle("Assets/test_image.png")
    assert handle is not None
    assert handle.is_valid()
    assert handle.guid == info.guid
    
    resolved_info = db.get_asset_by_handle(handle)
    assert resolved_info == info
    
    resolved_path = db.resolve_path(handle)
    assert resolved_path == info.absolute_path

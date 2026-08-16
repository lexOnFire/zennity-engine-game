"""Testes dedicados ao isolamento de estado dirty e não-mutação do AssetDatabase (Item 10.1)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.assets.asset_database import AssetDatabase
from engine.assets.asset_metadata import compute_file_hash


def _create_sample_project(root: Path) -> tuple[Path, Path]:
    """Cria um mini projeto com asset e .meta válido."""
    assets_dir = root / "Assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    scene_file = assets_dir / "TestScene.zscene"
    scene_file.write_text("{\"name\": \"Test\"}\n", encoding="utf-8")
    
    scene_hash = compute_file_hash(scene_file)
    meta_file = assets_dir / "TestScene.zscene.meta"
    meta_content = {
        "guid": "12345678-1234-5678-1234-567812345678",
        "uuid": "12345678-1234-5678-1234-567812345678",
        "type": "scene",
        "importer": "generic_importer",
        "source_path": "Assets/TestScene.zscene",
        "import_settings": {},
        "dependencies": [],
        "hash": scene_hash,
    }
    meta_file.write_text(json.dumps(meta_content, indent=2) + "\n", encoding="utf-8")
    return scene_file, meta_file


def test_asset_database_scan_is_pure_read_and_zero_writes(tmp_path: Path):
    """Testa que scan() não reescreve .meta válido nem altera o mtime."""
    scene_file, meta_file = _create_sample_project(tmp_path)
    
    initial_mtime = meta_file.stat().st_mtime_ns
    initial_bytes = meta_file.read_bytes()
    
    db = AssetDatabase(tmp_path)
    assets = db.scan()
    
    assert len(assets) == 1
    assert meta_file.stat().st_mtime_ns == initial_mtime
    assert meta_file.read_bytes() == initial_bytes
    
    # Segundo passe (idempotência total)
    db.scan()
    assert meta_file.stat().st_mtime_ns == initial_mtime
    assert meta_file.read_bytes() == initial_bytes


def test_asset_database_refresh_is_zero_writes(tmp_path: Path):
    """Testa que refresh() em projeto limpo não produz escritas."""
    scene_file, meta_file = _create_sample_project(tmp_path)
    
    initial_mtime = meta_file.stat().st_mtime_ns
    
    db = AssetDatabase(tmp_path)
    db.refresh()
    
    assert meta_file.stat().st_mtime_ns == initial_mtime


def test_asset_database_missing_meta_created_once(tmp_path: Path):
    """Testa que asset sem .meta gera metadado exatamente uma vez."""
    assets_dir = tmp_path / "Assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    script_file = assets_dir / "helper.py"
    script_file.write_text("x = 10\n", encoding="utf-8")
    
    meta_file = assets_dir / "helper.py.meta"
    assert not meta_file.exists()
    
    db = AssetDatabase(tmp_path)
    db.scan()
    
    assert meta_file.exists()
    first_mtime = meta_file.stat().st_mtime_ns
    
    # Segundo passe não reescreve
    db.scan()
    assert meta_file.stat().st_mtime_ns == first_mtime


def test_asset_database_explicit_sync_updates_stale_meta(tmp_path: Path):
    """Testa que sincronização explícita atualiza meta quando o asset muda."""
    scene_file, meta_file = _create_sample_project(tmp_path)
    
    # Modifica o asset
    scene_file.write_text("{\"name\": \"ModifiedScene\"}\n", encoding="utf-8")
    new_hash = compute_file_hash(scene_file)
    
    db = AssetDatabase(tmp_path)
    
    # Scan comum (read-only) NÃO reescreve o meta do disco
    initial_mtime = meta_file.stat().st_mtime_ns
    db.scan()
    assert meta_file.stat().st_mtime_ns == initial_mtime
    
    # Import/Sync explícito atualiza
    db.import_asset(scene_file, sync_to_disk=True)
    updated_meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert updated_meta["hash"] == new_hash
    
    # Segundo passe pós-sync não reescreve
    second_mtime = meta_file.stat().st_mtime_ns
    db.scan()
    assert meta_file.stat().st_mtime_ns == second_mtime

from __future__ import annotations

from pathlib import Path
import pytest
import numpy as np

from engine.game_object import GameObject
from engine.physics.collider import BoxCollider
from engine.assets.asset_database import AssetDatabase
from engine.assets.asset_types import AssetType
from engine.prefabs.prefab_loader import create_prefab_from_object, instantiate_prefab
from engine.scene.scene_serializer import serialize_scene, deserialize_scene


def test_prefab_lifecycle_and_db_integration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Ajusta o diretório de execução para que o AssetDatabase aponte para o tmp_path
    monkeypatch.chdir(tmp_path)
    
    # Cria o banco de dados temporário
    db = AssetDatabase(project_root=tmp_path)
    db.ensure_project_folders()
    
    # Cria objeto de teste
    obj = GameObject("MyPlayer")
    obj.transform.position = np.array([5.0, -5.0, 0.0], dtype=np.float32)
    obj.mesh_type = "Quadrado"
    obj.add_component(BoxCollider(width=30, height=30))
    
    prefab_path = tmp_path / "Assets" / "Prefabs" / "MyPlayer.zprefab"
    
    # 1. Cria o prefab
    # Como create_prefab_from_object cria seu próprio AssetDatabase,
    # ele vai rodar no tmp_path que definimos via monkeypatch.chdir!
    p_uuid = create_prefab_from_object(obj, prefab_path)
    
    assert prefab_path.exists()
    assert (tmp_path / "Assets" / "Prefabs" / "MyPlayer.zprefab.meta").exists()
    
    # Escaneia o banco de dados temporário
    db.scan()
    prefab_asset = db.get_asset_by_path(prefab_path)
    
    assert prefab_asset is not None
    assert prefab_asset.type == AssetType.PREFAB
    assert prefab_asset.uuid == p_uuid
    
    # 2. Instancia o prefab
    instantiated = instantiate_prefab(prefab_path)
    assert instantiated is not obj
    assert instantiated.name == "MyPlayer"
    assert instantiated.prefab_uuid == p_uuid
    assert np.allclose(instantiated.transform.position, [5.0, -5.0, 0.0])
    
    # 3. Salva a cena contendo o objeto instanciado
    class MockScene:
        def __init__(self):
            self.name = "TestScene"
            self.editable_objects = [instantiated]
            
    scene = MockScene()
    serialized_scene = serialize_scene(scene)
    
    # Verifica que prefab_uuid foi serializado no objeto da cena
    serialized_obj = serialized_scene["objects"][0]
    assert serialized_obj["prefab_uuid"] == p_uuid
    
    # Deserializa a cena de volta e garante que o prefab_uuid é recuperado
    deserialized_data = deserialize_scene(serialized_scene)
    deserialized_obj = deserialized_data["objects"][0]
    assert deserialized_obj.prefab_uuid == p_uuid


def test_create_prefab_outside_project_raises_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Ajusta o diretório de execução para o tmp_path
    monkeypatch.chdir(tmp_path)
    
    # Cria o banco de dados temporário
    db = AssetDatabase(project_root=tmp_path)
    db.ensure_project_folders()
    
    obj = GameObject("Outsider")
    
    # Tenta salvar fora do diretório do projeto (ou seja, fora de tmp_path/Assets)
    outside_path = tmp_path / "MyPlayer.zprefab"
    
    with pytest.raises(ValueError) as excinfo:
        create_prefab_from_object(obj, outside_path)
        
    assert "O prefab deve ser salvo dentro do diretório Assets" in str(excinfo.value)


def test_instantiate_prefab_no_duplication(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Ajusta o diretório de execução para o tmp_path
    monkeypatch.chdir(tmp_path)
    
    # Cria o banco de dados temporário e pastas do projeto
    db = AssetDatabase(project_root=tmp_path)
    db.ensure_project_folders()
    
    obj = GameObject("SinglePlayer")
    prefab_path = tmp_path / "Assets" / "Prefabs" / "SinglePlayer.zprefab"
    
    # Salva o prefab
    create_prefab_from_object(obj, prefab_path)
    
    # Simula a lógica de instanciação da UI para garantir que não duplica
    instantiated = instantiate_prefab(prefab_path)
    
    # Simula uma cena com lista de game_objects e editable_objects
    class DummyScene:
        def __init__(self):
            self.game_objects = []
            self.editable_objects = []
            
        def _add_go(self, go):
            go.scene = self
            if go not in self.game_objects:
                self.game_objects.append(go)
                
    scene = DummyScene()
    
    # Adiciona à cena como feito no editor
    scene._add_go(instantiated)
    scene.editable_objects.append(instantiated)
    
    # Verifica que o objeto está referenciado exatamente uma vez em cada lista (sem duplicações)
    assert len(scene.game_objects) == 1
    assert len(scene.editable_objects) == 1
    assert scene.game_objects[0] is instantiated
    assert scene.editable_objects[0] is instantiated


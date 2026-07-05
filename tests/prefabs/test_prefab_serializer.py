from __future__ import annotations

import numpy as np
from engine.game_object import GameObject
from engine.physics.collider import BoxCollider
from engine.physics.rigidbody import RigidBody
from engine.prefabs.prefab_serializer import serialize_prefab, deserialize_prefab


def test_serialize_and_deserialize_simple_object() -> None:
    # 1. Cria objeto simples
    obj = GameObject("TestObj")
    obj.transform.position = np.array([10.0, 20.0, 0.0], dtype=np.float32)
    obj.transform.rotation = np.array([0.0, 0.0, 45.0], dtype=np.float32)
    obj.transform.scale = np.array([2.0, 3.0, 1.0], dtype=np.float32)
    
    obj.mesh_type = "Quadrado"
    obj.color = [255, 0, 0, 255]
    obj.material = "default"

    # Adiciona componentes
    obj.add_component(BoxCollider(width=40, height=40))
    obj.add_component(RigidBody(mass=5.0))

    # 2. Serializa para dicionário de prefab
    prefab_data = serialize_prefab(obj, prefab_uuid="custom-prefab-uuid-123")

    # Verifica chaves de root exigidas do prefab
    assert prefab_data["prefab_uuid"] == "custom-prefab-uuid-123"
    assert prefab_data["name"] == "TestObj"
    assert prefab_data["source_object_name"] == "TestObj"
    assert "transform" in prefab_data
    assert "components" in prefab_data
    assert "visual" in prefab_data
    assert "children" in prefab_data

    # 3. Deserializa e instancia
    instantiated = deserialize_prefab(prefab_data)

    # Verifica propriedades reconstruídas
    assert instantiated.name == "TestObj"
    assert instantiated.prefab_uuid == "custom-prefab-uuid-123"
    assert np.allclose(instantiated.transform.position, [10.0, 20.0, 0.0])
    assert np.allclose(instantiated.transform.rotation, [0.0, 0.0, 45.0])
    assert np.allclose(instantiated.transform.scale, [2.0, 3.0, 1.0])
    assert instantiated.mesh_type == "Quadrado"
    assert instantiated.color == [255, 0, 0, 255]
    assert instantiated.material == "default"

    # Verifica componentes
    collider = next((c for c in instantiated.components if type(c).__name__ == "BoxCollider"), None)
    assert collider is not None
    assert collider.width == 40
    assert collider.height == 40

    rb = next((c for c in instantiated.components if type(c).__name__ == "RigidBody"), None)
    assert rb is not None
    assert rb.mass == 5.0

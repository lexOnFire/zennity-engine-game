import json
import numpy as np
from typing import List, Dict, Any
from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider, CircleCollider


def serialize_game_object(go: GameObject) -> Dict[str, Any]:
    """Serializa recursivamente um GameObject e seus componentes para um dicionário."""
    data = {
        "id": go.id,
        "name": go.name,
        "tag": go.tag,
        "mesh_type": go.mesh_type,
        "active": go.active,
        "script_path": getattr(go, "script_path", ""),
        "transform": {
            "position": go.transform.position.tolist(),
            "scale": go.transform.scale.tolist(),
            "rotation": go.transform.rotation.tolist()
        },
        "components": [],
        "children": [serialize_game_object(child) for child in go.children]
    }
    
    # Serializa componentes conhecidos
    for comp in go.components:
        from engine.core import Transform
        if isinstance(comp, Transform):
            # O transform já é coberto no dicionário raiz do GameObject
            continue
            
        comp_data = {}
        if isinstance(comp, RigidBody):
            comp_data = {
                "type": "RigidBody",
                "mass": comp.mass,
                "gravity_scale": comp.gravity_scale,
                "is_kinematic": comp.is_kinematic
            }
        elif isinstance(comp, BoxCollider):
            comp_data = {
                "type": "BoxCollider",
                "width": comp.width,
                "height": comp.height,
                "is_trigger": comp.is_trigger
            }
        elif isinstance(comp, CircleCollider):
            comp_data = {
                "type": "CircleCollider",
                "radius": comp.radius,
                "is_trigger": comp.is_trigger
            }
            
        if comp_data:
            data["components"].append(comp_data)
            
    return data


def deserialize_game_object(data: Dict[str, Any]) -> GameObject:
    """Reconstrói recursivamente um GameObject e seus componentes a partir de um dicionário."""
    go = GameObject(data["name"], tag=data.get("tag", "Untagged"))
    
    # Força a restauração do UUID original
    go._id = data["id"]
    go.mesh_type = data.get("mesh_type")
    go.active = data.get("active", True)
    go.script_path = data.get("script_path", "")
    
    # Restaura transformações
    t_data = data["transform"]
    go.transform.position = np.array(t_data["position"], dtype=np.float32)
    go.transform.scale    = np.array(t_data["scale"], dtype=np.float32)
    go.transform.rotation = np.array(t_data["rotation"], dtype=np.float32)
    
    # Restaura componentes
    for comp_data in data.get("components", []):
        t = comp_data["type"]
        if t == "RigidBody":
            rb = RigidBody(
                mass=comp_data.get("mass", 1.0),
                gravity_scale=comp_data.get("gravity_scale", 1.0)
            )
            rb.is_kinematic = comp_data.get("is_kinematic", False)
            go.add_component(rb)
        elif t == "BoxCollider":
            bc = BoxCollider(
                width=comp_data.get("width", 32),
                height=comp_data.get("height", 32),
                is_trigger=comp_data.get("is_trigger", False)
            )
            go.add_component(bc)
        elif t == "CircleCollider":
            cc = CircleCollider(
                radius=comp_data.get("radius", 16),
                is_trigger=comp_data.get("is_trigger", False)
            )
            go.add_component(cc)
            
    # Restaura filhos recursivamente
    for child_data in data.get("children", []):
        child = deserialize_game_object(child_data)
        go.add_child(child)
        
    return go


def save_scene_to_file(filepath: str, root_objects: List[GameObject]) -> None:
    """Converte e salva a lista de objetos raiz em um arquivo JSON."""
    serialized_objs = [serialize_game_object(obj) for obj in root_objects]
    
    # Encapsula metadados da cena
    scene_data = {
        "engine_version": "Zennity 0.1.0",
        "objects": serialized_objs
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(scene_data, f, indent=4, ensure_ascii=False)


def load_scene_from_file(filepath: str) -> List[GameObject]:
    """Carrega e reconstrói a árvore de objetos a partir de um arquivo JSON."""
    with open(filepath, "r", encoding="utf-8") as f:
        scene_data = json.load(f)

    objs = []
    for obj_data in scene_data.get("objects", []):
        objs.append(deserialize_game_object(obj_data))
    return objs


def load_scene_file_with_metadata(filepath: str) -> tuple[List[GameObject], Dict[str, Any]]:
    """Carrega objects E metadados (ui, name, etc) do arquivo JSON da scene."""
    with open(filepath, "r", encoding="utf-8") as f:
        scene_data = json.load(f)

    # Carrega GameObjects
    objs = []
    for obj_data in scene_data.get("objects", []):
        objs.append(deserialize_game_object(obj_data))

    # Extrai metadados da scene (ui, scene_name, etc)
    metadata = {}
    if "ui" in scene_data:
        metadata["ui"] = scene_data["ui"]
    if "scene_name" in scene_data:
        metadata["scene_name"] = scene_data["scene_name"]
    if "blackboard" in scene_data:
        metadata["blackboard"] = scene_data["blackboard"]

    return objs, metadata

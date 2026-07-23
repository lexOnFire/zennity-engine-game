from __future__ import annotations

import json
from pathlib import Path
from engine.game_object import GameObject
from engine.assets.asset_database import AssetDatabase
from engine.prefabs.prefab_serializer import serialize_prefab, deserialize_prefab


def _resolve_project_root_from_path(path: Path) -> Path:
    # Procura recursivamente para cima até encontrar o diretório "Assets"
    for parent in path.parents:
        if parent.name.lower() == "assets":
            return parent.parent.resolve()
    return Path.cwd().resolve()


def create_prefab_from_object(obj: GameObject, path: str | Path) -> str:
    """Serializes a GameObject as a prefab and writes it to path, managing metadata."""
    path = Path(path).resolve()
    
    # Resolve project root e garante que o prefab é salvo dentro do diretório Assets do projeto
    project_root = _resolve_project_root_from_path(path)
    assets_root = project_root / "Assets"
    
    try:
        path.relative_to(assets_root)
    except ValueError:
        raise ValueError(
            f"Erro: O prefab deve ser salvo dentro do diretório Assets do projeto. "
            f"Caminho recebido fora de '{assets_root}': {path}"
        )
        
    db = AssetDatabase(project_root=project_root)
    
    # Ensure parent folder exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get/create metadata for this prefab path to get the stable UUID
    meta = db.ensure_meta(path)
    p_uuid = meta.uuid
    
    # Serialize prefab with the stable UUID
    prefab_data = serialize_prefab(obj, p_uuid)
    
    # Save prefab to disk
    path.write_text(json.dumps(prefab_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    
    # Import asset in database so it is indexed
    db.import_asset(path)
    
    # Link prefab_uuid to the source object
    obj.prefab_uuid = p_uuid
    
    return p_uuid


def instantiate_prefab(path: str | Path) -> GameObject:
    """Loads a prefab from path and returns a newly instantiated GameObject."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Prefab file not found at: {path}")
        
    data = json.loads(path.read_text(encoding="utf-8"))
    obj = deserialize_prefab(data)
    return obj

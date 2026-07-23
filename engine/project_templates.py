import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any


def get_template_manifest(template_name: str) -> Dict[str, Any]:
    """Retorna o manifesto padrao de um template de projeto."""
    manifests = {
        "empty": {
            "name": "New Project",
            "version": "1.0.0",
            "zennity_version": "1.2.0",
            "description": "An empty Zennity Engine project.",
        },
        "platformer": {
            "name": "2D Platformer",
            "version": "1.0.0",
            "zennity_version": "1.2.0",
            "description": "A basic 2D Platformer template.",
        }
    }
    return manifests.get(template_name.lower(), manifests["empty"])


def create_project(template_name: str, dest_dir: str | Path) -> None:
    """Cria um novo projeto Zennity usando o template especificado, de forma atomica."""
    project_root = Path(dest_dir).resolve()
    
    if project_root.exists() and any(project_root.iterdir()):
        raise ValueError(f"Destination directory '{project_root}' is not empty.")
        
    # Use atomic creation via a temporary directory next to destination or in temp
    temp_dir = Path(tempfile.mkdtemp(prefix="zennity_template_"))
    try:
        # Create standard directories
        (temp_dir / "Assets").mkdir(exist_ok=True)
        (temp_dir / "Assets" / "Scripts").mkdir(exist_ok=True)
        (temp_dir / "Assets" / "Sprites").mkdir(exist_ok=True)
        (temp_dir / "Assets" / "Prefabs").mkdir(exist_ok=True)
        (temp_dir / "Assets" / "Scenes").mkdir(exist_ok=True)
        (temp_dir / "Packages").mkdir(exist_ok=True)
        (temp_dir / "Library").mkdir(exist_ok=True)
        
        # Write project manifest
        manifest_data = get_template_manifest(template_name)
        manifest_path = temp_dir / "project.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=4)
            
        # Write default main scene if template is not empty
        if template_name.lower() == "platformer":
            _create_platformer_scene(temp_dir / "Assets" / "Scenes" / "Main.zscene")
            
        # Move atomically
        if project_root.exists():
             shutil.rmtree(project_root) # it was empty anyway based on check
        shutil.move(str(temp_dir), str(project_root))
        
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def _create_platformer_scene(scene_path: Path) -> None:
    """Cria uma cena base para o template platformer."""
    # Um mock de cena basica para o template.
    scene_data = {
        "name": "Main",
        "objects": [
            {
                "name": "Platform",
                "tag": "Ground",
                "components": [
                    {"type": "Transform", "position": [0, 160, 0], "scale": [320, 24, 1]},
                    {"type": "BoxCollider", "width": 320, "height": 24},
                    {"type": "RigidBody", "is_kinematic": True}
                ]
            },
            {
                "name": "Player",
                "tag": "Player",
                "components": [
                    {"type": "Transform", "position": [0, 40, 0], "scale": [36, 48, 1]},
                    {"type": "BoxCollider", "width": 36, "height": 48},
                    {"type": "RigidBody", "mass": 1.0, "gravity_scale": 1.0}
                ]
            }
        ]
    }
    with open(scene_path, "w", encoding="utf-8") as f:
        json.dump(scene_data, f, indent=4)

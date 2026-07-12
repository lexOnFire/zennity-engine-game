from __future__ import annotations

import json
import shutil
from pathlib import Path


def export_development_project(project_root: Path, scene_path: Path, output_dir: Path, project_name: str) -> Path:
    """Cria uma pasta executável de desenvolvimento baseada no runtime Pygame."""
    safe_name = "".join(char for char in project_name.strip() if char.isalnum() or char in "-_ ").strip() or "ZennityGame"
    destination = output_dir / safe_name
    destination.mkdir(parents=True, exist_ok=True)
    data_dir = destination / "Data"
    runtime_dir = destination / "zennity_runtime"
    data_dir.mkdir(exist_ok=True)
    runtime_dir.mkdir(exist_ok=True)

    shutil.copy2(scene_path, data_dir / "main.zscene")
    assets_source = project_root / "Assets"
    if assets_source.is_dir():
        shutil.copytree(assets_source, destination / "Assets", dirs_exist_ok=True)
    shutil.copy2(project_root / "editor" / "isolated_viewport.py", runtime_dir / "viewport.py")
    (runtime_dir / "__init__.py").write_text("", encoding="utf-8")
    (destination / "main.py").write_text(_launcher_source(), encoding="utf-8")
    (destination / "executar.bat").write_text("@echo off\npython main.py\npause\n", encoding="utf-8")
    (destination / "executar.sh").write_text("#!/usr/bin/env sh\npython3 main.py\n", encoding="utf-8")
    (destination / "requirements.txt").write_text("pygame-ce>=2.5\n", encoding="utf-8")
    manifest = {"project_name": safe_name, "entry_scene": "Data/main.zscene", "runtime": "pygame", "development": True}
    (destination / "package_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return destination


def _launcher_source() -> str:
    return '''from __future__ import annotations

import json
import multiprocessing as mp
import os
from pathlib import Path

from zennity_runtime.viewport import run_viewport


def load_objects(path):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    result = []
    for item in payload.get("objects", []):
        transform = item.get("transform", {})
        position = transform.get("position", [0, 0, 0])
        scale = transform.get("scale", [32, 32, 1])
        rotation = transform.get("rz", transform.get("rotation", [0, 0, 0])[2])
        visual = item.get("visual", {}) or {}
        components = item.get("components", {}) or {}
        obj = {
            "id": item.get("id", item.get("name")), "name": item.get("name", "Object"),
            "x": float(position[0]), "y": float(position[1]), "w": abs(float(scale[0])),
            "h": abs(float(scale[1])), "rotation": float(rotation),
            "color": visual.get("color") or [180, 180, 190], "tag": item.get("tag", "Untagged"),
            "active": item.get("active", True), "scripts": components.get("scripts", []),
            "texture": visual.get("texture", ""), "renderer_enabled": visual.get("enabled", True),
            "render_layer": visual.get("layer", "Default"), "sort_order": visual.get("order", 0),
        }
        for key in ("rigidbody", "collider", "camera", "audio"):
            if key in components:
                obj[key] = components[key]
        obj.update(item.get("editor_data", {}))
        result.append(obj)
    return result


def main():
    os.chdir(Path(__file__).resolve().parent)
    commands, events = mp.Queue(), mp.Queue()
    process = mp.Process(target=run_viewport, args=(commands, events, None, (1280, 720)), daemon=False)
    process.start()
    commands.put({"type": "scene_snapshot", "objects": load_objects("Data/main.zscene")})
    commands.put({"type": "set_view_mode", "mode": "game"})
    commands.put({"type": "play"})
    process.join()


if __name__ == "__main__":
    mp.freeze_support()
    main()
'''

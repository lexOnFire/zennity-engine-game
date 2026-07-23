"""Deprecated compatibility exporter for the legacy editor.

The official editor uses :mod:`engine.build.project_exporter`. This module
keeps the old object-list API working until the legacy window is removed.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import List

from editor.core.serializer import save_scene_to_file
from engine.game_object import GameObject

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = """import sys
import os
import pygame
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from engine.core import Application
from engine.core.scene import Scene
from engine.core.serializer import load_scene_from_file

def main():
    app = Application(800, 600, "Zennity Engine - Standalone Game")
    game_scene = Scene("GameScene")
    scene_file = os.path.join(os.path.dirname(__file__), "scene.zscene")
    if os.path.exists(scene_file):
        try:
            import serializer
            loaded_objs = serializer.load_scene_from_file(scene_file)
            for obj in loaded_objs:
                game_scene.add_game_object(obj)
        except Exception as e:
            print(f"[ERROR] Falha ao carregar cena do jogo: {e}")
    try:
        import script_manager

        def update_system(scene, dt):
            script_manager.ScriptManager.update_all(scene.game_objects, dt)

        app.engine.add_update_system(update_system)
        for obj in game_scene.game_objects:
            if getattr(obj, "script_path", ""):
                script_manager.ScriptManager.load(obj)
    except Exception as e:
        print(f"[WARNING] O gerenciador de scripts falhou ao inicializar: {e}")
    app.run(game_scene)

if __name__ == "__main__":
    main()
"""


def export_project(dest_dir: str, root_objects: List[GameObject]) -> str:
    """Exporta pela API legada; novos consumidores devem usar ``engine.build``."""
    destination = Path(dest_dir)
    destination.mkdir(parents=True, exist_ok=True)
    save_scene_to_file(str(destination / "scene.zscene"), root_objects)
    _replace_tree(PROJECT_ROOT / "engine", destination / "engine")
    _replace_tree(PROJECT_ROOT / "assets", destination / "assets")
    _replace_tree(PROJECT_ROOT / "scripts", destination / "scripts")
    _copy_optional(Path(__file__).with_name("script_manager.py"), destination)
    _copy_optional(Path(__file__).with_name("serializer.py"), destination)
    _write_launchers(destination)
    return str(destination)


def _replace_tree(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def _copy_optional(source: Path, destination: Path) -> None:
    if source.exists():
        shutil.copy2(source, destination / source.name)


def _write_launchers(destination: Path) -> None:
    (destination / "main_standalone.py").write_text(LAUNCHER, encoding="utf-8")
    (destination / "jogar.bat").write_text(
        "@echo off\npython main_standalone.py\npause\n", encoding="utf-8"
    )
    shell_launcher = destination / "jogar.sh"
    shell_launcher.write_text("#!/bin/bash\npython3 main_standalone.py\n", encoding="utf-8")
    try:
        os.chmod(shell_launcher, 0o755)
    except OSError:
        pass

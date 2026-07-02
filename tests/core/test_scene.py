"""
tests/core/test_scene.py
Testes de ciclo de vida da Scene e integração com GameObject.
"""
import os, sys
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest


class TestScene:
    def test_scene_starts_empty(self):
        from engine.core import Scene
        scene = Scene(name="Test")
        assert len(scene.game_objects) == 0
        assert scene.name == "Test"

    def test_add_game_object(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = GameObject("Player")
        scene.add_game_object(go)
        assert go in scene.game_objects
        assert go.scene is scene

    def test_no_duplicate_game_objects(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = GameObject("Player")
        scene.add_game_object(go)
        scene.add_game_object(go)  # segunda chamada deve ser ignorada
        assert scene.game_objects.count(go) == 1

    def test_remove_game_object(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = GameObject("Enemy")
        scene.add_game_object(go)
        scene.remove_game_object(go)
        assert go not in scene.game_objects
        assert go.scene is None

    def test_find_by_name(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = GameObject("Boss")
        scene.add_game_object(go)
        assert scene.find("Boss") is go
        assert scene.find("Missing") is None

    def test_find_by_tag(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        e1 = GameObject("Enemy1", tag="Enemy")
        e2 = GameObject("Enemy2", tag="Enemy")
        p  = GameObject("Player", tag="Player")
        for go in (e1, e2, p):
            scene.add_game_object(go)
        enemies = scene.find_by_tag("Enemy")
        assert len(enemies) == 2
        assert p not in enemies

    def test_scene_repr(self):
        from engine.core import Scene
        scene = Scene(name="GameScene")
        assert "GameScene" in repr(scene)

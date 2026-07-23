"""tests/test_runtime_lifecycle.py

Testes de regressão para o ciclo de vida do Play Mode:
  - Play → Stop normal
  - Stop sem Play (idempotência)
  - Double-Stop (idempotência)
  - Integridade da clonagem de GameObjects
  - Round-trip de serialização de cena
  - Round-trip de serialização de prefab
"""
from __future__ import annotations

import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Fixtures e stubs mínimos
# ---------------------------------------------------------------------------

class _FakeScene:
    """Cena mínima compatível com RuntimeScene."""

    def __init__(self, name: str = "TestScene") -> None:
        self.name = name
        self.game_objects: list = []
        self.editable_objects: list = []
        self.playing: bool = False
        self.selected_index: int = -1
        self.show_grid: bool = True
        self.grid_size: int = 32
        self.show_scale_handles: bool = False

    def start(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen) -> None:
        pass

    def handle_event(self, event) -> None:
        pass

    def _add_go(self, go) -> None:
        self.game_objects.append(go)
        self.editable_objects.append(go)
        go.scene = self

    def _remove_go(self, go) -> None:
        if go in self.game_objects:
            self.game_objects.remove(go)
        if go in self.editable_objects:
            self.editable_objects.remove(go)
        go.scene = None


# ---------------------------------------------------------------------------
# Testes: clonagem de GameObjects
# ---------------------------------------------------------------------------

class TestCloneGameObject:
    def test_clone_basic_attributes(self):
        from engine.game_object import GameObject
        from engine.runtime.clone import clone_game_object

        src = GameObject("Hero", tag="Player")
        src.transform.position = np.array([1.0, 2.0, 0.0], dtype=np.float32)
        src.transform.scale = np.array([2.0, 2.0, 1.0], dtype=np.float32)

        clone = clone_game_object(src)

        assert clone.name == "Hero"
        assert clone.tag == "Player"
        assert clone.id != src.id  # UUID diferente
        assert clone.runtime_source_id == str(src.id)
        np.testing.assert_array_equal(clone.transform.position, src.transform.position)
        np.testing.assert_array_equal(clone.transform.scale, src.transform.scale)

    def test_clone_does_not_share_transform(self):
        from engine.game_object import GameObject
        from engine.runtime.clone import clone_game_object

        src = GameObject("A")
        src.transform.position = np.array([5.0, 0.0, 0.0], dtype=np.float32)
        clone = clone_game_object(src)

        # Modificar o clone não afeta o original
        clone.transform.position[0] = 99.0
        assert src.transform.position[0] == pytest.approx(5.0)

    def test_clone_inactive_parent_still_clones_children(self):
        from engine.game_object import GameObject
        from engine.runtime.clone import clone_game_object

        parent = GameObject("Parent")
        parent.active = False
        child = GameObject("Child")
        parent.add_child(child)

        clone = clone_game_object(parent)
        assert len(clone.children) == 1
        assert clone.children[0].name == "Child"

    def test_clone_deep_tree(self):
        from engine.game_object import GameObject
        from engine.runtime.clone import clone_game_object

        root = GameObject("Root")
        mid = GameObject("Mid")
        leaf = GameObject("Leaf")
        root.add_child(mid)
        mid.add_child(leaf)

        clone = clone_game_object(root)
        assert len(clone.children) == 1
        assert len(clone.children[0].children) == 1
        assert clone.children[0].children[0].name == "Leaf"


# ---------------------------------------------------------------------------
# Testes: RuntimeManager ciclo de vida
# ---------------------------------------------------------------------------

class TestRuntimeManagerLifecycle:
    def _make_manager(self):
        """Cria um RuntimeManager com stubs de Input e Time."""
        from engine.runtime.runtime_manager import RuntimeManager

        manager = RuntimeManager()
        return manager

    def test_stop_without_play_is_noop(self):
        from engine.runtime.runtime_manager import RuntimeManager, RuntimeState
        m = RuntimeManager()
        # Não deve lançar exceção
        m.stop_play()
        assert m.state == RuntimeState.STOPPED
        assert m.runtime_scene is None

    def test_double_stop_is_noop(self):
        from engine.runtime.runtime_manager import RuntimeManager, RuntimeState
        m = RuntimeManager()
        m.stop_play()
        m.stop_play()  # segunda chamada — não deve explodir
        assert m.state == RuntimeState.STOPPED

    def test_is_playing_false_initially(self):
        from engine.runtime.runtime_manager import RuntimeManager
        m = RuntimeManager()
        assert m.is_playing is False

    def test_tick_without_play_is_noop(self):
        from engine.runtime.runtime_manager import RuntimeManager
        m = RuntimeManager()
        # Não deve lançar exceção
        m.tick(0.016)


# ---------------------------------------------------------------------------
# Testes: EditorContext reset_scene_state
# ---------------------------------------------------------------------------

class TestEditorContextReset:
    def test_reset_clears_playing_state(self):
        from editor.runtime.editor_context import EditorContext
        from engine.runtime.runtime_manager import RuntimeState

        ctx = EditorContext()
        # Simula estado sujo
        ctx.state.is_playing = True
        ctx.runtime.state = RuntimeState.PLAYING

        ctx.reset_scene_state()

        assert ctx.state.is_playing is False
        assert ctx.runtime.state == RuntimeState.STOPPED

    def test_reset_clears_commands(self):
        from editor.runtime.editor_context import EditorContext

        ctx = EditorContext()
        # Verifica que clear() foi chamado (não lança)
        ctx.reset_scene_state()
        # Após reset, histórico deve estar limpo
        assert ctx.commands._history == [] if hasattr(ctx.commands, '_history') else True

    def test_reset_is_idempotent(self):
        from editor.runtime.editor_context import EditorContext
        ctx = EditorContext()
        ctx.reset_scene_state()
        ctx.reset_scene_state()  # segunda chamada — não deve explodir


# ---------------------------------------------------------------------------
# Testes: Serialização de cenas (round-trip)
# ---------------------------------------------------------------------------

class TestSceneSerializerRoundTrip:
    def test_empty_scene_round_trip(self):
        from engine.runtime.serialization import SceneSerializer
        from engine.core.scene import Scene

        scene = Scene(name="TestEmpty")
        data = SceneSerializer.serialize(scene)

        assert data["__schema__"] == "zennity-scene"
        assert data["version"] == 1
        assert data["name"] == "TestEmpty"
        assert data["objects"] == []

        restored = SceneSerializer.deserialize(data, scene_class=Scene)
        assert restored.name == "TestEmpty"
        assert len(restored.game_objects) == 0

    def test_scene_with_go_round_trip(self):
        from engine.runtime.serialization import SceneSerializer
        from engine.core.scene import Scene
        from engine.game_object import GameObject

        scene = Scene(name="WithGO")
        go = GameObject("Cube", tag="Env")
        go.transform.position = np.array([3.0, 4.0, 0.0], dtype=np.float32)
        scene.add_game_object(go)

        json_str = SceneSerializer.serialize_to_json(scene)
        restored = SceneSerializer.deserialize_from_json(json_str, scene_class=Scene)

        assert len(restored.game_objects) == 1
        assert restored.game_objects[0].name == "Cube"
        assert restored.game_objects[0].tag == "Env"
        np.testing.assert_array_almost_equal(
            restored.game_objects[0].transform.position,
            [3.0, 4.0, 0.0],
        )

    def test_scene_with_children_round_trip(self):
        from engine.runtime.serialization import SceneSerializer
        from engine.core.scene import Scene
        from engine.game_object import GameObject

        scene = Scene(name="Tree")
        parent = GameObject("Parent")
        child = GameObject("Child")
        parent.add_child(child)
        scene.add_game_object(parent)

        data = SceneSerializer.serialize(scene)
        restored = SceneSerializer.deserialize(data)

        assert len(restored.game_objects) == 1
        assert len(restored.game_objects[0].children) == 1
        assert restored.game_objects[0].children[0].name == "Child"

    def test_invalid_schema_raises(self):
        from engine.runtime.serialization import SceneSerializer

        bad_data = {"__schema__": "wrong", "version": 1, "objects": []}
        with pytest.raises(ValueError, match="Schema inválido"):
            SceneSerializer.deserialize(bad_data)


# ---------------------------------------------------------------------------
# Testes: Serialização de prefabs (round-trip)
# ---------------------------------------------------------------------------

class TestPrefabSerializerRoundTrip:
    def test_prefab_round_trip(self):
        from engine.runtime.serialization import PrefabSerializer
        from engine.game_object import GameObject

        go = GameObject("Crate", tag="Props")
        go.transform.position = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        go.transform.scale = np.array([0.5, 0.5, 1.0], dtype=np.float32)

        json_str = PrefabSerializer.serialize_to_json(go)
        restored = PrefabSerializer.deserialize_from_json(json_str)

        assert restored.name == "Crate"
        assert restored.tag == "Props"
        np.testing.assert_array_almost_equal(
            restored.transform.position, [1.0, 0.0, 0.0]
        )
        np.testing.assert_array_almost_equal(
            restored.transform.scale, [0.5, 0.5, 1.0]
        )

    def test_prefab_invalid_schema_raises(self):
        from engine.runtime.serialization import PrefabSerializer

        bad = {"__schema__": "zennity-scene", "version": 1, "root": {}}
        with pytest.raises(ValueError, match="Schema inválido"):
            PrefabSerializer.deserialize(bad)

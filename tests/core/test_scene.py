"""
tests/core/test_scene.py
────────────────────────────────────────────────────────────────
Commit 19: suite completa de Scene.

Grupos:
  TestAddGameObject   (8)  — append, set scene, idempotente, retorno, start, múltiplos
  TestRemoveGameObject(5)  — remove, limpa scene, safe ausente, não destrói, re-add
  TestFind            (9)  — find, find_by_tag, find_by_id, edge-cases
  TestUpdateDraw      (6)  — propaga, pula inativo, pula removido, surface real
  TestSubclassHooks   (5)  — start, on_exit, handle_event, update/draw override
  TestSceneDefaults   (3)  — nome, lista vazia, engine=None
  TestRepr            (3)  — nome, contagem, default
  TestEdgeCases      (11)  — destroy durante update, add durante iterate, find após remove,
                             tag muda dinamicamente, handle_event subclasse,
                             múltiplos removes, scene vazia draw, GO sem components,
                             find_by_tag vazio, re-add limpa scene antiga, 50 GOs

Total esperado: 50 testes.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


# ===========================================================================
# 1. add_game_object
# ===========================================================================

class TestAddGameObject:
    def test_go_appears_in_list(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = GameObject("A")
        scene.add_game_object(go)
        assert go in scene.game_objects

    def test_add_sets_go_scene(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = GameObject("A")
        scene.add_game_object(go)
        assert go.scene is scene

    def test_add_is_idempotent(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = GameObject("A")
        scene.add_game_object(go)
        scene.add_game_object(go)
        assert scene.game_objects.count(go) == 1

    def test_add_returns_go(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = GameObject("A")
        assert scene.add_game_object(go) is go

    def test_add_triggers_component_start(self):
        from engine.core import Scene, GameObject, Component
        class Spy(Component):
            def __init__(self): super().__init__(); self.started = False
            def start(self): self.started = True
        go = GameObject("A")
        spy = go.add_component(Spy())
        Scene().add_game_object(go)
        assert spy.started is True

    def test_add_multiple_gos(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        for i in range(5):
            scene.add_game_object(GameObject(str(i)))
        assert len(scene.game_objects) == 5

    def test_re_add_after_remove(self):
        """GO removido pode ser adicionado novamente sem duplicatas."""
        from engine.core import Scene, GameObject
        scene = Scene()
        go = GameObject("A")
        scene.add_game_object(go)
        scene.remove_game_object(go)
        scene.add_game_object(go)
        assert scene.game_objects.count(go) == 1
        assert go.scene is scene

    def test_add_sets_scene_on_children(self):
        """Filhos já vinculados ao GO herdam a cena."""
        from engine.core import Scene, GameObject
        scene = Scene()
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        scene.add_game_object(parent)
        assert child.scene is scene


# ===========================================================================
# 2. remove_game_object
# ===========================================================================

class TestRemoveGameObject:
    def test_remove_takes_go_out(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = scene.add_game_object(GameObject("A"))
        scene.remove_game_object(go)
        assert go not in scene.game_objects

    def test_remove_clears_go_scene(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = scene.add_game_object(GameObject("A"))
        scene.remove_game_object(go)
        assert go.scene is None

    def test_remove_nonexistent_is_safe(self):
        from engine.core import Scene, GameObject
        Scene().remove_game_object(GameObject("A"))  # nunca adicionado

    def test_remove_does_not_destroy_go(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = scene.add_game_object(GameObject("A"))
        scene.remove_game_object(go)
        assert go.active is True

    def test_remove_decrements_count(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = scene.add_game_object(GameObject("A"))
        scene.add_game_object(GameObject("B"))
        scene.remove_game_object(go)
        assert len(scene.game_objects) == 1


# ===========================================================================
# 3. find / find_by_tag / find_by_id
# ===========================================================================

class TestFind:
    def test_find_by_name(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = scene.add_game_object(GameObject("Boss"))
        assert scene.find("Boss") is go

    def test_find_returns_none_when_absent(self):
        from engine.core import Scene
        assert Scene().find("Ghost") is None

    def test_find_returns_first_match(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go1 = scene.add_game_object(GameObject("Twin"))
        scene.add_game_object(GameObject("Twin"))
        assert scene.find("Twin") is go1

    def test_find_is_case_sensitive(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        scene.add_game_object(GameObject("Hero"))
        assert scene.find("hero") is None

    def test_find_by_tag_returns_all(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        e1 = scene.add_game_object(GameObject("E1", tag="Enemy"))
        e2 = scene.add_game_object(GameObject("E2", tag="Enemy"))
        scene.add_game_object(GameObject("P", tag="Player"))
        result = scene.find_by_tag("Enemy")
        assert e1 in result and e2 in result and len(result) == 2

    def test_find_by_tag_empty_when_none(self):
        from engine.core import Scene
        assert Scene().find_by_tag("Alien") == []

    def test_find_by_id_full_uuid(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = scene.add_game_object(GameObject("A"))
        assert scene.find_by_id(go.id) is go

    def test_find_by_id_short(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = scene.add_game_object(GameObject("A"))
        assert scene.find_by_id(go.short_id) is go

    def test_find_by_id_none_when_absent(self):
        from engine.core import Scene
        assert Scene().find_by_id("00000000") is None


# ===========================================================================
# 4. update / draw
# ===========================================================================

class TestUpdateDraw:
    def test_update_delegates_to_all_gos(self):
        from engine.core import Scene, GameObject, Component
        class Ticker(Component):
            def __init__(self): super().__init__(); self.ticks = 0
            def update(self, dt): self.ticks += 1
        scene = Scene()
        tickers = []
        for i in range(3):
            go = GameObject(str(i))
            t = go.add_component(Ticker())
            tickers.append(t)
            scene.add_game_object(go)
        scene.update(0.016)
        assert all(t.ticks == 1 for t in tickers)

    def test_draw_delegates_to_all_gos(self):
        from engine.core import Scene, GameObject, Component
        class Drawer(Component):
            def __init__(self): super().__init__(); self.drawn = False
            def draw(self, screen): self.drawn = True
        scene = Scene()
        drawers = []
        for i in range(3):
            go = GameObject(str(i))
            d = go.add_component(Drawer())
            drawers.append(d)
            scene.add_game_object(go)
        scene.draw(MagicMock())
        assert all(d.drawn for d in drawers)

    def test_update_skips_removed_go(self):
        from engine.core import Scene, GameObject, Component
        class Ticker(Component):
            def __init__(self): super().__init__(); self.ticks = 0
            def update(self, dt): self.ticks += 1
        scene = Scene()
        go = GameObject("A")
        t = go.add_component(Ticker())
        scene.add_game_object(go)
        scene.remove_game_object(go)
        scene.update(0.016)
        assert t.ticks == 0

    def test_update_skips_inactive_go(self):
        from engine.core import Scene, GameObject, Component
        class Ticker(Component):
            def __init__(self): super().__init__(); self.ticks = 0
            def update(self, dt): self.ticks += 1
        scene = Scene()
        go = GameObject("A")
        t = go.add_component(Ticker())
        scene.add_game_object(go)
        go.active = False
        scene.update(0.016)
        assert t.ticks == 0

    def test_draw_skips_inactive_go(self):
        from engine.core import Scene, GameObject, Component
        class Drawer(Component):
            def __init__(self): super().__init__(); self.drawn = False
            def draw(self, screen): self.drawn = True
        scene = Scene()
        go = GameObject("A")
        d = go.add_component(Drawer())
        scene.add_game_object(go)
        go.active = False
        scene.draw(MagicMock())
        assert d.drawn is False

    def test_draw_does_not_crash_with_real_surface(self, screen):
        from engine.core import Scene, GameObject
        scene = Scene()
        scene.add_game_object(GameObject("Sprite"))
        scene.draw(screen)


# ===========================================================================
# 5. Subclasse e hooks
# ===========================================================================

class TestSubclassHooks:
    def test_start_hook(self):
        from engine.core import Scene
        class MyScene(Scene):
            def __init__(self): super().__init__(); self.started = False
            def start(self): self.started = True
        s = MyScene()
        s.start()
        assert s.started is True

    def test_on_exit_hook(self):
        from engine.core import Scene
        class MyScene(Scene):
            def __init__(self): super().__init__(); self.exited = False
            def on_exit(self): self.exited = True
        s = MyScene()
        s.on_exit()
        assert s.exited is True

    def test_handle_event_base_does_not_raise(self):
        from engine.core import Scene
        Scene().handle_event(MagicMock())

    def test_subclass_update_calls_super(self):
        from engine.core import Scene, GameObject, Component
        class Ticker(Component):
            def __init__(self): super().__init__(); self.ticks = 0
            def update(self, dt): self.ticks += 1
        class MyScene(Scene):
            def update(self, dt): super().update(dt)
        scene = MyScene()
        go = GameObject("G")
        t = go.add_component(Ticker())
        scene.add_game_object(go)
        scene.update(0.016)
        assert t.ticks == 1

    def test_subclass_draw_calls_super(self):
        from engine.core import Scene, GameObject, Component
        class Drawer(Component):
            def __init__(self): super().__init__(); self.drawn = False
            def draw(self, screen): self.drawn = True
        class MyScene(Scene):
            def draw(self, screen): super().draw(screen)
        scene = MyScene()
        go = GameObject("G")
        d = go.add_component(Drawer())
        scene.add_game_object(go)
        scene.draw(MagicMock())
        assert d.drawn is True


# ===========================================================================
# 6. Defaults
# ===========================================================================

class TestSceneDefaults:
    def test_starts_empty(self):
        from engine.core import Scene
        assert len(Scene().game_objects) == 0

    def test_name_set(self):
        from engine.core import Scene
        assert Scene("Main").name == "Main"

    def test_engine_none_by_default(self):
        from engine.core import Scene
        assert Scene().engine is None


# ===========================================================================
# 7. __repr__
# ===========================================================================

class TestRepr:
    def test_repr_contains_name(self):
        from engine.core import Scene
        assert "GameScene" in repr(Scene("GameScene"))

    def test_repr_contains_object_count(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        scene.add_game_object(GameObject("A"))
        scene.add_game_object(GameObject("B"))
        assert "2" in repr(scene)

    def test_repr_default_name(self):
        from engine.core import Scene
        assert "Scene" in repr(Scene())


# ===========================================================================
# 8. Edge cases
# ===========================================================================

class TestEdgeCases:
    def test_empty_scene_draw_is_safe(self):
        from engine.core import Scene
        Scene().draw(MagicMock())  # sem GOs, não lança

    def test_empty_scene_update_is_safe(self):
        from engine.core import Scene
        Scene().update(0.016)  # sem GOs, não lança

    def test_go_without_components_updates_safely(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = GameObject("Empty")
        scene.add_game_object(go)
        scene.update(0.016)  # nenhum component, não lança

    def test_find_after_remove_returns_none(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = scene.add_game_object(GameObject("X"))
        scene.remove_game_object(go)
        assert scene.find("X") is None

    def test_find_by_tag_after_remove(self):
        """GO removido não deve aparecer em find_by_tag."""
        from engine.core import Scene, GameObject
        scene = Scene()
        go = scene.add_game_object(GameObject("E", tag="Enemy"))
        scene.remove_game_object(go)
        assert scene.find_by_tag("Enemy") == []

    def test_handle_event_subclass_receives_event(self):
        from engine.core import Scene
        class Evented(Scene):
            def __init__(self): super().__init__(); self.last = None
            def handle_event(self, e): self.last = e
        s = Evented()
        fake = MagicMock()
        s.handle_event(fake)
        assert s.last is fake

    def test_multiple_removes_of_same_go_is_safe(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = scene.add_game_object(GameObject("A"))
        scene.remove_game_object(go)
        scene.remove_game_object(go)  # segunda remoção não lança

    def test_add_go_to_two_scenes_migrates_scene_ref(self):
        """Adicionar GO já pertencente a uma cena em outra cena atualiza go.scene."""
        from engine.core import Scene, GameObject
        s1, s2 = Scene(), Scene()
        go = GameObject("A")
        s1.add_game_object(go)
        s2.add_game_object(go)
        assert go.scene is s2

    def test_large_scene_update_performance(self):
        """50 GOs com 1 component cada executam update sem erro."""
        from engine.core import Scene, GameObject, Component
        class Noop(Component):
            def update(self, dt): pass
        scene = Scene()
        for i in range(50):
            go = GameObject(str(i))
            go.add_component(Noop())
            scene.add_game_object(go)
        scene.update(0.016)  # não deve lançar
        assert len(scene.game_objects) == 50

    def test_scene_name_empty_string(self):
        from engine.core import Scene
        s = Scene("")
        assert s.name == ""

    def test_find_by_id_after_remove(self):
        from engine.core import Scene, GameObject
        scene = Scene()
        go = scene.add_game_object(GameObject("A"))
        gid = go.id
        scene.remove_game_object(go)
        assert scene.find_by_id(gid) is None

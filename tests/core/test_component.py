"""
tests/core/test_component.py
────────────────────────────────────────────────────────────────
Commit 15: suite completa de Component e Transform.

Grupos:
  TestComponentDefaults   (4)  — estado inicial, game_object, _started
  TestComponentLifecycle  (6)  — start() uma vez, update, draw, destroy
  TestComponentShortcuts  (4)  — .transform, .scene atalhos
  TestComponentRepr       (3)  — repr detached/attached/started
  TestTransformDefaults   (6)  — pos/rot/scale iniciais, arrays np.float32
  TestTransformPosition   (6)  — x/y/z setters, position setter, translate
  TestTransformRotation   (5)  — rx/ry/rz setters, rotation setter, rotate
  TestTransformScale      (5)  — sx/sy/sz setters, scale setter
  TestTransformWorld      (4)  — world_position local vs hierárquico
  TestTransformRepr       (3)  — repr formato correto
  TestStartGuarantee      (4)  — start() chamado 1× em cenários diferentes

Total esperado: 50 testes.
"""
from __future__ import annotations

import pytest
import numpy as np
from unittest.mock import MagicMock


# ===========================================================================
# 1. Component — Defaults
# ===========================================================================

class TestComponentDefaults:
    def test_not_started_by_default(self):
        from engine.core import Component
        assert Component()._started is False

    def test_game_object_none_by_default(self):
        from engine.core import Component
        assert Component().game_object is None

    def test_attached_after_add_component(self):
        from engine.core import Component, GameObject
        go = GameObject("GO")
        comp = go.add_component(Component())
        assert comp.game_object is go

    def test_detached_after_remove_component(self):
        from engine.core import Component, GameObject
        go = GameObject("GO")
        comp = go.add_component(Component())
        go.remove_component(comp)
        assert comp.game_object is None


# ===========================================================================
# 2. Component — Ciclo de vida
# ===========================================================================

class TestComponentLifecycle:
    def test_start_called_once_when_added_to_scene(self):
        from engine.core import Component, GameObject, Scene
        class Counter(Component):
            def __init__(self): super().__init__(); self.calls = 0
            def start(self): self.calls += 1
        scene = Scene()
        go = GameObject("G")
        c = go.add_component(Counter())
        scene.add_game_object(go)
        assert c.calls == 1

    def test_start_not_called_twice(self):
        from engine.core import Component, GameObject, Scene
        class Counter(Component):
            def __init__(self): super().__init__(); self.calls = 0
            def start(self): self.calls += 1
        scene = Scene()
        go = GameObject("G")
        c = go.add_component(Counter())
        scene.add_game_object(go)
        go.start()  # chamada manual extra
        assert c.calls == 1

    def test_update_called_on_tick(self):
        from engine.core import Component, GameObject
        class Ticker(Component):
            def __init__(self): super().__init__(); self.ticks = 0
            def update(self, dt): self.ticks += 1
        go = GameObject("G")
        t = go.add_component(Ticker())
        go.update(0.016)
        assert t.ticks == 1

    def test_draw_called_on_tick(self):
        from engine.core import Component, GameObject
        class Drawer(Component):
            def __init__(self): super().__init__(); self.drawn = False
            def draw(self, screen): self.drawn = True
        go = GameObject("G")
        d = go.add_component(Drawer())
        go.draw(MagicMock())
        assert d.drawn is True

    def test_destroy_called_on_remove(self):
        from engine.core import Component, GameObject
        class Spy(Component):
            def __init__(self): super().__init__(); self.destroyed = False
            def destroy(self): self.destroyed = True
        go = GameObject("G")
        spy = go.add_component(Spy())
        go.remove_component(spy)
        assert spy.destroyed is True

    def test_started_flag_set_after_start(self):
        from engine.core import Component, GameObject, Scene
        scene = Scene()
        go = GameObject("G")
        comp = go.add_component(Component())
        scene.add_game_object(go)
        assert comp._started is True


# ===========================================================================
# 3. Component — Atalhos
# ===========================================================================

class TestComponentShortcuts:
    def test_transform_shortcut_returns_go_transform(self):
        from engine.core import Component, GameObject, Transform
        go = GameObject("G")
        comp = go.add_component(Component())
        assert comp.transform is go.transform

    def test_transform_shortcut_raises_if_detached(self):
        from engine.core import Component
        comp = Component()
        with pytest.raises(AssertionError):
            _ = comp.transform

    def test_scene_shortcut_none_without_scene(self):
        from engine.core import Component, GameObject
        go = GameObject("G")
        comp = go.add_component(Component())
        assert comp.scene is None

    def test_scene_shortcut_returns_scene(self):
        from engine.core import Component, GameObject, Scene
        scene = Scene()
        go = GameObject("G")
        comp = go.add_component(Component())
        scene.add_game_object(go)
        assert comp.scene is scene


# ===========================================================================
# 4. Component — repr
# ===========================================================================

class TestComponentRepr:
    def test_repr_detached(self):
        from engine.core import Component
        assert "detached" in repr(Component())

    def test_repr_attached_contains_go_name(self):
        from engine.core import Component, GameObject
        go = GameObject("Hero")
        comp = go.add_component(Component())
        assert "Hero" in repr(comp)

    def test_repr_contains_started_flag(self):
        from engine.core import Component, GameObject, Scene
        scene = Scene()
        go = GameObject("G")
        comp = go.add_component(Component())
        scene.add_game_object(go)
        assert "started=True" in repr(comp)


# ===========================================================================
# 5. Transform — Defaults
# ===========================================================================

class TestTransformDefaults:
    def test_position_defaults_zero(self):
        from engine.core import Transform
        t = Transform()
        assert t.x == pytest.approx(0.0)
        assert t.y == pytest.approx(0.0)
        assert t.z == pytest.approx(0.0)

    def test_rotation_defaults_zero(self):
        from engine.core import Transform
        t = Transform()
        assert t.rx == pytest.approx(0.0)
        assert t.ry == pytest.approx(0.0)
        assert t.rz == pytest.approx(0.0)

    def test_scale_defaults_one(self):
        from engine.core import Transform
        t = Transform()
        assert t.sx == pytest.approx(1.0)
        assert t.sy == pytest.approx(1.0)
        assert t.sz == pytest.approx(1.0)

    def test_position_is_float32(self):
        from engine.core import Transform
        t = Transform()
        assert t.position.dtype == np.float32

    def test_rotation_is_float32(self):
        from engine.core import Transform
        t = Transform()
        assert t.rotation.dtype == np.float32

    def test_scale_is_float32(self):
        from engine.core import Transform
        t = Transform()
        assert t.scale.dtype == np.float32


# ===========================================================================
# 6. Transform — Posição
# ===========================================================================

class TestTransformPosition:
    def test_x_setter(self):
        from engine.core import Transform
        t = Transform()
        t.x = 42.0
        assert t.x == pytest.approx(42.0)

    def test_y_setter(self):
        from engine.core import Transform
        t = Transform()
        t.y = -7.5
        assert t.y == pytest.approx(-7.5)

    def test_z_setter(self):
        from engine.core import Transform
        t = Transform()
        t.z = 3.0
        assert t.z == pytest.approx(3.0)

    def test_position_setter(self):
        from engine.core import Transform
        t = Transform()
        t.position = [100, 200, 0]
        assert t.x == pytest.approx(100.0)
        assert t.y == pytest.approx(200.0)

    def test_translate_moves_position(self):
        from engine.core import Transform
        t = Transform(x=10, y=5)
        t.translate(3, -2)
        assert t.x == pytest.approx(13.0)
        assert t.y == pytest.approx(3.0)

    def test_translate_accumulates(self):
        from engine.core import Transform
        t = Transform()
        t.translate(5, 0)
        t.translate(5, 0)
        assert t.x == pytest.approx(10.0)


# ===========================================================================
# 7. Transform — Rotação
# ===========================================================================

class TestTransformRotation:
    def test_rz_setter(self):
        from engine.core import Transform
        t = Transform()
        t.rz = 90.0
        assert t.rz == pytest.approx(90.0)

    def test_rx_setter(self):
        from engine.core import Transform
        t = Transform()
        t.rx = 45.0
        assert t.rx == pytest.approx(45.0)

    def test_ry_setter(self):
        from engine.core import Transform
        t = Transform()
        t.ry = -30.0
        assert t.ry == pytest.approx(-30.0)

    def test_rotation_setter(self):
        from engine.core import Transform
        t = Transform()
        t.rotation = [10, 20, 30]
        assert t.rx == pytest.approx(10.0)
        assert t.ry == pytest.approx(20.0)
        assert t.rz == pytest.approx(30.0)

    def test_rotate_accumulates(self):
        from engine.core import Transform
        t = Transform()
        t.rotate(0, 0, 45)
        t.rotate(0, 0, 45)
        assert t.rz == pytest.approx(90.0)


# ===========================================================================
# 8. Transform — Escala
# ===========================================================================

class TestTransformScale:
    def test_sx_setter(self):
        from engine.core import Transform
        t = Transform()
        t.sx = 2.0
        assert t.sx == pytest.approx(2.0)

    def test_sy_setter(self):
        from engine.core import Transform
        t = Transform()
        t.sy = 0.5
        assert t.sy == pytest.approx(0.5)

    def test_sz_setter(self):
        from engine.core import Transform
        t = Transform()
        t.sz = 3.0
        assert t.sz == pytest.approx(3.0)

    def test_scale_setter(self):
        from engine.core import Transform
        t = Transform()
        t.scale = [2, 3, 4]
        assert t.sx == pytest.approx(2.0)
        assert t.sy == pytest.approx(3.0)
        assert t.sz == pytest.approx(4.0)

    def test_scale_defaults_independent_axes(self):
        from engine.core import Transform
        t = Transform(sx=2.0, sy=3.0, sz=4.0)
        assert t.sx == pytest.approx(2.0)
        assert t.sy == pytest.approx(3.0)
        assert t.sz == pytest.approx(4.0)


# ===========================================================================
# 9. Transform — World position
# ===========================================================================

class TestTransformWorld:
    def test_world_position_equals_local_without_parent(self):
        from engine.core import GameObject
        go = GameObject("G")
        go.transform.x = 10
        go.transform.y = 20
        wp = go.transform.world_position
        assert float(wp[0]) == pytest.approx(10.0)
        assert float(wp[1]) == pytest.approx(20.0)

    def test_world_position_accumulates_parent(self):
        from engine.core import GameObject
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        parent.transform.x = 100
        child.transform.x  = 10
        wp = child.transform.world_position
        assert float(wp[0]) == pytest.approx(110.0)

    def test_world_rotation_accumulates_parent(self):
        from engine.core import GameObject
        parent = GameObject("P")
        child  = GameObject("C")
        parent.add_child(child)
        parent.transform.rz = 30
        child.transform.rz  = 15
        wr = child.transform.world_rotation
        assert float(wr[2]) == pytest.approx(45.0)

    def test_get_world_position_alias(self):
        from engine.core import GameObject
        go = GameObject("G")
        go.transform.x = 5
        assert float(go.transform.get_world_position()[0]) == pytest.approx(5.0)


# ===========================================================================
# 10. Transform — repr
# ===========================================================================

class TestTransformRepr:
    def test_repr_contains_position(self):
        from engine.core import Transform
        t = Transform(x=5, y=3)
        r = repr(t)
        assert "5.0" in r and "3.0" in r

    def test_repr_contains_rotation(self):
        from engine.core import Transform
        t = Transform(rz=45)
        assert "45.0" in repr(t)

    def test_repr_detached(self):
        from engine.core import Transform
        t = Transform()
        assert "detached" in repr(t)


# ===========================================================================
# 11. Garantia de start()
# ===========================================================================

class TestStartGuarantee:
    def test_start_not_called_before_scene(self):
        from engine.core import Component, GameObject
        class Spy(Component):
            def __init__(self): super().__init__(); self.calls = 0
            def start(self): self.calls += 1
        go = GameObject("G")
        spy = go.add_component(Spy())
        assert spy.calls == 0

    def test_start_called_when_scene_assigned(self):
        from engine.core import Component, GameObject, Scene
        class Spy(Component):
            def __init__(self): super().__init__(); self.calls = 0
            def start(self): self.calls += 1
        go = GameObject("G")
        spy = go.add_component(Spy())
        go.scene = Scene()
        assert spy.calls == 1

    def test_start_not_duplicated_on_add_game_object(self):
        from engine.core import Component, GameObject, Scene
        class Spy(Component):
            def __init__(self): super().__init__(); self.calls = 0
            def start(self): self.calls += 1
        scene = Scene()
        go = GameObject("G")
        spy = go.add_component(Spy())
        scene.add_game_object(go)
        scene.add_game_object(go)  # duplicata
        assert spy.calls == 1

    def test_component_added_after_scene_starts_immediately(self):
        from engine.core import Component, GameObject, Scene
        class Spy(Component):
            def __init__(self): super().__init__(); self.calls = 0
            def start(self): self.calls += 1
        scene = Scene()
        go = GameObject("G")
        scene.add_game_object(go)
        spy = go.add_component(Spy())
        assert spy.calls == 1

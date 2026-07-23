"""
tests/core/test_transform.py
────────────────────────────────────────────────────────────────
Commit 5: cobertura complementar de Transform e Component.
test_component.py já cobre defaults, translate e start-once.
Este arquivo cobre o restante da API.
"""
from __future__ import annotations
import pytest
import numpy as np


# ===========================================================================
# Transform — setters individuais
# ===========================================================================

class TestTransformSetters:
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

    def test_rz_setter(self):
        from engine.core import Transform
        t = Transform()
        t.rz = 90.0
        assert t.rz == pytest.approx(90.0)

    def test_sx_setter(self):
        from engine.core import Transform
        t = Transform()
        t.sx = 2.5
        assert t.sx == pytest.approx(2.5)

    def test_sy_setter(self):
        from engine.core import Transform
        t = Transform()
        t.sy = 0.5
        assert t.sy == pytest.approx(0.5)

    def test_position_setter_array(self):
        from engine.core import Transform
        t = Transform()
        t.position = [10.0, 20.0, 30.0]
        assert t.x == pytest.approx(10.0)
        assert t.y == pytest.approx(20.0)
        assert t.z == pytest.approx(30.0)

    def test_scale_setter_array(self):
        from engine.core import Transform
        t = Transform()
        t.scale = [2.0, 3.0, 4.0]
        assert t.sx == pytest.approx(2.0)
        assert t.sy == pytest.approx(3.0)
        assert t.sz == pytest.approx(4.0)

    def test_rotation_setter_array(self):
        from engine.core import Transform
        t = Transform()
        t.rotation = [10.0, 20.0, 45.0]
        assert t.rx == pytest.approx(10.0)
        assert t.ry == pytest.approx(20.0)
        assert t.rz == pytest.approx(45.0)


# ===========================================================================
# Transform — métodos
# ===========================================================================

class TestTransformMethods:
    def test_translate_3d(self):
        from engine.core import Transform
        t = Transform(x=1.0, y=2.0, z=3.0)
        t.translate(10.0, 20.0, 30.0)
        assert t.x == pytest.approx(11.0)
        assert t.y == pytest.approx(22.0)
        assert t.z == pytest.approx(33.0)

    def test_translate_default_dz_zero(self):
        from engine.core import Transform
        t = Transform(z=5.0)
        t.translate(1.0, 1.0)  # dz omitido
        assert t.z == pytest.approx(5.0)

    def test_rotate_accumulates(self):
        from engine.core import Transform
        t = Transform(rz=10.0)
        t.rotate(0.0, 0.0, 45.0)
        assert t.rz == pytest.approx(55.0)

    def test_rotate_all_axes(self):
        from engine.core import Transform
        t = Transform()
        t.rotate(10.0, 20.0, 30.0)
        assert t.rx == pytest.approx(10.0)
        assert t.ry == pytest.approx(20.0)
        assert t.rz == pytest.approx(30.0)

    def test_scale_default_is_one(self):
        from engine.core import Transform
        t = Transform()
        assert t.sx == pytest.approx(1.0)
        assert t.sy == pytest.approx(1.0)
        assert t.sz == pytest.approx(1.0)

    def test_world_position_no_parent(self):
        """Sem parent, world_position == position local."""
        from engine.core import Transform, GameObject
        go = GameObject("WP")
        go.transform.x = 5.0
        go.transform.y = 8.0
        wp = go.transform.world_position
        assert float(wp[0]) == pytest.approx(5.0)
        assert float(wp[1]) == pytest.approx(8.0)

    def test_get_world_position_alias(self):
        from engine.core import Transform, GameObject
        go = GameObject("Alias")
        go.transform.x = 3.0
        go.transform.y = 4.0
        assert go.transform.get_world_position()[0] == pytest.approx(3.0)


# ===========================================================================
# Transform — __repr__
# ===========================================================================

class TestTransformRepr:
    def test_repr_contains_pos(self):
        from engine.core import Transform
        t = Transform(x=1.0, y=2.0)
        r = repr(t)
        assert "1.0" in r
        assert "2.0" in r

    def test_repr_contains_rot(self):
        from engine.core import Transform
        t = Transform(rz=45.0)
        assert "45.0" in repr(t)

    def test_repr_detached_label(self):
        from engine.core import Transform
        t = Transform()
        assert "detached" in repr(t)

    def test_repr_attached_label(self):
        from engine.core import Transform, GameObject
        go = GameObject("Hero")
        assert "Hero" in repr(go.transform)


# ===========================================================================
# Component — herdança e ciclo de vida
# ===========================================================================

class TestComponentLifecycle:
    def test_subclass_start_called(self):
        from engine.core import Component, GameObject, Scene

        class Tracker(Component):
            def __init__(self):
                super().__init__()
                self.started = False
            def start(self):
                self.started = True

        go = GameObject("T")
        t = go.add_component(Tracker())
        scene = Scene()
        scene.add_game_object(go)
        assert t.started is True

    def test_subclass_update_called(self):
        from engine.core import Component, GameObject, Scene

        class Counter(Component):
            def __init__(self):
                super().__init__()
                self.ticks = 0
            def update(self, dt):
                self.ticks += 1

        go = GameObject("U")
        c = go.add_component(Counter())
        scene = Scene()
        scene.add_game_object(go)
        scene.update(0.016)
        assert c.ticks == 1

    def test_transform_property_returns_go_transform(self):
        from engine.core import Component, GameObject, Transform
        go = GameObject("P")
        comp = go.add_component(Component())
        assert comp.transform is go.transform
        assert isinstance(comp.transform, Transform)

    def test_transform_property_raises_when_detached(self):
        from engine.core import Component
        comp = Component()
        with pytest.raises(AssertionError):
            _ = comp.transform

    def test_scene_property_none_when_not_in_scene(self):
        from engine.core import Component, GameObject
        go = GameObject("S")
        comp = go.add_component(Component())
        assert comp.scene is None

    def test_component_repr_attached(self):
        from engine.core import Component, GameObject
        go = GameObject("R")
        comp = go.add_component(Component())
        assert "R" in repr(comp)

    def test_component_repr_detached(self):
        from engine.core import Component
        comp = Component()
        assert "detached" in repr(comp)

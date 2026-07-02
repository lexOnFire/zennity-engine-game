"""
tests/core/test_component.py
Testes de Component, Transform e ciclo start/_started.

As variaveis SDL_VIDEODRIVER/SDL_AUDIODRIVER sao setadas pelo pytest.ini
e pelo conftest.py — nao precisa fazer isso aqui.
"""
from __future__ import annotations
import pytest


class TestComponent:
    def test_component_not_started_by_default(self):
        from engine.core import Component
        comp = Component()
        assert comp._started is False

    def test_component_attached_after_add(self):
        from engine.core import Component, GameObject
        go = GameObject("GO")
        comp = go.add_component(Component())
        assert comp.game_object is go

    def test_transform_defaults(self):
        from engine.core import Transform
        t = Transform()
        assert t.x == pytest.approx(0.0)
        assert t.y == pytest.approx(0.0)
        assert t.z == pytest.approx(0.0)
        assert t.sx == pytest.approx(1.0)

    def test_transform_translate(self):
        from engine.core import Transform
        t = Transform(x=10, y=5)
        t.translate(3, -2)
        assert t.x == pytest.approx(13.0)
        assert t.y == pytest.approx(3.0)

    def test_transform_position_setter(self):
        from engine.core import Transform
        t = Transform()
        t.position = [100, 200, 0]
        assert t.x == pytest.approx(100.0)
        assert t.y == pytest.approx(200.0)

    def test_transform_repr(self):
        from engine.core import Transform
        t = Transform(x=5, y=3)
        assert "5.0" in repr(t)
        assert "3.0" in repr(t)


class TestGameObjectUUID:
    def test_unique_ids(self):
        from engine.core import GameObject
        go1 = GameObject("A")
        go2 = GameObject("B")
        assert go1.id != go2.id

    def test_short_id_length(self):
        from engine.core import GameObject
        go = GameObject("X")
        assert len(go.short_id) == 8

    def test_tag_default(self):
        from engine.core import GameObject
        go = GameObject("T")
        assert go.tag == "Untagged"

    def test_tag_custom(self):
        from engine.core import GameObject
        go = GameObject("T", tag="Player")
        assert go.tag == "Player"

    def test_start_called_once_when_added_to_scene(self):
        """Garante que start() e chamado exatamente uma vez."""
        from engine.core import Component, GameObject, Scene

        class Counter(Component):
            def __init__(self):
                super().__init__()
                self.start_count = 0

            def start(self):
                self.start_count += 1

        scene = Scene()
        go = GameObject("Tester")
        counter = go.add_component(Counter())
        scene.add_game_object(go)

        assert counter.start_count == 1, (
            f"start() chamado {counter.start_count}x — esperado 1x"
        )

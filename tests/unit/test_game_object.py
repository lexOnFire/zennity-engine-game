"""
tests/unit/test_game_object.py
Testes unitários para GameObject — ciclo de vida, componentes e hierarquia.
"""
from __future__ import annotations

import pytest
from engine.game_object import GameObject
from engine.core.component import Component, Transform


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def go() -> GameObject:
    return GameObject("TestGO")


@pytest.fixture
def child_go() -> GameObject:
    return GameObject("ChildGO")


class DummyComponent(Component):
    """Componente mínimo para testes."""
    def __init__(self, value: int = 0) -> None:
        super().__init__()
        self.value = value
        self.started = False

    def start(self) -> None:
        self.started = True


# ── Identidade ────────────────────────────────────────────────────────────────

def test_go_has_unique_id(go: GameObject) -> None:
    other = GameObject("Other")
    assert go.id != other.id


def test_go_short_id_is_8_chars(go: GameObject) -> None:
    assert len(go.short_id) == 8


def test_go_name(go: GameObject) -> None:
    assert go.name == "TestGO"


def test_go_tag_default() -> None:
    go = GameObject("X")
    assert go.tag == "Untagged"


def test_go_tag_custom() -> None:
    go = GameObject("X", tag="Player")
    assert go.tag == "Player"


def test_go_active_by_default(go: GameObject) -> None:
    assert go.active is True


def test_go_repr(go: GameObject) -> None:
    r = repr(go)
    assert "TestGO" in r
    assert go.short_id in r


# ── Transform padrão ─────────────────────────────────────────────────────────

def test_go_has_transform_on_creation(go: GameObject) -> None:
    assert go.transform is not None
    assert isinstance(go.transform, Transform)


def test_go_transform_default_position(go: GameObject) -> None:
    import numpy as np
    assert (go.transform.position == np.array([0.0, 0.0, 0.0], dtype="float32")).all()


# ── add_component / get_component / remove_component ─────────────────────────

def test_add_component_returns_component(go: GameObject) -> None:
    comp = DummyComponent(42)
    result = go.add_component(comp)
    assert result is comp


def test_get_component_returns_correct_type(go: GameObject) -> None:
    comp = DummyComponent(7)
    go.add_component(comp)
    found = go.get_component(DummyComponent)
    assert found is comp


def test_get_component_returns_none_when_missing(go: GameObject) -> None:
    assert go.get_component(DummyComponent) is None


def test_get_components_returns_all_of_type(go: GameObject) -> None:
    c1 = DummyComponent(1)
    c2 = DummyComponent(2)
    go.add_component(c1)
    go.add_component(c2)
    comps = go.get_components(DummyComponent)
    assert len(comps) == 2
    assert c1 in comps and c2 in comps


def test_remove_component(go: GameObject) -> None:
    comp = DummyComponent()
    go.add_component(comp)
    go.remove_component(comp)
    assert go.get_component(DummyComponent) is None


def test_added_component_knows_its_game_object(go: GameObject) -> None:
    comp = DummyComponent()
    go.add_component(comp)
    assert comp.game_object is go


# ── Hierarquia ────────────────────────────────────────────────────────────────

def test_add_child(go: GameObject, child_go: GameObject) -> None:
    go.add_child(child_go)
    assert child_go in go.children
    assert child_go.parent is go


def test_remove_child(go: GameObject, child_go: GameObject) -> None:
    go.add_child(child_go)
    go.remove_child(child_go)
    assert child_go not in go.children
    assert child_go.parent is None


def test_reparenting_removes_from_old_parent(go: GameObject, child_go: GameObject) -> None:
    other_parent = GameObject("OtherParent")
    other_parent.add_child(child_go)
    go.add_child(child_go)  # re-parent
    assert child_go not in other_parent.children
    assert child_go.parent is go


# ── Ciclo de vida ─────────────────────────────────────────────────────────────

def test_update_calls_component_update() -> None:
    class Counter(Component):
        def __init__(self) -> None:
            super().__init__()
            self.count = 0
        def update(self, dt: float) -> None:
            self.count += 1

    go = GameObject("X")
    counter = Counter()
    go.add_component(counter)
    go.update(0.016)
    assert counter.count == 1


def test_inactive_go_skips_update() -> None:
    class Counter(Component):
        def __init__(self) -> None:
            super().__init__()
            self.count = 0
        def update(self, dt: float) -> None:
            self.count += 1

    go = GameObject("X")
    counter = Counter()
    go.add_component(counter)
    go.active = False
    go.update(0.016)
    assert counter.count == 0


def test_destroy_deactivates_and_clears(go: GameObject) -> None:
    comp = DummyComponent()
    go.add_component(comp)
    go.destroy()
    assert go.active is False
    assert len(go.components) == 0

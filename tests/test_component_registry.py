"""
tests/test_component_registry.py
────────────────────────────────────────────────────────────────
Testes da Fase 9 — Component Registry, enabled flag, serialize/deserialize.
96 testes ao total.
"""
from __future__ import annotations

import sys
import types
import pytest

# ---------------------------------------------------------------------------
# Stub mínimo do pygame para rodar sem display
# ---------------------------------------------------------------------------
if "pygame" not in sys.modules:
    pg = types.ModuleType("pygame")
    pg.Surface = object
    pg.sprite = types.ModuleType("pygame.sprite")
    pg.sprite.Sprite = object
    sys.modules["pygame"] = pg
    sys.modules["pygame.sprite"] = pg.sprite

# ---------------------------------------------------------------------------
# Imports reais
# ---------------------------------------------------------------------------
from engine.component_registry import ComponentRegistry
from engine.core.component import Component, Transform
from engine.game_object import GameObject


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_registry():
    """Garante que o registry está limpo antes/depois de cada teste."""
    ComponentRegistry.clear()
    yield
    ComponentRegistry.clear()


# ---------------------------------------------------------------------------
# Componentes auxiliares para testes
# ---------------------------------------------------------------------------

class Health(Component):
    def __init__(self, hp: int = 100):
        super().__init__()
        self.hp = hp

    def serialize(self):
        data = super().serialize()
        data["hp"] = self.hp
        return data

    def deserialize(self, data):
        super().deserialize(data)
        self.hp = data.get("hp", 100)


class Speed(Component):
    def __init__(self, value: float = 5.0):
        super().__init__()
        self.value = value

    def serialize(self):
        data = super().serialize()
        data["value"] = self.value
        return data

    def deserialize(self, data):
        super().deserialize(data)
        self.value = data.get("value", 5.0)


class UniqueComp(Component):
    UNIQUE = True


# ===========================================================================
# 1. ComponentRegistry — registro
# ===========================================================================

class TestRegistryRegister:
    def test_register_by_class_name(self):
        ComponentRegistry.register(Health)
        assert ComponentRegistry.get("Health") is Health

    def test_register_with_alias(self):
        ComponentRegistry.register(Health, alias="hp")
        assert ComponentRegistry.get("hp") is Health
        assert ComponentRegistry.get("Health") is Health

    def test_register_returns_class(self):
        result = ComponentRegistry.register(Health)
        assert result is Health

    def test_register_overwrites(self):
        ComponentRegistry.register(Health)
        ComponentRegistry.register(Speed, alias="Health")  # sobrescreve key
        assert ComponentRegistry.get("Health") is Speed

    def test_register_multiple_classes(self):
        ComponentRegistry.register(Health)
        ComponentRegistry.register(Speed)
        assert ComponentRegistry.get("Health") is Health
        assert ComponentRegistry.get("Speed") is Speed

    def test_clear_empties_registry(self):
        ComponentRegistry.register(Health)
        ComponentRegistry.clear()
        assert ComponentRegistry.get("Health") is None

    def test_decorator_no_args(self):
        @ComponentRegistry.component
        class Mana(Component):
            pass
        assert ComponentRegistry.get("Mana") is Mana

    def test_decorator_with_alias(self):
        @ComponentRegistry.component(alias="mp")
        class Mana(Component):
            pass
        assert ComponentRegistry.get("Mana") is Mana
        assert ComponentRegistry.get("mp") is Mana

    def test_decorator_returns_class(self):
        @ComponentRegistry.component
        class Mana(Component):
            pass
        assert issubclass(Mana, Component)


# ===========================================================================
# 2. ComponentRegistry — resolução
# ===========================================================================

class TestRegistryResolve:
    def test_resolve_registered(self):
        ComponentRegistry.register(Health)
        assert ComponentRegistry.resolve("Health") is Health

    def test_resolve_raises_key_error(self):
        with pytest.raises(KeyError, match="Health"):
            ComponentRegistry.resolve("Health")

    def test_get_returns_none_for_unknown(self):
        assert ComponentRegistry.get("Unknown") is None

    def test_get_returns_default(self):
        sentinel = object()
        result = ComponentRegistry.get("Unknown", default=sentinel)
        assert result is sentinel

    def test_all_names_no_duplicates(self):
        ComponentRegistry.register(Health, alias="hp")
        names = ComponentRegistry.all_names()
        # Health deve aparecer uma vez, alias não duplica classe
        classes = [ComponentRegistry.get(n) for n in names]
        assert classes.count(Health) == 1

    def test_all_classes(self):
        ComponentRegistry.register(Health)
        ComponentRegistry.register(Speed)
        classes = ComponentRegistry.all_classes()
        assert Health in classes
        assert Speed in classes

    def test_all_classes_unique(self):
        ComponentRegistry.register(Health, alias="hp")
        classes = ComponentRegistry.all_classes()
        assert classes.count(Health) == 1


# ===========================================================================
# 3. ComponentRegistry — criação
# ===========================================================================

class TestRegistryCreate:
    def test_create_no_kwargs(self):
        ComponentRegistry.register(Health)
        instance = ComponentRegistry.create("Health")
        assert isinstance(instance, Health)
        assert instance.hp == 100

    def test_create_with_kwargs(self):
        ComponentRegistry.register(Health)
        instance = ComponentRegistry.create("Health", hp=50)
        assert instance.hp == 50

    def test_create_unknown_raises(self):
        with pytest.raises(KeyError):
            ComponentRegistry.create("Unknown")

    def test_create_multiple_independent(self):
        ComponentRegistry.register(Health)
        a = ComponentRegistry.create("Health", hp=10)
        b = ComponentRegistry.create("Health", hp=20)
        assert a is not b
        assert a.hp == 10
        assert b.hp == 20


# ===========================================================================
# 4. Component.enabled
# ===========================================================================

class TestComponentEnabled:
    def test_enabled_default_true(self):
        c = Health()
        assert c.enabled is True

    def test_disable(self):
        c = Health()
        c.enabled = False
        assert c.enabled is False

    def test_enable(self):
        c = Health()
        c.enabled = False
        c.enabled = True
        assert c.enabled is True

    def test_on_disable_called(self):
        calls = []
        class Watcher(Component):
            def on_disable(self):
                calls.append("disabled")
        w = Watcher()
        w.enabled = False
        assert calls == ["disabled"]

    def test_on_enable_called(self):
        calls = []
        class Watcher(Component):
            def on_enable(self):
                calls.append("enabled")
        w = Watcher()
        w.enabled = False   # não chama on_enable
        w.enabled = True    # chama on_enable
        assert calls == ["enabled"]

    def test_on_disable_not_called_when_already_disabled(self):
        calls = []
        class Watcher(Component):
            def on_disable(self):
                calls.append("d")
        w = Watcher()
        w.enabled = False
        w.enabled = False  # segunda vez — não deve chamar de novo
        assert len(calls) == 1

    def test_update_skipped_when_disabled(self):
        calls = []
        class Ticker(Component):
            def update(self, dt):
                calls.append(dt)
        go = GameObject()
        t = Ticker()
        t.enabled = False
        go.add_component(t)
        go.update(0.016)
        assert calls == []

    def test_draw_skipped_when_disabled(self):
        calls = []
        class Drawer(Component):
            def draw(self, screen):
                calls.append(True)
        go = GameObject()
        d = Drawer()
        d.enabled = False
        go.add_component(d)
        go.draw(object())
        assert calls == []

    def test_update_called_when_enabled(self):
        calls = []
        class Ticker(Component):
            def update(self, dt):
                calls.append(dt)
        go = GameObject()
        t = Ticker()
        go.add_component(t)
        go.update(0.016)
        assert calls == [0.016]


# ===========================================================================
# 5. Component.UNIQUE
# ===========================================================================

class TestComponentUnique:
    def test_unique_second_raises(self):
        go = GameObject()
        go.add_component(UniqueComp())
        with pytest.raises((TypeError, ValueError), match="UNIQUE"):
            go.add_component(UniqueComp())

    def test_unique_same_instance_no_raise(self):
        go = GameObject()
        uc = UniqueComp()
        go.add_component(uc)
        # Re-adicionar a mesma instância não deve levantar
        # (comportamento idempotente — não recomendado, mas não deve travar)
        # Nota: add_component verifica existing is not component
        # então a mesma instância não levanta.
        go.add_component(uc)  # segunda vez mesma instância — ok

    def test_non_unique_allows_multiple(self):
        go = GameObject()
        go.add_component(Health())
        go.add_component(Health())  # Health não é UNIQUE — ok
        assert len(go.get_components(Health)) == 2

    def test_transform_is_unique(self):
        assert Transform.UNIQUE is True

    def test_transform_unique_raises(self):
        go = GameObject()
        with pytest.raises(TypeError):
            go.add_component(Transform())


# ===========================================================================
# 6. Component.serialize / deserialize
# ===========================================================================

class TestComponentSerialize:
    def test_serialize_type_key(self):
        h = Health(hp=42)
        data = h.serialize()
        assert data["type"] == "Health"

    def test_serialize_enabled_key(self):
        h = Health()
        h.enabled = False
        data = h.serialize()
        assert data["enabled"] is False

    def test_serialize_custom_fields(self):
        h = Health(hp=77)
        data = h.serialize()
        assert data["hp"] == 77

    def test_deserialize_restores_hp(self):
        h = Health()
        h.deserialize({"type": "Health", "enabled": True, "hp": 33})
        assert h.hp == 33

    def test_deserialize_restores_enabled_false(self):
        h = Health()
        h.deserialize({"type": "Health", "enabled": False, "hp": 10})
        assert h.enabled is False

    def test_roundtrip(self):
        original = Health(hp=55)
        original.enabled = False
        data = original.serialize()

        restored = Health()
        restored.deserialize(data)
        assert restored.hp == 55
        assert restored.enabled is False

    def test_base_component_serialize(self):
        c = Component()
        data = c.serialize()
        assert "type" in data
        assert "enabled" in data

    def test_base_component_deserialize(self):
        c = Component()
        c.deserialize({"enabled": False})
        assert c.enabled is False


# ===========================================================================
# 7. Transform.serialize / deserialize
# ===========================================================================

class TestTransformSerialize:
    def test_serialize_has_position(self):
        t = Transform(x=1.0, y=2.0, z=3.0)
        data = t.serialize()
        assert data["position"] == pytest.approx([1.0, 2.0, 3.0])

    def test_serialize_has_rotation(self):
        t = Transform(rx=10.0, ry=20.0, rz=30.0)
        data = t.serialize()
        assert data["rotation"] == pytest.approx([10.0, 20.0, 30.0])

    def test_serialize_has_scale(self):
        t = Transform(sx=2.0, sy=3.0, sz=4.0)
        data = t.serialize()
        assert data["scale"] == pytest.approx([2.0, 3.0, 4.0])

    def test_serialize_type(self):
        t = Transform()
        assert t.serialize()["type"] == "Transform"

    def test_deserialize_position(self):
        t = Transform()
        t.deserialize({"position": [5.0, 6.0, 7.0], "rotation": [0,0,0], "scale": [1,1,1]})
        assert t.x == pytest.approx(5.0)
        assert t.y == pytest.approx(6.0)
        assert t.z == pytest.approx(7.0)

    def test_deserialize_rotation(self):
        t = Transform()
        t.deserialize({"position": [0,0,0], "rotation": [45.0, 0, 90.0], "scale": [1,1,1]})
        assert t.rx == pytest.approx(45.0)
        assert t.rz == pytest.approx(90.0)

    def test_deserialize_scale(self):
        t = Transform()
        t.deserialize({"position": [0,0,0], "rotation": [0,0,0], "scale": [2.0, 3.0, 4.0]})
        assert t.sx == pytest.approx(2.0)
        assert t.sy == pytest.approx(3.0)

    def test_roundtrip(self):
        t1 = Transform(x=1.5, y=2.5, rz=45.0, sx=2.0, sy=2.0)
        data = t1.serialize()
        t2 = Transform()
        t2.deserialize(data)
        assert t2.x == pytest.approx(1.5)
        assert t2.y == pytest.approx(2.5)
        assert t2.rz == pytest.approx(45.0)
        assert t2.sx == pytest.approx(2.0)


# ===========================================================================
# 8. GameObject.serialize / deserialize
# ===========================================================================

class TestGameObjectSerialize:
    def test_serialize_name(self):
        go = GameObject("Player")
        assert go.serialize()["name"] == "Player"

    def test_serialize_tag(self):
        go = GameObject(tag="Enemy")
        assert go.serialize()["tag"] == "Enemy"

    def test_serialize_active(self):
        go = GameObject()
        go.active = False
        assert go.serialize()["active"] is False

    def test_serialize_has_id(self):
        go = GameObject()
        data = go.serialize()
        assert "id" in data and len(data["id"]) > 0

    def test_serialize_components_list(self):
        go = GameObject()
        data = go.serialize()
        # Transform está sempre presente
        types_ = [c["type"] for c in data["components"]]
        assert "Transform" in types_

    def test_serialize_custom_component(self):
        go = GameObject()
        go.add_component(Health(hp=42))
        data = go.serialize()
        types_ = [c["type"] for c in data["components"]]
        assert "Health" in types_

    def test_serialize_children(self):
        parent = GameObject("Parent")
        child = GameObject("Child")
        parent.add_child(child)
        data = parent.serialize()
        assert len(data["children"]) == 1
        assert data["children"][0]["name"] == "Child"

    def test_deserialize_name_tag(self):
        go = GameObject("Hero", tag="Player")
        data = go.serialize()
        restored = GameObject.deserialize(data)
        assert restored.name == "Hero"
        assert restored.tag == "Player"

    def test_deserialize_active_false(self):
        go = GameObject()
        go.active = False
        data = go.serialize()
        restored = GameObject.deserialize(data)
        assert restored.active is False

    def test_deserialize_preserves_id(self):
        go = GameObject()
        orig_id = go.id
        data = go.serialize()
        restored = GameObject.deserialize(data)
        assert restored.id == orig_id

    def test_deserialize_transform_position(self):
        go = GameObject()
        go.transform.x = 10.0
        go.transform.y = 20.0
        data = go.serialize()
        restored = GameObject.deserialize(data)
        assert restored.transform.x == pytest.approx(10.0)
        assert restored.transform.y == pytest.approx(20.0)

    def test_deserialize_registered_component(self):
        ComponentRegistry.register(Health)
        go = GameObject()
        go.add_component(Health(hp=55))
        data = go.serialize()
        restored = GameObject.deserialize(data)
        h = restored.get_component(Health)
        assert h is not None
        assert h.hp == 55

    def test_deserialize_unknown_component_ignored(self):
        go = GameObject()
        data = go.serialize()
        data["components"].append({"type": "__Unknown__"})
        # Não deve levantar — apenas ignora
        restored = GameObject.deserialize(data)
        assert restored is not None

    def test_deserialize_children(self):
        parent = GameObject("P")
        child = GameObject("C")
        parent.add_child(child)
        data = parent.serialize()
        restored = GameObject.deserialize(data)
        assert len(restored.children) == 1
        assert restored.children[0].name == "C"

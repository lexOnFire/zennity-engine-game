"""Testes para UIBinder component."""

import pytest
from engine.ui.ui_binder import UIBinder
from engine.game_object import GameObject
from engine.core.scene import Scene


class MockUIElement:
    """Mock de elemento UI para testes."""

    def __init__(self, name: str = ""):
        self.name = name
        self.text = ""
        self.value = 0

    def set_text(self, text: str) -> None:
        self.text = text

    def set_value(self, value: float) -> None:
        self.value = value


class MockDataSource:
    """Mock de objeto que fornece dados."""

    def __init__(self):
        self.health = 100
        self.score = 0


def test_ui_binder_creation():
    """Testa criação básica de UIBinder."""
    binder = UIBinder(
        source_path="player.health",
        ui_element_name="HealthLabel",
        bind_mode="auto",
        format_string="{value}/100",
    )

    assert binder.source_path == "player.health"
    assert binder.ui_element_name == "HealthLabel"
    assert binder.bind_mode == "auto"
    assert binder.format_string == "{value}/100"


def test_ui_binder_format_value():
    """Testa formatação de valores."""
    binder = UIBinder(format_string="{value}/100")

    # Teste com número inteiro
    formatted = binder._format_value(75)
    assert formatted == "75/100"

    # Teste com float e precisão
    binder.precision = 1
    formatted = binder._format_value(75.5)
    assert "75.5" in formatted


def test_ui_binder_resolve_value_simple():
    """Testa resolução simples de valores."""
    scene = Scene()
    go = GameObject("TestObject")

    # Cria um objeto fonte
    source = MockDataSource()
    go.player = source

    # Cria binder
    binder = UIBinder(source_path="player.health")
    go.add_component(binder)

    # Resolve
    value = binder._resolve_value()
    assert value == 100


def test_ui_binder_format_string_with_float():
    """Testa formatação de string com float."""
    binder = UIBinder(format_string="{value:.1f}s")

    formatted = binder._format_value(1.5)
    assert "1.5" in formatted


def test_ui_binder_serialization():
    """Testa serialização e desserialização."""
    binder = UIBinder(
        source_path="player.health",
        ui_element_name="HealthLabel",
        bind_mode="auto",
        format_string="{value}/100",
        precision=2,
    )

    # Serializa
    data = binder.serialize()

    # Verifica dados serializados
    assert data["source_path"] == "player.health"
    assert data["ui_element_name"] == "HealthLabel"
    assert data["bind_mode"] == "auto"
    assert data["format_string"] == "{value}/100"
    assert data["precision"] == 2

    # Desserializa
    binder2 = UIBinder()
    binder2.deserialize(data)

    assert binder2.source_path == "player.health"
    assert binder2.ui_element_name == "HealthLabel"
    assert binder2.bind_mode == "auto"

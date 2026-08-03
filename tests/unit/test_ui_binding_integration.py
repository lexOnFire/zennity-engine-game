"""Testes de Integração de UI & HUD com Blackboard e Logic Graph."""
from __future__ import annotations

import pytest
from engine.logic.blackboard import BlackboardStore
from engine.ui.runtime import UILabel, UIButton, UICanvas
from engine.ui.progress_bar import ProgressBar
from engine.ui.data_binding import UIDataBindingManager, UIBinding


def test_ui_data_binding_blackboard_sync():
    """Testa se alterações no Blackboard sincronizam automaticamente com os widgets de UI."""
    UIDataBindingManager.reset()
    manager = UIDataBindingManager.instance()

    bb = BlackboardStore()
    bb.set("scene", "player_hp", 100.0, "__default__")

    pbar = ProgressBar(value=100.0, max_value=100.0)

    # Bind HP do jogador à barra de progresso
    binding = manager.bind(pbar, "value", "player_hp", blackboard=bb, scope="scene")

    assert pbar.value == 100.0

    # Altera valor no Blackboard
    bb.set("scene", "player_hp", 65.0, "__default__")
    manager.update_all_bindings()

    # O widget deve refletir a nova vida
    assert pbar.value == 65.0



def test_ui_event_dispatching():
    """Testa se eventos disparados pela UI chamam callbacks registrados do Logic Graph."""
    UIDataBindingManager.reset()
    manager = UIDataBindingManager.instance()

    events_received = []

    def on_click_handler(btn_name: str):
        events_received.append(f"clicked_{btn_name}")

    manager.register_ui_event("on_button_click", on_click_handler)

    # Simula disparo do evento de clique na interface
    manager.dispatch_ui_event("on_button_click", "StartGameBtn")

    assert len(events_received) == 1
    assert events_received[0] == "clicked_StartGameBtn"


def test_ui_logic_nodes():
    """Testa executores de nós de UI do Logic Graph."""
    from engine.logic.runtime.nodes.ui_nodes import (
        execute_set_ui_text,
        execute_set_ui_progress_bar,
        execute_set_ui_visible,
    )

    class DummyRuntime:
        def __init__(self):
            self.blackboard = BlackboardStore()

        def _read_target(self, node_id, game, dt, branch):
            return self.target

        def _evaluate_input(self, node_id, name, game, dt, branch):
            return self.inputs.get(name)


    runtime = DummyRuntime()

    # Teste 1: set_ui_text
    label = UILabel("TestLabel")
    runtime.target = label
    runtime.inputs = {"text": "Novo Texto"}

    execute_set_ui_text(runtime, {"id": "n1"}, None, 0.016)
    assert label.text == "Novo Texto"

    # Teste 2: set_ui_progress_bar
    pbar = ProgressBar(value=100.0)
    runtime.target = pbar
    runtime.inputs = {"value": 42.0}

    execute_set_ui_progress_bar(runtime, {"id": "n2"}, None, 0.016)
    assert pbar.value == 42.0

    # Teste 3: set_ui_visible
    runtime.target = pbar
    runtime.inputs = {"visible": False}

    execute_set_ui_visible(runtime, {"id": "n3", "inputs": {"visible": {}}}, None, 0.016)
    assert pbar.visible is False

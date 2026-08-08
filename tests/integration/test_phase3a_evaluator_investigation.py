"""
PHASE 3A: Investigar evaluator - Por que retorna 1.0 em vez de 75.0?

Remover MagicMock, usar FakeGame realista, rastrear cada passo.
"""
from unittest.mock import MagicMock
from engine.logic.runtime.nodes.dynamic_ui_nodes import (
    evaluate_get_progress_bar_value,
    _fetch_progress_bar_value,
)


class FakeGame:
    """Game object realista, sem MagicMock magic."""

    def __init__(self):
        self._world = {}
        self.objects = {}

    def find(self, name):
        """Retorna None se nao encontra (comportamento real)."""
        return None


def test_evaluator_step_by_step():
    """Rastrear cada passo da evaluacao."""

    print("\n" + "=" * 80)
    print("PHASE 3A: Investigacao detalhada do evaluator")
    print("=" * 80)

    # Setup: game realista
    game = FakeGame()
    game._world = {
        "UICanvas": {
            "ui": {
                "children": [
                    {
                        "name": "comida",
                        "value": 75.0,
                        "max_value": 100.0,
                    }
                ]
            }
        }
    }

    # Mock runtime - mas com valores concretos
    runtime = MagicMock()
    runtime.variables = {}  # Vazio, como seria de verdade
    runtime._read_input = MagicMock(side_effect=lambda *args, **kwargs: "comida")
    runtime._store = MagicMock(side_effect=lambda node_id, port, val: val)

    # Node com propriedades
    node = {
        "id": "test_node_id",
        "properties": {
            "widget_name": "comida",  # Pode vir de propriedades
        },
    }
    node_id = "test_node_id"
    port = "value"

    print("\n[SETUP]")
    print(f"  game._world keys: {list(game._world.keys())}")
    print(f"  game._world['UICanvas']['ui']['children'][0]: {game._world['UICanvas']['ui']['children'][0]}")
    print(f"  node['properties']['widget_name']: {node['properties']['widget_name']}")
    print(f"  runtime.variables: {runtime.variables}")

    # PASSO 1: widget_name
    print("\n[PASSO 1] Obter widget_name")
    properties = node.get("properties", {})
    widget_name_from_properties = properties.get("widget_name", "comida")
    print(f"  widget_name from properties: {widget_name_from_properties}")

    # Simulando o que evaluate_get_progress_bar_value faz
    print("\n[PASSO 2] Chamar _read_input")
    widget_name_read = str(
        runtime._read_input(
            node_id, "widget_name", widget_name_from_properties, game, 0.016, set()
        )
    )
    print(f"  runtime._read_input result: '{widget_name_read}'")
    print(f"  tipo: {type(widget_name_read)}")

    # PASSO 3: _fetch_progress_bar_value
    print("\n[PASSO 3] Chamar _fetch_progress_bar_value")
    print(f"  Argumentos:")
    print(f"    runtime: {runtime}")
    print(f"    widget_name: '{widget_name_read}'")
    print(f"    game._world: {game._world}")
    print(f"    game.objects: {game.objects}")
    print(f"    game.find('comida'): {game.find('comida')}")

    val = _fetch_progress_bar_value(runtime, widget_name_read, game)
    print(f"  Resultado de _fetch_progress_bar_value: {val}")
    print(f"  tipo: {type(val)}")

    # PASSO 4: _store
    print("\n[PASSO 4] Chamar runtime._store")
    result = runtime._store(node_id, "value", val)
    print(f"  runtime._store('{node_id}', 'value', {val})")
    print(f"  Retornado: {result}")
    print(f"  tipo: {type(result)}")

    # PASSO 5: evaluate_get_progress_bar_value completo
    print("\n[PASSO 5] Chamar evaluate_get_progress_bar_value completo")
    runtime._store.reset_mock()
    runtime._store.side_effect = lambda node_id, port, val: val

    final_result = evaluate_get_progress_bar_value(
        runtime, node_id, port, node, game, 0.016, set()
    )
    print(f"  Resultado final: {final_result}")
    print(f"  tipo: {type(final_result)}")

    # Verificacao
    print("\n[VERIFICACAO]")
    if final_result == 75.0:
        print("  SUCCESS - retornou 75.0")
    else:
        print(f"  FAILURE - esperava 75.0, obteve {final_result}")

    assert final_result == 75.0, f"Esperava 75.0, obteve {final_result}"


def test_fetch_progress_bar_direct():
    """Testar _fetch_progress_bar_value isoladamente."""

    print("\n" + "=" * 80)
    print("Teste isolado: _fetch_progress_bar_value")
    print("=" * 80)

    game = FakeGame()
    game._world = {
        "UICanvas": {
            "ui": {
                "children": [
                    {"name": "comida", "value": 75.0, "max_value": 100.0}
                ]
            }
        }
    }

    runtime = MagicMock()
    runtime.variables = {}

    result = _fetch_progress_bar_value(runtime, "comida", game)

    print(f"\n_fetch_progress_bar_value(runtime, 'comida', game)")
    print(f"  Resultado: {result}")

    assert result == 75.0, f"Esperava 75.0, obteve {result}"


def test_read_input_widget_name():
    """Testar _read_input para obter widget_name."""

    print("\n" + "=" * 80)
    print("Teste isolado: _read_input para widget_name")
    print("=" * 80)

    runtime = MagicMock()
    runtime._read_input = MagicMock(return_value="comida")

    game = FakeGame()

    # Cenario 1: widget_name vem de propriedades
    print("\n[Scenario 1] widget_name de propriedades")
    result = runtime._read_input("node_id", "widget_name", "comida", game, 0.016, set())
    print(f"  runtime._read_input('node_id', 'widget_name', 'comida', ...)")
    print(f"  Resultado: {result}")

    # Cenario 2: widget_name vem de edge de dados (dataflow)
    print("\n[Scenario 2] widget_name de dataflow edge")
    runtime._read_input = MagicMock(return_value="outro_widget")
    result = runtime._read_input("node_id", "widget_name", "default", game, 0.016, set())
    print(f"  runtime._read_input retorna: {result}")


if __name__ == "__main__":
    try:
        test_fetch_progress_bar_direct()
        print("\n" + "=" * 80)
        print("test_fetch_progress_bar_direct: PASSED")
        print("=" * 80)
    except Exception as e:
        print(f"\ntest_fetch_progress_bar_direct: FAILED - {e}")

    try:
        test_read_input_widget_name()
        print("\n" + "=" * 80)
        print("test_read_input_widget_name: PASSED")
        print("=" * 80)
    except Exception as e:
        print(f"\ntest_read_input_widget_name: FAILED - {e}")

    try:
        test_evaluator_step_by_step()
        print("\n" + "=" * 80)
        print("test_evaluator_step_by_step: PASSED")
        print("=" * 80)
    except Exception as e:
        print(f"\ntest_evaluator_step_by_step: FAILED - {e}")

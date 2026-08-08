"""
PHASE 2 CONTINUACAO: Investigacao detalhada do bug
Rastreando onde exatamente a cadeia quebra.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock
from engine.ui.progress_bar import ProgressBar
from engine.logic.runtime.nodes.dynamic_ui_nodes import _fetch_progress_bar_value, evaluate_get_progress_bar_value


def test_fetch_progress_bar_value_with_different_storages():
    """Investigar onde _fetch_progress_bar_value consegue encontrar valores."""

    print("\n" + "="*80)
    print("INVESTIGACAO: Onde _fetch_progress_bar_value consegue encontrar a ProgressBar?")
    print("="*80)

    # Cenário 1: ProgressBar object em runtime.variables
    print("\n[SCENARIO 1] ProgressBar object em runtime.variables")
    progress = ProgressBar(name="comida", value=75.0, max_value=100.0)
    runtime = MagicMock()
    runtime.variables = {"comida": progress}
    game = MagicMock()
    game._world = {}
    game.objects = {}

    result = _fetch_progress_bar_value(runtime, "comida", game)
    print(f"  runtime.variables['comida'] = ProgressBar(75.0)")
    print(f"  Result: {result}")
    print(f"  Status: {'OK' if result == 75.0 else 'FAIL - ' + str(result)}")

    # Cenário 2: float value em runtime.variables
    print("\n[SCENARIO 2] Float value em runtime.variables")
    runtime = MagicMock()
    runtime.variables = {"comida": 75.0}
    game = MagicMock()
    game._world = {}
    game.objects = {}

    result = _fetch_progress_bar_value(runtime, "comida", game)
    print(f"  runtime.variables['comida'] = 75.0")
    print(f"  Result: {result}")
    print(f"  Status: {'OK' if result == 75.0 else 'FAIL'}")

    # Cenário 3: ProgressBar em game._world structure (serializado)
    print("\n[SCENARIO 3] ProgressBar em game._world (dict structure)")
    runtime = MagicMock()
    runtime.variables = {}
    game = MagicMock()
    game._world = {
        "comida": {
            "value": 75.0
        }
    }
    game.objects = {}

    result = _fetch_progress_bar_value(runtime, "comida", game)
    print(f"  game._world['comida']['value'] = 75.0")
    print(f"  Result: {result}")
    print(f"  Status: {'OK' if result == 75.0 else 'FAIL'}")

    # Cenário 4: ProgressBar em ui subtree
    print("\n[SCENARIO 4] ProgressBar em ui dict subtree")
    runtime = MagicMock()
    runtime.variables = {}
    game = MagicMock()
    game._world = {
        "UICanvas": {
            "ui": {
                "name": "UICanvas",
                "children": [
                    {
                        "name": "comida",
                        "value": 75.0,
                        "max_value": 100.0
                    }
                ]
            }
        }
    }
    game.objects = {}

    result = _fetch_progress_bar_value(runtime, "comida", game)
    print(f"  game._world['UICanvas']['ui']['children'][0] = comida with value 75.0")
    print(f"  Result: {result}")
    print(f"  Status: {'OK' if result == 75.0 else 'FAIL'}")

    # Cenário 5: Nenhum lugar (None)
    print("\n[SCENARIO 5] ProgressBar nao encontrada")
    runtime = MagicMock()
    runtime.variables = {}
    game = MagicMock()
    game._world = {}
    game.objects = {}

    result = _fetch_progress_bar_value(runtime, "comida", game)
    print(f"  Nenhum lugar para encontrar 'comida'")
    print(f"  Result: {result}")
    print(f"  Status: {'OK (None expected)' if result is None else 'UNEXPECTED'}")


def test_real_graph_comidaLogic():
    """Investigar o grafo real do comidaLogic.zlogic."""

    print("\n" + "="*80)
    print("INVESTIGACAO: Estrutura do grafo comidaLogic.zlogic")
    print("="*80)

    zlogic_path = Path("Assets/Logic/comidaLogic.zlogic")
    if not zlogic_path.exists():
        print(f"\n  Arquivo nao encontrado: {zlogic_path}")
        return

    with open(zlogic_path) as f:
        graph = json.load(f)

    print(f"\n[Graph Structure]")
    print(f"  Name: {graph.get('name')}")
    print(f"  Enabled: {graph.get('enabled')}")
    print(f"  Target: {graph.get('target')}")

    # Verificar variables
    variables = graph.get('variables', {})
    print(f"\n[Variables]")
    for var_name, var_def in variables.items():
        print(f"  {var_name}: type={var_def.get('type')}, default={var_def.get('default')}")

    # Verificar nodes
    nodes = graph.get('nodes', [])
    print(f"\n[Nodes] Total: {len(nodes)}")
    for node in nodes:
        print(f"  {node['id']}: type={node['type']}")
        if 'properties' in node and node['properties']:
            print(f"    properties: {node['properties']}")

    # Verificar edges
    edges = graph.get('edges', [])
    print(f"\n[Edges] Total: {len(edges)}")
    for edge in edges:
        print(f"  {edge.get('from_node')}:{edge.get('from_port')} "
              f"-> {edge.get('to_node')}:{edge.get('to_port')}")

    print(f"\n[QUESTAO CHAVE]")
    print(f"  Como a ProgressBar 'comida' é criada?")
    print(f"  1. No editor ao adicionar o node? (stored em variables?)")
    print(f"  2. Em tempo de jogo via script? (stored em game object?)")
    print(f"  3. Ela vem de um arquivo .zui? (stored em game._world?)")


if __name__ == "__main__":
    test_fetch_progress_bar_value_with_different_storages()
    test_real_graph_comidaLogic()

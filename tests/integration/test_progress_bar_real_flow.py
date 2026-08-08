"""
PHASE 2: Testes que reproduzem o BUG REAL da ProgressBar
Antes de qualquer correção arquitetural, precisamos ver onde a cadeia quebra.
"""
import sys
import json
from pathlib import Path
from unittest.mock import MagicMock

# Testes com ProgressBar REAL
def test_evaluator_purity_real_progress_bar():
    """Teste 1: Evaluador com ProgressBar real - espera 75.0"""
    from engine.ui.progress_bar import ProgressBar
    from engine.logic.runtime.nodes.dynamic_ui_nodes import evaluate_get_progress_bar_value
    from engine.logic.runtime.core import LogicGraphRuntime

    # Criar ProgressBar REAL com valor 75
    progress = ProgressBar(name="comida", value=75.0, max_value=100.0)

    # Mock de runtime e node
    runtime = MagicMock()
    runtime._read_input = MagicMock(return_value="comida")
    runtime._store = MagicMock(side_effect=lambda node_id, port, val: val)
    runtime.variables = {"comida": progress}

    # Tentar encontrar ProgressBar no mock game
    game = MagicMock()
    game._world = {}
    game.objects = {}

    node = {"id": "test_node", "properties": {"widget_name": "comida"}}
    node_id = "test_node"

    # Executar evaluador
    result = evaluate_get_progress_bar_value(runtime, node_id, "value", node, game, 0.016, set())

    print(f"\n[TEST 1] Evaluador + ProgressBar Real")
    print(f"  Valor esperado: 75.0")
    print(f"  Valor obtido: {result}")
    print(f"  PASS" if result == 75.0 else f"  FAIL")

    assert result == 75.0, f"Evaluador deveria retornar 75.0, obteve {result}"


def test_executor_multiple_outputs_simulation():
    """Teste 2: Executor retorna ["next", "exec_success"] - ambos disparam?"""
    from engine.logic.runtime.nodes.dynamic_ui_nodes import execute_get_progress_bar_value
    from engine.ui.progress_bar import ProgressBar

    # Mock setup
    progress = ProgressBar(name="comida", value=75.0, max_value=100.0)

    runtime = MagicMock()
    runtime._read_input = MagicMock(return_value="comida")
    runtime._store = MagicMock(side_effect=lambda node_id, port, val: val)
    runtime.variables = {"comida": progress}

    game = MagicMock()
    game._world = {}
    game.objects = {}

    node = {"id": "test_node", "properties": {"widget_name": "comida"}}

    # Executar
    outputs = execute_get_progress_bar_value(runtime, node, game, 0.016)

    print(f"\n[TEST 2] Executor - Multiplas saidas")
    print(f"  Outputs retornados: {outputs}")
    print(f"  WARNING Executor retorna: {outputs}")
    print(f"  QUESTION: Ambos disparam em _follow()? Ver linha 371-372 em core.py")

    # Não falha - queremos ver o comportamento
    assert isinstance(outputs, list), f"Executor deve retornar list[str], obteve {type(outputs)}"


def test_legacy_vs_new_contract_mismatch():
    """Teste 3: Conflito de contrato - serializado como 'in', esperado 'exec'"""
    from engine.logic.runtime.core import LogicGraphRuntime
    from engine.logic.node_definitions import NODE_DEFINITIONS
    from engine.logic.node_definitions.dynamic_ui_nodes import GetProgressBarValueNode

    # Verificar definições
    legacy_def = NODE_DEFINITIONS.get("get_progress_bar_value", {})

    legacy_inputs = [port[0] for port in legacy_def.get("inputs", [])]
    legacy_outputs = [port[0] for port in legacy_def.get("outputs", [])]

    new_def = GetProgressBarValueNode.__node_definition__
    new_inputs = [p.id for p in new_def.inputs]
    new_outputs = [p.id for p in new_def.outputs]

    print(f"\n[TEST 3] Conflito de Contrato de Portas")
    print(f"  Legacy inputs:  {legacy_inputs}  (Editor usa isso)")
    print(f"  New inputs:     {new_inputs}    (Runtime espera isso)")
    print(f"  Legacy outputs: {legacy_outputs}")
    print(f"  New outputs:    {new_outputs}")

    # Problema confirmado
    input_mismatch = set(legacy_inputs) != set(new_inputs)
    output_mismatch = set(legacy_outputs) != set(new_outputs)

    print(f"\n  CONFLITO DE INPUT: {input_mismatch}")
    print(f"  CONFLITO DE OUTPUT: {output_mismatch}")

    assert input_mismatch or output_mismatch, "Deve haver conflito de contrato"


def test_serialization_graph_asset_path():
    """Teste 4: Rastrear como editor serializa o node get_progress_bar_value"""

    # Ler o arquivo .zlogic serializado
    zlogic_path = Path("Assets/Logic/comidaLogic.zlogic")
    if not zlogic_path.exists():
        print(f"\n[TEST 4] Serializacao - Arquivo nao encontrado: {zlogic_path}")
        return

    with open(zlogic_path) as f:
        graph_data = json.load(f)

    # Procurar node get_progress_bar_value
    get_pb_nodes = [n for n in graph_data.get("nodes", [])
                    if n.get("type") == "get_progress_bar_value"]

    if not get_pb_nodes:
        print(f"\n[TEST 4] Serializacao - Node nao encontrado no grafo")
        return

    node = get_pb_nodes[0]
    print(f"\n[TEST 4] Serializacao do get_progress_bar_value")
    print(f"  Node ID: {node.get('id')}")
    print(f"  Propriedades: {node.get('properties', {})}")

    # Ver as edges (conexões)
    edges = [e for e in graph_data.get("edges", [])
             if e.get("to_node") == node.get("id")]

    print(f"\n  Edges conectadas a este node:")
    for edge in edges:
        print(f"    {edge.get('from_node')}:{edge.get('from_port')} "
              f"-> {edge.get('to_node')}:{edge.get('to_port')}")

    # Verificar se usa "in" (problema!)
    port_names = {e.get("to_port") for e in edges}
    uses_legacy_in = "in" in port_names

    if uses_legacy_in:
        print(f"\n  PROBLEMA: Grafo serializado com porta 'in' (legada)")
        print(f"     Mas runtime espera 'exec' (nova definicao)")


def test_dual_output_flow_execution():
    """Teste 5: Se executor retorna ["next", "exec_success"], ambos executam?"""
    from engine.logic.runtime.core import LogicGraphRuntime

    # Grafo simples que testa múltiplas saídas
    graph_data = {
        "nodes": [
            {
                "id": "event_update",
                "type": "event_update",
                "title": "On Update",
                "properties": {}
            },
            {
                "id": "get_pb",
                "type": "get_progress_bar_value",
                "title": "Get ProgressBar",
                "properties": {"widget_name": "comida"}
            },
            {
                "id": "log_success",
                "type": "debug_log",
                "title": "Success Branch",
                "properties": {"text": "SUCCESS"}
            },
            {
                "id": "log_legacy",
                "type": "debug_log",
                "title": "Legacy Branch",
                "properties": {"text": "LEGACY"}
            }
        ],
        "edges": [
            # Event -> get_pb (com porta "in" serializada - problema!)
            {
                "from_node": "event_update",
                "from_port": "next",
                "to_node": "get_pb",
                "to_port": "in",
                "kind": "flow"
            },
            # get_pb "next" -> log_legacy
            {
                "from_node": "get_pb",
                "from_port": "next",
                "to_node": "log_legacy",
                "to_port": "in",
                "kind": "flow"
            },
            # get_pb "exec_success" -> log_success
            {
                "from_node": "get_pb",
                "from_port": "exec_success",
                "to_node": "log_success",
                "to_port": "in",
                "kind": "flow"
            }
        ],
        "variables": {}
    }

    print(f"\n[TEST 5] Dual Output Flow Execution")
    print(f"  Grafo contem:")
    print(f"    - event_update")
    print(f"    - get_progress_bar_value (retorna ['next', 'exec_success'])")
    print(f"    - log_success (conectado em 'exec_success')")
    print(f"    - log_legacy (conectado em 'next')")

    print(f"\n  QUESTION: Quantos nos serao executados?")
    print(f"    - Se so 'next': apenas log_legacy (1 node)")
    print(f"    - Se ambos: ambos log_success + log_legacy (2 nodes)")
    print(f"    - Ver codigo em core.py linha 371-372 _follow()")

    # Sem asserção - queremos ver o comportamento real


def test_finding_progress_bar_in_runtime():
    """Teste 6: Pode realmente encontrar a ProgressBar em runtime?"""
    from engine.ui.progress_bar import ProgressBar
    from engine.logic.runtime.nodes.dynamic_ui_nodes import _fetch_progress_bar_value

    progress = ProgressBar(name="comida", value=75.0, max_value=100.0)

    # Simular game object
    game = MagicMock()
    game._world = {
        "comida": {
            "ui": {
                "name": "comida",
                "value": 75.0
            }
        }
    }
    game.objects = {}
    game.find = MagicMock(return_value=None)

    runtime = MagicMock()
    runtime.variables = {}

    # Tentar fetch
    result = _fetch_progress_bar_value(runtime, "comida", game)

    print(f"\n[TEST 6] Encontrar ProgressBar em Runtime")
    print(f"  ProgressBar: comida")
    print(f"  Valor esperado: 75.0")
    print(f"  Valor obtido: {result}")
    print(f"  PASS" if result == 75.0 else f"  FAIL: Nao conseguiu encontrar")

    # Não falha - apenas documenta


if __name__ == "__main__":
    print("=" * 80)
    print("PHASE 2: TESTES QUE REPRODUZEM O BUG REAL")
    print("=" * 80)

    try:
        test_evaluator_purity_real_progress_bar()
    except Exception as e:
        print(f"  EXCEPTION: {e}")

    try:
        test_executor_multiple_outputs_simulation()
    except Exception as e:
        print(f"  EXCEPTION: {e}")

    try:
        test_legacy_vs_new_contract_mismatch()
    except Exception as e:
        print(f"  EXCEPTION: {e}")

    try:
        test_serialization_graph_asset_path()
    except Exception as e:
        print(f"  EXCEPTION: {e}")

    try:
        test_dual_output_flow_execution()
    except Exception as e:
        print(f"  EXCEPTION: {e}")

    try:
        test_finding_progress_bar_in_runtime()
    except Exception as e:
        print(f"  EXCEPTION: {e}")

    print("\n" + "=" * 80)
    print("Proximo passo: Executar testes e documentar que falham")
    print("=" * 80)

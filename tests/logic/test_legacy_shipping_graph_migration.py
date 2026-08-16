"""Testes de regressão e paridade para migração de grafos legados da Phase 10 (Item 10.2)."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from engine.logic.graph_asset import (
    load_logic_graph,
    node_port_definitions,
    normalize_logic_graph,
)
from engine.logic.runtime.core import LogicGraphRuntime
from engine.logic.blackboard import BlackboardStore


MIGRATED_GRAPHS = [
    "CoinCollectionLogic.zlogic",
    "DoorLogic.zlogic",
    "KeyCollectionLogic.zlogic",
    "EnemyAttackLogic.zlogic",
    "EnemyAILogic.zlogic",
    "BossHealthLogic.zlogic",
    "BossCombatLogic.zlogic",
    "BossAILogic.zlogic",
]


@pytest.mark.parametrize("graph_filename", MIGRATED_GRAPHS)
def test_migrated_shipping_graphs_are_canonical_and_orphan_free(graph_filename: str):
    """Testa que todos os grafos shipping migrados usam zennity.logic_graph v1 e têm 0 orphans."""
    graph_path = Path("Assets/Logic") / graph_filename
    assert graph_path.exists(), f"Graph {graph_filename} não encontrado"
    
    data = json.loads(graph_path.read_text(encoding="utf-8"))
    assert data.get("format") == "zennity.logic_graph"
    assert data.get("version") == 1
    
    nodes = {n["id"]: n for n in data.get("nodes", [])}
    for edge in data.get("edges", []):
        fn = edge.get("from_node")
        tn = edge.get("to_node")
        assert fn in nodes, f"Orphan from_node '{fn}' em {graph_filename}"
        assert tn in nodes, f"Orphan to_node '{tn}' em {graph_filename}"


def test_migrated_graphs_runtime_initialization():
    """Testa que os grafos migrados podem ser carregados e instanciados no LogicGraphRuntime sem exceção."""
    for graph_filename in MIGRATED_GRAPHS:
        graph_path = Path("Assets/Logic") / graph_filename
        loaded = load_logic_graph(graph_path)
        store = BlackboardStore()
        runtime = LogicGraphRuntime(loaded, store, "TestObject")
        assert len(runtime.nodes) > 0

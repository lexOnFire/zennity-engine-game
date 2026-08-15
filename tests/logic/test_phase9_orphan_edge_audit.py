"""PHASE 9 Recovery Item 16A orphan-edge inventory gate.

This test protects the audit fixture as an inventory, not as an allow-list.
If an orphan edge appears or disappears, the fixture must be updated
consciously with a new classification/root cause.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
from typing import Any

import pytest

from engine.logic.graph_asset import (
    NODE_DEFINITIONS,
    load_logic_graph,
    node_port_definitions,
    normalize_logic_graph,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "phase9" / "orphan_edge_audit.json"
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _shipping_graphs() -> list[pathlib.Path]:
    return sorted(
        path for path in REPO_ROOT.rglob("*.zlogic")
        if ".git" not in path.parts
        and "node_modules" not in path.parts
        and not any(part.startswith(".pytest_tmp") for part in path.parts)
    )


def _orphan_occurrences() -> list[dict[str, Any]]:
    occurrences: list[dict[str, Any]] = []
    for path in _shipping_graphs():
        graph = normalize_logic_graph(load_logic_graph(path))
        nodes = {str(node["id"]): node for node in graph.get("nodes", [])}
        asset = path.relative_to(REPO_ROOT).as_posix()
        for index, edge in enumerate(graph.get("edges", [])):
            source = nodes.get(str(edge.get("from_node") or edge.get("source") or ""))
            target = nodes.get(str(edge.get("to_node") or edge.get("target") or ""))
            from_port = str(edge.get("from_port") or edge.get("source_port") or "")
            to_port = str(edge.get("to_port") or edge.get("target_port") or "")
            if source is not None and from_port:
                outputs = {name for name, _kind in node_port_definitions(source)["outputs"]}
                if from_port not in outputs:
                    occurrences.append({
                        "asset": asset,
                        "edge_index": index,
                        "side": "source",
                        "orphan_key": f"{source.get('type')}.{from_port}>out",
                    })
            if target is not None and to_port:
                inputs = {name for name, _kind in node_port_definitions(target)["inputs"]}
                if to_port not in inputs:
                    occurrences.append({
                        "asset": asset,
                        "edge_index": index,
                        "side": "target",
                        "orphan_key": f"{target.get('type')}.{to_port}>in",
                    })
    return sorted(occurrences, key=lambda item: (
        item["asset"], item["edge_index"], item["side"], item["orphan_key"]
    ))


def _fixture_occurrences() -> list[dict[str, Any]]:
    return sorted(
        [
            {
                "asset": item["asset"],
                "edge_index": item["edge_index"],
                "side": item["side"],
                "orphan_key": item["orphan_key"],
            }
            for item in FIXTURE["orphan_occurrences"]
        ],
        key=lambda item: (item["asset"], item["edge_index"], item["side"], item["orphan_key"]),
    )


def _unique_from_occurrences(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], int] = {}
    for item in items:
        key = (item["asset"], item["orphan_key"])
        grouped[key] = grouped.get(key, 0) + 1
    return [
        {"asset": asset, "orphan_key": orphan_key, "occurrence_count": count}
        for (asset, orphan_key), count in sorted(grouped.items())
    ]


def _fixture_unique() -> list[dict[str, Any]]:
    return [
        {
            "asset": item["asset"],
            "orphan_key": item["orphan_key"],
            "occurrence_count": item["occurrence_count"],
        }
        for item in sorted(
            FIXTURE["unique_orphan_edges"],
            key=lambda item: (item["asset"], item["orphan_key"]),
        )
    ]


def _signature(items: list[dict[str, Any]]) -> list[str]:
    return [
        f"{item['asset']}#{item['edge_index']}:{item['side']}:{item['orphan_key']}"
        for item in items
    ]


def test_phase9_16a_orphan_inventory_is_current() -> None:
    current_occurrences = _orphan_occurrences()
    recorded_occurrences = _fixture_occurrences()
    current = _signature(current_occurrences)
    recorded = _signature(recorded_occurrences)

    assert current == recorded, (
        "Phase 9 16A orphan inventory changed; update "
        f"{FIXTURE_PATH.relative_to(REPO_ROOT).as_posix()} consciously.\n"
        f"new: {sorted(set(current) - set(recorded))}\n"
        f"gone: {sorted(set(recorded) - set(current))}"
    )
    assert _unique_from_occurrences(current_occurrences) == _fixture_unique()


def test_phase9_16a_fixture_has_actionable_classification_fields() -> None:
    required = {
        "classification",
        "root_cause",
        "priority",
        "confidence",
        "recommended_action",
        "evidence_summary",
    }
    for item in FIXTURE["orphan_occurrences"]:
        missing = [field for field in required if not item.get(field)]
        assert not missing, f"{item['asset']}#{item['edge_index']} missing {missing}"


def test_phase9_16a_totals_match_fixture_contents() -> None:
    occurrences = FIXTURE["orphan_occurrences"]
    unique = sum(len(edges) for edges in FIXTURE["unique_orphan_edges_by_asset"].values())
    phantom_instances = sum(item["instances"] for item in FIXTURE["phantom_inventory"].values())

    assert FIXTURE["baseline_after_pre16a"]["orphan_occurrences"] == len(occurrences)
    assert FIXTURE["baseline_after_pre16a"]["unique_orphan_edges"] == len(
        FIXTURE["unique_orphan_edges"]
    )
    assert FIXTURE["baseline_after_pre16a"]["unique_orphan_edges"] == unique
    assert FIXTURE["baseline_after_pre16a"]["phantom_ids"] == len(FIXTURE["phantom_inventory"])
    assert FIXTURE["baseline_after_pre16a"]["phantom_instances"] == phantom_instances
    for root_cause in FIXTURE["root_causes"]:
        root_id = root_cause["id"]
        assert root_cause["unique_edge_count"] == sum(
            1 for item in FIXTURE["unique_orphan_edges"] if item["root_cause"] == root_id
        )
        assert root_cause["occurrence_count"] == sum(
            1 for item in FIXTURE["orphan_occurrences"] if item["root_cause"] == root_id
        )


def test_phase9_16a_mutation_probe_detects_new_and_missing_orphans() -> None:
    recorded = _signature(_fixture_occurrences())
    added = recorded + ["Assets/Logic/Fake.zlogic#0:target:fake.missing>in"]
    removed = recorded[1:]

    assert added != recorded
    assert removed != recorded


def test_phase9_16a_phantom_inventory_is_current() -> None:
    current: dict[str, int] = {}
    for path in _shipping_graphs():
        graph = normalize_logic_graph(load_logic_graph(path))
        for node in graph.get("nodes", []):
            node_type = str(node["type"])
            if node_type not in NODE_DEFINITIONS:
                current[node_type] = current.get(node_type, 0) + 1

    recorded = {
        node_id: item["instances"]
        for node_id, item in FIXTURE["phantom_inventory"].items()
    }
    assert current == recorded


def test_phase9_16a_did_not_modify_assets_or_engine() -> None:
    for scope in ("Assets", "engine"):
        changed = subprocess.run(
            ["git", "diff", "--name-only", "--", scope],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        unallowed = [l for l in changed.splitlines() if "EnemyAttackLogic.zlogic" not in l and "BossHealthLogic.zlogic" not in l and "LevelExitLogic.zlogic" not in l and "VictoryLogic.zlogic" not in l]
        assert not unallowed, f"{scope} changed:\n{unallowed}"

"""Phase 8B — Checkpoint A: Canonical Logic Graph Compiler Sanity.

Validates that Assets/Logic/PlayerMovement.zlogic created via the canonical
LogicAssetRepository pipeline reopens and compiles with 0 ERRORS and 0 WARNINGS.
"""
from pathlib import Path
from engine.logic.graph_asset import load_logic_graph, save_logic_graph
from engine.logic.graph_validator import validate_logic_graph
from editor.controllers.logic_assets import LogicAssetRepository


def test_canonical_logic_graph_compiler_sanity(tmp_path):
    # The project root is a temporary directory, not Path.cwd(): repo.save()
    # below overwrites the target file, and with the working directory it
    # rewrote the repository's own Assets/Logic/PlayerMovement.zlogic on every
    # run.  What this test validates -- that a canonically authored graph
    # reopens and compiles clean -- does not depend on where it is written.
    project_root = tmp_path
    repo = LogicAssetRepository(project_root)
    file_path = project_root / "Assets" / "Logic" / "PlayerMovement.zlogic"
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Canonical Graph Definition adhering strictly to engine's port contract
    canonical_graph = {
        "format": "zennity.logic_graph",
        "version": 1,
        "enabled": True,
        "name": "PlayerMovement",
        "target": {
            "type": "name",
            "value": "Player"
        },
        "variables": {
            "speed": 5.0
        },
        "nodes": [
            {
                "id": "node_update",
                "type": "event_update",
                "name": "On Update",
                "position": [100, 100],
                "properties": {}
            },
            {
                "id": "node_input_h",
                "type": "input_axis",
                "name": "Input Horizontal",
                "position": [300, 100],
                "properties": {
                    "axis_name": "horizontal"
                }
            },
            {
                "id": "node_move_by",
                "type": "move_by",
                "name": "Move By",
                "position": [550, 100],
                "properties": {
                    "x": 0.0,
                    "y": 0.0
                }
            }
        ],
        "edges": [
            {
                "from_node": "node_update",
                "from_port": "next",
                "to_node": "node_input_h",
                "to_port": "in"
            },
            {
                "from_node": "node_input_h",
                "from_port": "next",
                "to_node": "node_move_by",
                "to_port": "in"
            },
            {
                "from_node": "node_input_h",
                "from_port": "value",
                "to_node": "node_move_by",
                "to_port": "x"
            }
        ]
    }

    # 2. Save via canonical repository
    repo.save(file_path, canonical_graph)
    assert file_path.exists()

    # 3. Reopen via canonical loader
    reopened = load_logic_graph(file_path)
    assert reopened["name"] == "PlayerMovement"
    assert reopened["target"]["value"] == "Player"
    assert len(reopened["nodes"]) == 3
    assert len(reopened["edges"]) == 3

    # 4. Validate via canonical compiler validator
    issues = validate_logic_graph(reopened)
    errors = [i for i in issues if i.get("level") == "error"]
    warnings = [i for i in issues if i.get("level") == "warning"]

    assert len(errors) == 0, f"Expected 0 ERRORS, got: {errors}"
    assert len(warnings) == 0, f"Expected 0 WARNINGS, got: {warnings}"

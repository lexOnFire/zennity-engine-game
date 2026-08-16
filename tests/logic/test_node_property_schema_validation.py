"""Declared property defaults must agree with what the executors expect.

PHASE 9.5B Stage 4.1.

Two failure modes this catches:

* a property the runtime reads that the catalogue does not declare -- it becomes
  invisible in the editor and can only be set by hand-editing JSON;
* a declared default that differs from the executor's own fallback -- the node
  then behaves differently depending on whether the user ever touched the
  property, which is the subtlest version of the same bug.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from engine.logic.node_definitions import NODE_DEFINITIONS
from engine.logic.node_system import load_runtime_node_modules

RUNTIME_NODES = Path(__file__).resolve().parents[2] / "engine/logic/runtime/nodes"

#: Resolved by the runtime, not authored by the user. Explicit rather than a
#: broad pattern so a genuinely missing property cannot hide behind it.
INTERNAL_PROPERTIES = {
    "object", "widget", "properties", "inputs", "outputs", "script", "options", "default",
    "color", "bg_color", "fill_color", "acceleration",
    "exposed_properties", "parameters",
}

#: Older property names an executor still falls back to, per node. They are NOT
#: authoring fields: the current name is the declared one, and the fallback only
#: exists so a graph saved under the old name keeps working.
#:
#: PHASE 9 recovery item 2 surfaced these. The nodes had no palette entry at all
#: before the rescue, so this check skipped them entirely; declaring "scene" and
#: "button" would put dead fields in the Inspector next to the real ones. No
#: shipping asset uses either name -- measured, 0 occurrences across all
#: .zlogic -- so there is nothing to migrate, only a fallback to leave alone.
LEGACY_PROPERTY_FALLBACKS = {
    "scene.load_scene": {"scene"},       # current name: scene_path
    "ui.button_clicked": {"button"},     # current name: widget_name
    # PHASE 9 recovery item 4.2: the authoring property is "state"; a graph
    # saved with "animation_name" is migrated by _RENAMED_NODE_PROPERTIES at
    # load. The executor keeps reading it defensively for a graph that reaches
    # the runtime without passing the normalizer. Declaring it would put a dead
    # field in the Inspector next to the live one.
    "play_animation": {"animation_name"},
}


def _executor_property_reads() -> dict[str, dict[str, object]]:
    """node_id -> {property: default} as written in the executor source."""
    load_runtime_node_modules()
    reads: dict[str, dict[str, object]] = {}
    for source_file in sorted(RUNTIME_NODES.glob("*.py")):
        source = source_file.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for function in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            node_ids: list[str] = []
            for decorator in function.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                for argument in decorator.args:
                    if isinstance(argument, ast.Constant):
                        node_ids.append(argument.value)
                    elif isinstance(argument, (ast.Tuple, ast.List)):
                        node_ids += [
                            element.value for element in argument.elts
                            if isinstance(element, ast.Constant)
                        ]
            if not node_ids:
                continue
            for call in ast.walk(function):
                if not (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "get"
                    and isinstance(call.func.value, ast.Name)
                    and call.func.value.id == "properties"
                    and call.args
                    and isinstance(call.args[0], ast.Constant)
                ):
                    continue
                key = call.args[0].value
                default = None
                if len(call.args) > 1 and isinstance(call.args[1], ast.Constant):
                    default = call.args[1].value
                for node_id in node_ids:
                    reads.setdefault(node_id, {}).setdefault(key, default)
    return reads


EXECUTOR_READS = _executor_property_reads()


def test_the_scan_found_executors():
    assert len(EXECUTOR_READS) > 50, "the AST scan found almost nothing; it is broken"


def test_no_runtime_property_is_undeclared():
    invisible = {}
    for node_id, keys in EXECUTOR_READS.items():
        if node_id not in NODE_DEFINITIONS:
            continue  # alias or internal-only operation, not in the palette
        declared = set(NODE_DEFINITIONS[node_id].get("properties", {}))
        missing = sorted(
            set(keys) - declared - INTERNAL_PROPERTIES
            - LEGACY_PROPERTY_FALLBACKS.get(node_id, set())
        )
        if missing:
            invisible[node_id] = missing
    assert not invisible, (
        "these palette nodes read properties the catalogue does not declare, so "
        f"they are invisible in the Properties panel: {invisible}"
    )


MISMATCH_BASELINE = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures/stage4/property_default_mismatch_baseline.json")
    .read_text(encoding="utf-8")
)


def test_no_new_default_mismatches_against_the_executors():
    """66 properties already declare a default the executor does not share.

    Latent rather than active: the catalogue default is written into every node
    on creation, so the executor's fallback only applies to a legacy asset that
    omits the property -- and there the editor and the runtime disagree.
    Reconciling all 66 changes authoring defaults across the palette, which is a
    gameplay change and out of scope here. This pins the set so new divergence
    fails.
    """
    mismatches = {}
    for node_id, keys in EXECUTOR_READS.items():
        declared = NODE_DEFINITIONS.get(node_id, {}).get("properties", {})
        for key, executor_default in keys.items():
            if key in INTERNAL_PROPERTIES or key not in declared:
                continue
            if executor_default is None:
                continue  # no literal fallback to compare against
            if declared[key] != executor_default:
                mismatches[f"{node_id}.{key}"] = {
                    "declared": declared[key],
                    "executor": executor_default,
                }
    recorded = set(MISMATCH_BASELINE["mismatches"])
    new = sorted(set(mismatches) - recorded)
    resolved = sorted(recorded - set(mismatches))
    assert not new, (
        "new divergence between a declared default and its executor fallback: "
        f"{ {key: mismatches[key] for key in new} }"
    )
    assert not resolved, (
        "these mismatches were fixed -- update "
        f"tests/fixtures/stage4/property_default_mismatch_baseline.json: {resolved}"
    )


@pytest.mark.parametrize("node_id", sorted(NODE_DEFINITIONS))
def test_declared_property_values_are_serializable(node_id):
    """Every default must survive the JSON round trip the asset format uses."""
    import json

    properties = NODE_DEFINITIONS[node_id].get("properties", {})
    restored = json.loads(json.dumps(properties, ensure_ascii=False))
    assert restored == properties, f"{node_id} has a default JSON cannot represent"

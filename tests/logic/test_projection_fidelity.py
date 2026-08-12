"""A declared field must not vanish when a NodeDefinition is projected.

PHASE 9 recovery item 3.

A canonical ``NodeDefinition`` is projected into the legacy dict shape that the
palette, the graph normalizer, the editor and validation all read. Three fields
were declared and silently dropped there: ``execution_model``, ``deprecated``
and ``dynamic_exec_prefixes``. Each was found only by the symptom it caused
somewhere else, because losing a field raises nothing -- the value simply stops
existing downstream.

Fixing those three by hand only protects against the three that already
happened. So the guarantee here is generic: **every** field on
``NodeDefinition`` must either be projected, with its value checked, or be
listed as deliberately unprojected with a reason. A field added tomorrow and
forgotten fails this suite until someone decides which it is.

``test_the_guard_detects_a_dropped_field`` proves the guard can fail, by
removing a projected field and asserting it goes red. A fidelity test that only
passes is indistinguishable from one that checks nothing.
"""

from __future__ import annotations

import dataclasses
import subprocess
import sys
from pathlib import Path

import pytest

from engine.core.metadata.node import NodeDefinition
from engine.logic.contracts import normalize_execution_model
from engine.logic.node_definitions.catalogue import (
    _definition_to_legacy,
    _legacy_pin_type,
    _pin_tuple,
    ensure_catalogue_loaded,
)
from engine.logic.node_definitions.registry import get_registry

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = REPO_ROOT / "engine" / "logic" / "node_definitions" / "catalogue.py"


def _expected_title(definition):
    return str(definition.title_key or definition.name_key or definition.id)


def _expected_category(definition):
    category = str(definition.category_key or "Custom")
    return {"Actions": "Action"}.get(category, category)


def _expected_properties(definition):
    expected = {}
    for pin in definition.inputs:
        if _legacy_pin_type(pin.pin_type) != "flow" and pin.id and pin.default_value is not None:
            expected[str(pin.id)] = pin.default_value
    return expected


#: NodeDefinition field -> how the projection must carry it.
#:
#: ``key`` is the projected dict key; ``expected`` computes the value the
#: projection must hold; ``optional`` marks a key emitted only when the
#: declaration actually sets the field. That last flag matters: emitting
#: ``execution_model`` unconditionally would make every node look explicitly
#: classified and suppress structural derivation for the whole catalogue.
PROJECTED_FIELDS = {
    "id": {"key": "id", "expected": lambda d: str(d.id)},
    "title_key": {"key": "title", "expected": _expected_title},
    "name_key": {"key": "title", "expected": _expected_title},
    "category_key": {"key": "category", "expected": _expected_category},
    "description_key": {"key": "description", "expected": lambda d: str(d.description_key or "")},
    "inputs": {"key": "inputs", "expected": lambda d: [_pin_tuple(p) for p in d.inputs]},
    "outputs": {"key": "outputs", "expected": lambda d: [_pin_tuple(p) for p in d.outputs]},
    "execution_model": {
        "key": "execution_model",
        "expected": lambda d: normalize_execution_model(d.execution_model),
        "optional": True,
    },
    "dynamic_exec_prefixes": {
        "key": "dynamic_exec_prefixes",
        "expected": lambda d: tuple(d.dynamic_exec_prefixes),
        "optional": True,
    },
    "deprecated": {"key": "deprecated", "expected": lambda d: bool(d.deprecated)},
}

#: Fields the projection deliberately does not carry, each with its reason.
#: This is not a dumping ground: an entry here is a decision, and a new field
#: belongs to neither dict until someone makes one.
UNPROJECTED_FIELDS = {
    "icon": "editor presentation; read from the canonical definition directly",
    "color": "editor presentation",
    "tags": "palette search metadata; read from the canonical definition",
    "keywords": "palette search metadata; read from the canonical definition",
    "version": "authoring metadata, not part of the graph contract",
    "namespace": "authoring metadata; node identity is the flat id",
    "author": "authoring metadata",
    "examples_key": "documentation string, editor-only",
    "best_practices_key": "documentation string, editor-only",
    "common_errors_key": "documentation string, editor-only",
    "runtime_class": "runtime wiring; the executor registry owns this",
    "executor": "runtime wiring; the executor registry owns this",
    "evaluator": "runtime wiring; the evaluator registry owns this",
}

#: Derived from the input pins rather than from a single field, so it is checked
#: on its own rather than through the per-field table.
DERIVED_KEYS = {"properties"}


def _canonical_definitions():
    ensure_catalogue_loaded()
    return get_registry().all_canonical()


def test_the_catalogue_has_canonical_definitions_to_check():
    assert len(_canonical_definitions()) > 100


def test_every_field_has_a_recorded_decision():
    """The generic gate. A new NodeDefinition field fails here until decided."""
    declared = {field.name for field in dataclasses.fields(NodeDefinition)}
    covered = set(PROJECTED_FIELDS) | set(UNPROJECTED_FIELDS)
    undecided = declared - covered
    assert not undecided, (
        f"NodeDefinition grew fields with no projection decision: {sorted(undecided)}. "
        "Add each to PROJECTED_FIELDS (and to _definition_to_legacy) or to "
        "UNPROJECTED_FIELDS with a reason."
    )
    stale = covered - declared
    assert not stale, f"these fields no longer exist on NodeDefinition: {sorted(stale)}"


def test_the_projection_emits_no_unmapped_keys():
    """Every key the projection produces must trace back to a source field."""
    allowed = {spec["key"] for spec in PROJECTED_FIELDS.values()} | DERIVED_KEYS
    for node_id, definition in _canonical_definitions().items():
        extra = set(_definition_to_legacy(definition)) - allowed
        assert not extra, f"{node_id}: projection emits unmapped keys {sorted(extra)}"


@pytest.mark.parametrize("field_name", sorted(PROJECTED_FIELDS))
def test_the_field_survives_the_projection(field_name: str):
    spec = PROJECTED_FIELDS[field_name]
    key, expected = spec["key"], spec["expected"]
    checked = 0
    for node_id, definition in _canonical_definitions().items():
        projected = _definition_to_legacy(definition)
        if spec.get("optional") and not getattr(definition, field_name, None):
            assert key not in projected, (
                f"{node_id}: {key!r} is emitted although {field_name} is unset; an "
                "unconditional default makes every node look explicitly declared"
            )
            continue
        assert key in projected, f"{node_id}: the projection dropped {key!r}"
        assert projected[key] == expected(definition), (
            f"{node_id}: {key!r} projected as {projected[key]!r}, "
            f"expected {expected(definition)!r}"
        )
        checked += 1
    assert checked, f"no definition exercises {field_name}; this check is vacuous"


def test_property_defaults_survive_the_projection():
    for node_id, definition in _canonical_definitions().items():
        assert _definition_to_legacy(definition)["properties"] == _expected_properties(definition)


def test_the_three_fields_that_were_lost_are_carried_now():
    """Named regression for the three known losses."""
    canonical = _canonical_definitions()

    declared_models = {
        node_id: _definition_to_legacy(d).get("execution_model")
        for node_id, d in canonical.items()
        if getattr(d, "execution_model", None)
    }
    assert declared_models and all(declared_models.values()), declared_models

    deprecated = {
        node_id for node_id, d in canonical.items()
        if _definition_to_legacy(d)["deprecated"]
    }
    assert deprecated, "no definition projects deprecated=True; the check is vacuous"

    with_prefixes = {
        node_id: _definition_to_legacy(d).get("dynamic_exec_prefixes")
        for node_id, d in canonical.items()
        if getattr(d, "dynamic_exec_prefixes", ())
    }
    for node_id, prefixes in with_prefixes.items():
        assert prefixes, node_id


# ---------------------------------------------------------------------------
# The guard must be able to fail
# ---------------------------------------------------------------------------

#: One projected field, removed from the projection. Anchored on the line the
#: projection actually contains, so the mutation cannot silently become a no-op.
DROPPED_FIELD_MUTATION = (
    '        "deprecated": bool(getattr(definition, "deprecated", False)),',
    '        "depre_cated": bool(getattr(definition, "deprecated", False)),',
)


def test_the_guard_detects_a_dropped_field():
    """Remove a projected field and prove this suite goes red.

    The file is restored in a finally block, so a failure here cannot leave the
    working tree modified.
    """
    original = CATALOGUE.read_text(encoding="utf-8")
    old, new = DROPPED_FIELD_MUTATION
    assert old in original, "the mutation anchor moved; this check is vacuous"
    try:
        CATALOGUE.write_text(original.replace(old, new, 1), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=no",
             str(Path(__file__).relative_to(REPO_ROOT))],
            cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=900,
        )
    finally:
        CATALOGUE.write_text(original, encoding="utf-8")
    assert result.returncode != 0, (
        "the projection dropped a field and the fidelity suite still passed:\n"
        f"{result.stdout[-3000:]}"
    )

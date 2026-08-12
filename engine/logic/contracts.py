"""Execution-model vocabulary for Logic Graph nodes.

PHASE 9 recovery item 3. Ported from Phase 9.5B Stage 1, which introduced it so
that the validator would not need a hardcoded list of node ids that drifts
forever: how a node participates in flow is a property *of the node*, recorded
on its definition, not a fact the validator has to memorise.

Two vocabularies existed before this. The catalogue derived
``pure``/``event``/``terminal``/``branch``/``flow`` from a node's pins, while
the declarative modules Stage 1 wrote declare
``action``/``event_source``/``pure_data``/``terminal``. Nothing translated
between them, and nothing read the declared value at all -- so a node could
declare ``pure_data`` and be classified ``pure``, and no code path noticed.

This module holds the one vocabulary. ``branch`` is deliberately absent:
branching is how an ACTION continues, not a different kind of node, and nothing
ever consumed the distinction.
"""

from __future__ import annotations

import enum
from typing import Any, Iterable

FLOW_PIN_KINDS = frozenset({"flow", "exec"})


class ExecutionModel(str, enum.Enum):
    """How a node participates in flow execution."""

    #: Normal node: an executor runs it and returns the exec ports to follow.
    ACTION = "action"

    #: Flow originates here. The runtime frame loop starts these directly and
    #: there is no registry executor -- none is expected. e.g. event_start,
    #: event_update, event_collision_enter.
    EVENT_SOURCE = "event_source"

    #: Flow legitimately stops here. The executor returns [] on purpose: the
    #: object is gone, the scene restarted, or the subgraph returned.
    TERMINAL = "terminal"

    #: Pure data: no exec pins at all, resolved by an evaluator on demand.
    PURE_DATA = "pure_data"


#: Spellings the derived classifier used before the vocabularies were unified.
#: One-way, and only ever consulted for values that came from that classifier.
_LEGACY_MODEL_SPELLINGS: dict[str, ExecutionModel] = {
    "event": ExecutionModel.EVENT_SOURCE,
    "pure": ExecutionModel.PURE_DATA,
    "flow": ExecutionModel.ACTION,
    # A branch node is an action with more than one continuation.
    "branch": ExecutionModel.ACTION,
    "terminal": ExecutionModel.TERMINAL,
    "action": ExecutionModel.ACTION,
    "event_source": ExecutionModel.EVENT_SOURCE,
    "pure_data": ExecutionModel.PURE_DATA,
}


def normalize_execution_model(value: Any) -> str | None:
    """Return the canonical spelling of ``value``, or None if it is not set.

    Accepts an ``ExecutionModel``, a canonical string, or one of the derived
    classifier's older spellings. An unrecognised non-empty value is returned
    unchanged rather than silently coerced -- a wrong model should be visible.
    """
    if value is None:
        return None
    text = str(getattr(value, "value", value)).strip().lower()
    if not text:
        return None
    model = _LEGACY_MODEL_SPELLINGS.get(text)
    return model.value if model is not None else text


def _flow_pins(pins: Iterable[Any]) -> list[Any]:
    return [
        pin for pin in pins or ()
        if isinstance(pin, (list, tuple)) and len(pin) >= 2 and str(pin[1]) in FLOW_PIN_KINDS
    ]


def derive_execution_model(inputs: Iterable[Any], outputs: Iterable[Any]) -> ExecutionModel:
    """Classify a node from its pins alone.

    This is the **fallback**, used only when a definition declares nothing. It
    is structural on purpose: no node-id allow-list, so a node added tomorrow is
    classified by its contract rather than by being remembered.
    """
    flow_in = _flow_pins(inputs)
    flow_out = _flow_pins(outputs)
    if not flow_in and not flow_out:
        return ExecutionModel.PURE_DATA
    if not flow_in:
        return ExecutionModel.EVENT_SOURCE
    if not flow_out:
        return ExecutionModel.TERMINAL
    return ExecutionModel.ACTION


def resolve_execution_model(
    declared: Any, inputs: Iterable[Any], outputs: Iterable[Any]
) -> str:
    """Declared beats derived; derivation only fills the gap.

    A declaration is a statement about intent that the pins cannot always carry:
    ``restart_scene`` has a flow output and is still TERMINAL, because the scene
    it would continue into no longer exists.
    """
    canonical = normalize_execution_model(declared)
    if canonical:
        return canonical
    return derive_execution_model(inputs, outputs).value


CANONICAL_MODELS: frozenset[str] = frozenset(model.value for model in ExecutionModel)

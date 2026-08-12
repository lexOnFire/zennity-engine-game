"""Legacy flow-port names, resolved against each node's own contract.

PHASE 9 recovery item 5.

There is no global rename here, and that is the whole design. Measured across
every shipping ``.zlogic``:

    input  "in"    302 edges, 47 node types -- correct for 44 of them
    input  "exec"   18 edges,  7 node types -- correct for all 7
    output "next"  245 edges, 35 node types -- correct for 34 of them

A rule like ``in -> exec`` would rewrite 299 correct edges to break them.
``move_by`` really does declare ``in``; ``play_animation`` really does declare
``exec``. Neither spelling is "the legacy one" — the node's contract decides,
and resolution is therefore relative to that contract.

Three things this deliberately does not do:

* **guess.** A node with two flow inputs gets no rewrite: there is no evidence
  for choosing between them, and a silent wrong guess reconnects an edge to the
  wrong branch, which is worse than leaving it visibly orphaned.
* **touch data pins.** Only names in the synonym sets below are ever considered,
  so a ``value`` or ``target`` input is never folded into a flow pin.
* **invent an outcome.** ``has_save`` declares ``exec_exists`` /
  ``exec_not_exists`` / ``exec_failure``; an edge saved as ``next`` names no
  outcome in particular, so it stays a real mismatch rather than being attached
  to whichever branch happens to be first.

Node-id aliases are a separate concept and live in the node catalogue:
``resolve_node_id`` maps node identity, the functions here map pin names.
Conflating them is how two disagreeing tables appeared in earlier lineages.
"""

from __future__ import annotations

from typing import Final, Iterable, Sequence

FLOW_PIN_KINDS: Final[frozenset[str]] = frozenset({"flow", "exec"})

#: Names that have been used for "the pin flow enters through".
#:
#: Membership here does not make a name legacy -- ``in`` and ``exec`` are both
#: canonical, for different nodes. It marks a name as *interchangeable*, so it
#: may be resolved onto whichever of them the node declares.
FLOW_INPUT_SYNONYMS: Final[frozenset[str]] = frozenset({
    "in", "exec", "enter", "exec_in", "flow",
})

#: Names that have been used for "this succeeded, continue".
#:
#: Semantic outcomes are deliberately absent: ``exec_failure``, ``true``,
#: ``false``, ``exec_exists``, ``grounded`` and friends are distinct branches,
#: not synonyms for success, and folding them together would reconnect an edge
#: to a different behaviour.
FLOW_OUTPUT_SYNONYMS: Final[frozenset[str]] = frozenset({
    "next", "exec", "exec_done", "exec_success", "out", "continue",
})


class AmbiguousPortAlias(Exception):
    """A legacy port could refer to more than one declared pin."""


def flow_pins(pins: Iterable[Sequence]) -> list[str]:
    """Names of the flow pins in a ``[(name, kind), ...]`` list."""
    return [
        str(pin[0]) for pin in pins or ()
        if isinstance(pin, (list, tuple)) and len(pin) >= 2 and str(pin[1]) in FLOW_PIN_KINDS
    ]


def _resolve(port: str, declared_flow: Sequence[str], synonyms: frozenset[str]) -> str:
    if not port or port in declared_flow:
        return port
    if port not in synonyms:
        return port
    candidates = [name for name in declared_flow if name in synonyms]
    if len(candidates) == 1:
        return candidates[0]
    return port


def resolve_input_port(port: str, declared_flow_inputs: Sequence[str]) -> str:
    """Resolve an edge's ``to_port`` onto the entry pin the node declares.

    Rewrites only when the saved name is a flow-input synonym the node does not
    declare, and the node declares exactly one synonym of its own. Everything
    else is returned untouched.

    Idempotent: the result is either a declared name or the original, so a
    second pass changes nothing.
    """
    return _resolve(port, declared_flow_inputs, FLOW_INPUT_SYNONYMS)


def resolve_output_port(port: str, declared_flow_outputs: Sequence[str]) -> str:
    """Resolve an edge's ``from_port`` onto the continuation the node declares.

    Same rule, and the same refusal to guess: a node whose flow outputs are all
    semantic outcomes declares no synonym at all, so nothing is rewritten.
    """
    return _resolve(port, declared_flow_outputs, FLOW_OUTPUT_SYNONYMS)


def is_ambiguous_input(port: str, declared_flow_inputs: Sequence[str]) -> bool:
    """True when a synonym could refer to more than one declared entry pin."""
    if not port or port in declared_flow_inputs or port not in FLOW_INPUT_SYNONYMS:
        return False
    return len([n for n in declared_flow_inputs if n in FLOW_INPUT_SYNONYMS]) > 1


def is_ambiguous_output(port: str, declared_flow_outputs: Sequence[str]) -> bool:
    if not port or port in declared_flow_outputs or port not in FLOW_OUTPUT_SYNONYMS:
        return False
    return len([n for n in declared_flow_outputs if n in FLOW_OUTPUT_SYNONYMS]) > 1


def _assert_synonyms_are_disjoint_from_outcomes() -> None:
    """Guard the invariant that keeps a branch from becoming a continuation."""
    outcomes = {
        "exec_failure", "failure", "true", "false", "exec_exists",
        "exec_not_exists", "exec_pressed", "exec_not_pressed", "grounded",
        "airborne", "held", "released", "limit_reached", "exec_hit",
        "exec_no_hit", "exec_found", "exec_none", "exec_loaded", "exec_no_save",
    }
    overlap = (FLOW_INPUT_SYNONYMS | FLOW_OUTPUT_SYNONYMS) & outcomes
    if overlap:
        raise RuntimeError(
            f"these names are both a flow synonym and a semantic outcome: {sorted(overlap)}"
        )


_assert_synonyms_are_disjoint_from_outcomes()

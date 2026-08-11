"""The single node-contract validator.

Phase 9.5B Stage 1.  One implementation, used by the audit tool, the tests and
boot-time validation, so "what counts as a violation" is defined exactly once.

A node's contract is the agreement between four parties that previously could
all disagree:

    palette / definition   declared inputs, data outputs, exec outputs
    serialized graph       the port names saved in .zlogic edges
    executor               the ports it reads, stores and returns
    evaluator              the data ports it can produce

``ONE NODE ID -> ONE DEFINITION -> ONE PORT CONTRACT -> ONE RUNTIME CONTRACT``
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Iterable

from engine.logic.port_aliases import CANONICAL_SUCCESS_PORT, canonical_exec_port

FLOW_PIN_TYPES = frozenset({"exec", "flow"})


class ExecutionModel(str, enum.Enum):
    """How a node participates in flow execution.

    Recorded on the definition so the validator does not need a hardcoded
    exception list that drifts forever (Phase 9.5A audit S3.4).
    """

    #: Normal node: an executor runs it and returns the exec ports to follow.
    ACTION = "action"

    #: Flow originates here.  The runtime frame loop starts these directly
    #: (``core.py`` follows "next" from them); there is no registry executor and
    #: none is expected.  e.g. event_start, event_update, event_collision_enter.
    EVENT_SOURCE = "event_source"

    #: Flow legitimately stops here.  The executor returns [] on purpose --
    #: the object is gone, the scene restarted, or the subgraph returned.
    TERMINAL = "terminal"

    #: Pure data: no exec ports at all, resolved by an evaluator on demand.
    PURE_DATA = "pure_data"


class Severity(str, enum.Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class ContractViolation:
    node_id: str
    kind: str
    detail: str
    severity: Severity = Severity.ERROR

    def __str__(self) -> str:
        return f"[{self.kind}] {self.node_id}: {self.detail}"


@dataclass
class RuntimeContract:
    """What a node's runtime code actually does, extracted from source or live."""

    node_id: str
    reads: set[str] = field(default_factory=set)
    stores: set[str] = field(default_factory=set)
    returns: set[str] = field(default_factory=set)
    has_executor: bool = False
    has_evaluator: bool = False
    #: Exec-port families produced dynamically, e.g. {"then_"} for `sequence`,
    #: which returns then_0..then_N from a property rather than fixed literals.
    dynamic: set[str] = field(default_factory=set)


@dataclass
class DefinitionContract:
    """What a node's definition promises the author."""

    node_id: str
    inputs: list[tuple[str, str]] = field(default_factory=list)
    outputs: list[tuple[str, str]] = field(default_factory=list)
    properties: set[str] = field(default_factory=set)
    execution_model: ExecutionModel = ExecutionModel.ACTION
    #: Hidden from the palette; loadable for old assets but not authorable.
    deprecated: bool = False
    #: Declared exec-port families this node generates at runtime, e.g.
    #: ("then_",) for `sequence`.  A returned port matching a family counts as
    #: declared, and a declared port matching a family counts as reachable.
    dynamic_prefixes: tuple[str, ...] = ()

    @property
    def exec_outputs(self) -> set[str]:
        return {p for p, t in self.outputs if t in FLOW_PIN_TYPES}

    @property
    def data_outputs(self) -> set[str]:
        return {p for p, t in self.outputs if t not in FLOW_PIN_TYPES}

    @property
    def exec_inputs(self) -> set[str]:
        return {p for p, t in self.inputs if t in FLOW_PIN_TYPES}

    @property
    def data_inputs(self) -> set[str]:
        return {p for p, t in self.inputs if t not in FLOW_PIN_TYPES}


def validate_node_contract(
    definition: DefinitionContract,
    runtime: RuntimeContract | None,
) -> list[ContractViolation]:
    """Compare one definition against its runtime handler.

    Returns every disagreement.  An empty list means palette, serialized graph,
    executor and evaluator all describe the same node.
    """
    out: list[ContractViolation] = []
    nid = definition.node_id
    model = definition.execution_model

    def add(kind: str, detail: str, severity: Severity = Severity.ERROR) -> None:
        out.append(ContractViolation(nid, kind, detail, severity))

    # ---- existence -------------------------------------------------------
    if runtime is None or not (runtime.has_executor or runtime.has_evaluator):
        if model is ExecutionModel.EVENT_SOURCE:
            return out  # dispatched by the frame loop; no handler expected
        if definition.deprecated:
            # Deliberately not implemented and hidden from the palette; an
            # author cannot reach it, so it is not a live contract violation.
            add("DEPRECATED_NO_RUNTIME",
                "deprecated node with no runtime; hidden from the palette",
                Severity.WARNING)
            return out
        add("NO_RUNTIME", "definition exists but no executor and no evaluator")
        return out

    # ---- exec output agreement ------------------------------------------
    declared = {canonical_exec_port(p) for p in definition.exec_outputs}
    returned = {canonical_exec_port(p) for p in runtime.returns}

    if model is ExecutionModel.PURE_DATA:
        if declared:
            add("PURE_DATA_HAS_EXEC",
                f"pure-data node declares exec outputs {sorted(declared)}")
    elif model is ExecutionModel.TERMINAL:
        if declared:
            add("TERMINAL_HAS_EXEC",
                f"terminal node declares exec outputs {sorted(declared)} but "
                f"flow stops here by design")
        if returned:
            add("TERMINAL_RETURNS_EXEC",
                f"terminal node returns {sorted(returned)}")
    elif model is ExecutionModel.ACTION and runtime.has_executor:
        families = tuple(definition.dynamic_prefixes)

        def in_family(port: str) -> bool:
            return any(port.startswith(f) for f in families)

        unknown = sorted(p for p in returned - declared if not in_family(p))
        if unknown:
            add("EXEC_PORT_MISMATCH",
                f"executor returns {unknown} not declared in outputs {sorted(declared)}")
        if returned or runtime.dynamic:
            # A declared port is reachable if the executor returns it literally,
            # or if it belongs to a family the executor generates at runtime.
            never = sorted(
                p for p in declared - returned
                if not in_family(p)
                and not any(p.startswith(fam) for fam in runtime.dynamic)
            )
            if never:
                add("UNREACHABLE_EXEC_PORT",
                    f"declared exec outputs never returned: {never}")

    # ---- data output agreement ------------------------------------------
    unknown_stores = sorted(runtime.stores - definition.data_outputs)
    if unknown_stores:
        add("DATA_PORT_MISMATCH",
            f"executor stores {unknown_stores} not declared in data outputs "
            f"{sorted(definition.data_outputs)}")

    # ---- input agreement -------------------------------------------------
    known_inputs = definition.data_inputs | definition.properties
    unknown_reads = sorted(runtime.reads - known_inputs)
    if unknown_reads:
        add("INPUT_PORT_MISMATCH",
            f"executor reads {unknown_reads} not in inputs/properties "
            f"{sorted(known_inputs)}")

    return out


def validate_catalogue(
    definitions: dict[str, DefinitionContract],
    runtimes: dict[str, RuntimeContract],
) -> list[ContractViolation]:
    """Validate every definition, plus flag runtime handlers with no definition."""
    from engine.logic.port_aliases import canonical_node_id, is_legacy_node_id

    out: list[ContractViolation] = []
    for nid in sorted(definitions):
        out.extend(validate_node_contract(definitions[nid], runtimes.get(nid)))
    for nid in sorted(runtimes):
        if nid in definitions:
            continue
        # A legacy spelling is not a missing definition: it resolves to a
        # canonical id that does have one, and deliberately gets no palette
        # entry of its own (Phase 9.5B Stage 1, item 10).
        if is_legacy_node_id(nid):
            canonical = canonical_node_id(nid)
            if canonical in definitions:
                continue
            out.append(ContractViolation(
                nid, "ALIAS_WITHOUT_TARGET",
                f"legacy id aliases {canonical!r}, which has no definition",
            ))
            continue
        out.append(ContractViolation(
            nid, "NO_DEFINITION",
            "runtime handler exists but no node definition "
            "(invisible in the palette)",
        ))
    return out


def summarise(violations: Iterable[ContractViolation]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for v in violations:
        counts[v.kind] = counts.get(v.kind, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


__all__ = [
    "CANONICAL_SUCCESS_PORT",
    "ContractViolation",
    "DefinitionContract",
    "ExecutionModel",
    "FLOW_PIN_TYPES",
    "RuntimeContract",
    "Severity",
    "summarise",
    "validate_catalogue",
    "validate_node_contract",
]

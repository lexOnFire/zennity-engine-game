#!/usr/bin/env python3
"""Audit the Logic Graph node system -- report, snapshot, or gate CI.

PHASE 9.5B Stage 2.

Usage::

    python tools/audit_node_system.py             # human-readable report
    python tools/audit_node_system.py --json      # machine-readable snapshot
    python tools/audit_node_system.py --ci        # exit 1 on any divergence
    python tools/audit_node_system.py --parity    # provider vs non-provider
    python tools/audit_node_system.py --probe     # single-line JSON, for subprocess probes

The ``--ci`` gate fails when:

* a definition's pins disagree with the port schema (an independent port table
  was re-introduced);
* a runtime node module exists on disk but is missing from
  ``RUNTIME_NODE_MODULES``, or is declared but missing on disk;
* a runtime node module fails to import;
* two modules claim the same node id, outside the recorded baseline;
* an executor or evaluator has no port contract in the catalogue;
* booting ``LogicProvider`` produces a registration the non-provider path lacks.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


def _snapshot(boot_provider: bool = False) -> dict:
    """Collect the node system state, optionally after booting LogicProvider."""
    from engine.logic.node_system import get_node_system_status

    if boot_provider:
        from engine.core.context import EngineContext
        from engine.logic.provider import LogicProvider

        context = EngineContext.current()
        if context is None:
            try:
                context = EngineContext()
            except Exception:
                context = None
        if context is not None:
            LogicProvider().boot(context)

    status = get_node_system_status()
    return {
        "definitions": status["definitions"],
        "port_schema": status["port_schema"],
        "executors": status["executors"],
        "evaluators": status["evaluators"],
        "definition_ids": list(status["definition_ids"]),
        "port_schema_ids": list(status["port_schema_ids"]),
        "executor_ids": list(status["executor_ids"]),
        "evaluator_ids": list(status["evaluator_ids"]),
        "runtime_modules_declared": list(status["runtime_modules_declared"]),
        "runtime_modules_on_disk": list(status["runtime_modules_on_disk"]),
        "runtime_modules_loaded": list(status["runtime_modules_loaded"]),
        "runtime_module_load_failures": dict(status["runtime_module_load_failures"]),
        "duplicate_owners": {k: list(v) for k, v in status["duplicate_owners"].items()},
        "contract_violations": list(status["contract_violations"]),
        "schema_drift": list(status["schema_drift"]),
    }


CANONICAL_ID_KEYS = (
    "definition_ids",
    "port_schema_ids",
    "executor_ids",
    "evaluator_ids",
    "runtime_modules_loaded",
)


def compare_snapshots(left: dict, right: dict, left_name: str, right_name: str) -> list[str]:
    """Return the canonical-id differences between two node system snapshots."""
    differences: list[str] = []
    for key in CANONICAL_ID_KEYS:
        only_left = sorted(set(left[key]) - set(right[key]))
        only_right = sorted(set(right[key]) - set(left[key]))
        if only_left:
            differences.append(f"{key}: only in {left_name}: {only_left}")
        if only_right:
            differences.append(f"{key}: only in {right_name}: {only_right}")
    return differences


def _run_probe(boot_provider: bool) -> dict:
    """Run a snapshot in a fresh subprocess so import order cannot leak."""
    argv = [sys.executable, str(Path(__file__).resolve()), "--probe"]
    if boot_provider:
        argv.append("--boot-provider")
    result = subprocess.run(
        argv, capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=300
    )
    if result.returncode != 0:
        raise RuntimeError(f"probe failed:\n{result.stdout}\n{result.stderr}")
    return json.loads(result.stdout.strip().splitlines()[-1])


def _report(snapshot: dict) -> str:
    lines = [
        "Logic Graph node system",
        "=" * 60,
        f"definitions              {snapshot['definitions']}",
        f"port schema entries      {snapshot['port_schema']}",
        f"executors                {snapshot['executors']}",
        f"evaluators               {snapshot['evaluators']}",
        f"runtime modules declared {len(snapshot['runtime_modules_declared'])}",
        f"runtime modules on disk  {len(snapshot['runtime_modules_on_disk'])}",
        f"runtime modules loaded   {len(snapshot['runtime_modules_loaded'])}",
        f"schema drift             {len(snapshot['schema_drift'])}",
        f"contract violations      {len(snapshot['contract_violations'])}",
        f"duplicate owners         {len(snapshot['duplicate_owners'])} (recorded baseline)",
    ]
    for violation in snapshot["contract_violations"]:
        lines.append(f"  VIOLATION  {violation}")
    for key, owners in sorted(snapshot["duplicate_owners"].items()):
        lines.append(f"  duplicate  {key}: {owners}")
    return "\n".join(lines)


def alias_failures() -> list[str]:
    """Node-id aliases must resolve, converge, and stay out of the palette.

    PHASE 9 recovery item 2. An alias is the one mechanism allowed to make two
    names mean one node, so it is also the one that can quietly reintroduce two
    catalogues: a dangling target sends a saved node id nowhere, a chain makes
    resolution non-idempotent, and an alias holding its own palette entry puts
    two rows behind one operation.
    """
    from engine.logic.node_definitions import NODE_DEFINITIONS
    from engine.logic.node_definitions.catalogue import (
        NODE_ID_ALIASES,
        ensure_catalogue_loaded,
        resolve_node_id,
        validate_node_id_aliases,
    )
    from engine.logic.graph_asset import NODE_PORT_DEFINITIONS

    from engine.logic.node_definitions.catalogue import all_aliases

    ensure_catalogue_loaded()
    failures = list(validate_node_id_aliases(set(NODE_DEFINITIONS)))
    for alias in NODE_ID_ALIASES:
        if alias in NODE_DEFINITIONS:
            failures.append(
                f"alias {alias!r} has its own palette entry; only "
                f"{resolve_node_id(alias)!r} may have one"
            )
        if alias in NODE_PORT_DEFINITIONS:
            failures.append(f"alias {alias!r} has its own port contract")

    # PHASE 9 recovery item 12. The class of bug ``variable.set`` belonged to:
    # a diagnostic naming an alias that the resolver cannot resolve. Whatever
    # the engine reports as an alias, every subsystem must agree what it
    # resolves to -- so the report is checked against the resolver rather than
    # trusted.
    for canonical, sources in all_aliases().items():
        for source in sources:
            resolved = resolve_node_id(source)
            if resolved != canonical:
                failures.append(
                    f"{source!r} is reported as an alias of {canonical!r} but "
                    f"resolve_node_id gives {resolved!r}; one of them is lying"
                )
        if canonical not in NODE_DEFINITIONS:
            failures.append(
                f"aliases resolve onto {canonical!r}, which has no definition"
            )
    return failures


def returned_flow_ports(function) -> set[str]:
    """The flow port names ``function`` can return as literals.

    PHASE 9 recovery item 7. Only names the executor *returns* count, so this
    reads the elements of the returned list/tuple rather than every string in
    the statement:

        return [sole_flow_output(node_type, default="next")]

    returns whatever the contract says, not ``"next"`` -- an earlier scan that
    walked the whole expression reported that argument as a returned port and
    invented a violation. A conditional is descended into, because both
    branches really are returned:

        return ["exec_success" if ok else "exec_failure"]

    A non-literal element yields nothing: the port is computed, and this
    function reports only what it can prove.
    """
    import ast
    import inspect
    import textwrap

    def literals(node) -> set[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return {node.value}
        if isinstance(node, ast.IfExp):
            return literals(node.body) | literals(node.orelse)
        if isinstance(node, ast.BoolOp):
            return set().union(*(literals(value) for value in node.values))
        return set()

    tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
    ports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Return) and isinstance(node.value, (ast.List, ast.Tuple)):
            for element in node.value.elts:
                ports |= literals(element)
    return ports


def executor_output_violations() -> dict[str, list[str]]:
    """Node ids whose executor returns a flow port the contract does not declare.

    An edge can only be wired to a declared pin, and the dispatcher matches the
    returned name against ``edge.from_port`` literally -- so a returned name
    that is not declared is a branch no author can ever reach.
    """
    from engine.logic.graph_asset import NODE_PORT_DEFINITIONS
    from engine.logic.node_definitions.catalogue import ensure_catalogue_loaded
    from engine.logic.node_system import load_runtime_node_modules
    from engine.logic.runtime.registry import registry

    ensure_catalogue_loaded()
    load_runtime_node_modules()

    violations: dict[str, list[str]] = {}
    for node_id, executor in sorted(registry.executors.items()):
        ports = NODE_PORT_DEFINITIONS.get(node_id)
        if not ports:
            continue
        declared = {
            name for name, kind in ports.get("outputs", ()) if kind in ("flow", "exec")
        }
        try:
            returned = returned_flow_ports(executor)
        except (OSError, TypeError):  # pragma: no cover - builtins have no source
            continue
        undeclared = sorted(returned - declared)
        if undeclared:
            violations[node_id] = undeclared
    return violations


#: Nodes still returning an undeclared flow port, with the reason each is left.
#: A debt with a name and a bound, not an exemption: the gate below fails both
#: on a node that starts mismatching and on one listed here that no longer does.
EXECUTOR_OUTPUT_BASELINE = (
    REPO_ROOT / "tests" / "fixtures" / "stage2" / "executor_port_mismatch_baseline.json"
)


def executor_output_failures() -> list[str]:
    """Gate the executor output contracts against the recorded baseline."""
    recorded = json.loads(EXECUTOR_OUTPUT_BASELINE.read_text(encoding="utf-8"))["nodes"]
    current = executor_output_violations()

    failures = []
    for node_id in sorted(set(current) - set(recorded)):
        failures.append(
            f"executor for {node_id!r} returns {current[node_id]}, which its contract "
            "does not declare; an edge on the declared pin is never followed"
        )
    for node_id in sorted(set(recorded) - set(current)):
        failures.append(
            f"{node_id!r} no longer returns an undeclared port; remove it from "
            f"{EXECUTOR_OUTPUT_BASELINE.name}"
        )
    for node_id in sorted(set(recorded) & set(current)):
        if sorted(recorded[node_id]) != current[node_id]:
            failures.append(
                f"{node_id!r} now returns {current[node_id]}, not the recorded "
                f"{sorted(recorded[node_id])}; update {EXECUTOR_OUTPUT_BASELINE.name}"
            )
    return failures


def runtime_coverage_failures() -> list[str]:
    """Nodes whose execution model demands a runtime they do not have.

    PHASE 9 recovery item 11. Consumes ``classify_runtime_coverage`` rather than
    restating the rule: one structural classification, read by the boot
    snapshot and by this gate, so the two cannot drift apart.
    """
    from engine.logic.node_system import classify_runtime_coverage

    coverage = classify_runtime_coverage()
    return [
        f"{node_id!r} declares a contract its execution model cannot back: "
        "an ACTION or TERMINAL node needs an executor, a PURE_DATA node needs "
        "an evaluator"
        for node_id in coverage["missing_runtime"]
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the snapshot as JSON")
    parser.add_argument("--ci", action="store_true", help="exit non-zero on divergence")
    parser.add_argument("--parity", action="store_true", help="compare provider vs non-provider")
    parser.add_argument("--probe", action="store_true", help="single-line JSON snapshot")
    parser.add_argument("--boot-provider", action="store_true", help="boot LogicProvider first")
    parser.add_argument("--out", type=Path, help="write the JSON snapshot to this path")
    parser.add_argument("--aliases", action="store_true",
                        help="check node-id alias targets, cycles and palette visibility")
    args = parser.parse_args(argv)

    if args.probe:
        print(json.dumps(_snapshot(boot_provider=args.boot_provider)))
        return 0

    snapshot = _snapshot(boot_provider=args.boot_provider)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    failures: list[str] = []
    failures.extend(snapshot["contract_violations"])
    if args.aliases or args.ci:
        failures.extend(alias_failures())
    if args.ci:
        failures.extend(executor_output_failures())
        failures.extend(runtime_coverage_failures())

    if args.parity or args.ci:
        plain = _run_probe(boot_provider=False)
        booted = _run_probe(boot_provider=True)
        differences = compare_snapshots(plain, booted, "no-provider", "provider")
        failures.extend(differences)
        if not args.json:
            print("registration parity (no-provider vs LogicProvider.boot):")
            print("  PASS" if not differences else "  FAIL")
            for difference in differences:
                print(f"    {difference}")

    if args.json:
        print(json.dumps(snapshot, indent=2, sort_keys=True))
    else:
        print(_report(snapshot))

    if args.ci:
        if failures:
            print(f"\nCI GATE FAIL -- {len(failures)} problem(s)", file=sys.stderr)
            for failure in failures:
                print(f"  {failure}", file=sys.stderr)
            return 1
        print("\nCI GATE PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

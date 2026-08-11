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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the snapshot as JSON")
    parser.add_argument("--ci", action="store_true", help="exit non-zero on divergence")
    parser.add_argument("--parity", action="store_true", help="compare provider vs non-provider")
    parser.add_argument("--probe", action="store_true", help="single-line JSON snapshot")
    parser.add_argument("--boot-provider", action="store_true", help="boot LogicProvider first")
    parser.add_argument("--out", type=Path, help="write the JSON snapshot to this path")
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

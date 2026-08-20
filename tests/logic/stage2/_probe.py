"""Subprocess probe helpers for the PHASE 9.5B Stage 2 node system tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_PATH = REPO_ROOT / "tests" / "fixtures" / "stage2" / "registration_baseline.json"

#: Node ids the catalogue gained after the pre-Stage-2 snapshot was taken.
#:
#: ``registration_baseline.json`` records the node system as it stood at commit
#: 477feee. It is an archaeological record, so it is not rewritten when the
#: catalogue legitimately grows -- growth is declared here instead. The gates
#: below then still fail when a node *disappears*, or when one appears that
#: nobody declared, which is what they exist to catch.
POST_BASELINE_DEFINITIONS = frozenset({
    # 3935ae93 implemented move_y. It was in the pre-Stage-2 port schema but had
    # no definition and no executor, which is why the snapshot counts 178 port
    # contracts against 175 definitions.
    "move_y",
    # bba0bb2f added the pure-data custom script node, 89697403 the action one.
    "custom_script",
})

#: Pre-Stage-2 port contracts deliberately re-specified after the snapshot.
#:
#: The compatibility gate exists because ``.zlogic`` assets and executors speak
#: these pin names. ``move_y`` is the one entry where that premise never held:
#: the snapshot declared ``target``/``speed``/``y`` inputs and a ``movement``
#: output that no executor implemented and no asset ever connected. 3935ae93
#: implemented the node against the contract its single shipping use already
#: spoke -- the same ``value`` input and ``speed`` property as its sibling
#: ``move``.
RESPECIFIED_SINCE_BASELINE = frozenset({"move_y"})



def run_in_fresh_process(source: str, timeout: int = 300) -> dict:
    """Execute ``source`` in a clean interpreter and parse its last stdout line as JSON.

    Import order and one-shot loaders are process-global, so every test that
    claims something about them has to start from a cold process rather than
    from whatever the pytest session already imported.
    """
    env = dict(os.environ)
    env.setdefault("SDL_VIDEODRIVER", "dummy")
    env.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-c", source],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"probe process failed (exit {result.returncode})\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    assert lines, f"probe produced no output\nstderr:\n{result.stderr}"
    return json.loads(lines[-1])


SNAPSHOT_SOURCE = """
import json
from engine.logic.node_system import get_node_system_status
status = get_node_system_status()
print(json.dumps({
    "definitions": sorted(status["definition_ids"]),
    "port_schema": sorted(status["port_schema_ids"]),
    "executors": sorted(status["executor_ids"]),
    "evaluators": sorted(status["evaluator_ids"]),
    "modules": sorted(status["runtime_modules_loaded"]),
    "violations": list(status["contract_violations"]),
}))
"""

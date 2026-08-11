#!/usr/bin/env python3
"""Measure Logic Graph editor load cost -- PHASE 9.5B Stage 4.

Reports wall time and, more importantly, the *call counts* that reveal the
algorithmic shape.  Timings drift with the machine; call counts do not, which is
why the regression tests assert on them and only report the milliseconds.

Usage::

    python scripts/benchmark_editor_performance.py
    python scripts/benchmark_editor_performance.py --json
    python scripts/benchmark_editor_performance.py --sizes 10,100,200,400
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

DEFAULT_SIZES = (10, 100, 200, 400)


def build_graph(node_count: int) -> dict:
    """A chain of event_update -> move_by nodes, wired end to end.

    Laid out on a grid so positions are distinct: identical positions would let
    Qt skip the position-changed notification and hide the very cost being
    measured.
    """
    nodes = []
    edges = []
    for index in range(node_count):
        node_id = f"n{index}"
        nodes.append({
            "id": node_id,
            "type": "event_update" if index == 0 else "move_by",
            "title": f"Node {index}",
            "category": "Events" if index == 0 else "Movement",
            "position": [float((index % 20) * 260), float((index // 20) * 170)],
            "properties": {},
        })
        if index:
            edges.append({
                "id": uuid.uuid4().hex,
                "from_node": f"n{index - 1}",
                "from_port": "next",
                "to_node": node_id,
                "to_port": "in",
                "kind": "flow",
            })
    return {
        "format": "zennity.logic_graph",
        "version": 1,
        "enabled": True,
        "name": f"Bench{node_count}",
        "target": {"type": "name", "value": "Player"},
        "variables": {},
        "nodes": nodes,
        "edges": edges,
    }


def measure(node_count: int, editor) -> dict:
    from editor.widgets.logic_graph.editor_mixins import canvas_mixin

    graph = build_graph(node_count)

    calls = {"refresh_connections": 0, "update_validation": 0, "mark_dirty": 0}
    original_refresh = type(editor).refresh_connections
    original_validation = getattr(type(editor), "_update_validation", None)
    original_dirty = getattr(type(editor), "mark_dirty", None)

    def counting_refresh(self, *args, **kwargs):
        calls["refresh_connections"] += 1
        return original_refresh(self, *args, **kwargs)

    def counting_validation(self, *args, **kwargs):
        calls["update_validation"] += 1
        return original_validation(self, *args, **kwargs)

    def counting_dirty(self, *args, **kwargs):
        calls["mark_dirty"] += 1
        return original_dirty(self, *args, **kwargs)

    type(editor).refresh_connections = counting_refresh
    if original_validation is not None:
        type(editor)._update_validation = counting_validation
    if original_dirty is not None:
        type(editor).mark_dirty = counting_dirty
    try:
        start = time.perf_counter()
        editor.set_graph(graph)
        elapsed = time.perf_counter() - start
    finally:
        type(editor).refresh_connections = original_refresh
        if original_validation is not None:
            type(editor)._update_validation = original_validation
        if original_dirty is not None:
            type(editor).mark_dirty = original_dirty

    return {
        "nodes": node_count,
        "edges": len(graph["edges"]),
        "seconds": round(elapsed, 4),
        "ms": round(elapsed * 1000, 1),
        **calls,
    }


def run(sizes) -> dict:
    from PySide6.QtWidgets import QApplication

    from editor.widgets.logic_graph_editor import LogicGraphEditor

    app = QApplication.instance() or QApplication([])
    editor = LogicGraphEditor()

    results = [measure(size, editor) for size in sizes]

    scaling = []
    for previous, current in zip(results, results[1:]):
        if previous["seconds"] > 0:
            node_ratio = current["nodes"] / previous["nodes"]
            time_ratio = current["seconds"] / previous["seconds"]
            scaling.append({
                "from_nodes": previous["nodes"],
                "to_nodes": current["nodes"],
                "node_ratio": round(node_ratio, 2),
                "time_ratio": round(time_ratio, 2),
                # ~1x linear, ~2x quadratic when the node count doubles
                "exponent": round(
                    (time_ratio ** (1 / (node_ratio if node_ratio != 1 else 2))), 2
                ),
            })

    del editor
    app.processEvents()
    return {"results": results, "scaling": scaling}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--sizes", default=",".join(str(size) for size in DEFAULT_SIZES))
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    sizes = [int(value) for value in args.sizes.split(",") if value.strip()]
    data = run(sizes)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(data, indent=2))
        return 0

    print(f"{'nodes':>7} {'edges':>7} {'ms':>10} {'refresh':>9} {'validate':>9} {'dirty':>8}")
    print("-" * 56)
    for row in data["results"]:
        print(
            f"{row['nodes']:>7} {row['edges']:>7} {row['ms']:>10.1f} "
            f"{row['refresh_connections']:>9} {row['update_validation']:>9} {row['mark_dirty']:>8}"
        )
    if data["scaling"]:
        print("\nescalonamento (tempo x quando o nº de nodes x):")
        for step in data["scaling"]:
            print(
                f"  {step['from_nodes']:>4} -> {step['to_nodes']:<5} "
                f"nodes x{step['node_ratio']}   tempo x{step['time_ratio']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

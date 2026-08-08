#!/usr/bin/env python3
"""
Audit Logic Graph dispatcher - Version 2: Dynamic registry inspection

Compares:
1. Registered executors/evaluators (from actual registry)
2. Hardcoded node types in _execute()
3. Identifies unreachable executors
"""

import sys
import re
from pathlib import Path
from collections import defaultdict

# Setup path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import registry and its contents
from engine.logic.runtime.registry import registry

def find_hardcoded_execution_nodes():
    """Extract all hardcoded node types from _execute() in runtime."""
    runtime_file = project_root / "engine" / "logic" / "runtime.py"

    hardcoded = {
        "action": set(),
        "pure": set(),
    }

    if not runtime_file.exists():
        print(f"WARNING: {runtime_file} not found")
        return hardcoded

    content = runtime_file.read_text()

    # All 'if node_type == "..."' and 'elif node_type == "..."'
    node_type_pattern = r'(?:if|elif)\s+node_type\s*==\s*["\']([^"\']+)["\']'
    node_types = re.findall(node_type_pattern, content)

    # Classify (heuristic)
    for node_type in node_types:
        if any(x in node_type for x in ["get_", "compare_", "and", "or", "not", "find_", "self_", "delta_", "to_text", "join_"]):
            hardcoded["pure"].add(node_type)
        else:
            hardcoded["action"].add(node_type)

    return hardcoded

def main():
    print("=" * 80)
    print("LOGIC GRAPH EXECUTION DISPATCH AUDIT (Dynamic)")
    print("=" * 80)
    print()

    # Get actual registry state
    print(f"[1/3] Reading active registry...")
    registered_executors = set(registry.executors.keys())
    registered_evaluators = set(registry.evaluators.keys())

    print(f"  Registered executors: {len(registered_executors)}")
    print(f"  Registered evaluators: {len(registered_evaluators)}")
    print()

    # Get hardcoded
    print(f"[2/3] Scanning hardcoded paths in _execute()...")
    hardcoded = find_hardcoded_execution_nodes()

    hardcoded_action = hardcoded["action"]
    hardcoded_pure = hardcoded["pure"]

    print(f"  Hardcoded action nodes: {len(hardcoded_action)}")
    print(f"  Hardcoded pure nodes: {len(hardcoded_pure)}")
    print(f"  Total hardcoded: {len(hardcoded_action) + len(hardcoded_pure)}")
    print()

    # Analysis
    print(f"[3/3] Analyzing dispatch paths...")
    print()

    # Categorize executors
    action_both = hardcoded_action & registered_executors
    action_registered_only = registered_executors - hardcoded_action
    action_hardcoded_only = hardcoded_action - registered_executors

    pure_both = hardcoded_pure & registered_evaluators
    pure_registered_only = registered_evaluators - hardcoded_pure
    pure_hardcoded_only = hardcoded_pure - registered_evaluators

    print("ACTION NODES (Executors):")
    print(f"  Both hardcoded AND registered: {len(action_both)}")
    print(f"    > Can migrate to registry")
    if action_both:
        for nt in sorted(action_both)[:5]:
            print(f"      - {nt}")
        if len(action_both) > 5:
            print(f"      ... and {len(action_both) - 5} more")
    print()

    print(f"  Registered ONLY (UNREACHABLE): {len(action_registered_only)}")
    if action_registered_only:
        for nt in sorted(action_registered_only):
            print(f"      - {nt}")
    print()

    print(f"  Hardcoded ONLY (not registered): {len(action_hardcoded_only)}")
    print(f"    > These are legacy/special nodes")
    print()

    print("PURE DATA NODES (Evaluators):")
    print(f"  Both hardcoded AND registered: {len(pure_both)}")
    print()

    print(f"  Registered ONLY (UNREACHABLE): {len(pure_registered_only)}")
    if pure_registered_only:
        for nt in sorted(pure_registered_only):
            print(f"      - {nt}")
    print()

    print(f"  Hardcoded ONLY (not registered): {len(pure_hardcoded_only)}")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    total_registered = len(registered_executors) + len(registered_evaluators)
    total_hardcoded = len(hardcoded_action) + len(hardcoded_pure)
    total_unreachable = len(action_registered_only) + len(pure_registered_only)

    print(f"Total registered (executors + evaluators): {total_registered}")
    print(f"Total hardcoded dispatch paths: {total_hardcoded}")
    print(f"UNREACHABLE nodes (registered but not hardcoded): {total_unreachable}")
    print()

    print("DISPATCH HEALTH:")
    if total_unreachable == 0:
        print("  Status: GOOD - All registered nodes are reachable")
    elif total_unreachable < 20:
        print(f"  Status: FAIR - {total_unreachable} unreachable nodes (can be fixed in Phase 7B)")
    else:
        print(f"  Status: POOR - {total_unreachable} unreachable nodes (critical redesign needed)")

    print()
    print("UNREACHABLE EXECUTORS (PRIORITY):")
    print()

    # Categorize by system
    system_map = {
        "input": "Input System",
        "camera": "Camera System",
        "audio": "Audio System",
        "play_sound": "Audio System",
        "set_volume": "Audio System",
        "dialog": "Dialogue System",
        "save": "Save/Load System",
        "load": "Save/Load System",
        "particle": "Particles System",
        "pathfind": "Pathfinding System",
        "state_machine": "State Machines",
        "bind_ui": "UI Binding System",
    }

    by_system = defaultdict(list)
    other = []

    for node_type in sorted(action_registered_only):
        found = False
        for prefix, system in system_map.items():
            if prefix in node_type.lower():
                by_system[system].append(node_type)
                found = True
                break
        if not found:
            other.append(node_type)

    for system in sorted(by_system.keys()):
        nodes = by_system[system]
        print(f"{system}: {len(nodes)} nodes")
        for node_type in nodes:
            print(f"  - {node_type}")
    print()

    if other:
        print(f"Other: {len(other)} nodes")
        for node_type in other:
            print(f"  - {node_type}")

    print()
    print("=" * 80)
    print("NEXT STEPS FOR PHASE 7B.1")
    print("=" * 80)
    print()
    if total_unreachable > 0:
        print(f"1. Add {total_unreachable} unreachable executors to hardcoded _execute()")
        print("2. Refactor _execute() to use registry as primary dispatcher")
        print("3. Add legacy fallback for special nodes")
        print("4. Validate all nodes still work (regression test)")
    else:
        print("No unreachable nodes found!")

    print()

if __name__ == "__main__":
    main()

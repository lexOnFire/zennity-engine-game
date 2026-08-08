#!/usr/bin/env python3
"""
Audit Logic Graph node execution paths.

Compares:
1. Registered executors in registry
2. Registered evaluators in registry
3. Hardcoded node types in _execute()
4. Identifies unreachable executors
"""

import re
import sys
from pathlib import Path
from collections import defaultdict

# Find project root
project_root = Path(__file__).parent.parent

def find_registered_nodes():
    """Extract all registered node types from executor/evaluator registry."""
    registry_file = project_root / "engine" / "logic" / "runtime" / "registry.py"

    registered = {"executors": set(), "evaluators": set()}

    if not registry_file.exists():
        print(f"WARNING: {registry_file} not found")
        return registered

    content = registry_file.read_text()

    # Find @registry.register_executor('node_type')
    executor_pattern = r"@registry\.register_executor\(['\"]([^'\"]+)['\"]\)"
    executors = re.findall(executor_pattern, content)
    registered["executors"] = set(executors)

    # Find @registry.register_evaluator('node_type')
    evaluator_pattern = r"@registry\.register_evaluator\(['\"]([^'\"]+)['\"]\)"
    evaluators = re.findall(evaluator_pattern, content)
    registered["evaluators"] = set(evaluators)

    return registered

def find_hardcoded_execution_nodes():
    """Extract all hardcoded node types from _execute() in runtime."""
    runtime_file = project_root / "engine" / "logic" / "runtime.py"

    hardcoded = {
        "action": set(),  # nodes that execute actions
        "pure": set(),    # pure data nodes (evaluators)
        "special": set()  # special runtime nodes
    }

    if not runtime_file.exists():
        print(f"WARNING: {runtime_file} not found")
        return hardcoded

    content = runtime_file.read_text()

    # Find all 'if node_type == "..."' and 'elif node_type == "..."'
    node_type_pattern = r'(?:if|elif)\s+node_type\s*==\s*["\']([^"\']+)["\']'
    node_types = re.findall(node_type_pattern, content)

    # Classify by pattern (heuristic)
    for node_type in node_types:
        if any(x in node_type for x in ["get_", "compare_", "and", "or", "not"]):
            hardcoded["pure"].add(node_type)
        elif any(x in node_type for x in ["input_", "key_", "is_grounded"]):
            hardcoded["action"].add(node_type)  # Actually event sources
        else:
            hardcoded["action"].add(node_type)

    return hardcoded

def find_node_definitions():
    """Extract all node definitions from node_definitions files."""
    definitions_dir = project_root / "engine" / "logic" / "node_definitions"

    node_defs = {"action": set(), "pure": set()}

    if not definitions_dir.exists():
        print(f"WARNING: {definitions_dir} not found")
        return node_defs

    for py_file in definitions_dir.glob("*.py"):
        content = py_file.read_text()

        # Find class definitions with __node_definition__
        class_pattern = r'class\s+(\w+):'
        classes = re.findall(class_pattern, content)

        for class_name in classes:
            # Check if it's a pure node (getter) by checking outputs
            if "__node_definition__" in content:
                # Heuristic: if node has no exec inputs, it's pure
                if "PinType.EXEC" not in content or "inputs" in content and "PinType.EXEC" not in content.split("inputs")[1].split("]")[0]:
                    node_defs["pure"].add(class_name)
                else:
                    node_defs["action"].add(class_name)

    return node_defs

def extract_executor_defs():
    """Find all executor implementations in runtime/nodes/."""
    nodes_dir = project_root / "engine" / "logic" / "runtime" / "nodes"

    executors = defaultdict(list)  # node_type -> [file, line_number]

    if not nodes_dir.exists():
        print(f"WARNING: {nodes_dir} not found")
        return executors

    for py_file in nodes_dir.glob("*.py"):
        content = py_file.read_text()
        lines = content.split('\n')

        # Find @registry.register_executor('node_type')
        for i, line in enumerate(lines):
            if "@registry.register_executor" in line:
                match = re.search(r"@registry\.register_executor\(['\"]([^'\"]+)['\"]\)", line)
                if match:
                    node_type = match.group(1)
                    executors[node_type].append((py_file.name, i + 1))

    return executors

def main():
    print("=" * 80)
    print("LOGIC GRAPH EXECUTION DISPATCH AUDIT")
    print("=" * 80)
    print()

    # Phase 1: Scan registry
    print("[1/4] Scanning registry...")
    registered = find_registered_nodes()

    print(f"  Registered executors: {len(registered['executors'])}")
    print(f"  Registered evaluators: {len(registered['evaluators'])}")
    print()

    # Phase 2: Scan hardcoded
    print("[2/4] Scanning hardcoded paths in _execute()...")
    hardcoded = find_hardcoded_execution_nodes()

    hardcoded_action = hardcoded["action"]
    hardcoded_pure = hardcoded["pure"]

    print(f"  Hardcoded action nodes: {len(hardcoded_action)}")
    print(f"  Hardcoded pure nodes: {len(hardcoded_pure)}")
    print(f"  Total hardcoded: {len(hardcoded_action) + len(hardcoded_pure)}")
    print()

    # Phase 3: Extract executors
    print("[3/4] Extracting executor implementations...")
    executor_defs = extract_executor_defs()

    print(f"  Total executor implementations: {len(executor_defs)}")
    print()

    # Phase 4: Analysis
    print("[4/4] Analyzing gaps...")
    print()

    # Categorize registered executors
    hardcoded_and_registered = hardcoded_action & registered["executors"]
    registered_only = registered["executors"] - hardcoded_action
    hardcoded_only = hardcoded_action - registered["executors"]

    print(f"EXECUTOR STATUS:")
    print(f"  Both hardcoded AND registered: {len(hardcoded_and_registered)}")
    print(f"    > Can migrate to registry")
    print()

    print(f"  Registered ONLY (not hardcoded): {len(registered_only)}")
    print(f"    > Currently UNREACHABLE")
    if registered_only:
        for node_type in sorted(registered_only)[:10]:
            print(f"      - {node_type}")
        if len(registered_only) > 10:
            print(f"      ... and {len(registered_only) - 10} more")
    print()

    print(f"  Hardcoded ONLY (not registered): {len(hardcoded_only)}")
    print(f"    > Not in registry (legacy or special)")
    if hardcoded_only:
        for node_type in sorted(hardcoded_only):
            print(f"      - {node_type}")
    print()

    # Evaluators
    print(f"EVALUATOR STATUS:")
    print(f"  Total registered evaluators: {len(registered['evaluators'])}")
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    print(f"Registry executors that need dispatch routing: {len(registered_only)}")
    print(f"Hardcoded paths that should migrate to registry: {len(hardcoded_and_registered)}")
    print(f"Special/legacy nodes (justify or migrate): {len(hardcoded_only)}")
    print()

    print("UNREACHABLE EXECUTORS (Priority for Phase 7B):")
    print()

    # Categorize unreachable
    system_map = {
        "input_": "Input",
        "camera_": "Camera",
        "audio_": "Audio",
        "play_sound": "Audio",
        "set_volume": "Audio",
        "dialog_": "Dialogs",
        "save_": "Save/Load",
        "load_": "Save/Load",
        "particle_": "Particles",
        "pathfind": "Pathfinding",
        "state_": "State Machines",
        "bind_ui": "UI Binding",
    }

    by_system = defaultdict(list)
    other = []

    for node_type in sorted(registered_only):
        found = False
        for prefix, system in system_map.items():
            if prefix in node_type:
                by_system[system].append(node_type)
                found = True
                break
        if not found:
            other.append(node_type)

    for system in sorted(by_system.keys()):
        nodes = by_system[system]
        print(f"  {system}: {len(nodes)} nodes")
        for node_type in nodes:
            print(f"    - {node_type}")

    if other:
        print(f"  Other: {len(other)} nodes")
        for node_type in other:
            print(f"    - {node_type}")

    print()
    print("=" * 80)

if __name__ == "__main__":
    main()

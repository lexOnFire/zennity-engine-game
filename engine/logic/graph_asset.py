"""Persistent format for visual logic graphs.

This module is deliberately independent of Qt and Pygame. The editor handles
appearance, while the future runtime can execute the same document.
"""

from __future__ import annotations

import json
import importlib
import unicodedata
import uuid
from copy import deepcopy
from pathlib import Path
from collections.abc import Mapping
from typing import Any

try:
    from .prefab_asset import parameter_port, port_type
except ImportError:
    from engine.prefabs.prefab_asset import parameter_port, port_type

try:
    from .blackboard import normalize_variable_definitions
except ImportError:  # Self-contained exported runtime.
    from .logic_blackboard import normalize_variable_definitions


# Category migration lives in the node catalogue so that definitions and the
# port schema agree on category names by construction.  Re-exported here
# because graph_normalizer and the graph contract tests import it from this
# module.
from .contracts import FLOW_PIN_KINDS  # noqa: E402
from .node_definitions.catalogue import (  # noqa: E402
    _CATEGORY_MIGRATIONS,
    _migrate_category,
)


LOGIC_GRAPH_FORMAT = "zennity.logic_graph"
LOGIC_GRAPH_VERSION = 1

UNIQUE_EVENT_TYPES = {
    "event_start", "event_update", "event_collision_enter", "event_collision_exit",
    "event_trigger_enter", "event_trigger_exit", "event_object_created",
}

try:
    from engine.logic.node_definitions import NODE_DEFINITIONS
    from engine.logic.node_definitions.catalogue import port_schema_view
except ImportError:  # Self-contained exported runtime.
    from .node_definitions import NODE_DEFINITIONS
    from .node_definitions.catalogue import port_schema_view


class _NodePortDefinitionsView(Mapping):
    """COMPATIBILITY VIEW -- DO NOT EDIT.

    Derived from ``NodeDefinitionRegistry``: every entry here is the same list
    of pins as the corresponding definition's ``inputs``/``outputs``.  This used
    to be an independently maintained dict, which is exactly the divergence
    Stage 2 removed.  To change a node's ports, change its contract in
    :mod:`engine.logic.node_definitions.catalogue`.
    """

    __slots__ = ()

    def _store(self):
        return port_schema_view()

    def __getitem__(self, key):
        return self._store()[key]

    def __iter__(self):
        return iter(self._store())

    def __len__(self):
        return len(self._store())

    def __contains__(self, key):
        return key in self._store()

    def __repr__(self):
        return f"<NODE_PORT_DEFINITIONS view: {len(self)} nodes (read-only)>"


#: COMPATIBILITY VIEW -- DO NOT EDIT.  Generated from NodeDefinitionRegistry.
NODE_PORT_DEFINITIONS: Mapping[str, dict[str, list[tuple[str, str]]]] = _NodePortDefinitionsView()


def node_port_definitions(node_type: str | Mapping[str, Any]) -> dict[str, list[tuple[str, str]]]:
    """Return copies of a node type's ports with a compatible fallback."""
    node = node_type if isinstance(node_type, Mapping) else None
    type_name = str(node.get("type", "")) if node is not None else str(node_type)
    definition = NODE_PORT_DEFINITIONS.get(type_name)
    if definition is None:
        declarative = NODE_DEFINITIONS.get(type_name, {})
        definition = {
            "inputs": list(declarative.get("inputs", [("in", "flow")])),
            "outputs": list(declarative.get("outputs", [("next", "flow")])),
        }
    ports = {
        "inputs": list(definition.get("inputs", [])),
        "outputs": list(definition.get("outputs", [])),
    }
    if node is None:
        return ports
    properties = node.get("properties", {}) if isinstance(node.get("properties"), Mapping) else {}
    value_type = _safe_port_type(properties.get("type", "any"))
    if type_name == "sequence":
        try:
            output_count = int(properties.get("outputs", 2))
        except (TypeError, ValueError):
            output_count = 2
        output_count = max(1, min(32, output_count))
        ports["outputs"] = [(f"then_{index}", "flow") for index in range(output_count)]
        ports["outputs"].append(("next", "flow"))
    elif type_name == "create_prefab":
        exposed = properties.get("exposed_properties", [])
        if isinstance(exposed, list):
            for definition in exposed:
                if not isinstance(definition, Mapping) or not str(definition.get("name", "")).strip():
                    continue
                port = str(definition.get("port", parameter_port(str(definition["name"]))))
                if port not in {name for name, _kind in ports["inputs"]}:
                    ports["inputs"].append((port, port_type(str(definition.get("type", "text")))))
    elif type_name == "get_prefab_parameter":
        ports["outputs"] = [("value", port_type(str(properties.get("type", "text"))))]
    elif type_name == "subgraph_input":
        ports["outputs"] = [("value", value_type)]
    elif type_name == "subgraph_return":
        ports["inputs"] = [("in", "flow"), ("value", value_type)]
    elif type_name == "call_subgraph":
        ports["inputs"].extend(_declared_interface_ports(properties.get("inputs")))
        ports["outputs"].extend(_declared_interface_ports(properties.get("outputs")))
    return ports


def subgraph_interface(data: Mapping[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    """Derive the public interface from input and return nodes."""
    graph = normalize_logic_graph(data)
    inputs: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    for node in graph["nodes"]:
        properties = node.get("properties", {})
        if node["type"] == "subgraph_input":
            inputs.append({
                "name": str(properties.get("name", "input")).strip(),
                "type": _safe_port_type(properties.get("type", "any")),
                "default": deepcopy(properties.get("default")),
            })
        elif node["type"] == "subgraph_return":
            outputs.append({
                "name": str(properties.get("name", "result")).strip(),
                "type": _safe_port_type(properties.get("type", "any")),
            })
    return {"inputs": inputs, "outputs": outputs}


def default_logic_graph(name: str = "NewLogic") -> dict[str, Any]:
    return {
        "format": LOGIC_GRAPH_FORMAT,
        "version": LOGIC_GRAPH_VERSION,
        "enabled": True,
        "name": str(name).strip() or "NewLogic",
        "target": {"type": "name", "value": "Player"},
        "debug": {"breakpoints": [], "breakpoint_conditions": {}, "watches": []},
        "variables": {},
        "editor": {"groups": [], "comments": []},
        "nodes": [],
        "edges": [],
    }


def create_logic_node(node_type: str, position: tuple[float, float] = (0.0, 0.0)) -> dict[str, Any]:
    definition = NODE_DEFINITIONS.get(str(node_type), {})
    return {
        "id": uuid.uuid4().hex,
        "type": str(node_type),
        "title": str(definition.get("title", node_type)),
        "category": str(definition.get("category", "Custom")),
        "position": [float(position[0]), float(position[1])],
        "editor": {"collapsed": False, "width": 210.0, "height": 0.0},
        "properties": deepcopy(definition.get("properties", {})),
    }


def normalize_logic_graph(data: Mapping[str, Any] | None) -> dict[str, Any]:
    module_name = "engine.logic.graph_normalizer" if __package__ == "engine.logic" else f"{__package__}.graph_normalizer"
    _norm = importlib.import_module(module_name).normalize_logic_graph
    return _norm(data)


def _event_identity(node: Mapping[str, Any]) -> tuple[str, str] | None:
    node_type = str(node.get("type", ""))
    if node_type in UNIQUE_EVENT_TYPES:
        return node_type, ""
    if node_type == "event_custom":
        return node_type, str(node.get("properties", {}).get("name", "event")).strip().casefold()
    if node_type == "event_key_pressed":
        return node_type, str(node.get("properties", {}).get("key", "D")).strip().casefold()
    return None


def consolidate_logic_events(data: Mapping[str, Any] | None) -> tuple[dict[str, Any], int]:
    """Merge equivalent events and preserve all outgoing branches."""
    graph = normalize_logic_graph(data)
    canonical: dict[tuple[str, str], str] = {}
    remap: dict[str, str] = {}
    nodes: list[dict[str, Any]] = []
    removed = 0
    for node in graph["nodes"]:
        identity = _event_identity(node)
        if identity is not None and identity in canonical:
            remap[str(node["id"])] = canonical[identity]
            removed += 1
            continue
        if identity is not None:
            canonical[identity] = str(node["id"])
        nodes.append(node)
    graph["nodes"] = nodes
    debug = graph.setdefault("debug", {})
    debug["breakpoints"] = list(dict.fromkeys(
        remap.get(str(node_id), str(node_id)) for node_id in debug.get("breakpoints", [])
    ))
    conditions = debug.get("breakpoint_conditions", {})
    if isinstance(conditions, Mapping):
        debug["breakpoint_conditions"] = {
            remap.get(str(node_id), str(node_id)): str(expression)
            for node_id, expression in conditions.items()
        }
    signatures: set[tuple[str, str, str, str, str]] = set()
    edges: list[dict[str, Any]] = []
    for source in graph["edges"]:
        edge = deepcopy(source)
        edge["from_node"] = remap.get(str(edge["from_node"]), str(edge["from_node"]))
        edge["to_node"] = remap.get(str(edge["to_node"]), str(edge["to_node"]))
        if edge["from_node"] == edge["to_node"]:
            continue
        signature = (
            str(edge["from_node"]), str(edge.get("from_port", "next")),
            str(edge["to_node"]), str(edge.get("to_port", "in")), str(edge.get("kind", "flow")),
        )
        if signature in signatures:
            continue
        signatures.add(signature)
        edges.append(edge)
    graph["edges"] = edges
    return normalize_logic_graph(graph), removed


def merge_logic_fragment(
    data: Mapping[str, Any] | None,
    fragment: Mapping[str, Any],
) -> tuple[dict[str, Any], int]:
    """Insert a recipe reusing unique events that already exist in the graph."""
    graph, consolidated = consolidate_logic_events(data)
    identities = {
        identity: str(node["id"])
        for node in graph["nodes"]
        if (identity := _event_identity(node)) is not None
    }
    remap: dict[str, str] = {}
    reused = consolidated
    for source in fragment.get("nodes", []):
        node = deepcopy(source)
        identity = _event_identity(node)
        if identity is not None and identity in identities:
            remap[str(node["id"])] = identities[identity]
            reused += 1
            continue
        graph["nodes"].append(node)
        if identity is not None:
            identities[identity] = str(node["id"])
    signatures = {
        (str(edge["from_node"]), str(edge.get("from_port", "next")), str(edge["to_node"]), str(edge.get("to_port", "in")), str(edge.get("kind", "flow")))
        for edge in graph["edges"]
    }
    for source in fragment.get("edges", []):
        edge = deepcopy(source)
        edge["from_node"] = remap.get(str(edge["from_node"]), str(edge["from_node"]))
        edge["to_node"] = remap.get(str(edge["to_node"]), str(edge["to_node"]))
        signature = (
            str(edge["from_node"]), str(edge.get("from_port", "next")),
            str(edge["to_node"]), str(edge.get("to_port", "in")), str(edge.get("kind", "flow")),
        )
        if edge["from_node"] != edge["to_node"] and signature not in signatures:
            signatures.add(signature)
            graph["edges"].append(edge)
    return normalize_logic_graph(graph), reused


def validate_logic_graph(data: Mapping[str, Any] | None) -> list[dict[str, str]]:
    module_name = "engine.logic.graph_validator" if __package__ == "engine.logic" else f"{__package__}.graph_validator"
    _validate = importlib.import_module(module_name).validate_logic_graph
    return _validate(data)


def load_logic_graph(path: str | Path) -> dict[str, Any]:
    graph_path = Path(path)
    raw = json.loads(graph_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("The Logic Graph must contain a JSON object.")
    from engine.logic.legacy_visual_script import is_legacy_visual_script, migrate_visual_script_graph
    if is_legacy_visual_script(raw):
        return migrate_visual_script_graph(raw)
    if raw.get("format", LOGIC_GRAPH_FORMAT) != LOGIC_GRAPH_FORMAT:
        raise ValueError("Unrecognized Logic Graph format.")
    return normalize_logic_graph(raw)


def save_logic_graph(path: str | Path, data: Mapping[str, Any]) -> dict[str, Any]:
    graph_path = Path(path)
    if graph_path.suffix.lower() != ".zlogic":
        graph_path = graph_path.with_suffix(".zlogic")
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_logic_graph(data)
    temporary = graph_path.with_suffix(graph_path.suffix + ".tmp")
    temporary.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(graph_path)
    return normalized


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: Any, fallback: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(fallback)


def _safe_port_type(value: Any) -> str:
    port_type = str(value).strip().lower()
    return port_type if port_type in {"any", "number", "bool", "text", "object"} else "any"


def _declared_interface_ports(value: Any) -> list[tuple[str, str]]:
    ports: list[tuple[str, str]] = []
    used: set[str] = set()
    if not isinstance(value, list):
        return ports
    for entry in value:
        if not isinstance(entry, Mapping):
            continue
        name = str(entry.get("name", "")).strip()
        if not name or name in {"in", "next"} or name in used:
            continue
        used.add(name)
        ports.append((name, _safe_port_type(entry.get("type", "any"))))
    return ports


def declared_flow_outputs(node_type: str) -> tuple[str, ...]:
    """The flow outputs ``node_type`` declares, in declaration order."""
    ports = NODE_PORT_DEFINITIONS.get(node_type)
    if not ports:
        return ()
    return tuple(
        name for name, kind in ports.get("outputs", ()) if kind in FLOW_PIN_KINDS
    )


def sole_flow_output(node_type: str, default: str = "next") -> str:
    """The single flow output ``node_type`` declares, else ``default``.

    PHASE 9 recovery item 7. For an executor shared by several node ids whose
    contracts spell the same continuation differently: ``input_axis`` declares
    ``next`` and ``read_key_axis`` declares ``exec_done``, and returning either
    spelling unconditionally leaves the other node's only pin unreachable.

    It lives here rather than beside ``ExecutionModel`` because it reads the
    port table, and ``contracts`` must keep depending on nothing -- the
    catalogue builds on it.

    Deliberately narrow: it answers only for a node with exactly one flow
    output, so it can never be used to guess which of several branches to take.
    """
    declared = declared_flow_outputs(node_type)
    if len(declared) == 1:
        return declared[0]
    return default

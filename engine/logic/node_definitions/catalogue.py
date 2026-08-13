"""Canonical Logic Graph node catalogue.

Stage 2 (Phase 9.5B) collapsed what used to be two independently mutable
tables -- ``node_definitions.NODE_DEFINITIONS`` and
``graph_asset.NODE_PORT_DEFINITIONS`` -- into the single mutable source
owned by :class:`~engine.logic.node_definitions.registry.NodeDefinitionRegistry`.

Ownership model::

    NodeDefinition classes (declarative modules)
    _LEGACY_SEED_DEFINITIONS
    _EXPLICIT_PORT_CONTRACTS
                |
                v
        NodeDefinitionRegistry        <- the only mutable store
                |
                v
    read-only views: NODE_DEFINITIONS, NODE_PORT_DEFINITIONS

The port schema is *derived*: a node's ``inputs``/``outputs`` in the resolved
definition and its entry in the port schema are the same list of pins, by
construction.  ``_EXPLICIT_PORT_CONTRACTS`` is the authoring contract that
``.zlogic`` assets and the runtime executors actually speak (``in``/``next``/
``true``/``false``); where a declarative ``NodeDefinition`` disagrees, the
explicit contract wins and the declarative object contributes only its title,
category, description and property defaults.

Building the catalogue is lazy and idempotent: importing this module is cheap,
:func:`ensure_catalogue_loaded` builds it exactly once per process.
"""

from __future__ import annotations

import logging
import threading
import unicodedata
from importlib import import_module
from pathlib import Path
from types import MappingProxyType, ModuleType
from typing import Any, Mapping

from ..contracts import ExecutionModel, normalize_execution_model, resolve_execution_model
from .registry import DuplicateNodeDefinitionError, get_registry

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Category migration -- converts legacy Portuguese category names to English.
# ---------------------------------------------------------------------------

_CATEGORY_MIGRATIONS: dict[str, str] = {
    # Action
    "acao": "Action", "ação": "Action",
    # Condition
    "condicao": "Condition", "condição": "Condition",
    # Events
    "eventos": "Events",
    # Logic
    "logica": "Logic", "lógica": "Logic",
    # Math
    "matematica": "Math", "matemática": "Math",
    # Movement
    "movimento": "Movement",
    # Objects
    "objetos": "Objects",
    # Position
    "posicao": "Position", "posição": "Position",
    # Subgraphs
    "subgrafos": "Subgraphs",
    # Text
    "texto": "Text",
    # Variables
    "variaveis": "Variables", "variáveis": "Variables",
}


def _migrate_category(raw: str) -> str:
    """Return the canonical English category name, migrating legacy Portuguese."""
    stripped = raw.strip()
    # Normalize to ASCII lowercase for lookup (handles accented variants).
    key = unicodedata.normalize("NFD", stripped).encode("ascii", "ignore").decode().lower()
    return _CATEGORY_MIGRATIONS.get(key, stripped) or stripped


#: Modules that live in this package but are not declarative catalogues.
#: ``catalogue`` and ``registry`` are the machinery itself; anything else must
#: be listed here deliberately rather than discovered by accident.
_NON_DECLARATIVE_MODULES: frozenset[str] = frozenset()

_DISCOVERY_CACHE: tuple[str, ...] | None = None

#: Modules whose import failed, module name -> reason.  Never silent: a
#: declarative module that fails to import takes its whole domain out of the
#: palette, and that used to happen with nothing to point at.
DECLARATIVE_IMPORT_FAILURES: dict[str, str] = {}

#: Node ids that two declarative modules genuinely claim today, recorded so the
#: catalogue still builds while the split brain is resolved.
#:
#: PHASE 9 recovery item 4.1 made the real catalogue path detect duplicates and
#: immediately found play_animation and stop_animation, declared in BOTH
#: actions_nodes and animation_nodes. Item 4.2 resolved them, so the set is
#: empty -- which is the point: it holds scheduled debts, and a debt that is
#: paid must leave.
#:
#: An entry here is a debt with a name, not an exemption: any id NOT listed
#: still raises, so a new duplicate cannot slip in behind these.
KNOWN_DUPLICATE_DEFINITIONS: frozenset[str] = frozenset()


def unexpected_definition_conflicts() -> list[tuple[str, str, str]]:
    """Recorded conflicts minus the ones already known and scheduled."""
    return [
        conflict for conflict in get_registry().definition_conflicts()
        if conflict[0] not in KNOWN_DUPLICATE_DEFINITIONS
    ]


def assert_no_unexpected_duplicates() -> None:
    """Raise unless every duplicate is one of the recorded, scheduled ones."""
    unexpected = unexpected_definition_conflicts()
    if not unexpected:
        return
    lines = ["Duplicate NodeDefinition ids detected while building the catalogue:"]
    for node_id, first, second in unexpected:
        lines.append(f"  id={node_id!r}")
        lines.append(f"      module A: {first}")
        lines.append(f"      module B: {second}")
    lines.append(
        "Exactly one module must own each node id -- "
        "ONE NODE ID -> ONE DEFINITION -> ONE PORT CONTRACT."
    )
    raise DuplicateNodeDefinitionError("\n".join(lines))


#: Declarative definitions whose id is currently an alias, kept aside rather
#: than dropped. The node-id alias item decides which spelling is canonical;
#: until then these do not reach the palette. See _harvest_declarative.
ALIASED_DECLARATIVE_DEFINITIONS: dict[str, Any] = {}


def _discover_declarative_modules() -> tuple[str, ...]:
    """Find the declarative node modules on disk, deterministically.

    PHASE 9 recovery item 1.  This replaced a hand-written tuple.  A tuple is a
    second source of truth: a module could be added to the package, imported by
    nobody, and simply not exist as far as the palette was concerned -- with no
    error anywhere, because nothing compared the list to the directory.

    Sorted, so build order is stable across filesystems, and cached, so repeated
    catalogue builds in one process cannot disagree.
    """
    global _DISCOVERY_CACHE
    if _DISCOVERY_CACHE is not None:
        return _DISCOVERY_CACHE
    directory = Path(__file__).resolve().parent
    _DISCOVERY_CACHE = tuple(sorted(
        path.stem
        for path in directory.glob("*_nodes.py")
        if not path.stem.startswith("_") and path.stem not in _NON_DECLARATIVE_MODULES
    ))
    return _DISCOVERY_CACHE


def reset_discovery_cache_for_tests() -> None:
    """Forget the discovery result so a test can re-run it from disk."""
    global _DISCOVERY_CACHE
    _DISCOVERY_CACHE = None


#: Declarative ``NodeDefinition`` modules harvested into the catalogue.
DECLARATIVE_DEFINITION_MODULES: tuple[str, ...] = _discover_declarative_modules()


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

_LEGACY_SEED_DEFINITIONS: dict[str, dict] = {
    # Basic event nodes
    "event_start": {"id": "event_start", "title": "On Start", "category": "Events", "inputs": [], "outputs": [("next", "flow")]},
    "event_update": {"id": "event_update", "title": "On Update", "category": "Events", "inputs": [], "outputs": [("next", "flow")]},
    "event_custom": {"id": "event_custom", "title": "Custom Event", "category": "Events", "inputs": [], "outputs": [("next", "flow"), ("payload", "any")]},
    "event_collision_enter": {"id": "event_collision_enter", "title": "On Collision Enter", "category": "Events", "inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_collision_exit": {"id": "event_collision_exit", "title": "On Collision Exit", "category": "Events", "inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_trigger_enter": {"id": "event_trigger_enter", "title": "On Trigger Enter", "category": "Events", "inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_trigger_exit": {"id": "event_trigger_exit", "title": "On Trigger Exit", "category": "Events", "inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_timer": {"id": "event_timer", "title": "Timer", "category": "Events", "inputs": [], "outputs": [("next", "flow")]},
    "event_key_pressed": {"id": "event_key_pressed", "title": "On Key Pressed", "category": "Events", "inputs": [], "outputs": [("next", "flow")]},
    "event_object_created": {"id": "event_object_created", "title": "On Object Created", "category": "Events", "inputs": [], "outputs": [("next", "flow"), ("object", "object")]},

    # Self/object access
    "self_object": {"id": "self_object", "title": "This Object", "category": "Objects", "inputs": [], "outputs": [("object", "object")]},
    "find_tag": {"id": "find_tag", "title": "Find by Tag", "category": "Objects", "inputs": [("in", "flow")], "outputs": [("next", "flow"), ("object", "object")]},
    "get_tag": {"id": "get_tag", "title": "Get Tag", "category": "Objects", "inputs": [("target", "object")], "outputs": [("value", "text")]},
    "get_prefab_parameter": {"id": "get_prefab_parameter", "title": "Get Prefab Parameter", "category": "Objects", "inputs": [("target", "object")], "outputs": [("value", "any")]},

    # Object creation
    "create_object": {"id": "create_object", "title": "Create Object", "category": "Objects", "inputs": [("in", "flow"), ("source", "object"), ("name", "text"), ("x", "number"), ("y", "number")], "outputs": [("next", "flow"), ("limit_reached", "flow"), ("object", "object")]},
    "create_prefab": {"id": "create_prefab", "title": "Create Prefab Instance", "category": "Objects", "inputs": [("in", "flow"), ("prefab", "text"), ("x", "number"), ("y", "number")], "outputs": [("next", "flow"), ("object", "object")]},

    # Condition nodes
    "key_pressed": {"id": "key_pressed", "title": "Key Pressed?", "category": "Condition", "inputs": [], "outputs": [], "properties": {"key": "SPACE"}},
    "key_held": {"id": "key_held", "title": "Key Held?", "category": "Condition", "inputs": [], "outputs": []},

    # Motion
    "start_continuous_motion": {"id": "start_continuous_motion", "title": "Start Continuous Motion", "category": "Movement", "inputs": [], "outputs": [], "properties": {}},

    # Value nodes
    "number_value": {"id": "number_value", "title": "Number", "category": "Values", "inputs": [], "outputs": [], "properties": {"value": 0.0}},
    "bool_value": {"id": "bool_value", "title": "Boolean", "category": "Values", "inputs": [], "outputs": [], "properties": {"value": True}},
    "text_value": {"id": "text_value", "title": "Text", "category": "Values", "inputs": [], "outputs": [], "properties": {"value": ""}},

    # UI Binding
    "bind_ui_to_variable": {"id": "bind_ui_to_variable", "title": "Vincular UI → Variável", "category": "UI", "inputs": [("in", "flow"), ("widget_name", "text"), ("variable_name", "text"), ("property", "text")], "outputs": [("next", "flow"), ("exec_success", "flow"), ("exec_not_found", "flow"), ("exec_failure", "flow")], "properties": {"widget_name": "comida", "variable_name": "comida", "property": "value"}},
    "update_ui_binding": {"id": "update_ui_binding", "title": "Atualizar Binding UI", "category": "UI", "inputs": [("in", "flow"), ("widget_name", "text"), ("variable_name", "text"), ("property", "text")], "outputs": [("next", "flow"), ("exec_success", "flow"), ("exec_not_found", "flow"), ("exec_failure", "flow")], "properties": {"widget_name": "comida", "variable_name": "comida", "property": "value"}},
}


_EXPLICIT_PORT_CONTRACTS: dict[str, dict[str, list[tuple[str, str]]]] = {
    "event_start": {"inputs": [], "outputs": [("next", "flow")]},
    "event_update": {"inputs": [], "outputs": [("next", "flow")]},
    "event_custom": {"inputs": [], "outputs": [("next", "flow"), ("payload", "any")]},
    "event_collision_enter": {"inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_collision_exit": {"inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_trigger_enter": {"inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_trigger_exit": {"inputs": [], "outputs": [("next", "flow"), ("other", "object")]},
    "event_timer": {"inputs": [], "outputs": [("next", "flow")]},
    "event_key_pressed": {"inputs": [], "outputs": [("next", "flow")]},
    "event_object_created": {"inputs": [], "outputs": [("next", "flow"), ("object", "object")]},
    "self_object": {"inputs": [], "outputs": [("object", "object")]},
    "find_tag": {"inputs": [("in", "flow")], "outputs": [("next", "flow"), ("object", "object")]},
    "get_tag": {"inputs": [("target", "object")], "outputs": [("value", "text")]},
    "get_prefab_parameter": {"inputs": [("target", "object")], "outputs": [("value", "any")]},
    "create_object": {
        "inputs": [("in", "flow"), ("source", "object"), ("name", "text"), ("x", "number"), ("y", "number")],
        "outputs": [("next", "flow"), ("limit_reached", "flow"), ("object", "object")],
    },
    "create_prefab": {
        "inputs": [
            ("in", "flow"), ("x", "number"), ("y", "number"),
            ("rotation", "number"), ("width", "number"), ("height", "number"),
        ],
        "outputs": [("next", "flow"), ("limit_reached", "flow"), ("object", "object")],
    },
    "clone_object": {"inputs": [("in", "flow"), ("target", "object"), ("name", "text")], "outputs": [("next", "flow"), ("limit_reached", "flow"), ("object", "object")]},
    "add_component": {"inputs": [("in", "flow"), ("target", "object")], "outputs": [("next", "flow")]},
    "remove_component": {"inputs": [("in", "flow"), ("target", "object")], "outputs": [("next", "flow")]},
    "input_axis": {"inputs": [("in", "flow")], "outputs": [("next", "flow"), ("value", "number")]},
    "move": {"inputs": [("in", "flow"), ("value", "number")], "outputs": [("next", "flow")]},
    "jump": {"inputs": [("in", "flow"), ("force", "number")], "outputs": [("next", "flow")]},
    "get_position": {"inputs": [("target", "object")], "outputs": [("x", "number"), ("y", "number")]},
    # One entry: this key was declared TWICE with different pins and the second
    # silently won, which is how delta_x/delta_y reached the palette at all.
    # ``velocity`` stays declared -- BossAILogic and EnemyAILogic wire
    # multiply_number.value into it, so dropping the pin would orphan two
    # shipping edges. The executor does not read it; that is recorded debt, not
    # something to hide by deleting the port the assets use.
    "move_by": {"inputs": [("in", "flow"), ("target", "object"), ("velocity", "vector2"), ("x", "number"), ("y", "number")], "outputs": [("next", "flow")]},
    "start_continuous_motion": {
        "inputs": [("in", "flow"), ("target", "object"), ("x", "number"), ("y", "number")],
        "outputs": [("next", "flow"), ("movement", "movement")],
    },
    "update_continuous_motion": {
        "inputs": [("in", "flow"), ("target", "object"), ("movement", "movement"), ("x", "number"), ("y", "number")],
        "outputs": [("next", "flow")],
    },
    "pause_continuous_motion": {"inputs": [("in", "flow"), ("target", "object"), ("movement", "movement")], "outputs": [("next", "flow")]},
    "resume_continuous_motion": {"inputs": [("in", "flow"), ("target", "object"), ("movement", "movement")], "outputs": [("next", "flow")]},
    "stop_continuous_motion": {"inputs": [("in", "flow"), ("target", "object"), ("movement", "movement")], "outputs": [("next", "flow")]},
    "get_continuous_motion": {
        "inputs": [("in", "flow"), ("target", "object"), ("movement", "movement")],
        "outputs": [
            ("next", "flow"), ("x", "number"), ("y", "number"), ("speed", "number"),
            ("paused", "bool"), ("active", "bool"),
        ],
    },
    "patrol_axis": {"inputs": [("in", "flow"), ("target", "object"), ("minimum", "number"), ("maximum", "number"), ("speed", "number")], "outputs": [("next", "flow"), ("direction", "number"), ("position", "number")]},
    "if_else": {"inputs": [("in", "flow"), ("condition", "any")], "outputs": [("true", "flow"), ("false", "flow")]},
    "sequence": {"inputs": [("in", "flow")], "outputs": [("then_0", "flow"), ("then_1", "flow"), ("next", "flow")]},
    "once": {"inputs": [("in", "flow")], "outputs": [("next", "flow"), ("blocked", "flow")]},
    "cooldown": {"inputs": [("in", "flow"), ("seconds", "number")], "outputs": [("next", "flow"), ("blocked", "flow")]},
    "and": {"inputs": [("a", "bool"), ("b", "bool")], "outputs": [("value", "bool")]},
    "or": {"inputs": [("a", "bool"), ("b", "bool")], "outputs": [("value", "bool")]},
    "not": {"inputs": [("value", "bool")], "outputs": [("value", "bool")]},
    "key_pressed": {"inputs": [("in", "flow")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "key_held": {"inputs": [("in", "flow")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "is_grounded": {"inputs": [("in", "flow")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "compare_number": {"inputs": [("in", "flow"), ("value", "number")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "compare_text": {"inputs": [("in", "flow"), ("value", "text")], "outputs": [("true", "flow"), ("false", "flow"), ("value", "bool")]},
    "play_animation_asset": {"inputs": [("in", "flow"), ("path", "text")], "outputs": [("next", "flow")]},
    "play_sound": {"inputs": [("in", "flow"), ("path", "text")], "outputs": [("next", "flow")]},
    "set_ui_text": {"inputs": [("in", "flow"), ("text", "text")], "outputs": [("next", "flow")]},
    "set_ui_progress_bar": {"inputs": [("in", "flow"), ("value", "number")], "outputs": [("next", "flow")]},
    "get_progress_bar_value": {"inputs": [("in", "flow"), ("widget_name", "text")], "outputs": [("next", "flow"), ("value", "number")]},
    "bind_ui_to_variable": {"inputs": [("in", "flow"), ("widget_name", "text"), ("variable_name", "text"), ("property", "text")], "outputs": [("next", "flow"), ("exec_success", "flow"), ("exec_not_found", "flow"), ("exec_failure", "flow")]},
    "update_ui_binding": {"inputs": [("in", "flow"), ("widget_name", "text"), ("variable_name", "text"), ("property", "text")], "outputs": [("next", "flow"), ("exec_success", "flow"), ("exec_not_found", "flow"), ("exec_failure", "flow")]},
    "set_sprite": {"inputs": [("in", "flow"), ("target", "object"), ("path", "text")], "outputs": [("next", "flow")]},
    "start_texture_scroll": {
        "inputs": [
            ("in", "flow"), ("target", "object"), ("path", "text"),
            ("speed_x", "number"), ("speed_y", "number"),
        ],
        "outputs": [("next", "flow")],
    },
    "stop_texture_scroll": {"inputs": [("in", "flow"), ("target", "object")], "outputs": [("next", "flow")]},
    "set_hud": {"inputs": [("in", "flow"), ("text", "text")], "outputs": [("next", "flow")]},
    "emit_event": {"inputs": [("in", "flow"), ("payload", "any")], "outputs": [("next", "flow")]},
    "set_position": {"inputs": [("in", "flow"), ("target", "object"), ("x", "number"), ("y", "number")], "outputs": [("next", "flow")]},
    "rotate": {"inputs": [("in", "flow"), ("target", "object"), ("degrees", "number")], "outputs": [("next", "flow")]},
    "set_active": {"inputs": [("in", "flow"), ("target", "object"), ("active", "bool")], "outputs": [("next", "flow")]},
    "destroy_object": {"inputs": [("in", "flow"), ("target", "object")], "outputs": []},
    "destroy_after_time": {"inputs": [("in", "flow"), ("target", "object"), ("seconds", "number")], "outputs": [("next", "flow")]},
    "restart_scene": {"inputs": [("in", "flow")], "outputs": []},
    "log_message": {"inputs": [("in", "flow"), ("text", "text")], "outputs": [("next", "flow")]},
    "subgraph_start": {"inputs": [], "outputs": [("next", "flow")]},
    "subgraph_input": {"inputs": [], "outputs": [("value", "any")]},
    "subgraph_return": {"inputs": [("in", "flow"), ("value", "any")], "outputs": []},
    "call_subgraph": {"inputs": [("in", "flow")], "outputs": [("next", "flow")]},
    "vector2": {"inputs": [("x", "number"), ("y", "number")], "outputs": [("vector", "vector2"), ("value", "vector2")]},
    "normalize_vector": {"inputs": [("vector", "vector2")], "outputs": [("value", "vector2")]},
    "magnitude_vector": {"inputs": [("vector", "vector2")], "outputs": [("value", "number")]},
    "sign_number": {"inputs": [("value", "number")], "outputs": [("value", "number")]},
    "move_x": {"inputs": [("in", "flow"), ("target", "object"), ("speed", "number"), ("x", "number")], "outputs": [("next", "flow"), ("movement", "movement")]},
    "move_y": {"inputs": [("in", "flow"), ("target", "object"), ("speed", "number"), ("y", "number")], "outputs": [("next", "flow"), ("movement", "movement")]},
    "move_towards": {"inputs": [("in", "flow"), ("target", "object"), ("destination_x", "number"), ("destination_y", "number"), ("speed", "number")], "outputs": [("next", "flow"), ("handle", "movement")]},
    "set_animator_parameter": {"inputs": [("in", "flow"), ("value", "any")], "outputs": [("next", "flow")]},
    "input_axis": {"inputs": [("in", "flow")], "outputs": [("next", "flow"), ("value", "number")]},
    "get_variable": {"inputs": [("in", "flow")], "outputs": [("next", "flow"), ("value", "any")]},
    "number_value": {"inputs": [], "outputs": [("value", "number")]},
    "bool_value": {"inputs": [], "outputs": [("value", "bool")]},
    "text_value": {"inputs": [], "outputs": [("value", "text")]},
    "add_number": {"inputs": [("a", "number"), ("b", "number")], "outputs": [("value", "number")]},
    "subtract_number": {"inputs": [("a", "number"), ("b", "number")], "outputs": [("value", "number")]},
    "multiply_number": {"inputs": [("a", "number"), ("b", "number")], "outputs": [("value", "number")]},
    "divide_number": {"inputs": [("a", "number"), ("b", "number")], "outputs": [("value", "number")]},
    "absolute_number": {"inputs": [("value", "number")], "outputs": [("value", "number")]},
    "clamp_number": {"inputs": [("value", "number"), ("minimum", "number"), ("maximum", "number")], "outputs": [("value", "number")]},
    "random_number": {"inputs": [("minimum", "number"), ("maximum", "number")], "outputs": [("value", "number")]},
    "delta_time": {"inputs": [], "outputs": [("value", "number")]},
    "join_text": {"inputs": [("a", "any"), ("b", "any")], "outputs": [("value", "text")]},
    "to_text": {"inputs": [("value", "any")], "outputs": [("value", "text")]},
    # Compatibility shim operations implemented in
    # ``engine.logic.runtime.nodes.scene_nodes``.  They shipped with executors
    # but no port contract at all, so a graph using them had undefined ports.
    # Declaring the contract here does not add palette entries -- the palette
    # iterates NODE_DEFINITIONS, not the port schema.
    "load_scene": {
        "inputs": [("in", "flow"), ("scene_path", "text")],
        "outputs": [("next", "flow"), ("success", "flow")],
    },
    "quit_game": {"inputs": [("in", "flow")], "outputs": []},
    "button_clicked": {
        "inputs": [("in", "flow"), ("widget_name", "text")],
        "outputs": [("next", "flow"), ("clicked", "flow"), ("exec", "flow")],
    },
    "set_ui_enabled": {
        "inputs": [("in", "flow"), ("widget_name", "text"), ("enabled", "bool")],
        "outputs": [("next", "flow")],
    },
}


#: LEGACY NODE ID -> CANONICAL NODE ID.  One-way, and the only node-id alias
#: table in the engine.
#:
#: PHASE 9 recovery item 2.  The direction used to be the opposite -- dotted
#: spellings resolved onto flat ones -- which contradicted every shipping asset.
#: Measured on this branch:
#:
#:     scene.load_scene       5 uses     load_scene       0
#:     ui.button_clicked      5 uses     button_clicked   0
#:     app.quit               1 use      quit_game        0
#:     ui.set_widget_enabled  1 use      set_ui_enabled   0
#:
#: The dotted form is what authors actually saved, so it owns the definition,
#: the palette entry and the port contract; the flat form is a load/runtime
#: alias. Renaming ids that assets already use buys nothing.
#:
#: The three entries at the bottom keep their original direction: their targets
#: are the flat spelling and there is no asset evidence to flip them.
#:
#: An alias is compatibility, never authoring identity: it gets no definition,
#: no palette row and no port contract of its own.
NODE_ID_ALIASES: Mapping[str, str] = MappingProxyType({
    "load_scene": "scene.load_scene",
    "open_scene": "scene.load_scene",
    "quit_game": "app.quit",
    "exit_game": "app.quit",
    "button_clicked": "ui.button_clicked",
    "on_ui_click": "ui.button_clicked",
    "set_ui_enabled": "ui.set_widget_enabled",
    "variable.set": "set_variable",
    "variables.set": "set_variable",
    "game.load_game": "load_game",
    "game.has_save": "has_save",
})

#: Deprecated spelling kept so existing importers keep working.
RUNTIME_ID_ALIASES: Mapping[str, str] = NODE_ID_ALIASES


def resolve_node_id(node_id: str) -> str:
    """Resolve a legacy node id onto the id that owns the definition.

    Idempotent by construction: no alias target is itself an alias key, and
    :func:`validate_node_id_aliases` enforces that.
    """
    return NODE_ID_ALIASES.get(node_id, node_id)


#: Historical name for :func:`resolve_node_id`.
canonical_node_id = resolve_node_id


def get_node_aliases() -> Mapping[str, str]:
    """The whole legacy -> canonical table, read-only."""
    return NODE_ID_ALIASES


def get_aliases_for(canonical_id: str) -> tuple[str, ...]:
    """Legacy spellings that resolve onto ``canonical_id``."""
    return tuple(sorted(k for k, v in NODE_ID_ALIASES.items() if v == canonical_id))


def validate_node_id_aliases(known_ids: set[str] | None = None) -> list[str]:
    """Structural problems in the alias table.  Empty means healthy.

    Catches the three ways an alias table rots: an entry pointing at itself, a
    chain that never converges (which would make resolution non-idempotent),
    and a target that does not exist -- each of which silently sends a saved
    node id nowhere.
    """
    problems: list[str] = []
    for source, target in NODE_ID_ALIASES.items():
        if source == target:
            problems.append(f"self-alias: {source!r}")
            continue
        if target in NODE_ID_ALIASES:
            problems.append(
                f"alias chain: {source!r} -> {target!r} -> {NODE_ID_ALIASES[target]!r}; "
                "resolution must converge in one step"
            )
        if known_ids is not None and target not in known_ids:
            problems.append(f"alias {source!r} points at {target!r}, which has no definition")
    # A cycle longer than the one-step check above cannot exist while no target
    # is also a key, but prove it rather than assume it.
    for source in NODE_ID_ALIASES:
        seen, current = {source}, resolve_node_id(source)
        while current in NODE_ID_ALIASES:
            if current in seen:
                problems.append(f"alias cycle through {source!r}")
                break
            seen.add(current)
            current = resolve_node_id(current)
    return problems


def all_aliases() -> Mapping[str, tuple[str, ...]]:
    """Canonical node id -> the legacy ids that normalize onto it."""
    try:
        from ..legacy_visual_script import LEGACY_NODE_TYPES
    except Exception:  # pragma: no cover
        LEGACY_NODE_TYPES = {}
    merged: dict[str, set[str]] = {}
    for source, target in {**LEGACY_NODE_TYPES, **NODE_ID_ALIASES}.items():
        merged.setdefault(target, set()).add(source)
    return MappingProxyType(
        {target: tuple(sorted(sources)) for target, sources in sorted(merged.items())}
    )


# ---------------------------------------------------------------------------
# Declarative harvesting helpers
# ---------------------------------------------------------------------------

_LEGACY_PIN_TYPES = {
    "exec": "flow",
    "float": "number",
    "int": "number",
    "string": "text",
    "vector2": "vector2",
    "vector3": "vector3",
    "color": "color",
    "bool": "bool",
    "object": "object",
}


def _legacy_pin_type(pin_type: Any) -> str:
    value = str(getattr(pin_type, "value", pin_type)).lower()
    return _LEGACY_PIN_TYPES.get(value, value or "any")


def _pin_tuple(pin: Any) -> tuple[str, str]:
    return (str(getattr(pin, "id", "")), _legacy_pin_type(getattr(pin, "pin_type", "any")))


def _definition_to_legacy(definition: Any) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    for pin in list(getattr(definition, "inputs", [])):
        pin_type = _legacy_pin_type(getattr(pin, "pin_type", "any"))
        pin_id = str(getattr(pin, "id", ""))
        default = getattr(pin, "default_value", None)
        if pin_type != "flow" and pin_id and default is not None:
            properties[pin_id] = default
    category = str(getattr(definition, "category_key", "") or "Custom")
    category = {"Actions": "Action"}.get(category, category)
    return {
        "id": str(getattr(definition, "id", "")),
        "title": str(
            getattr(definition, "title_key", "")
            or getattr(definition, "name_key", "")
            or getattr(definition, "id", "")
        ),
        "category": category,
        "description": str(getattr(definition, "description_key", "") or ""),
        "inputs": [_pin_tuple(pin) for pin in list(getattr(definition, "inputs", []))],
        "outputs": [_pin_tuple(pin) for pin in list(getattr(definition, "outputs", []))],
        "properties": properties,
        # PHASE 9 recovery item 3. These three were declared and then dropped
        # here, which is the quietest bug in the system: nothing fails, the
        # value simply stops existing downstream. execution_model is emitted
        # ONLY when actually declared -- an unconditional default would make
        # every node look explicitly classified and suppress derivation for the
        # entire catalogue. test_projection_fidelity.py makes the class of bug
        # impossible to reintroduce for any field, not just these.
        **(
            {"execution_model": declared_model}
            if (declared_model := normalize_execution_model(
                getattr(definition, "execution_model", None)))
            else {}
        ),
        **(
            {"dynamic_exec_prefixes": tuple(declared_prefixes)}
            if (declared_prefixes := getattr(definition, "dynamic_exec_prefixes", ()))
            else {}
        ),
        "deprecated": bool(getattr(definition, "deprecated", False)),
    }


def _iter_declarative_definitions(module: ModuleType):
    for value in vars(module).values():
        definition = getattr(value, "__node_definition__", None)
        if definition is None and getattr(value, "__class__", None).__name__ == "NodeDefinition":
            definition = value
        if definition is None:
            continue
        node_id = str(getattr(definition, "id", "")).strip()
        if not node_id:
            continue
        yield node_id, definition


def _property_default(pin_id: str, pin_type: str) -> Any:
    """Default value seeded for a data pin that has no explicit default."""
    if pin_id == "widget_name":
        return "comida"
    if pin_id == "variable_name":
        return "comida"
    if pin_id == "property":
        return "value"
    if pin_id == "target":
        return ""
    if pin_type == "number":
        return 0.0
    if pin_type == "bool":
        return True
    return ""


def _seed_properties_from_pins(definition: dict[str, Any]) -> None:
    properties = definition.setdefault("properties", {})
    for pin in definition.get("inputs", []):
        if isinstance(pin, (list, tuple)) and len(pin) >= 2:
            pin_id, pin_type = str(pin[0]), str(pin[1])
            if pin_type not in ("flow", "exec") and pin_id not in properties:
                properties[pin_id] = _property_default(pin_id, pin_type)


# ---------------------------------------------------------------------------
# Explicit contract overrides applied after the generic build
# ---------------------------------------------------------------------------

_COMPONENT_NODE_DEFAULTS: dict[str, dict[str, Any]] = {
    "add_sprite_renderer": {"texture": "", "color": "#ffffff", "sort_order": 0},
    "add_animator": {"controller": "", "autoplay": True},
    "add_rigidbody": {"body_type": "dynamic", "mass": 1.0, "gravity_scale": 1.0},
    "add_box_collider": {"width": 32.0, "height": 32.0, "is_trigger": False},
    "add_circle_collider": {"radius": 16.0, "is_trigger": False},
    "add_camera": {"background_color": [22, 24, 31], "zoom": 1.0, "active": True},
    "add_audio_source": {"path": "", "volume": 1.0, "loop": False, "autoplay": False},
    "add_ui_canvas": {"sort_order": 0},
    "add_ui_text": {"text": "Text", "color": "#ffffff", "font_size": 24},
    "add_ui_image": {"texture": "", "color": "#ffffff"},
    "add_ui_button": {"text": "Button", "color": "#4c9aff"},
}

#: Nodes whose authoring properties REPLACE anything harvested from the
#: declarative definition, rather than merging with it.  These three used
#: ``dict.update({"properties": ...})`` before Stage 2, which swaps the whole
#: dict -- so the declarative pin defaults (``a``/``b``/``operation`` on the
#: comparison nodes) were never part of the shipped contract and must not
#: reappear.  Merging here is a regression, not a cleanup.
_REPLACED_PROPERTY_SETS: dict[str, dict[str, Any]] = {
    "compare_number": {"operator": ">", "value": 0.0},
    "compare_text": {"operator": "==", "value": ""},
    "key_pressed": {"key": "SPACE"},
}

#: Property defaults that the editor and exported graphs rely on.  These are
#: authoring defaults, not pins, so they are not derivable from the schema.
#: Merged on top of whatever the node already carries.
_EXPLICIT_PROPERTY_DEFAULTS: dict[str, dict[str, Any]] = {
    "if_else": {"condition": False},
    "number_value": {"value": 0.0},
    "bool_value": {"value": True},
    "text_value": {"value": ""},
    "create_object": {
        "name": "Object", "x": 0.0, "y": 0.0, "width": 32.0, "height": 32.0,
        "color": "#4c9aff", "texture": "", "tag": "", "relative": True,
        "inherit_source": True, "inherit_logic": False, "lifetime": 0.0,
        "max_instances": 0, "max_distance": 0.0, "use_pool": False,
    },
    "start_continuous_motion": {
        "movement": "Movement", "x": 100.0, "y": 0.0, "space": "global",
        "acceleration": 0.0, "deceleration": 0.0,
    },
}

#: PHASE 9.5B Stage 4.1 -- properties the runtime reads but the catalogue never
#: declared, so they never reached the Properties panel and could only be set by
#: hand-editing the .zlogic JSON.  An audit of every executor found 26 such
#: nodes; the defaults below are the ones the executors themselves fall back to,
#: read out of ``properties.get(key, default)`` in their source.
#:
#: Deliberately NOT declared here (see Stage 4.1 doc): runtime object handles
#: (``object``, ``widget``), nested structures (``add_component.properties``,
#: ``call_subgraph.inputs``, ``show_dialog.options``), type-dependent defaults
#: (``get_prefab_parameter.default``) and colour properties whose ``None``
#: default means "inherit the theme" -- declaring those would change behaviour
#: rather than merely expose it.
_RUNTIME_READ_PROPERTY_DEFAULTS: dict[str, dict[str, Any]] = {
    "add_component": {"component": "BoxCollider"},
    "remove_component": {"component": "BoxCollider"},
    "bind_ui_to_blackboard": {"blackboard_key": "", "widget_property": "value"},
    "call_subgraph": {"path": ""},
    "clone_object": {"use_pool": False},
    "create_prefab": {
        "include_audio": False, "include_camera": False,
        "include_logic": False, "use_pool": True,
    },
    "emit_event": {"name": "evento"},
    "find_tag": {"tag": "Player"},
    "get_prefab_parameter": {"name": "speed"},
    "get_variable": {"name": "value", "scope": "object"},
    "set_variable": {"name": "value", "scope": "object"},
    # The key bindings of the movement axis: the single most-authored property
    # in the palette, and it was invisible.
    "input_axis": {"negative": "A", "positive": "D"},
    "read_key_axis": {"negative": "A", "positive": "D"},
    # PHASE 9 recovery item 6: "slot" was the property the removed stub executor
    # invented. The declared pin -- and what the real executor reads -- is
    # slot_name, so declaring "slot" here put a dead field in the Inspector next
    # to the live one. Saved graphs are migrated by _RENAMED_NODE_PROPERTIES.
    "sequence": {"outputs": 2},
    "set_ui_text": {"object_name": "", "widget_name": ""},
    "set_ui_progress_bar": {"max_value": 100.0, "object_name": "", "widget_name": ""},
    "set_ui_visible": {"widget_name": ""},
    "start_texture_scroll": {
        "parallax": 1.0, "repeat_x": False,
        "repeat_y": True, "send_to_background": True,
    },
    "stop_continuous_motion": {"smooth": False},
    "stop_texture_scroll": {"reset": False},
    "subgraph_return": {"name": "resultado"},
}

#: Titles/categories the palette must show regardless of the declarative source.
_EXPLICIT_METADATA: dict[str, dict[str, str]] = {
    "key_pressed": {"title": "Key Pressed Now?", "category": "Condition"},
    "key_held": {"title": "Key Held?", "category": "Condition"},
}


#: Node types whose ports are expanded at authoring time from node properties.
#: ``node_port_definitions()`` in :mod:`engine.logic.graph_asset` owns the
#: expansion; the catalogue only records that the static schema is a floor.
#: Nodes whose pins expand at runtime.  Seeded for the ones with no declarative
#: definition to carry the information; where a NodeDefinition declares
#: ``dynamic_exec_prefixes`` the declaration wins, and _build_catalogue merges
#: it in.  Two tables for one fact is the failure this phase keeps finding.
_DYNAMIC_PORT_SEED: dict[str, tuple[str, ...]] = {
    "get_prefab_parameter": (),
    "subgraph_input": (),
    "subgraph_return": (),
    "call_subgraph": (),
}

DYNAMIC_PORT_NODES: Mapping[str, tuple[str, ...]] = MappingProxyType(dict(_DYNAMIC_PORT_SEED))


def _execution_model(inputs: list[Any], outputs: list[Any]) -> str:
    """Structural fallback classification.

    Kept as a thin wrapper so existing callers keep working; the vocabulary and
    the rule now live in :mod:`engine.logic.contracts`. It used to return a
    second vocabulary (pure/event/flow/branch) that nothing translated.
    """
    return resolve_execution_model(None, inputs, outputs)


# ---------------------------------------------------------------------------
# Catalogue construction
# ---------------------------------------------------------------------------

_BUILD_LOCK = threading.RLock()
_LOADED = False


def _harvest_declarative(
    definitions: dict[str, dict[str, Any]],
    declarative: dict[str, Any],
    claims: list[tuple[str, str]],
) -> None:
    """Harvest every declarative module, recording *every* ownership claim.

    PHASE 9 recovery item 4.1. This used to write ``owners[node_id] =
    module_name`` -- a plain dict -- so when two modules declared the same id
    the first claim was overwritten before the registry ever saw it. The
    registry's duplicate detection was correct and its unit tests passed; it
    simply was never handed the evidence. ``play_animation`` and
    ``stop_animation`` were declared twice, in actions_nodes and
    animation_nodes, and ``duplicate_definition_conflicts()`` reported nothing.

    Claims are now a list in discovery order. Collapsing is the registry's
    decision, and the registry records a conflict when it collapses.
    """
    for module_name in _discover_declarative_modules():
        try:
            module = import_module(f"{__package__}.{module_name}")
        except Exception as exc:
            # Never silent. A declarative module that fails to import takes its
            # node definitions with it, and the palette simply loses a domain
            # with nothing to point at. Recorded and logged; the build carries
            # on so one broken module cannot take down the editor.
            DECLARATIVE_IMPORT_FAILURES[module_name] = f"{type(exc).__name__}: {exc}"
            _log.exception("Declarative node module %r failed to import", module_name)
            continue
        for node_id, definition in _iter_declarative_definitions(module):
            if node_id in NODE_ID_ALIASES:
                # This lineage's rule, unchanged here: an alias never gets its
                # own definition, palette entry or port contract. Stage 1's
                # scene_nodes declares the dotted ids (scene.load_scene,
                # app.quit, ui.button_clicked, ui.set_widget_enabled), and
                # letting them through would put two palette rows behind one
                # operation and give the alias a contract whose entry pin the
                # shipping assets do not use.
                #
                # Which spelling *should* be canonical is a real question -- the
                # assets use the dotted form exclusively -- but it is the
                # node-id alias item's question, not this one. Kept here so that
                # item has the declarations to work from rather than having to
                # re-derive them.
                ALIASED_DECLARATIVE_DEFINITIONS[node_id] = definition
                continue
            definitions[node_id] = _definition_to_legacy(definition)
            declarative[node_id] = definition
            claims.append((node_id, module_name))


def _harvest_metadata_manager(definitions: dict[str, dict[str, Any]]) -> None:
    """Additive-only harvest of externally registered node metadata."""
    try:
        from engine.metadata.manager import MetadataManager

        metadata = MetadataManager().get_nodes_metadata()
    except Exception:
        return
    for node_id, node_def in metadata.items():
        if node_id in definitions:
            continue
        definitions[node_id] = {
            "id": node_id,
            "title": node_def.get("title", node_id),
            "category": node_def.get("category", "Custom"),
            "description": node_def.get("description", ""),
            "inputs": list(node_def.get("inputs", [])),
            "outputs": list(node_def.get("outputs", [])),
            "properties": dict(node_def.get("properties", {})),
        }


def _build_catalogue() -> None:
    """Populate the registry.  Called exactly once via ensure_catalogue_loaded()."""
    definitions: dict[str, dict[str, Any]] = {
        node_id: {
            **{k: (list(v) if isinstance(v, list) else v) for k, v in seed.items()},
            "properties": dict(seed.get("properties", {})),
        }
        for node_id, seed in _LEGACY_SEED_DEFINITIONS.items()
    }
    declarative: dict[str, Any] = {}
    definition_claims: list[tuple[str, str]] = []

    _harvest_declarative(definitions, declarative, definition_claims)
    _harvest_metadata_manager(definitions)

    # --- port schema: explicit graph contracts first, definitions as fallback
    # PHASE 9 recovery item 2: the contract follows the canonical id. Several
    # contracts are still keyed by the flat spelling (load_scene, quit_game,
    # button_clicked, set_ui_enabled); an alias must not own a port contract,
    # so they are re-keyed onto the id that owns the definition.
    port_schema: dict[str, dict[str, list[tuple[str, str]]]] = {
        resolve_node_id(node_id): {
            "inputs": [tuple(pin) for pin in contract.get("inputs", [])],
            "outputs": [tuple(pin) for pin in contract.get("outputs", [])],
        }
        for node_id, contract in _EXPLICIT_PORT_CONTRACTS.items()
    }
    for node_id, definition in definitions.items():
        definition["category"] = _migrate_category(str(definition.get("category", "Custom")))
        port_schema.setdefault(
            node_id,
            {
                "inputs": [tuple(pin) for pin in definition.get("inputs", [])],
                "outputs": [tuple(pin) for pin in definition.get("outputs", [])],
            },
        )

    # --- component nodes are declared as a family, in both layers at once
    for node_id, properties in _COMPONENT_NODE_DEFAULTS.items():
        port_schema[node_id] = {
            "inputs": [("in", "flow"), ("target", "object")],
            "outputs": [("next", "flow")],
        }
        definitions[node_id] = {
            "id": node_id,
            "title": node_id.removeprefix("add_").replace("_", " ").title(),
            "category": "Components",
            "description": "",
            "inputs": [],
            "outputs": [],
            "properties": dict(properties),
        }

    # --- PALETTE RESCUE (PHASE 9 recovery item 2)
    # The canonical dotted ids have a port contract and an executor but no
    # authoring entry, so they are invisible in the palette: an author cannot
    # place scene.load_scene at all, even though five shipping graphs use it.
    # Stage 1's scene_nodes declares exactly the missing metadata, and item 1
    # parked it in ALIASED_DECLARATIVE_DEFINITIONS.
    #
    # Metadata ONLY. Writing the declaration's pins here is how a good contract
    # once got overwritten with an empty one: the entries carry authoring
    # information, and the pins keep coming from the port schema below.
    for node_id, declaration in ALIASED_DECLARATIVE_DEFINITIONS.items():
        canonical = resolve_node_id(node_id)
        if canonical not in port_schema:
            continue
        projected = _definition_to_legacy(declaration)
        entry = definitions.setdefault(canonical, {"id": canonical, "properties": {}})
        for field in ("title", "category", "description"):
            value = projected.get(field)
            if value:
                entry[field] = value
        # Defaults are additive: a default already resolved for this id was
        # decided against the real contract and outranks the declaration's.
        for name, default in (projected.get("properties") or {}).items():
            entry.setdefault("properties", {}).setdefault(name, default)
        entry["id"] = canonical
        if not any(claim_id == canonical for claim_id, _ in definition_claims):
            definition_claims.append((canonical, "scene_nodes"))

    # An alias is compatibility, never an authoring identity: it must not carry
    # a palette entry of its own next to the id it resolves onto.
    for alias in NODE_ID_ALIASES:
        definitions.pop(alias, None)
        port_schema.pop(alias, None)

    # --- UNIFICATION: a definition's pins ARE its port schema entry.
    # This is what makes NODE_PORT_DEFINITIONS a derived view rather than a
    # second hand-maintained table.  Where a declarative NodeDefinition used
    # aspirational pins (``exec``/``exec_done``) the explicit graph contract
    # that assets and executors actually speak wins.
    for node_id, definition in definitions.items():
        schema = port_schema[node_id]
        definition["inputs"] = list(schema["inputs"])
        definition["outputs"] = list(schema["outputs"])
        definition.setdefault("id", node_id)
        definition.setdefault("description", "")

    # --- authoring defaults, seeded from the canonical pins
    for node_id, definition in definitions.items():
        _seed_properties_from_pins(definition)

    for node_id, metadata in _EXPLICIT_METADATA.items():
        if node_id in definitions:
            definitions[node_id].update(metadata)

    for node_id, properties in _REPLACED_PROPERTY_SETS.items():
        if node_id in definitions:
            definitions[node_id]["properties"] = dict(properties)

    for node_id, properties in _RUNTIME_READ_PROPERTY_DEFAULTS.items():
        if node_id in definitions:
            target = definitions[node_id].setdefault("properties", {})
            for key, value in properties.items():
                target.setdefault(key, value)

    for node_id, properties in _EXPLICIT_PROPERTY_DEFAULTS.items():
        if node_id in definitions:
            definitions[node_id].setdefault("properties", {}).update(properties)

    # --- publish into the single mutable store
    registry = get_registry()
    registry.reset_catalogue()
    for node_id, definition in definitions.items():
        registry.set_resolved(node_id, definition)
    for node_id, schema in port_schema.items():
        registry.set_port_schema(node_id, schema)
    for node_id, definition in declarative.items():
        registry.register_canonical(definition, allow_override=True)
    for node_id, module_name in definition_claims:
        registry.set_definition_owner(node_id, module_name)
    # Loud, and only once every owner is known: a conflict is not knowable
    # until both claimants have been seen, so the check cannot live inside the
    # loop above.
    assert_no_unexpected_duplicates()

    # Dynamic pin families come from the declarations that own them, falling
    # back to the seed for nodes with no declarative definition.
    global DYNAMIC_PORT_NODES
    merged_prefixes = dict(_DYNAMIC_PORT_SEED)
    for node_id, definition in definitions.items():
        declared_prefixes = definition.get("dynamic_exec_prefixes")
        if declared_prefixes:
            merged_prefixes[node_id] = tuple(declared_prefixes)
    DYNAMIC_PORT_NODES = MappingProxyType(merged_prefixes)
    # Declared beats derived; derivation only fills the gap. The declaration
    # carries intent the pins cannot: restart_scene has a flow output and is
    # still TERMINAL, because the scene it would continue into is gone.
    for node_id, schema in port_schema.items():
        declared = (definitions.get(node_id) or {}).get("execution_model")
        model = resolve_execution_model(declared, schema["inputs"], schema["outputs"])
        registry.set_execution_model(node_id, model)
        if node_id in definitions:
            definitions[node_id]["execution_model"] = model


def ensure_catalogue_loaded() -> None:
    """Build the node definition catalogue once per process.  Idempotent."""
    global _LOADED
    if _LOADED:
        return
    with _BUILD_LOCK:
        if _LOADED:
            return
        _build_catalogue()
        _LOADED = True


def reset_catalogue_for_tests() -> None:
    """Force the next :func:`ensure_catalogue_loaded` to rebuild from scratch."""
    global _LOADED
    with _BUILD_LOCK:
        _LOADED = False
        get_registry().reset_catalogue()


# ---------------------------------------------------------------------------
# Read-only views
# ---------------------------------------------------------------------------


def definitions_view() -> Mapping[str, dict[str, Any]]:
    """Read-only mapping of node id -> resolved definition."""
    ensure_catalogue_loaded()
    return get_registry().definitions_view()


def port_schema_view() -> Mapping[str, dict[str, list[tuple[str, str]]]]:
    """Read-only mapping of node id -> {"inputs": [...], "outputs": [...]}."""
    ensure_catalogue_loaded()
    return get_registry().port_schema_view()

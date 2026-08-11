"""Canonical exec-port names and the one-way legacy alias bridge.

Phase 9.5B Stage 1.

ARCHITECTURAL DECISION
----------------------
``CANONICAL_SUCCESS_PORT = "next"``

Rationale (measured, Phase 9.5A):
  * all 56 project ``.zlogic`` assets use ``next`` -- 137 edges
  * **zero** saved edges use ``exec_done``
  * ``engine/logic/runtime/core.py`` defaults ``from_port`` to ``"next"``
  * 49 executors already return ``["next"]``

The engine therefore has exactly ONE name for "this node succeeded, continue":
``next``.  Nodes with genuinely different *outcomes* keep explicit, semantic
port names -- ``exec_failure``, ``limit_reached``, ``grounded``/``airborne`` --
because those are distinct branches, not synonyms for success.

What this module is NOT
-----------------------
It is a **migration bridge**, not a source of truth.  The mapping is strictly
one-way, LEGACY -> CANONICAL.  There are deliberately no bidirectional or
chained aliases (``next -> exec_done -> exec_success -> ...``): normalisation
must be idempotent and must converge on a single form.

Lifecycle: every alias below is scheduled for removal.  ``engine.logic``
emits a DEBUG log the first time each one is resolved at runtime, so real usage
can be measured before the compatibility layer is dropped.
"""
from __future__ import annotations

from typing import Final

#: The one canonical "continue on success" exec port.
CANONICAL_SUCCESS_PORT: Final[str] = "next"

#: LEGACY -> CANONICAL.  One-way only.  A key must never also be a value.
EXEC_PORT_ALIASES: Final[dict[str, str]] = {
    # Pre-Stage-1 declarative definitions used these for plain continuation
    # while every executor returned "next".
    "exec_done": CANONICAL_SUCCESS_PORT,
    "exec_success": CANONICAL_SUCCESS_PORT,
    # Some early event/definition modules named the single outgoing pin "exec".
    "exec": CANONICAL_SUCCESS_PORT,
    # Very old hand-authored graphs.
    "out": CANONICAL_SUCCESS_PORT,
    "continue": CANONICAL_SUCCESS_PORT,
}

#: Ports that look like aliases but are real, distinct outcomes.  Listed so the
#: intent is explicit and nobody "helpfully" folds them into ``next`` later.
SEMANTIC_EXEC_PORTS: Final[frozenset[str]] = frozenset({
    "exec_failure", "failure",
    "limit_reached",
    "true", "false",
    "grounded", "airborne",
    "held", "released",
    "exec_pressed", "exec_not_pressed",
    "blocked",
    "exec_hit", "exec_no_hit",
    "exec_found", "exec_not_found",
    "exec_no_save", "exec_loaded", "exec_saved", "exec_deleted", "exec_exists",
    "exec_none",
    "exec_playing", "exec_stopped", "exec_waiting",
    "exec_created", "exec_following", "exec_shaking",
    "exec_showing", "exec_touched", "exec_swiped", "exec_pinched",
    "exec_in_state", "exec_not_in_state",
    "exec_changed",
})


#: Node-scoped aliases, for branch nodes whose runtime used generic
#: ``true``/``false`` while the definition offered domain names.
#:
#: These CANNOT be global: ``if_else``, ``compare_number`` and ``compare_text``
#: use ``true``/``false`` as their real, canonical ports, and 23 saved edges
#: depend on that.  Only the nodes listed here remap them.
NODE_EXEC_PORT_ALIASES: Final[dict[str, dict[str, str]]] = {
    # 2 saved edges use "true" on is_grounded
    "is_grounded": {"true": "grounded", "false": "airborne"},
    # 12 saved edges use "true" on key_held
    "key_held": {"true": "held", "false": "released"},
    # 3 saved edges use "true" on key_pressed
    "key_pressed": {"true": "exec_pressed", "false": "exec_not_pressed"},
}


#: LEGACY NODE ID -> CANONICAL NODE ID.  One-way, like the port table.
#:
#: The runtime already grouped these in single ``register_executor((...))``
#: tuples, so the grouping is not new -- Stage 1 makes it explicit, gives the
#: canonical id the only palette entry, and stops the audit from reporting the
#: aliases as missing definitions.
#:
#: The canonical spelling is the dotted one wherever assets already use it:
#: ``scene.load_scene`` (5 uses), ``ui.button_clicked`` (5), ``app.quit`` (1),
#: ``ui.set_widget_enabled`` (1).  See docs/PHASE9_5B_STAGE1_NODE_CONTRACTS.md.
NODE_ID_ALIASES: Final[dict[str, str]] = {
    # scene loading -- five spellings for one action
    "load_scene": "scene.load_scene",
    "open_scene": "scene.load_scene",
    "scene_load": "scene.load_scene",
    "scene.load": "scene.load_scene",
    # quitting -- three spellings
    "exit_game": "app.quit",
    "quit_game": "app.quit",
    # UI click -- three spellings
    "button_clicked": "ui.button_clicked",
    "on_ui_click": "ui.button_clicked",
    # UI enable -- two spellings
    "set_ui_enabled": "ui.set_widget_enabled",
    # dotted duplicates of nodes that already had a canonical definition
    "variables.set": "set_variable",
    "game.load_game": "load_game",
    "game.has_save": "has_save",
}


def canonical_node_id(node_type: str) -> str:
    """Resolve a legacy node id to the id that owns the definition."""
    return NODE_ID_ALIASES.get(node_type, node_type)


def is_legacy_node_id(node_type: str) -> bool:
    return node_type in NODE_ID_ALIASES


def canonical_exec_port(port: str, node_type: str | None = None) -> str:
    """Resolve one exec port name to its canonical form.

    ``node_type`` enables the node-scoped aliases above; without it only the
    global table applies.

    Idempotent: ``canonical_exec_port(canonical_exec_port(p)) == canonical_exec_port(p)``
    for every ``p``, because no alias value is itself an alias key.
    """
    if not port:
        return CANONICAL_SUCCESS_PORT
    if node_type:
        scoped = NODE_EXEC_PORT_ALIASES.get(node_type)
        if scoped and port in scoped:
            return scoped[port]
    return EXEC_PORT_ALIASES.get(port, port)


def is_legacy_exec_port(port: str, node_type: str | None = None) -> bool:
    """True if ``port`` is a deprecated spelling that normalisation rewrites."""
    if node_type and port in NODE_EXEC_PORT_ALIASES.get(node_type, {}):
        return True
    return port in EXEC_PORT_ALIASES


def _assert_one_way() -> None:
    """Guard the invariant that makes normalisation idempotent."""
    overlapping = set(EXEC_PORT_ALIASES) & set(EXEC_PORT_ALIASES.values())
    if overlapping:
        raise RuntimeError(
            "EXEC_PORT_ALIASES must be one-way; these names are both a legacy "
            f"key and a canonical target: {sorted(overlapping)}"
        )
    for node_type, table in NODE_EXEC_PORT_ALIASES.items():
        bad = set(table) & set(table.values())
        if bad:
            raise RuntimeError(
                f"NODE_EXEC_PORT_ALIASES[{node_type!r}] must be one-way: {sorted(bad)}"
            )
    collide = set(EXEC_PORT_ALIASES) & SEMANTIC_EXEC_PORTS
    if collide:
        raise RuntimeError(
            "A port cannot be both a legacy alias and a semantic outcome: "
            f"{sorted(collide)}"
        )


_assert_one_way()

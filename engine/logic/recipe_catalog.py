"""Catálogo de receitas pré-fabricadas para o Logic Graph."""

from __future__ import annotations

from typing import Any

LOGIC_RECIPES: tuple[dict[str, Any], ...] = (
    {
        "id": "player_movement_x",
        "topics": ("Movement",),
        "title": "Horizontal Player Movement (A/D & Arrows)",
        "category": "Player & Character",
        "summary": "Reads A/D and Arrow Left/Right keys and moves the object smoothly horizontally.",
        "keywords": "move x speed player character input movement a d left right",
        "steps": (
            "On Update drives the Move X action every frame.",
            "Read Input Axis turns A/D or Left/Right into a -1 to +1 multiplier.",
            "Adjust Speed property in Move X to change top speed.",
        ),
        "nodes": (
            {"key": "update", "type": "event_update", "position": (0.0, 0.0)},
            {"key": "axis", "type": "input_axis", "position": (0.0, 180.0), "properties": {"negative": "A", "positive": "D"}},
            {"key": "move", "type": "move_x", "position": (270.0, 0.0), "properties": {"speed": 220.0}},
        ),
        "edges": (
            ("update", "next", "move", "in", "flow"),
            ("axis", "value", "move", "speed", "number"),
        ),
    },
    {
        "id": "jump_on_space",
        "topics": ("Movement", "Condition"),
        "title": "Jump on Space Key",
        "category": "Player & Character",
        "summary": "Applies an upward impulse when Space is pressed while object is grounded.",
        "keywords": "jump space key impulse ground physics",
        "steps": (
            "On Key Pressed detects when Space is hit.",
            "Is Grounded checks if object is on a collider.",
            "If / Else branch fires Jump only when grounded is True.",
        ),
        "nodes": (
            {"key": "press", "type": "event_key_pressed", "position": (0.0, 0.0), "properties": {"key": "SPACE"}},
            {"key": "ground", "type": "is_grounded", "position": (270.0, 180.0)},
            {"key": "branch", "type": "if_else", "position": (270.0, 0.0)},
            {"key": "jump", "type": "jump", "position": (540.0, 0.0), "properties": {"force": 440.0}},
        ),
        "edges": (
            ("press", "next", "branch", "in", "flow"),
            ("ground", "is_grounded", "branch", "condition", "bool"),
            ("branch", "true", "jump", "in", "flow"),
        ),
    },
    {
        "id": "spawn_bullet_on_shoot",
        "topics": ("Action", "Objects"),
        "title": "Spawn Prefab / Bullet on Key",
        "category": "Combat & Weapons",
        "summary": "Instantiates a Prefab or object at current position when a trigger key is pressed.",
        "keywords": "spawn create prefab bullet shoot key press instance",
        "steps": (
            "On Key Pressed triggers on shoot key (e.g. F or SPACE).",
            "Get Position reads shooter coordinates.",
            "Create Prefab instantiates the projectile asset at position.",
        ),
        "nodes": (
            {"key": "press", "type": "event_key_pressed", "position": (0.0, 0.0), "properties": {"key": "F"}},
            {"key": "pos", "type": "get_position", "position": (0.0, 180.0)},
            {"key": "spawn", "type": "create_prefab", "position": (320.0, 0.0), "properties": {"path": "Assets/Prefabs/Bullet.zprefab"}},
        ),
        "edges": (
            ("press", "next", "spawn", "in", "flow"),
            ("pos", "x", "spawn", "x", "number"),
            ("pos", "y", "spawn", "y", "number"),
        ),
    },
    {
        "id": "cooldown_timer_example",
        "topics": ("Logic",),
        "title": "Cooldown Before Next Action",
        "category": "Logic & Timers",
        "summary": "Enforces a mandatory delay before an action can be triggered again.",
        "keywords": "cooldown timer delay rate limit pause logic",
        "steps": (
            "On Update attempts action every frame.",
            "Cooldown block filters execution; allows flow only after duration passes.",
            "Adjust duration property to control frequency.",
        ),
        "nodes": (
            {"key": "update", "type": "event_update", "position": (0.0, 0.0)},
            {"key": "cd", "type": "cooldown", "position": (270.0, 0.0), "properties": {"duration": 0.5}},
            {"key": "log", "type": "log_message", "position": (540.0, 0.0), "properties": {"text": "Action triggered after cooldown"}},
        ),
        "edges": (
            ("update", "next", "cd", "in", "flow"),
            ("cd", "next", "log", "in", "flow"),
        ),
    },
    {
        "id": "repeating_timer_log",
        "topics": ("Events", "Logic"),
        "title": "Repeating Timer",
        "category": "Logic & Timers",
        "summary": "Executes a block of logic on a fixed repeating interval.",
        "keywords": "timer repeat loop interval tick period",
        "steps": (
            "Timer event fires automatically every X seconds.",
            "Connected actions execute on each tick.",
            "Enable Repeat property to keep timer firing indefinitely.",
        ),
        "nodes": (
            {"key": "timer", "type": "event_timer", "position": (0.0, 0.0), "properties": {"seconds": 1.0, "repeat": True}},
            {"key": "log", "type": "log_message", "position": (270.0, 0.0), "properties": {"text": "One second passed"}},
        ),
        "edges": (("timer", "next", "log", "in", "flow"),),
    },
    {
        "id": "if_else_example",
        "topics": ("Logic", "Condition"),
        "title": "Choose Between Two Actions",
        "category": "Logic & Conditions",
        "summary": "Demonstrates how to split execution paths based on a boolean condition.",
        "keywords": "if else true false decision condition logic",
        "steps": (
            "On Start enters the If / Else block.",
            "True and False paths run completely independent blocks.",
            "Edit the Condition parameter in properties to test both paths.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "branch", "type": "if_else", "position": (270.0, 0.0), "properties": {"condition": True}},
            {"key": "yes", "type": "log_message", "position": (540.0, -80.0), "properties": {"text": "Condition is true"}},
            {"key": "no", "type": "log_message", "position": (540.0, 100.0), "properties": {"text": "Condition is false"}},
        ),
        "edges": (
            ("start", "next", "branch", "in", "flow"),
            ("branch", "true", "yes", "in", "flow"),
            ("branch", "false", "no", "in", "flow"),
        ),
    },
    {
        "id": "find_and_hide_tag",
        "topics": ("Objects",),
        "title": "Find Object by Tag and Disable",
        "category": "Objects & Scene",
        "summary": "Searches for an object with a specific tag and disables it during runtime.",
        "keywords": "object search find tag hide disable scene",
        "steps": (
            "Find by Tag locates the first active object with that tag.",
            "The object output port sends the reference to Enable / Disable.",
            "Edit the Target Tag and Active properties in the node panel.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "find", "type": "find_tag", "position": (270.0, 0.0), "properties": {"tag": "Enemy"}},
            {"key": "active", "type": "set_active", "position": (540.0, 0.0), "properties": {"active": False}},
        ),
        "edges": (
            ("start", "next", "find", "in", "flow"),
            ("find", "next", "active", "in", "flow"),
            ("find", "object", "active", "target", "object"),
        ),
    },
    {
        "id": "store_starting_health",
        "topics": ("Variables",),
        "title": "Create Health Variable",
        "category": "Variables",
        "summary": "Saves an initial Health variable on the object with a value of 100.",
        "keywords": "variable health points value store set",
        "steps": (
            "On Start triggers only once.",
            "Number node outputs the value 100.0.",
            "Set Variable stores 'Health' on the object scope.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "number", "type": "number_value", "position": (0.0, 180.0), "properties": {"value": 100.0}},
            {"key": "set", "type": "set_variable", "position": (270.0, 0.0), "properties": {"scope": "object", "name": "Health", "value": 100.0}},
        ),
        "edges": (
            ("start", "next", "set", "in", "flow"),
            ("number", "value", "set", "value", "number"),
        ),
    },
    {
        "id": "math_to_hud",
        "topics": ("Math",),
        "title": "Add Numbers and Show on HUD",
        "category": "Math & HUD",
        "summary": "Adds two numbers, converts the sum to text, and displays it on screen.",
        "keywords": "add math numbers sum convert hud",
        "steps": (
            "Add calculates A plus B from input ports or properties.",
            "Convert to Text transforms the numeric value to a string.",
            "Update HUD displays the result string on screen.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "add", "type": "add_number", "position": (0.0, 180.0), "properties": {"a": 10.0, "b": 5.0}},
            {"key": "text", "type": "to_text", "position": (270.0, 180.0)},
            {"key": "hud", "type": "set_hud", "position": (540.0, 0.0)},
        ),
        "edges": (
            ("start", "next", "hud", "in", "flow"),
            ("add", "value", "text", "value", "number"),
            ("text", "value", "hud", "text", "text"),
        ),
    },
    {
        "id": "join_text_to_hud",
        "topics": ("Text",),
        "title": "Join Texts and Show on HUD",
        "category": "Text & HUD",
        "summary": "Combines two pieces of text and displays the resulting phrase on screen.",
        "keywords": "text concatenate phrase name hud UI",
        "steps": (
            "Join Texts combines inputs A and B.",
            "The output value port enters the HUD text property.",
            "Edit both input strings to customize your message.",
        ),
        "nodes": (
            {"key": "start", "type": "event_start", "position": (0.0, 0.0)},
            {"key": "join", "type": "join_text", "position": (0.0, 180.0), "properties": {"a": "Hello, ", "b": "player!"}},
            {"key": "hud", "type": "set_hud", "position": (320.0, 0.0)},
        ),
        "edges": (
            ("start", "next", "hud", "in", "flow"),
            ("join", "value", "hud", "text", "text"),
        ),
    },
)

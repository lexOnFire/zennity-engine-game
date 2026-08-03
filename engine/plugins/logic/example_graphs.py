"""Example Graphs — Item 2: Grafos de Exemplo Reais para o Visual Scripting.

Cinco grafos pré-montados, prontos para carregar no GraphCanvas via
``GraphCanvas.load_graph_data(data)``.

Grafos incluídos:
  1. PLATFORMER_MOVEMENT  — Movimento de plataforma (teclado → velocidade → posição)
  2. ENEMY_AI             — IA de inimigo simples (detectar → perseguir → atacar)
  3. HUD                  — HUD reativa (vida, stamina, pontos, texto)
  4. COMBAT               — Combate (colisão → dano → check morte → respawn)
  5. SAVE_LOAD            — Save / Load de dados (persistência em variável global)

Uso:
    from engine.plugins.logic.example_graphs import EXAMPLE_GRAPHS
    canvas.load_graph_data(EXAMPLE_GRAPHS["platformer_movement"])
"""
from __future__ import annotations
import uuid

# ─────────────────────────────────────────────────────────────────────────────
#  Helper para gerar IDs determinísticos (legíveis nos grafos)
# ─────────────────────────────────────────────────────────────────────────────

def _nid(name: str) -> str:
    """Gera um UUID v5 determinístico a partir de um nome legível."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"zennity.example.{name}"))


def _eid(name: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"zennity.edge.{name}"))


# ─────────────────────────────────────────────────────────────────────────────
#  1. PLATFORMER MOVEMENT
# ─────────────────────────────────────────────────────────────────────────────
_PM = "platformer_movement"
_PLATFORMER_MOVEMENT: dict = {
    "nodes": [
        # Row 1 — Events
        {"id": _nid(f"{_PM}.update"),    "type": "logic.events.update",    "position": [40,  60],  "properties": {}},
        {"id": _nid(f"{_PM}.key_left"),  "type": "logic.events.key_press", "position": [40,  180], "properties": {"key_name": "A"}},
        {"id": _nid(f"{_PM}.key_right"), "type": "logic.events.key_press", "position": [40,  300], "properties": {"key_name": "D"}},
        {"id": _nid(f"{_PM}.key_jump"),  "type": "logic.events.key_press", "position": [40,  420], "properties": {"key_name": "Space"}},
        # Row 2 — Movement / Physics
        {"id": _nid(f"{_PM}.set_vel_x"), "type": "logic.movement.set_velocity", "position": [320, 240], "properties": {"x": -5.0, "y": 0.0}},
        {"id": _nid(f"{_PM}.add_force"), "type": "logic.physics.add_force",     "position": [320, 420], "properties": {"x": 0.0, "y": 8.0}},
        # Row 3 — Clamp speed
        {"id": _nid(f"{_PM}.get_vel"),   "type": "logic.physics.get_velocity",  "position": [600, 140]},
        {"id": _nid(f"{_PM}.clamp"),     "type": "logic.math.clamp",            "position": [600, 260], "properties": {"min": -8.0, "max": 8.0}},
        {"id": _nid(f"{_PM}.set_vel2"),  "type": "logic.movement.set_velocity", "position": [830, 260]},
        # Row 4 — Animation
        {"id": _nid(f"{_PM}.anim_run"),  "type": "logic.animation.play",        "position": [600, 380], "properties": {"clip": "Run"}},
        {"id": _nid(f"{_PM}.anim_idle"), "type": "logic.animation.play",        "position": [600, 460], "properties": {"clip": "Idle"}},
    ],
    "edges": [
        # Update → get velocity
        {"id": _eid(f"{_PM}.e1"), "source_node": _nid(f"{_PM}.update"),    "source_port": "exec",   "target_node": _nid(f"{_PM}.get_vel"),   "target_port": "exec",   "type": "exec"},
        # Get vel X → clamp input
        {"id": _eid(f"{_PM}.e2"), "source_node": _nid(f"{_PM}.get_vel"),   "source_port": "x",      "target_node": _nid(f"{_PM}.clamp"),     "target_port": "value",  "type": "float"},
        # Clamp → set vel 2
        {"id": _eid(f"{_PM}.e3"), "source_node": _nid(f"{_PM}.clamp"),     "source_port": "result", "target_node": _nid(f"{_PM}.set_vel2"),  "target_port": "x",      "type": "float"},
        # Key Left/Right → set_vel_x
        {"id": _eid(f"{_PM}.e4"), "source_node": _nid(f"{_PM}.key_left"),  "source_port": "exec",   "target_node": _nid(f"{_PM}.set_vel_x"), "target_port": "exec",   "type": "exec"},
        {"id": _eid(f"{_PM}.e5"), "source_node": _nid(f"{_PM}.key_right"), "source_port": "exec",   "target_node": _nid(f"{_PM}.set_vel_x"), "target_port": "exec",   "type": "exec"},
        # Key Jump → add force
        {"id": _eid(f"{_PM}.e6"), "source_node": _nid(f"{_PM}.key_jump"),  "source_port": "exec",   "target_node": _nid(f"{_PM}.add_force"), "target_port": "exec",   "type": "exec"},
        # Key Left/Right → anim_run
        {"id": _eid(f"{_PM}.e7"), "source_node": _nid(f"{_PM}.key_left"),  "source_port": "exec",   "target_node": _nid(f"{_PM}.anim_run"),  "target_port": "exec",   "type": "exec"},
        {"id": _eid(f"{_PM}.e8"), "source_node": _nid(f"{_PM}.key_right"), "source_port": "exec",   "target_node": _nid(f"{_PM}.anim_run"),  "target_port": "exec",   "type": "exec"},
        # Update → anim_idle (fallback)
        {"id": _eid(f"{_PM}.e9"), "source_node": _nid(f"{_PM}.update"),    "source_port": "exec",   "target_node": _nid(f"{_PM}.anim_idle"), "target_port": "exec",   "type": "exec"},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
#  2. ENEMY AI
# ─────────────────────────────────────────────────────────────────────────────
_EA = "enemy_ai"
_ENEMY_AI: dict = {
    "nodes": [
        {"id": _nid(f"{_EA}.update"),   "type": "logic.events.update",         "position": [40,  80]},
        {"id": _nid(f"{_EA}.find"),     "type": "logic.objects.find",          "position": [300, 80],  "properties": {"tag": "Player"}},
        {"id": _nid(f"{_EA}.branch"),   "type": "logic.flow.branch",           "position": [580, 80]},
        {"id": _nid(f"{_EA}.dist"),     "type": "logic.math.distance",         "position": [300, 220]},
        {"id": _nid(f"{_EA}.cmp"),      "type": "logic.math.compare",          "position": [580, 220], "properties": {"operator": "<=", "b": 5.0}},
        {"id": _nid(f"{_EA}.chase"),    "type": "logic.ai.chase",              "position": [840, 80],  "properties": {"speed": 3.5}},
        {"id": _nid(f"{_EA}.patrol"),   "type": "logic.ai.patrol",             "position": [840, 220], "properties": {"speed": 1.5}},
        {"id": _nid(f"{_EA}.attack"),   "type": "logic.ai.attack",             "position": [1100, 80]},
        {"id": _nid(f"{_EA}.anim_run"), "type": "logic.animation.play",        "position": [1100, 200], "properties": {"clip": "EnemyRun"}},
    ],
    "edges": [
        {"id": _eid(f"{_EA}.e1"), "source_node": _nid(f"{_EA}.update"), "source_port": "exec", "target_node": _nid(f"{_EA}.find"),   "target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_EA}.e2"), "source_node": _nid(f"{_EA}.find"),   "source_port": "exec", "target_node": _nid(f"{_EA}.dist"),   "target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_EA}.e3"), "source_node": _nid(f"{_EA}.find"),   "source_port": "result","target_node": _nid(f"{_EA}.dist"),  "target_port": "b",     "type": "object"},
        {"id": _eid(f"{_EA}.e4"), "source_node": _nid(f"{_EA}.dist"),   "source_port": "result","target_node": _nid(f"{_EA}.cmp"),   "target_port": "a",     "type": "float"},
        {"id": _eid(f"{_EA}.e5"), "source_node": _nid(f"{_EA}.cmp"),    "source_port": "result","target_node": _nid(f"{_EA}.branch"),"target_port": "condition","type": "bool"},
        {"id": _eid(f"{_EA}.e6"), "source_node": _nid(f"{_EA}.branch"), "source_port": "true", "target_node": _nid(f"{_EA}.chase"),  "target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_EA}.e7"), "source_node": _nid(f"{_EA}.branch"), "source_port": "false","target_node": _nid(f"{_EA}.patrol"), "target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_EA}.e8"), "source_node": _nid(f"{_EA}.chase"),  "source_port": "exec", "target_node": _nid(f"{_EA}.attack"), "target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_EA}.e9"), "source_node": _nid(f"{_EA}.chase"),  "source_port": "exec", "target_node": _nid(f"{_EA}.anim_run"),"target_port": "exec", "type": "exec"},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
#  3. HUD
# ─────────────────────────────────────────────────────────────────────────────
_HU = "hud"
_HUD: dict = {
    "nodes": [
        {"id": _nid(f"{_HU}.update"),     "type": "logic.events.update",          "position": [40,  80]},
        {"id": _nid(f"{_HU}.get_hp"),     "type": "logic.variables.get",          "position": [300, 80],  "properties": {"name": "player_hp"}},
        {"id": _nid(f"{_HU}.get_stamina"),"type": "logic.variables.get",          "position": [300, 200], "properties": {"name": "player_stamina"}},
        {"id": _nid(f"{_HU}.get_score"),  "type": "logic.variables.get",          "position": [300, 320], "properties": {"name": "score"}},
        {"id": _nid(f"{_HU}.hp_bar"),     "type": "logic.ui.set_progress_bar",    "position": [600, 80],  "properties": {"element": "HP_Bar"}},
        {"id": _nid(f"{_HU}.stamina_bar"),"type": "logic.ui.set_progress_bar",    "position": [600, 200], "properties": {"element": "Stamina_Bar"}},
        {"id": _nid(f"{_HU}.score_text"), "type": "logic.ui.set_text",            "position": [600, 320], "properties": {"element": "Score_Label", "prefix": "Score: "}},
        {"id": _nid(f"{_HU}.anim_hp"),    "type": "logic.animation.play",         "position": [860, 80],  "properties": {"clip": "HP_Pulse"}},
    ],
    "edges": [
        {"id": _eid(f"{_HU}.e1"), "source_node": _nid(f"{_HU}.update"),     "source_port": "exec",  "target_node": _nid(f"{_HU}.get_hp"),     "target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_HU}.e2"), "source_node": _nid(f"{_HU}.get_hp"),     "source_port": "exec",  "target_node": _nid(f"{_HU}.get_stamina"),"target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_HU}.e3"), "source_node": _nid(f"{_HU}.get_stamina"),"source_port": "exec",  "target_node": _nid(f"{_HU}.get_score"),  "target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_HU}.e4"), "source_node": _nid(f"{_HU}.get_hp"),     "source_port": "value", "target_node": _nid(f"{_HU}.hp_bar"),     "target_port": "value", "type": "float"},
        {"id": _eid(f"{_HU}.e5"), "source_node": _nid(f"{_HU}.get_stamina"),"source_port": "value", "target_node": _nid(f"{_HU}.stamina_bar"),"target_port": "value", "type": "float"},
        {"id": _eid(f"{_HU}.e6"), "source_node": _nid(f"{_HU}.get_score"),  "source_port": "value", "target_node": _nid(f"{_HU}.score_text"), "target_port": "value", "type": "float"},
        {"id": _eid(f"{_HU}.e7"), "source_node": _nid(f"{_HU}.hp_bar"),     "source_port": "exec",  "target_node": _nid(f"{_HU}.anim_hp"),    "target_port": "exec",  "type": "exec"},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
#  4. COMBAT
# ─────────────────────────────────────────────────────────────────────────────
_CB = "combat"
_COMBAT: dict = {
    "nodes": [
        {"id": _nid(f"{_CB}.collision"),  "type": "logic.events.collision_enter",  "position": [40,  100]},
        {"id": _nid(f"{_CB}.get_hp"),     "type": "logic.variables.get",           "position": [320, 100], "properties": {"name": "player_hp"}},
        {"id": _nid(f"{_CB}.sub"),        "type": "logic.math.subtract",           "position": [560, 100], "properties": {"b": 10.0}},
        {"id": _nid(f"{_CB}.set_hp"),     "type": "logic.variables.set",           "position": [800, 100], "properties": {"name": "player_hp"}},
        {"id": _nid(f"{_CB}.cmp_dead"),   "type": "logic.math.compare",            "position": [800, 240], "properties": {"operator": "<=", "b": 0.0}},
        {"id": _nid(f"{_CB}.branch"),     "type": "logic.flow.branch",             "position": [1060, 100]},
        {"id": _nid(f"{_CB}.game_over"),  "type": "logic.scene.load",              "position": [1280, 80],  "properties": {"scene": "GameOver"}},
        {"id": _nid(f"{_CB}.anim_hurt"),  "type": "logic.animation.play",          "position": [1280, 200], "properties": {"clip": "Hurt"}},
        {"id": _nid(f"{_CB}.audio_hit"),  "type": "logic.audio.play",              "position": [560, 240], "properties": {"clip": "hit_sfx"}},
    ],
    "edges": [
        {"id": _eid(f"{_CB}.e1"), "source_node": _nid(f"{_CB}.collision"), "source_port": "exec",  "target_node": _nid(f"{_CB}.get_hp"),    "target_port": "exec",    "type": "exec"},
        {"id": _eid(f"{_CB}.e2"), "source_node": _nid(f"{_CB}.get_hp"),    "source_port": "value", "target_node": _nid(f"{_CB}.sub"),       "target_port": "a",       "type": "float"},
        {"id": _eid(f"{_CB}.e3"), "source_node": _nid(f"{_CB}.sub"),       "source_port": "result","target_node": _nid(f"{_CB}.set_hp"),    "target_port": "value",   "type": "float"},
        {"id": _eid(f"{_CB}.e4"), "source_node": _nid(f"{_CB}.sub"),       "source_port": "result","target_node": _nid(f"{_CB}.cmp_dead"),  "target_port": "a",       "type": "float"},
        {"id": _eid(f"{_CB}.e5"), "source_node": _nid(f"{_CB}.cmp_dead"),  "source_port": "result","target_node": _nid(f"{_CB}.branch"),    "target_port": "condition","type": "bool"},
        {"id": _eid(f"{_CB}.e6"), "source_node": _nid(f"{_CB}.set_hp"),    "source_port": "exec",  "target_node": _nid(f"{_CB}.branch"),    "target_port": "exec",    "type": "exec"},
        {"id": _eid(f"{_CB}.e7"), "source_node": _nid(f"{_CB}.branch"),    "source_port": "true",  "target_node": _nid(f"{_CB}.game_over"), "target_port": "exec",    "type": "exec"},
        {"id": _eid(f"{_CB}.e8"), "source_node": _nid(f"{_CB}.branch"),    "source_port": "false", "target_node": _nid(f"{_CB}.anim_hurt"), "target_port": "exec",    "type": "exec"},
        {"id": _eid(f"{_CB}.e9"), "source_node": _nid(f"{_CB}.collision"), "source_port": "exec",  "target_node": _nid(f"{_CB}.audio_hit"), "target_port": "exec",    "type": "exec"},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
#  5. SAVE / LOAD
# ─────────────────────────────────────────────────────────────────────────────
_SL = "save_load"
_SAVE_LOAD: dict = {
    "nodes": [
        # Save path
        {"id": _nid(f"{_SL}.key_save"),  "type": "logic.events.key_press", "position": [40,  60],  "properties": {"key_name": "F5"}},
        {"id": _nid(f"{_SL}.get_hp"),    "type": "logic.variables.get",    "position": [300, 60],  "properties": {"name": "player_hp"}},
        {"id": _nid(f"{_SL}.get_score"), "type": "logic.variables.get",    "position": [300, 180], "properties": {"name": "score"}},
        {"id": _nid(f"{_SL}.get_pos"),   "type": "logic.transform.get_pos","position": [300, 300]},
        {"id": _nid(f"{_SL}.save_hp"),   "type": "logic.variables.set",    "position": [580, 60],  "properties": {"name": "save_hp",    "scope": "global"}},
        {"id": _nid(f"{_SL}.save_score"),"type": "logic.variables.set",    "position": [580, 180], "properties": {"name": "save_score", "scope": "global"}},
        {"id": _nid(f"{_SL}.save_pos"),  "type": "logic.variables.set",    "position": [580, 300], "properties": {"name": "save_pos",   "scope": "global"}},
        {"id": _nid(f"{_SL}.notify"),    "type": "logic.ui.set_text",      "position": [860, 180], "properties": {"element": "Notify", "value": "Game Saved!"}},

        # Load path
        {"id": _nid(f"{_SL}.key_load"),  "type": "logic.events.key_press", "position": [40,  480], "properties": {"key_name": "F9"}},
        {"id": _nid(f"{_SL}.load_hp"),   "type": "logic.variables.get",    "position": [300, 480], "properties": {"name": "save_hp",    "scope": "global"}},
        {"id": _nid(f"{_SL}.load_score"),"type": "logic.variables.get",    "position": [300, 600], "properties": {"name": "save_score", "scope": "global"}},
        {"id": _nid(f"{_SL}.load_pos"),  "type": "logic.variables.get",    "position": [300, 720], "properties": {"name": "save_pos",   "scope": "global"}},
        {"id": _nid(f"{_SL}.set_hp"),    "type": "logic.variables.set",    "position": [580, 480], "properties": {"name": "player_hp"}},
        {"id": _nid(f"{_SL}.set_score"), "type": "logic.variables.set",    "position": [580, 600], "properties": {"name": "score"}},
        {"id": _nid(f"{_SL}.set_pos"),   "type": "logic.transform.set_pos","position": [580, 720]},
        {"id": _nid(f"{_SL}.notif_load"),"type": "logic.ui.set_text",      "position": [860, 600], "properties": {"element": "Notify", "value": "Game Loaded!"}},
    ],
    "edges": [
        # Save chain
        {"id": _eid(f"{_SL}.e1"),  "source_node": _nid(f"{_SL}.key_save"),  "source_port": "exec",  "target_node": _nid(f"{_SL}.get_hp"),    "target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_SL}.e2"),  "source_node": _nid(f"{_SL}.get_hp"),    "source_port": "exec",  "target_node": _nid(f"{_SL}.get_score"), "target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_SL}.e3"),  "source_node": _nid(f"{_SL}.get_score"), "source_port": "exec",  "target_node": _nid(f"{_SL}.get_pos"),   "target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_SL}.e4"),  "source_node": _nid(f"{_SL}.get_hp"),    "source_port": "value", "target_node": _nid(f"{_SL}.save_hp"),   "target_port": "value", "type": "float"},
        {"id": _eid(f"{_SL}.e5"),  "source_node": _nid(f"{_SL}.get_score"), "source_port": "value", "target_node": _nid(f"{_SL}.save_score"),"target_port": "value", "type": "float"},
        {"id": _eid(f"{_SL}.e6"),  "source_node": _nid(f"{_SL}.get_pos"),   "source_port": "exec",  "target_node": _nid(f"{_SL}.save_pos"),  "target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_SL}.e7"),  "source_node": _nid(f"{_SL}.save_pos"),  "source_port": "exec",  "target_node": _nid(f"{_SL}.notify"),    "target_port": "exec",  "type": "exec"},
        # Load chain
        {"id": _eid(f"{_SL}.e8"),  "source_node": _nid(f"{_SL}.key_load"),  "source_port": "exec",  "target_node": _nid(f"{_SL}.load_hp"),   "target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_SL}.e9"),  "source_node": _nid(f"{_SL}.load_hp"),   "source_port": "exec",  "target_node": _nid(f"{_SL}.load_score"),"target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_SL}.e10"), "source_node": _nid(f"{_SL}.load_score"),"source_port": "exec",  "target_node": _nid(f"{_SL}.load_pos"),  "target_port": "exec",  "type": "exec"},
        {"id": _eid(f"{_SL}.e11"), "source_node": _nid(f"{_SL}.load_hp"),   "source_port": "value", "target_node": _nid(f"{_SL}.set_hp"),    "target_port": "value", "type": "float"},
        {"id": _eid(f"{_SL}.e12"), "source_node": _nid(f"{_SL}.load_score"),"source_port": "value", "target_node": _nid(f"{_SL}.set_score"), "target_port": "value", "type": "float"},
        {"id": _eid(f"{_SL}.e13"), "source_node": _nid(f"{_SL}.load_pos"),  "source_port": "value", "target_node": _nid(f"{_SL}.set_pos"),   "target_port": "value", "type": "any"},
        {"id": _eid(f"{_SL}.e14"), "source_node": _nid(f"{_SL}.set_score"), "source_port": "exec",  "target_node": _nid(f"{_SL}.notif_load"),"target_port": "exec",  "type": "exec"},
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
#  Public dict: key → graph data
# ─────────────────────────────────────────────────────────────────────────────
EXAMPLE_GRAPHS: dict[str, dict] = {
    "platformer_movement": _PLATFORMER_MOVEMENT,
    "enemy_ai":            _ENEMY_AI,
    "hud":                 _HUD,
    "combat":              _COMBAT,
    "save_load":           _SAVE_LOAD,
}

EXAMPLE_GRAPH_META: dict[str, dict] = {
    "platformer_movement": {
        "label": "🎮 Platformer Movement",
        "description": "Movimento de plataforma: teclado → velocidade → clampe → animação.",
        "icon": "🎮",
    },
    "enemy_ai": {
        "label": "🤖 Enemy AI",
        "description": "IA de inimigo: detectar jogador → perseguir / patrulhar → atacar.",
        "icon": "🤖",
    },
    "hud": {
        "label": "🖥️ HUD",
        "description": "HUD reativa: vida, stamina e pontos atualizados a cada frame.",
        "icon": "🖥️",
    },
    "combat": {
        "label": "⚔️ Combat",
        "description": "Sistema de combate: colisão → dano → check de morte → game over.",
        "icon": "⚔️",
    },
    "save_load": {
        "label": "💾 Save / Load",
        "description": "Persistência: F5 salva HP/Score/Posição; F9 restaura tudo.",
        "icon": "💾",
    },
}

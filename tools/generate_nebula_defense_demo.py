"""Gera a demo completa Nebula Defense usando somente assets nativos da engine."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.logic.graph_asset import normalize_logic_graph  # noqa: E402


LOGIC_DIR = ROOT / "Assets" / "Logic" / "NebulaDefense"
PREFAB_DIR = ROOT / "Assets" / "Prefabs" / "NebulaDefense"
SCENE_PATH = ROOT / "Assets" / "Scenes" / "NebulaDefense.zscene"


def projectile_properties() -> list[dict[str, Any]]:
    return [
        {"name": "speed", "label": "Velocidade", "type": "number", "default": 680.0, "target": "gameplay.speed", "minimum": 0.0},
        {"name": "damage", "label": "Dano", "type": "number", "default": 1.0, "target": "gameplay.damage", "minimum": 0.0},
        {"name": "direction_x", "label": "Direção X", "type": "number", "default": 1.0, "target": "gameplay.direction_x"},
        {"name": "direction_y", "label": "Direção Y", "type": "number", "default": 0.0, "target": "gameplay.direction_y"},
        {"name": "lifetime", "label": "Tempo de vida", "type": "number", "default": 2.2, "target": "gameplay.lifetime", "semantic": "lifetime", "minimum": 0.0},
        {"name": "image", "label": "Imagem", "type": "image", "default": "", "target": "texture", "asset_kind": "image"},
        {"name": "animation", "label": "Animação", "type": "animation", "default": "", "target": "animator.asset_path", "asset_kind": "animation"},
        {"name": "sound", "label": "Som", "type": "audio", "default": "Assets/Audio/jump-sound-531048.mp3", "target": "gameplay.sound", "asset_kind": "audio"},
        {"name": "width", "label": "Escala X", "type": "number", "default": 30.0, "target": "w", "minimum": 1.0},
        {"name": "height", "label": "Escala Y", "type": "number", "default": 10.0, "target": "h", "minimum": 1.0},
        {"name": "color", "label": "Cor", "type": "color", "default": [86, 221, 255], "target": "color"},
        {"name": "tag", "label": "Tag", "type": "text", "default": "ProjectileNebula", "target": "tag"},
        {"name": "layer", "label": "Layer", "type": "text", "default": "Default", "target": "layer"},
    ]


def projectile_values(**overrides: Any) -> dict[str, Any]:
    values = {item["name"]: item["default"] for item in projectile_properties()}
    values.update(overrides)
    return values


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def node(node_id: str, node_type: str, canvas_x: float, canvas_y: float, **properties: Any) -> dict[str, Any]:
    return {"id": node_id, "type": node_type, "position": [canvas_x, canvas_y], "properties": properties}


def edge(
    source: str,
    target: str,
    *,
    source_port: str = "next",
    target_port: str = "in",
    kind: str = "flow",
    order: int = 0,
) -> dict[str, Any]:
    return {
        "id": f"{source}_{source_port}_{target}_{target_port}",
        "from_node": source,
        "from_port": source_port,
        "to_node": target,
        "to_port": target_port,
        "kind": kind,
        "order": order,
    }


def graph(
    name: str,
    target_type: str,
    target_value: str,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    comments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return normalize_logic_graph({
        "format": "zennity.logic_graph",
        "version": 1,
        "name": name,
        "target": {"type": target_type, "value": target_value},
        "nodes": nodes,
        "edges": edges,
        "editor": {"groups": [], "comments": comments or []},
    })


def scene_object(
    object_id: str,
    name: str,
    x: float,
    y: float,
    width: float,
    height: float,
    color: list[int],
    *,
    tag: str = "Untagged",
    texture: str = "",
    order: int = 0,
    active: bool = True,
    renderer_enabled: bool = True,
    collider: dict[str, Any] | None = None,
    rigidbody: dict[str, Any] | None = None,
    camera: dict[str, Any] | None = None,
    audio: dict[str, Any] | None = None,
) -> dict[str, Any]:
    components: dict[str, Any] = {"scripts": []}
    for key, value in (("collider", collider), ("rigidbody", rigidbody), ("camera", camera), ("audio", audio)):
        if value is not None:
            components[key] = value
    return {
        "id": object_id,
        "uuid": object_id,
        "name": name,
        "tag": tag,
        "layer": "Default",
        "active": active,
        "enabled": active,
        "transform": {
            "position": [x, y, 0.0],
            "rotation": [0.0, 0.0, 0.0],
            "rz": 0.0,
            "scale": [width, height, 1.0],
        },
        "visual": {
            "enabled": renderer_enabled,
            "mesh_type": "Sprite" if texture else "Quadrado",
            "texture": texture,
            "color": color,
            "layer": "Default",
            "order": order,
        },
        "components": components,
    }


def player_graph() -> dict[str, Any]:
    nodes = [
        node("update", "event_update", 20, 80),
        node("left", "key_held", 260, 20, key="A"),
        node("move_left", "move_by", 520, 20, x=-260.0, y=0.0),
        node("right", "key_held", 260, 160, key="D"),
        node("move_right", "move_by", 520, 160, x=260.0, y=0.0),
        node("up", "key_held", 260, 300, key="W"),
        node("move_up", "move_by", 520, 300, x=0.0, y=-260.0),
        node("down", "key_held", 260, 440, key="S"),
        node("move_down", "move_by", 520, 440, x=0.0, y=260.0),
        node("shoot", "event_key_pressed", 20, 650, key="SPACE"),
        node(
            "spawn_bolt", "create_prefab", 300, 650,
            path="Assets/Prefabs/NebulaDefense/NebulaBolt.zprefab",
            override_position=True, x=48.0, y=0.0, relative=True,
            override_rotation=False, override_scale=False,
            include_camera=False, include_audio=False, include_logic=False,
            lifetime=2.2, max_instances=24, max_distance=1400.0, use_pool=True,
            parameters=projectile_values(),
            exposed_properties=projectile_properties(),
        ),
        node("missile", "event_key_pressed", 20, 800, key="M"),
        node(
            "spawn_missile", "create_prefab", 300, 800,
            path="Assets/Prefabs/NebulaDefense/NebulaMissile.zprefab",
            override_position=True, x=56.0, y=0.0, relative=True,
            override_rotation=False, override_scale=False,
            include_camera=False, include_audio=False, include_logic=False,
            lifetime=4.0, max_instances=8, max_distance=1600.0, use_pool=True,
            parameters=projectile_values(speed=420.0, damage=3.0, lifetime=4.0, width=48.0, height=16.0, color=[255, 168, 62]),
            exposed_properties=projectile_properties(),
        ),
        node("hit", "event_trigger_enter", 20, 980),
        node("other_tag", "get_tag", 260, 900),
        node("is_enemy", "compare_text", 500, 980, operator="==", value="EnemyNebula"),
        node("hit_sequence", "sequence", 760, 980, outputs=3),
        node("get_lives", "get_variable", 1020, 860, scope="project", name="lives"),
        node("lose_life", "subtract_number", 1260, 860, a=0.0, b=1.0),
        node("save_lives", "set_variable", 1500, 860, scope="project", name="lives", value=2.0),
        node("is_dead", "compare_number", 1740, 860, operator="<=", value=0.0),
        node("disable_player", "set_active", 1980, 820, active=False),
        node("death_hud", "set_hud", 1980, 940, text="FIM DE JOGO — pressione R para reiniciar"),
        node("reset_position", "set_position", 1020, 1040, x=120.0, y=360.0),
        node("hit_sound", "play_sound", 1020, 1180, path="Assets/Audio/freesound_community-videogame-death-sound-43894.mp3"),
    ]
    edges = [
        edge("update", "left", order=0), edge("left", "move_left", source_port="true"),
        edge("update", "right", order=1), edge("right", "move_right", source_port="true"),
        edge("update", "up", order=2), edge("up", "move_up", source_port="true"),
        edge("update", "down", order=3), edge("down", "move_down", source_port="true"),
        edge("shoot", "spawn_bolt"),
        edge("missile", "spawn_missile"),
        edge("hit", "is_enemy"),
        edge("hit", "other_tag", source_port="other", target_port="target", kind="object"),
        edge("other_tag", "is_enemy", source_port="value", target_port="value", kind="text"),
        edge("is_enemy", "hit_sequence", source_port="true"),
        edge("hit_sequence", "save_lives", source_port="then_0", order=0),
        edge("get_lives", "lose_life", source_port="value", target_port="a", kind="number"),
        edge("lose_life", "save_lives", source_port="value", target_port="value", kind="number"),
        edge("save_lives", "is_dead"),
        edge("lose_life", "is_dead", source_port="value", target_port="value", kind="number"),
        edge("is_dead", "disable_player", source_port="true", order=0),
        edge("is_dead", "death_hud", source_port="true", order=1),
        edge("hit_sequence", "reset_position", source_port="then_1", order=1),
        edge("hit_sequence", "hit_sound", source_port="then_2", order=2),
    ]
    return graph(
        "Nebula Player Controls", "name", "NebulaPilot", nodes, edges,
        [{"id": "help-player", "text": "WASD move • Espaço dispara • M lança variante de míssil", "position": [10, -80], "width": 560}],
    )


def spawner_graph() -> dict[str, Any]:
    nodes = [
        node("spawn_timer", "event_timer", 40, 120, seconds=1.15, repeat=True),
        node("random_y", "random_number", 300, 20, minimum=80.0, maximum=640.0),
        node(
            "spawn_enemy", "create_prefab", 560, 120,
            path="Assets/Prefabs/NebulaDefense/NebulaDrone.zprefab",
            override_position=True, x=1160.0, y=360.0, relative=False,
            override_rotation=False, override_scale=False,
            include_camera=False, include_audio=False, include_logic=False,
            lifetime=10.0, max_instances=9, max_distance=1500.0, use_pool=True,
        ),
    ]
    edges = [
        edge("spawn_timer", "spawn_enemy"),
        edge("random_y", "spawn_enemy", source_port="value", target_port="y", kind="number"),
    ]
    return graph("Nebula Enemy Spawner", "name", "NebulaSpawner", nodes, edges)


def enemy_graph() -> dict[str, Any]:
    nodes = [
        node("start", "event_start", 20, 100),
        node(
            "advance", "start_continuous_motion", 280, 100,
            movement="Ataque", x=-155.0, y=0.0, space="global",
            acceleration=100.0, deceleration=0.0,
        ),
        node("trigger", "event_trigger_enter", 20, 360),
        node("other_tag", "get_tag", 260, 280),
        node("is_bolt", "compare_text", 500, 360, operator="==", value="ProjectileNebula"),
        node("destroy_sequence", "sequence", 760, 300, outputs=3),
        node("destroy_enemy", "destroy_object", 1020, 220),
        node("get_score", "get_variable", 1020, 380, scope="project", name="score"),
        node("add_score", "add_number", 1260, 380, a=0.0, b=1.0),
        node("get_damage", "get_prefab_parameter", 1020, 470, name="damage", type="number", default=1.0),
        node("save_score", "set_variable", 1500, 380, scope="project", name="score", value=1.0),
        node("score_sound", "play_sound", 1020, 540, path="Assets/Audio/collect-points-190037.mp3"),
        node("is_player", "compare_text", 760, 660, operator="==", value="Player"),
        node("destroy_on_player", "destroy_object", 1020, 660),
    ]
    edges = [
        edge("start", "advance"),
        edge("trigger", "is_bolt"),
        edge("trigger", "other_tag", source_port="other", target_port="target", kind="object"),
        edge("other_tag", "is_bolt", source_port="value", target_port="value", kind="text"),
        edge("is_bolt", "destroy_sequence", source_port="true"),
        edge("destroy_sequence", "destroy_enemy", source_port="then_0", order=0),
        edge("destroy_sequence", "save_score", source_port="then_1", order=1),
        edge("get_score", "add_score", source_port="value", target_port="a", kind="number"),
        edge("trigger", "get_damage", source_port="other", target_port="target", kind="object"),
        edge("get_damage", "add_score", source_port="value", target_port="b", kind="number"),
        edge("add_score", "save_score", source_port="value", target_port="value", kind="number"),
        edge("destroy_sequence", "score_sound", source_port="then_2", order=2),
        edge("is_bolt", "is_player", source_port="false"),
        edge("other_tag", "is_player", source_port="value", target_port="value", kind="text"),
        edge("is_player", "destroy_on_player", source_port="true"),
    ]
    return graph("Nebula Drone Behavior", "tag", "EnemyNebula", nodes, edges)


def projectile_graph() -> dict[str, Any]:
    nodes = [
        node("start", "event_start", 20, -260),
        node("speed", "get_prefab_parameter", 260, -360, name="speed", type="number", default=680.0),
        node("direction_x", "get_prefab_parameter", 260, -240, name="direction_x", type="number", default=1.0),
        node("velocity_x", "multiply_number", 520, -320, a=680.0, b=1.0),
        node("direction_y", "get_prefab_parameter", 260, -100, name="direction_y", type="number", default=0.0),
        node("velocity_y", "multiply_number", 520, -140, a=680.0, b=0.0),
        node("motion", "start_continuous_motion", 780, -260, movement="PrefabMotion", x=680.0, y=0.0, space="global", acceleration=1200.0, deceleration=0.0),
        node("sound", "get_prefab_parameter", 520, 20, name="sound", type="audio", default="Assets/Audio/jump-sound-531048.mp3"),
        node("play_sound", "play_sound", 780, 20, path="Assets/Audio/jump-sound-531048.mp3"),
        node("trigger", "event_trigger_enter", 20, 120),
        node("other_tag", "get_tag", 280, 20),
        node("is_enemy", "compare_text", 520, 120, operator="==", value="EnemyNebula"),
        node("destroy", "destroy_object", 780, 120),
    ]
    edges = [
        edge("start", "motion", order=0),
        edge("start", "play_sound", order=1),
        edge("speed", "velocity_x", source_port="value", target_port="a", kind="number"),
        edge("direction_x", "velocity_x", source_port="value", target_port="b", kind="number"),
        edge("velocity_x", "motion", source_port="value", target_port="x", kind="number"),
        edge("speed", "velocity_y", source_port="value", target_port="a", kind="number"),
        edge("direction_y", "velocity_y", source_port="value", target_port="b", kind="number"),
        edge("velocity_y", "motion", source_port="value", target_port="y", kind="number"),
        edge("sound", "play_sound", source_port="value", target_port="path", kind="text"),
        edge("trigger", "is_enemy"),
        edge("trigger", "other_tag", source_port="other", target_port="target", kind="object"),
        edge("other_tag", "is_enemy", source_port="value", target_port="value", kind="text"),
        edge("is_enemy", "destroy", source_port="true"),
    ]
    return graph("Nebula Bolt Collision", "tag", "ProjectileNebula", nodes, edges)


def manager_graph() -> dict[str, Any]:
    nodes = [
        node("start", "event_start", 20, 80),
        node("start_sequence", "sequence", 260, 80, outputs=4),
        node("reset_score", "set_variable", 520, 0, scope="project", name="score", value=0.0),
        node("reset_lives", "set_variable", 520, 120, scope="project", name="lives", value=3.0),
        node("help_hud", "set_hud", 520, 240, text="WASD: mover  •  ESPAÇO: disparar  •  M: míssil  •  R: reiniciar"),
        node("start_sound", "play_sound", 520, 360, path="Assets/Audio/game-start-317318.mp3"),
        node("update", "event_update", 20, 620),
        node("get_score", "get_variable", 280, 520, scope="project", name="score"),
        node("score_text", "join_text", 520, 520, a="PONTOS: ", b="0"),
        node("score_hud", "set_hud", 780, 520, text="PONTOS: 0"),
        node("get_lives", "get_variable", 280, 680, scope="project", name="lives"),
        node("lives_text", "join_text", 520, 680, a="VIDAS: ", b="3"),
        node("lives_hud", "set_hud", 780, 680, text="VIDAS: 3"),
        node("victory", "compare_number", 520, 840, operator=">=", value=10.0),
        node("victory_hud", "set_hud", 780, 840, text="VITÓRIA! A frota inimiga foi derrotada — pressione R"),
        node("defeat", "compare_number", 520, 1000, operator="<=", value=0.0),
        node("defeat_hud", "set_hud", 780, 1000, text="FIM DE JOGO — pressione R para tentar novamente"),
        node("restart", "event_key_pressed", 20, 1200, key="R"),
        node("restart_scene", "restart_scene", 300, 1200),
    ]
    edges = [
        edge("start", "start_sequence"),
        edge("start_sequence", "reset_score", source_port="then_0", order=0),
        edge("start_sequence", "reset_lives", source_port="then_1", order=1),
        edge("start_sequence", "help_hud", source_port="then_2", order=2),
        edge("start_sequence", "start_sound", source_port="then_3", order=3),
        edge("update", "score_hud", order=0),
        edge("get_score", "score_text", source_port="value", target_port="b", kind="any"),
        edge("score_text", "score_hud", source_port="value", target_port="text", kind="text"),
        edge("update", "lives_hud", order=1),
        edge("get_lives", "lives_text", source_port="value", target_port="b", kind="any"),
        edge("lives_text", "lives_hud", source_port="value", target_port="text", kind="text"),
        edge("update", "victory", order=2),
        edge("get_score", "victory", source_port="value", target_port="value", kind="number"),
        edge("victory", "victory_hud", source_port="true"),
        edge("update", "defeat", order=3),
        edge("get_lives", "defeat", source_port="value", target_port="value", kind="number"),
        edge("defeat", "defeat_hud", source_port="true"),
        edge("restart", "restart_scene"),
    ]
    return graph("Nebula Game Manager", "name", "NebulaGameManager", nodes, edges)


def background_graph() -> dict[str, Any]:
    nodes = [
        node("start", "event_start", 20, 100),
        node(
            "scroll", "start_texture_scroll", 300, 100,
            path="Assets/Materials/CEU.PNG", speed_x=-18.0, speed_y=0.0,
            repeat_x=True, repeat_y=True, parallax=0.25, send_to_background=True,
        ),
    ]
    return graph(
        "Nebula Scrolling Background", "name", "NebulaBackground", nodes,
        [edge("start", "scroll")],
    )


def build_prefabs() -> None:
    drone = {
        "format_version": 1,
        "prefab_name": "NebulaDrone",
        "object": {
            "name": "NebulaDrone", "x": 1160.0, "y": 360.0,
            "w": 52.0, "h": 42.0, "rotation": 0.0,
            "color": [235, 74, 102], "texture": "Assets/Textures/formiga_2.PNG",
            "tag": "EnemyNebula", "layer": "Default", "renderer_enabled": True,
            "collider": {"type": "box", "width": 44.0, "height": 34.0, "is_trigger": True},
            "rigidbody": {"mass": 1.0, "use_gravity": False, "is_kinematic": True, "gravity_scale": 0.0},
        },
    }
    bolt = {
        "format_version": 2,
        "prefab_name": "NebulaBolt",
        "exposed_properties": projectile_properties(),
        "object": {
            "name": "NebulaBolt", "x": 0.0, "y": 0.0,
            "w": 30.0, "h": 10.0, "rotation": 0.0,
            "color": [86, 221, 255], "tag": "ProjectileNebula",
            "layer": "Default", "renderer_enabled": True,
            "collider": {"type": "box", "width": 30.0, "height": 10.0, "is_trigger": True},
            "rigidbody": {"mass": 0.1, "use_gravity": False, "is_kinematic": True, "gravity_scale": 0.0},
            "gameplay": {"speed": 680.0, "damage": 1.0, "direction_x": 1.0, "direction_y": 0.0, "lifetime": 2.2, "sound": "Assets/Audio/jump-sound-531048.mp3"},
            "animator": {"asset_path": ""},
        },
    }
    write_json(PREFAB_DIR / "NebulaDrone.zprefab", drone)
    write_json(PREFAB_DIR / "NebulaBolt.zprefab", bolt)
    write_json(PREFAB_DIR / "NebulaMissile.zprefab", {
        "format_version": 2,
        "prefab_name": "NebulaMissile",
        "base_prefab": "Assets/Prefabs/NebulaDefense/NebulaBolt.zprefab",
        "property_overrides": {
            "speed": 420.0, "damage": 3.0, "lifetime": 4.0,
            "width": 48.0, "height": 16.0, "color": [255, 168, 62],
        },
        "object_overrides": {"name": "NebulaMissile"},
    })
    write_json(PREFAB_DIR / "NebulaEnemyAttack.zprefab", {
        "format_version": 2,
        "prefab_name": "NebulaEnemyAttack",
        "base_prefab": "Assets/Prefabs/NebulaDefense/NebulaBolt.zprefab",
        "property_overrides": {
            "speed": 360.0, "damage": 1.0, "direction_x": -1.0,
            "lifetime": 4.0, "color": [255, 76, 116], "tag": "EnemyProjectileNebula",
        },
        "object_overrides": {"name": "NebulaEnemyAttack"},
    })


def build_scene() -> None:
    static_body = {"mass": 1.0, "use_gravity": False, "is_kinematic": True, "gravity_scale": 0.0}
    objects = [
        scene_object(
            "nebula-camera", "NebulaCamera", 640, 360, 32, 32, [255, 255, 255],
            tag="MainCamera", renderer_enabled=False,
            camera={"active": True, "zoom": 1.0, "background_color": [5, 8, 24], "priority": 10},
        ),
        scene_object(
            "nebula-background", "NebulaBackground", 640, 360, 1280, 720, [255, 255, 255],
            tag="Environment", texture="Assets/Materials/CEU.PNG", order=-100,
        ),
        scene_object(
            "nebula-player", "NebulaPilot", 120, 360, 52, 36, [64, 210, 255],
            tag="Player", order=20,
            collider={"type": "box", "width": 48.0, "height": 32.0, "is_trigger": False},
            rigidbody={"mass": 1.0, "use_gravity": False, "is_kinematic": False, "gravity_scale": 0.0, "drag": 8.0},
        ),
        scene_object("nebula-spawner", "NebulaSpawner", 0, 0, 1, 1, [0, 0, 0], renderer_enabled=False),
        scene_object(
            "nebula-manager", "NebulaGameManager", 0, 0, 1, 1, [0, 0, 0], renderer_enabled=False,
            audio={
                "path": "Assets/Audio/8bit-music-for-game-68698.mp3",
                "volume": 0.38, "loop": True, "autoplay": True, "enabled": True,
            },
        ),
        scene_object(
            "boundary-top", "NebulaBoundaryTop", 640, 20, 1280, 40, [8, 24, 58], tag="Boundary",
            collider={"type": "box", "width": 1280.0, "height": 40.0, "is_trigger": False}, rigidbody=static_body,
        ),
        scene_object(
            "boundary-bottom", "NebulaBoundaryBottom", 640, 700, 1280, 40, [8, 24, 58], tag="Boundary",
            collider={"type": "box", "width": 1280.0, "height": 40.0, "is_trigger": False}, rigidbody=static_body,
        ),
        scene_object(
            "boundary-left", "NebulaBoundaryLeft", 20, 360, 40, 720, [8, 24, 58], tag="Boundary",
            collider={"type": "box", "width": 40.0, "height": 720.0, "is_trigger": False}, rigidbody=static_body,
        ),
        scene_object(
            "boundary-right", "NebulaBoundaryRight", 1260, 360, 40, 720, [8, 24, 58], tag="Boundary",
            collider={"type": "box", "width": 40.0, "height": 720.0, "is_trigger": False}, rigidbody=static_body,
        ),
    ]
    scene = {
        "format_version": 1,
        "scene_name": "Nebula Defense",
        "engine_version": "0.1.0",
        "description": "Shooter 2D completo criado somente com Logic Graphs e Prefabs seguros.",
        "instructions": "WASD move, Espaço dispara, M lança míssil e R reinicia. Alcance 10 pontos.",
        "blackboard": {
            "variables": {
                "score": {"type": "number", "scope": "project", "default": 0.0},
                "lives": {"type": "number", "scope": "project", "default": 3.0},
            },
        },
        "objects": objects,
    }
    write_json(SCENE_PATH, scene)


def main() -> None:
    build_prefabs()
    build_scene()
    write_json(ROOT / "Assets" / "Logic" / "ProjectBlackboard.zblackboard", {
        "format": "zennity.blackboard",
        "version": 1,
        "variables": {
            "score": {"type": "number", "scope": "project", "default": 0.0},
            "lives": {"type": "number", "scope": "project", "default": 3.0},
        },
    })
    for filename, value in (
        ("NebulaPlayer.zlogic", player_graph()),
        ("NebulaSpawner.zlogic", spawner_graph()),
        ("NebulaEnemy.zlogic", enemy_graph()),
        ("NebulaProjectile.zlogic", projectile_graph()),
        ("NebulaGameManager.zlogic", manager_graph()),
        ("NebulaBackground.zlogic", background_graph()),
    ):
        write_json(LOGIC_DIR / filename, value)
    print(f"Demo gerada: {SCENE_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

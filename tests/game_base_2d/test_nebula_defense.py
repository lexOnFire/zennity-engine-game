from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from engine.build.runtime_scene_loader import load_objects
from engine.logic.blackboard import BlackboardStore, load_blackboard_asset
from engine.logic.graph_asset import load_logic_graph, validate_logic_graph
from engine.logic.runtime import LogicGraphRuntime


ROOT = Path(__file__).resolve().parents[2]
SCENE = ROOT / "Assets/Scenes/NebulaDefense.zscene"
LOGIC = ROOT / "Assets/Logic/NebulaDefense"
PREFABS = ROOT / "Assets/Prefabs/NebulaDefense"


def test_nebula_defense_is_a_complete_visual_logic_game() -> None:
    scene = json.loads(SCENE.read_text(encoding="utf-8"))
    objects = scene["objects"]

    assert scene["scene_name"] == "Nebula Defense"
    assert len(objects) == 9
    assert {item["name"] for item in objects} >= {
        "NebulaCamera", "NebulaBackground", "NebulaPilot",
        "NebulaSpawner", "NebulaGameManager",
    }
    assert all(not item.get("components", {}).get("scripts") for item in objects)
    assert scene["blackboard"]["variables"]["score"]["default"] == 0.0
    assert scene["blackboard"]["variables"]["lives"]["default"] == 3.0

    loaded = {item["name"]: item for item in load_objects(SCENE)}
    assert loaded["NebulaCamera"]["camera"]["active"] is True
    assert loaded["NebulaGameManager"]["audio"]["autoplay"] is True
    assert loaded["NebulaPilot"]["collider"]["is_trigger"] is False


def test_every_nebula_graph_is_valid_and_targets_a_scene_role() -> None:
    expected = {
        "NebulaBackground.zlogic", "NebulaEnemy.zlogic", "NebulaGameManager.zlogic",
        "NebulaPlayer.zlogic", "NebulaProjectile.zlogic", "NebulaSpawner.zlogic",
    }
    paths = set(LOGIC.glob("*.zlogic"))
    assert {path.name for path in paths} == expected

    for path in paths:
        graph = load_logic_graph(path)
        assert graph["target"]["value"]
        assert not validate_logic_graph(graph), path.name


def test_nebula_prefabs_are_safe_independent_runtime_objects() -> None:
    drone = json.loads((PREFABS / "NebulaDrone.zprefab").read_text(encoding="utf-8"))["object"]
    bolt = json.loads((PREFABS / "NebulaBolt.zprefab").read_text(encoding="utf-8"))["object"]

    assert drone["tag"] == "EnemyNebula"
    assert bolt["tag"] == "ProjectileNebula"
    assert drone["collider"]["is_trigger"] is True
    assert bolt["collider"]["is_trigger"] is True
    assert drone["rigidbody"]["use_gravity"] is False
    assert bolt["rigidbody"]["use_gravity"] is False

    player = load_logic_graph(LOGIC / "NebulaPlayer.zlogic")
    spawn = next(node for node in player["nodes"] if node["type"] == "create_prefab")
    assert spawn["properties"] | {
        "use_pool": True,
        "max_instances": 24,
        "lifetime": 2.2,
        "include_camera": False,
        "include_audio": False,
        "include_logic": False,
    } == spawn["properties"]


def test_enemy_collision_graph_awards_score_only_for_projectile_tag() -> None:
    project = load_blackboard_asset(ROOT / "Assets/Logic/ProjectBlackboard.zblackboard")
    store = BlackboardStore(project=project)
    graph = load_logic_graph(LOGIC / "NebulaEnemy.zlogic")

    class Game:
        name = "NebulaDrone"
        tag = "EnemyNebula"
        x = y = rotation = 0.0
        active = True
        def __init__(self): self.sounds = []
        def update_motion_debug(self, *_args): pass
        def destroy(self): self.active = False
        def play_sound(self, path): self.sounds.append(path)

    class Other:
        tag = "ProjectileNebula"

    game = Game()
    runtime = LogicGraphRuntime(graph, store, "NebulaDrone")
    runtime.start(game)
    runtime.trigger_event("event_trigger_enter", game, payload=Other())

    assert game.active is False
    assert store.get("project", "score", "NebulaDrone") == 1.0
    assert game.sounds == ["Assets/Audio/collect-points-190037.mp3"]


def test_nebula_defense_exports_with_logic_prefabs_audio_and_images(tmp_path: Path) -> None:
    exporter_path = ROOT / "engine/build/project_exporter.py"
    spec = importlib.util.spec_from_file_location("nebula_exporter", exporter_path)
    exporter = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(exporter)

    report = exporter.export_development_project_with_report(
        ROOT, SCENE, tmp_path, "Nebula Defense",
    )

    assert report.success, [issue.message for issue in report.errors]
    destination = Path(report.destination)
    assert (destination / "Data/main.zscene").is_file()
    assert (destination / "Assets/Logic/NebulaDefense/NebulaPlayer.zlogic").is_file()
    assert (destination / "Assets/Prefabs/NebulaDefense/NebulaBolt.zprefab").is_file()
    manifest = json.loads((destination / "package_manifest.json").read_text(encoding="utf-8"))
    assert manifest["asset_counts"]["logic"] >= 7
    assert manifest["asset_counts"]["prefab"] >= 2
    assert manifest["asset_counts"]["audio"] >= 5

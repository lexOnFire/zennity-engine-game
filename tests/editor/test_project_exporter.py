import importlib.util
import json
import subprocess
import sys
from pathlib import Path


RUNTIME_SOURCES = (
    "editor/isolated_viewport.py",
    "editor/runtime/native_ui.py",
    "editor/runtime/audio_playback_state.py",
    "editor/runtime/sprite_rendering.py",
    "editor/runtime/viewport_render_order.py",
    "editor/runtime/viewport_systems.py",
    "editor/runtime/benchmark_gameplay_compat.py",
    "editor/runtime/viewport_session.py",
    "editor/runtime/viewport_session_lifecycle.py",
    "editor/runtime/viewport_asset_hydration.py",
    "editor/runtime/viewport_logic_api.py",
    "editor/runtime/viewport_logic_api_behavior.py",
    "editor/runtime/viewport_logic_api_dialogue.py",
    "editor/runtime/viewport_logic_api_media.py",
    "editor/runtime/viewport_command_queue.py",
    "editor/runtime/viewport_editor_view_commands.py",
    "editor/runtime/viewport_edit_commands.py",
    "editor/runtime/viewport_control_commands.py",
    "editor/runtime/viewport_play_commands.py",
    "editor/runtime/viewport_navigation_events.py",
    "editor/runtime/viewport_transform_events.py",
    "editor/runtime/viewport_overlay_renderer.py",
    "editor/runtime/viewport_sprite_renderer.py",
    "editor/runtime/viewport_physics_stepper.py",
    "editor/runtime/viewport_animation_updater.py",
    "editor/runtime/viewport_session_orchestrator.py",
    "editor/runtime/viewport_logic_event_updater.py",
    "editor/runtime/viewport_contact_processor.py",
    "editor/runtime/viewport_runtime_initializer.py",
    "engine/physics/spatial_hash.py",
    "engine/graphics/tint.py",
    "engine/animation/clip_asset.py",
    "engine/animation/controller_asset.py",
    "engine/behavior/controller_asset.py",
    "engine/behavior/graph_runtime.py",
    "engine/logic/graph_asset.py",
    "engine/logic/contracts.py",
    "engine/logic/physics_event_dispatch.py",
    "engine/logic/animation_event_dispatch.py",
    "engine/logic/node_definitions",
    "engine/logic/graph_normalizer.py",
    "engine/logic/graph_validator.py",
    "engine/logic/blackboard.py",
    "engine/logic/event_bus.py",
    "engine/logic/runtime",
    "engine/prefabs/prefab_asset.py",
    "engine/runtime/runtime_world.py",
    "engine/build/runtime_scene_loader.py",
)


def _load_exporter():
    path = Path("engine/build/project_exporter.py")
    spec = importlib.util.spec_from_file_location("project_exporter_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _load_runtime_scene_loader():
    path = Path("engine/build/runtime_scene_loader.py")
    spec = importlib.util.spec_from_file_location("runtime_scene_loader_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _install_runtime_sources(project: Path) -> None:
    source_root = Path.cwd()
    for relative in RUNTIME_SOURCES:
        source_path = source_root / relative
        target = project / relative
        if source_path.is_dir():
            import shutil
            shutil.copytree(source_path, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source_path.read_bytes())


def test_development_export_contains_scene_assets_and_launchers(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "Assets" / "Scripts").mkdir(parents=True)
    (project / "Assets" / "Scripts" / "player.py").write_text("def on_update(game, dt): pass\n", encoding="utf-8")
    _install_runtime_sources(project)
    scene = project / "main.zscene"
    scene.write_text(json.dumps({"objects": []}), encoding="utf-8")

    exporter = _load_exporter()
    destination = exporter.export_development_project(project, scene, tmp_path / "output", "Meu Jogo")

    assert (destination / "Data" / "main.zscene").is_file()
    assert (destination / "Assets" / "Scripts" / "player.py").is_file()
    assert (destination / "main.py").is_file()
    assert (destination / "executar.bat").is_file()
    assert json.loads((destination / "package_manifest.json").read_text(encoding="utf-8"))["project_name"] == "Meu Jogo"


def test_exported_game_validates_outside_the_editor(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "Assets").mkdir(parents=True)
    _install_runtime_sources(project)
    scene = project / "main.zscene"
    scene.write_text(json.dumps({"objects": [{"name": "Player"}]}), encoding="utf-8")
    destination = _load_exporter().export_development_project(project, scene, tmp_path / "output", "Smoke")

    result = subprocess.run(
        [sys.executable, "main.py", "--validate-only"], cwd=destination,
        capture_output=True, text=True, timeout=15, check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "1 objeto(s)" in result.stdout


def test_export_report_contains_metrics_and_is_saved(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "Assets").mkdir(parents=True)
    _install_runtime_sources(project)
    scene = project / "main.zscene"
    scene.write_text(json.dumps({"objects": []}), encoding="utf-8")

    exporter = _load_exporter()
    report = exporter.export_development_project_with_report(project, scene, tmp_path / "output", "Jogo Teste")

    assert report.success is True
    assert report.file_count >= 7
    assert report.total_size_bytes > 0
    assert "Data/main.zscene" in report.files
    saved = json.loads((Path(report.destination) / "build_report.json").read_text(encoding="utf-8"))
    assert saved["success"] is True
    assert saved["project_name"] == "Jogo Teste"


def test_export_report_rejects_invalid_scene_without_partial_build(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "Assets").mkdir(parents=True)
    _install_runtime_sources(project)
    scene = project / "broken.zscene"
    scene.write_text("not-json", encoding="utf-8")

    exporter = _load_exporter()
    report = exporter.export_development_project_with_report(project, scene, tmp_path / "output", "Broken")

    assert report.success is False
    assert report.errors
    assert not Path(report.destination).exists()


def test_export_report_warns_about_missing_scene_asset(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "Assets").mkdir(parents=True)
    _install_runtime_sources(project)
    scene = project / "main.zscene"
    scene.write_text(
        json.dumps({"objects": [{"visual": {"texture": "Assets/Textures/missing.png"}}]}),
        encoding="utf-8",
    )

    exporter = _load_exporter()
    report = exporter.export_development_project_with_report(project, scene, tmp_path / "output", "Warnings")

    assert report.success is True
    assert any(issue.path == "Assets/Textures/missing.png" for issue in report.warnings)


def test_exported_runtime_contains_all_standalone_dependencies(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "Assets").mkdir(parents=True)
    _install_runtime_sources(project)
    scene = project / "main.zscene"
    scene.write_text(json.dumps({"objects": []}), encoding="utf-8")

    exporter = _load_exporter()
    report = exporter.export_development_project_with_report(project, scene, tmp_path / "output", "Standalone")

    assert report.success is True
    runtime = Path(report.destination) / "zennity_runtime"
    assert {path.name for path in runtime.glob("*.py")} == {
        "__init__.py", "viewport.py", "native_ui.py", "audio_playback_state.py", "sprite_rendering.py",
        "viewport_render_order.py",
        "viewport_systems.py", "benchmark_gameplay_compat.py",
        "viewport_session.py",
        "viewport_session_lifecycle.py",
        "viewport_asset_hydration.py",
        "viewport_logic_api.py",
        "viewport_logic_api_behavior.py",
        "viewport_logic_api_dialogue.py",
        "viewport_logic_api_media.py",
        "viewport_command_queue.py", "viewport_editor_view_commands.py",
        "viewport_edit_commands.py", "viewport_control_commands.py",
        "viewport_play_commands.py",
        "viewport_navigation_events.py", "viewport_transform_events.py",
        "viewport_overlay_renderer.py",
        "viewport_sprite_renderer.py", "viewport_physics_stepper.py",
        "viewport_animation_updater.py",
        "viewport_session_orchestrator.py",
        "viewport_logic_event_updater.py",
        "viewport_contact_processor.py", "spatial_hash.py",
        "viewport_runtime_initializer.py",
        "tint.py", "clip_asset.py", "controller_asset.py", "behavior_controller.py",
        "behavior_graph_runtime.py",
        "logic_graph_asset.py", "contracts.py", "physics_event_dispatch.py", "animation_event_dispatch.py",
        "graph_normalizer.py", "graph_validator.py",
        "logic_blackboard.py", "logic_event_bus.py",
        "prefab_asset.py", "runtime_world.py", "scene_loader.py",
    }
    # The node catalogue ships as a package so the exported game derives its
    # port schema from the same source the editor does.
    for relative in ("__init__.py", "catalogue.py", "registry.py"):
        assert (runtime / "node_definitions" / relative).is_file(), relative
    assert not (runtime / "node_definitions.py").exists(), (
        "the shadowed flat node_definitions module must not be exported"
    )

    launcher = (Path(report.destination) / "main.py").read_text(encoding="utf-8")
    assert "from zennity_runtime.scene_loader import load_objects" in launcher


def test_runtime_scene_loader_preserves_play_mode_components(tmp_path: Path) -> None:
    scene = tmp_path / "main.zscene"
    scene.write_text(json.dumps({"objects": [{
        "id": "player",
        "name": "Player",
        "tag": "Player",
        "transform": {"position": [10, 20, 0], "rotation": [0, 0, 30], "scale": [36, 48, 1]},
        "visual": {"texture": "Assets/player.png", "color": [255, 255, 255], "order": 2},
        "components": {
            "scripts": ["Assets/Scripts/player.py"],
            "audio": {"clip": "Assets/Audio/theme.ogg", "play_on_start": True},
            "items": [{"type": "Label", "properties": {"text": "VIDA: 3", "x": 16}}],
        },
        "editor_data": {"animator": {"active_clip": "andar", "clips": {}}},
    }]}), encoding="utf-8")

    player = _load_runtime_scene_loader().load_objects(scene)[0]

    assert (player["x"], player["y"], player["w"], player["h"], player["rotation"]) == (10, 20, 36, 48, 30)
    assert "scripts" not in player
    assert player["audio"]["play_on_start"] is True
    assert player["ui"]["type"] == "text"
    assert player["ui"]["text"] == "VIDA: 3"
    assert player["animator"]["active_clip"] == "andar"


def test_export_ignores_legacy_python_scripts(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "Assets" / "Scripts").mkdir(parents=True)
    (project / "Assets" / "Scripts" / "broken.py").write_text("def broken(:\n", encoding="utf-8")
    _install_runtime_sources(project)
    scene = project / "main.zscene"
    scene.write_text(json.dumps({"objects": []}), encoding="utf-8")

    report = _load_exporter().export_development_project_with_report(
        project, scene, tmp_path / "output", "Broken Script"
    )

    assert report.success is True
    assert not any(issue.category == "Script" for issue in report.errors)


def test_export_preserves_distinct_uppercase_and_lowercase_asset_roots(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "Assets" / "Scripts").mkdir(parents=True)
    (project / "assets" / "scripts").mkdir(parents=True, exist_ok=True)
    (project / "Assets" / "Scripts" / "player.py").write_text("def on_update(game, dt): pass\n", encoding="utf-8")
    (project / "assets" / "scripts" / "enemy.py").write_text("def on_update(game, dt): pass\n", encoding="utf-8")
    _install_runtime_sources(project)
    scene = project / "main.zscene"
    scene.write_text(json.dumps({"objects": [{
        "components": {"scripts": ["Assets/Scripts/player.py", "assets/scripts/enemy.py"]}
    }]}), encoding="utf-8")

    report = _load_exporter().export_development_project_with_report(
        project, scene, tmp_path / "output", "Case Sensitive"
    )

    assert report.success is True
    destination = Path(report.destination)
    assert (destination / "Assets/Scripts/player.py").is_file()
    assert (destination / "assets/scripts/enemy.py").is_file()


def test_export_bundles_visual_logic_prefabs_animation_audio_and_images(tmp_path: Path) -> None:
    project = tmp_path / "project"
    assets = project / "Assets"
    files = {
        "Logic/Player.zlogic": '{"format":"zennity.logic_graph","nodes":[],"edges":[]}',
        "Animations/Walk.zanim": "{}",
        "Animations/Player.zanimator": "{}",
        "Prefabs/Bullet.zprefab": "{}",
        "Audio/shot.ogg": "audio",
        "Textures/bullet.png": "image",
    }
    for relative, content in files.items():
        path = assets / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    _install_runtime_sources(project)
    scene = project / "main.zscene"
    scene.write_text(json.dumps({"objects": []}), encoding="utf-8")

    report = _load_exporter().export_development_project_with_report(
        project, scene, tmp_path / "output", "Asset Bundle"
    )

    assert report.success is True
    destination = Path(report.destination)
    for relative in files:
        assert (destination / "Assets" / relative).is_file()
    manifest = json.loads((destination / "package_manifest.json").read_text(encoding="utf-8"))
    assert manifest["asset_roots"] == ["Assets"]
    assert manifest["asset_counts"] == {
        "logic": 1, "animation": 2, "prefab": 1, "audio": 1, "image": 1,
    }

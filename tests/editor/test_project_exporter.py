import importlib.util
import json
from pathlib import Path


RUNTIME_SOURCES = (
    "editor/isolated_viewport.py",
    "editor/runtime/native_ui.py",
    "editor/runtime/audio_playback_state.py",
    "editor/runtime/sprite_rendering.py",
    "engine/graphics/tint.py",
    "engine/animation/clip_asset.py",
    "engine/animation/controller_asset.py",
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
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((source_root / relative).read_bytes())


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
        "tint.py", "clip_asset.py", "controller_asset.py", "scene_loader.py",
    }
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
    assert player["scripts"] == ["Assets/Scripts/player.py"]
    assert player["audio"]["play_on_start"] is True
    assert player["ui"]["type"] == "text"
    assert player["ui"]["text"] == "VIDA: 3"
    assert player["animator"]["active_clip"] == "andar"


def test_export_report_rejects_script_with_invalid_python(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "Assets" / "Scripts").mkdir(parents=True)
    (project / "Assets" / "Scripts" / "broken.py").write_text("def broken(:\n", encoding="utf-8")
    _install_runtime_sources(project)
    scene = project / "main.zscene"
    scene.write_text(json.dumps({"objects": []}), encoding="utf-8")

    report = _load_exporter().export_development_project_with_report(
        project, scene, tmp_path / "output", "Broken Script"
    )

    assert report.success is False
    assert any("Python inválido" in issue.message and "broken.py" in issue.path for issue in report.errors)


def test_export_preserves_distinct_uppercase_and_lowercase_asset_roots(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "Assets" / "Scripts").mkdir(parents=True)
    (project / "assets" / "scripts").mkdir(parents=True)
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

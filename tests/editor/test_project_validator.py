import importlib.util
import json
import sys
from pathlib import Path


RUNTIME_SOURCES = (
    "editor/isolated_viewport.py",
    "editor/runtime/native_ui.py",
    "editor/runtime/audio_playback_state.py",
    "editor/runtime/sprite_rendering.py",
    "editor/runtime/viewport_systems.py",
    "engine/graphics/tint.py",
    "engine/animation/clip_asset.py",
    "engine/animation/controller_asset.py",
    "engine/behavior/controller_asset.py",
    "engine/logic/graph_asset.py",
    "engine/logic/blackboard.py",
    "engine/logic/event_bus.py",
    "engine/logic/runtime.py",
    "engine/runtime/runtime_world.py",
    "engine/build/runtime_scene_loader.py",
)


def _load_validator():
    path = Path("engine/build/project_validator.py")
    spec = importlib.util.spec_from_file_location("project_validator_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _runtime_files(root: Path) -> None:
    for relative in RUNTIME_SOURCES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# runtime\n", encoding="utf-8")


def _write_scene(root: Path, objects: list[dict]) -> Path:
    scene = root / "Assets" / "Scenes" / "main.zscene"
    scene.parent.mkdir(parents=True, exist_ok=True)
    scene.write_text(json.dumps({"scene_name": "Main", "objects": objects}), encoding="utf-8")
    return scene


def test_valid_project_passes_with_player_camera_and_canvas(tmp_path: Path) -> None:
    _runtime_files(tmp_path)
    script = tmp_path / "Assets" / "Scripts" / "player.py"
    script.parent.mkdir(parents=True)
    script.write_text("def on_update(game, dt):\n    pass\n", encoding="utf-8")
    scene = _write_scene(tmp_path, [
        {
            "id": "camera", "name": "MainCamera", "tag": "MainCamera",
            "transform": {"position": [0, 0, 0], "scale": [32, 32, 1]},
            "components": {"items": [{"type": "Camera", "properties": {"active": True}}]},
        },
        {
            "id": "player", "name": "Player", "tag": "Player",
            "transform": {"position": [0, 0, 0], "scale": [32, 48, 1]},
            "components": {"scripts": ["Assets/Scripts/player.py"]},
        },
        {
            "id": "canvas", "name": "Canvas", "tag": "UI",
            "transform": {"position": [0, 0, 0], "scale": [1, 1, 1]},
            "components": {"items": [{"type": "Canvas", "properties": {}}]},
        },
    ])

    report = _load_validator().validate_project(tmp_path, scene)

    assert report.valid is True
    assert report.errors == []
    assert report.object_count == 3
    assert report.checked_files == len(RUNTIME_SOURCES) + 1


def test_validator_reports_duplicate_missing_assets_and_incomplete_runtime(tmp_path: Path) -> None:
    scene = _write_scene(tmp_path, [
        {
            "id": "duplicate", "name": "Object", "tag": "Untagged",
            "transform": {"position": [0, 0, 0], "scale": [0, 32, 1]},
            "visual": {"texture": "Assets/Textures/missing.png"},
            "components": {
                "scripts": ["Assets/Scripts/missing.py"],
                "collider": {"type": "box", "width": 0},
                "items": [{"type": "Label", "properties": {"text": "HUD"}}],
            },
        },
        {
            "id": "duplicate", "name": "Object", "tag": "Untagged",
            "transform": {"position": [0, 0, 0], "scale": [32, 32, 1]},
            "components": {},
        },
    ])

    report = _load_validator().validate_project(tmp_path, scene)
    messages = [issue.message for issue in report.issues]

    assert report.valid is False
    assert any("nome duplicado" in message for message in messages)
    assert any("ID duplicado" in message for message in messages)
    assert any(issue.category == "Sprite" for issue in report.errors)
    assert not any(issue.category == "Script" for issue in report.errors)
    assert any(issue.category == "Física" for issue in report.errors)
    assert any(issue.category == "Exportação" for issue in report.errors)
    assert any("câmera" in message for message in messages)
    assert any("Player" in message for message in messages)
    assert any("Canvas" in message for message in messages)


def test_legacy_script_is_ignored_by_visual_logic_validator(tmp_path: Path) -> None:
    _runtime_files(tmp_path)
    script = tmp_path / "Assets" / "Scripts" / "helper.py"
    script.parent.mkdir(parents=True)
    script.write_text("def helper():\n    return 1\n", encoding="utf-8")
    scene = _write_scene(tmp_path, [{
        "id": "player", "name": "Player", "tag": "Player",
        "transform": {"position": [0, 0, 0], "scale": [32, 32, 1]},
        "components": {
            "scripts": ["Assets/Scripts/helper.py"],
            "items": [{"type": "Camera", "properties": {"active": True}}],
        },
    }])

    report = _load_validator().validate_project(tmp_path, scene)

    assert report.valid is True


def test_validator_reports_broken_logic_graph_connections(tmp_path: Path) -> None:
    _runtime_files(tmp_path)
    scene = _write_scene(tmp_path, [{
        "name": "Player", "tag": "Player",
        "transform": {"position": [0, 0, 0], "scale": [32, 32, 1]},
        "components": {"camera": {"active": True}},
    }])
    logic = tmp_path / "Assets" / "Logic" / "broken.zlogic"
    logic.parent.mkdir(parents=True)
    logic.write_text(json.dumps({
        "format": "zennity.logic_graph", "nodes": [{"id": "start", "type": "event_start"}],
        "edges": [{"from_node": "start", "to_node": "missing"}],
    }), encoding="utf-8")

    report = _load_validator().validate_project(tmp_path, scene)

    assert report.valid is False
    assert any(issue.category == "Logic Graph" and "inexistente" in issue.message for issue in report.errors)
    assert not any(issue.category == "Script" for issue in report.errors)


def test_validation_ui_and_export_gate_are_integrated() -> None:
    editor = Path("editor/isolated_editor_main.py").read_text(encoding="utf-8")
    dialog = Path("editor/widgets/project_validation_dialog.py").read_text(encoding="utf-8")

    assert 'addAction("Validar projeto...")' in editor
    assert "validation = validate_project" in editor
    assert "if not validation.valid" in editor
    assert "ProjectValidationDialog" in editor
    assert 'setHeaderLabels(["Tipo", "Categoria", "Objeto", "Mensagem", "Arquivo"])' in dialog


def test_external_asset_is_rejected_because_build_would_not_be_portable(tmp_path: Path) -> None:
    project = tmp_path / "project"
    external = tmp_path / "external.png"
    external.write_bytes(b"image")
    _runtime_files(project)
    scene = _write_scene(project, [{
        "id": "player", "name": "Player", "tag": "Player",
        "transform": {"position": [0, 0, 0], "scale": [32, 32, 1]},
        "visual": {"texture": str(external)},
        "components": {"items": [{"type": "Camera", "properties": {"active": True}}]},
    }])

    report = _load_validator().validate_project(project, scene)

    assert report.valid is False
    assert any("fora da pasta do projeto" in issue.message for issue in report.errors)

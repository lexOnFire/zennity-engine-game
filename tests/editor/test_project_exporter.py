import importlib.util
import json
from pathlib import Path


def _load_exporter():
    path = Path("engine/build/project_exporter.py")
    spec = importlib.util.spec_from_file_location("project_exporter_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_development_export_contains_scene_assets_and_launchers(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "Assets" / "Scripts").mkdir(parents=True)
    (project / "Assets" / "Scripts" / "player.py").write_text("def on_update(game, dt): pass\n", encoding="utf-8")
    (project / "editor").mkdir()
    (project / "editor" / "isolated_viewport.py").write_text("def run_viewport(*args): pass\n", encoding="utf-8")
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
    (project / "editor").mkdir()
    (project / "editor" / "isolated_viewport.py").write_text("def run_viewport(*args): pass\n", encoding="utf-8")
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
    (project / "editor").mkdir()
    (project / "editor" / "isolated_viewport.py").write_text("", encoding="utf-8")
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
    (project / "editor").mkdir()
    (project / "editor" / "isolated_viewport.py").write_text("", encoding="utf-8")
    scene = project / "main.zscene"
    scene.write_text(
        json.dumps({"objects": [{"visual": {"texture": "Assets/Textures/missing.png"}}]}),
        encoding="utf-8",
    )

    exporter = _load_exporter()
    report = exporter.export_development_project_with_report(project, scene, tmp_path / "output", "Warnings")

    assert report.success is True
    assert any(issue.path == "Assets/Textures/missing.png" for issue in report.warnings)

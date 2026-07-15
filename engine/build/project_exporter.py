from __future__ import annotations

import json
import shutil
import sys
import time
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

try:
    from .build_report import BuildReport
except ImportError:  # Suporta os testes que carregam este arquivo isoladamente.
    _report_spec = spec_from_file_location("zennity_build_report", Path(__file__).with_name("build_report.py"))
    if _report_spec is None or _report_spec.loader is None:
        raise
    _report_module = module_from_spec(_report_spec)
    sys.modules[_report_spec.name] = _report_module
    _report_spec.loader.exec_module(_report_module)
    BuildReport = _report_module.BuildReport


def export_development_project(project_root: Path, scene_path: Path, output_dir: Path, project_name: str) -> Path:
    """Cria uma pasta executável de desenvolvimento baseada no runtime Pygame."""
    report = export_development_project_with_report(project_root, scene_path, output_dir, project_name)
    if not report.success:
        details = "; ".join(issue.message for issue in report.errors)
        raise ValueError(details or "Falha desconhecida durante a exportação")
    return Path(report.destination)


def export_development_project_with_report(
    project_root: Path,
    scene_path: Path,
    output_dir: Path,
    project_name: str,
) -> BuildReport:
    """Exporta o projeto e retorna diagnóstico completo sem quebrar a API antiga."""
    started = time.perf_counter()
    project_root = Path(project_root).resolve()
    scene_path = Path(scene_path).resolve()
    output_dir = Path(output_dir).resolve()
    safe_name = "".join(char for char in project_name.strip() if char.isalnum() or char in "-_ ").strip() or "ZennityGame"
    destination = output_dir / safe_name
    report = BuildReport(project_name=safe_name, destination=str(destination))

    scene_payload = _validate_export_inputs(project_root, scene_path, report)
    if report.errors:
        report.duration_seconds = time.perf_counter() - started
        return report

    try:
        _write_development_project(project_root, scene_path, destination, safe_name)
        _validate_asset_references(project_root, destination, scene_payload, report)
        _validate_exported_project(destination, report)
        _collect_exported_files(destination, report)
        report.success = not report.errors
    except (OSError, ValueError, TypeError) as exc:
        report.add_error(f"Falha ao gerar os arquivos: {exc}", destination)
        report.success = False

    report.duration_seconds = time.perf_counter() - started
    _save_report(destination, report)
    return report


def _validate_export_inputs(project_root: Path, scene_path: Path, report: BuildReport) -> dict:
    if not project_root.is_dir():
        report.add_error("A pasta do projeto não existe.", project_root)
    if not scene_path.is_file():
        report.add_error("A cena de entrada não existe.", scene_path)
        return {}
    runtime_sources = (
        "editor/isolated_viewport.py",
        "editor/runtime/native_ui.py",
        "editor/runtime/audio_playback_state.py",
        "editor/runtime/sprite_rendering.py",
        "engine/graphics/tint.py",
        "engine/animation/clip_asset.py",
        "engine/animation/controller_asset.py",
        "engine/behavior/controller_asset.py",
        "engine/logic/graph_asset.py",
        "engine/logic/runtime.py",
        "engine/build/runtime_scene_loader.py",
    )
    for relative in runtime_sources:
        source = project_root / relative
        if not source.is_file():
            report.add_error("Dependência do runtime de exportação não encontrada.", source)
    if not (project_root / "Assets").is_dir():
        report.add_warning("A pasta Assets não existe; o build será criado sem assets.", project_root / "Assets")
    try:
        payload = json.loads(scene_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        report.add_error(f"A cena não contém JSON válido: {exc}", scene_path)
        return {}
    if not isinstance(payload, dict) or not isinstance(payload.get("objects", []), list):
        report.add_error("A cena precisa conter uma lista 'objects'.", scene_path)
        return {}
    return payload


def _write_development_project(project_root: Path, scene_path: Path, destination: Path, safe_name: str) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    data_dir = destination / "Data"
    runtime_dir = destination / "zennity_runtime"
    data_dir.mkdir(exist_ok=True)
    runtime_dir.mkdir(exist_ok=True)

    shutil.copy2(scene_path, data_dir / "main.zscene")
    assets_source = project_root / "Assets"
    if assets_source.is_dir():
        shutil.copytree(assets_source, destination / "Assets", dirs_exist_ok=True)
    lowercase_assets = project_root / "assets"
    if lowercase_assets.is_dir() and (
        not assets_source.is_dir() or lowercase_assets.resolve() != assets_source.resolve()
    ):
        shutil.copytree(lowercase_assets, destination / "assets", dirs_exist_ok=True)
    runtime_sources = {
        project_root / "editor" / "isolated_viewport.py": runtime_dir / "viewport.py",
        project_root / "editor" / "runtime" / "native_ui.py": runtime_dir / "native_ui.py",
        project_root / "editor" / "runtime" / "audio_playback_state.py": runtime_dir / "audio_playback_state.py",
        project_root / "editor" / "runtime" / "sprite_rendering.py": runtime_dir / "sprite_rendering.py",
        project_root / "engine" / "graphics" / "tint.py": runtime_dir / "tint.py",
        project_root / "engine" / "animation" / "clip_asset.py": runtime_dir / "clip_asset.py",
        project_root / "engine" / "animation" / "controller_asset.py": runtime_dir / "controller_asset.py",
        project_root / "engine" / "behavior" / "controller_asset.py": runtime_dir / "behavior_controller.py",
        project_root / "engine" / "logic" / "graph_asset.py": runtime_dir / "logic_graph_asset.py",
        project_root / "engine" / "logic" / "runtime.py": runtime_dir / "logic_runtime.py",
        project_root / "engine" / "build" / "runtime_scene_loader.py": runtime_dir / "scene_loader.py",
    }
    for source, target in runtime_sources.items():
        shutil.copy2(source, target)
    (runtime_dir / "__init__.py").write_text("", encoding="utf-8")
    (destination / "main.py").write_text(_launcher_source(), encoding="utf-8")
    (destination / "executar.bat").write_text("@echo off\npython main.py\npause\n", encoding="utf-8")
    (destination / "executar.sh").write_text("#!/usr/bin/env sh\npython3 main.py\n", encoding="utf-8")
    (destination / "requirements.txt").write_text("pygame-ce>=2.5\n", encoding="utf-8")
    manifest = {"project_name": safe_name, "entry_scene": "Data/main.zscene", "runtime": "pygame", "development": True}
    (destination / "package_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _validate_asset_references(
    project_root: Path, destination: Path, payload: object, report: BuildReport
) -> None:
    references: set[str] = set()

    def visit(value: object) -> None:
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str):
            normalized = value.replace("\\", "/")
            if normalized.lower().startswith("assets/"):
                references.add(normalized)

    visit(payload)
    for reference in sorted(references, key=str.lower):
        if not (project_root / Path(reference)).is_file():
            report.add_warning("Asset referenciado pela cena não foi encontrado.", reference)
        elif not (destination / Path(reference)).is_file():
            report.add_error("Asset existente não foi incluído no build.", reference)


def _collect_exported_files(destination: Path, report: BuildReport) -> None:
    files = sorted(path for path in destination.rglob("*") if path.is_file() and path.name != "build_report.json")
    report.files = [path.relative_to(destination).as_posix() for path in files]
    report.file_count = len(files)
    report.total_size_bytes = sum(path.stat().st_size for path in files)


def _validate_exported_project(destination: Path, report: BuildReport) -> None:
    required = (
        "Data/main.zscene",
        "main.py",
        "package_manifest.json",
        "requirements.txt",
        "zennity_runtime/__init__.py",
        "zennity_runtime/viewport.py",
        "zennity_runtime/native_ui.py",
        "zennity_runtime/audio_playback_state.py",
        "zennity_runtime/sprite_rendering.py",
        "zennity_runtime/tint.py",
        "zennity_runtime/clip_asset.py",
        "zennity_runtime/controller_asset.py",
        "zennity_runtime/behavior_controller.py",
        "zennity_runtime/logic_graph_asset.py",
        "zennity_runtime/logic_runtime.py",
        "zennity_runtime/scene_loader.py",
    )
    for relative in required:
        path = destination / relative
        if not path.is_file():
            report.add_error("Arquivo obrigatório não foi incluído no build.", relative)
    # Somente o runtime da engine é executável. Arquivos Python antigos em
    # Assets são preservados como backup de projeto, mas não fazem parte do jogo.
    for relative in required:
        path = destination / relative
        if path.suffix.lower() != ".py" or not path.is_file():
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except (OSError, UnicodeError, SyntaxError) as exc:
            report.add_error(f"Python inválido no build: {exc}", path.relative_to(destination))


def _save_report(destination: Path, report: BuildReport) -> None:
    if not destination.is_dir():
        return
    try:
        (destination / "build_report.json").write_text(
            json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError:
        # O relatório visual ainda pode ser exibido mesmo se seu arquivo não puder ser salvo.
        pass


def _launcher_source() -> str:
    return '''from __future__ import annotations

import multiprocessing as mp
import os
from pathlib import Path

from zennity_runtime.scene_loader import load_objects
from zennity_runtime.viewport import run_viewport


def main():
    os.chdir(Path(__file__).resolve().parent)
    commands, events = mp.Queue(), mp.Queue()
    process = mp.Process(target=run_viewport, args=(commands, events, None, (1280, 720)), daemon=False)
    process.start()
    commands.put({"type": "scene_snapshot", "objects": load_objects("Data/main.zscene")})
    commands.put({"type": "set_view_mode", "mode": "game"})
    commands.put({"type": "play"})
    process.join()


if __name__ == "__main__":
    mp.freeze_support()
    main()
'''

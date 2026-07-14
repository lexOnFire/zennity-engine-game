"""Validação de pré-publicação para projetos Zennity."""
from __future__ import annotations

import ast
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


SCRIPT_HOOKS = {
    "on_update", "isolated_update", "update", "on_collision",
    "on_collision_exit", "on_trigger", "on_trigger_exit",
}
UI_TYPES = {"canvas", "label", "uilabel", "image", "uiimage", "button", "uibutton"}
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


@dataclass(frozen=True)
class ValidationIssue:
    severity: str
    category: str
    message: str
    path: str = ""
    object_name: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class ProjectValidationReport:
    project_root: str
    scene_path: str
    scene_name: str = ""
    object_count: int = 0
    checked_files: int = 0
    duration_seconds: float = 0.0
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def valid(self) -> bool:
        return not self.errors

    def add(self, severity: str, category: str, message: str, path: str | Path = "", object_name: str = "") -> None:
        self.issues.append(ValidationIssue(severity, category, message, str(path), object_name))

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_root": self.project_root,
            "scene_path": self.scene_path,
            "scene_name": self.scene_name,
            "valid": self.valid,
            "object_count": self.object_count,
            "checked_files": self.checked_files,
            "duration_seconds": round(self.duration_seconds, 4),
            "issues": [issue.to_dict() for issue in self.issues],
        }


def validate_project(project_root: str | Path, scene_path: str | Path) -> ProjectValidationReport:
    started = time.perf_counter()
    root = Path(project_root).resolve()
    scene = Path(scene_path).resolve()
    report = ProjectValidationReport(str(root), str(scene))
    try:
        payload = _load_scene(scene, report)
        if payload is not None:
            _validate_scene(root, payload, report)
        _validate_runtime_sources(root, report)
    except (OSError, TypeError, ValueError, OverflowError) as exc:
        report.add("error", "Validação", f"Não foi possível analisar o projeto: {exc}", scene)
    finally:
        report.duration_seconds = time.perf_counter() - started
    return report


def _load_scene(scene: Path, report: ProjectValidationReport) -> dict[str, Any] | None:
    if not scene.is_file():
        report.add("error", "Cena", "A cena principal não existe.", scene)
        return None
    report.checked_files += 1
    try:
        payload = json.loads(scene.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        report.add("error", "Cena", f"JSON inválido: {exc}", scene)
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("objects"), list):
        report.add("error", "Cena", "O documento precisa conter uma lista 'objects'.", scene)
        return None
    report.scene_name = str(payload.get("scene_name", scene.stem))
    return payload


def _validate_scene(root: Path, payload: dict[str, Any], report: ProjectValidationReport) -> None:
    objects = [item for item in payload["objects"] if isinstance(item, dict)]
    report.object_count = len(objects)
    if not objects:
        report.add("warning", "Cena", "A cena não possui objetos.")
        return

    _duplicates(objects, "name", "nome", report)
    _duplicates(objects, "id", "ID", report, ignore_missing=True)
    has_camera = False
    has_player = False
    has_canvas = False
    has_ui = False
    checked_paths: set[str] = set()

    for item in objects:
        name = str(item.get("name", "")).strip()
        if not name:
            report.add("error", "Objeto", "Objeto sem nome.")
            name = "<sem nome>"
        tag = str(item.get("tag", "")).casefold()
        has_player = has_player or tag == "player" or name.casefold() == "player"
        transform = item.get("transform")
        if not isinstance(transform, dict):
            report.add("error", "Transform", "Componente Transform ausente.", object_name=name)
        else:
            scale = transform.get("scale", [])
            if not isinstance(scale, (list, tuple)) or len(scale) < 2:
                report.add("error", "Transform", "Escala inválida.", object_name=name)
            elif _float(scale[0]) == 0 or _float(scale[1]) == 0:
                report.add("warning", "Transform", "Objeto possui escala zero e ficará invisível.", object_name=name)

        visual = item.get("visual") if isinstance(item.get("visual"), dict) else {}
        for key in ("texture", "sprite_path"):
            _check_asset(root, visual.get(key), "Sprite", name, report, checked_paths)

        components = item.get("components") if isinstance(item.get("components"), dict) else {}
        camera = components.get("camera")
        if isinstance(camera, dict) and bool(camera.get("active", True)):
            has_camera = True
        for component in components.get("items", []):
            if not isinstance(component, dict):
                continue
            kind = str(component.get("type", "")).casefold()
            properties = component.get("properties") if isinstance(component.get("properties"), dict) else {}
            if kind == "camera" and bool(properties.get("active", component.get("enabled", True))):
                has_camera = True
            if kind in UI_TYPES:
                has_ui = has_ui or kind != "canvas"
                has_canvas = has_canvas or kind == "canvas"
                _check_asset(root, properties.get("sprite_path") or properties.get("path"), "UI", name, report, checked_paths)

        for script in components.get("scripts", item.get("scripts", [])):
            _validate_script(root, script, name, report, checked_paths)
        audio = components.get("audio", item.get("audio"))
        if isinstance(audio, dict):
            path = audio.get("path") or audio.get("clip")
            _check_asset(root, path, "Áudio", name, report, checked_paths)
            if bool(audio.get("autoplay")) and not path:
                report.add("warning", "Áudio", "'Ao iniciar' está ativo, mas nenhum áudio foi escolhido.", object_name=name)
            volume = _float(audio.get("volume", 1.0), 1.0)
            if not 0.0 <= volume <= 1.0:
                report.add("warning", "Áudio", "Volume fora do intervalo 0–1.", object_name=name)
        collider = components.get("collider", item.get("collider"))
        if isinstance(collider, dict):
            for key in ("width", "height", "radius"):
                if key in collider and _float(collider[key]) <= 0:
                    report.add("error", "Física", f"Collider possui {key} inválido.", object_name=name)

        editor_data = item.get("editor_data") if isinstance(item.get("editor_data"), dict) else {}
        animator = editor_data.get("animator", item.get("animator"))
        if isinstance(animator, dict):
            _validate_animator(root, animator, name, report, checked_paths)

    if not has_camera:
        report.add("warning", "Runtime", "Nenhuma câmera principal ativa foi encontrada.")
    if not has_player:
        report.add("warning", "Gameplay", "Nenhum objeto chamado Player ou com Tag Player foi encontrado.")
    if has_ui and not has_canvas:
        report.add("warning", "UI", "Existem elementos de HUD, mas nenhum Canvas foi encontrado.")


def _duplicates(objects: list[dict[str, Any]], key: str, label: str, report: ProjectValidationReport, ignore_missing: bool = False) -> None:
    values = [str(item.get(key, "")).strip() for item in objects]
    seen: set[str] = set()
    for value in values:
        if not value and ignore_missing:
            continue
        if value in seen:
            report.add("error", "Cena", f"{label} duplicado: {value or '<vazio>'}")
        seen.add(value)


def _validate_script(root: Path, value: Any, object_name: str, report: ProjectValidationReport, checked: set[str]) -> None:
    path = _asset_path(root, value)
    if path is None:
        return
    key = str(path)
    if key in checked:
        return
    checked.add(key)
    report.checked_files += 1
    if not path.is_file():
        report.add("error", "Script", "Script não encontrado.", value, object_name)
        return
    if not _inside_project(root, path):
        report.add("error", "Script", "Script está fora da pasta do projeto e não será exportado.", value, object_name)
        return
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as exc:
        report.add("error", "Script", f"Python inválido: {exc}", value, object_name)
        return
    hooks = {node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    if not hooks.intersection(SCRIPT_HOOKS):
        report.add("error", "Script", "Nenhum hook compatível com o Play Mode foi encontrado.", value, object_name)


def _validate_animator(root: Path, animator: dict[str, Any], name: str, report: ProjectValidationReport, checked: set[str]) -> None:
    controller_value = animator.get("controller_path")
    controller_path = _asset_path(root, controller_value)
    controller_states: set[str] = set()
    if controller_path is not None:
        _check_asset(root, controller_value, "Animator Controller", name, report, checked)
        if controller_path.is_file():
            try:
                controller = json.loads(controller_path.read_text(encoding="utf-8"))
                states = controller.get("states", {}) if isinstance(controller, dict) else {}
                if not isinstance(states, dict) or not states:
                    report.add("error", "Animator Controller", "Controller não possui estados.", controller_value, name)
                else:
                    controller_states = set(states)
                    initial = str(controller.get("initial_state", ""))
                    if initial not in controller_states:
                        report.add("error", "Animator Controller", "Estado inicial não existe.", controller_value, name)
                    for state in states.values():
                        if isinstance(state, dict):
                            _check_asset(root, state.get("animation"), "Animação", name, report, checked)
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                report.add("error", "Animator Controller", f"Controller inválido: {exc}", controller_value, name)
    clips = animator.get("clips")
    if not isinstance(clips, dict) or not clips:
        if controller_path is None:
            report.add("warning", "Animação", "Animator não possui clips.", object_name=name)
        return
    active = str(animator.get("active_clip", ""))
    if active not in clips and active not in controller_states:
        report.add("error", "Animação", f"Clip ativo não existe: {active or '<vazio>'}.", object_name=name)
    for clip in clips.values():
        if not isinstance(clip, dict):
            continue
        _check_asset(root, clip.get("asset_path"), "Animação", name, report, checked)
        _check_asset(root, clip.get("texture"), "Sprite Sheet", name, report, checked)


def _check_asset(root: Path, value: Any, category: str, object_name: str, report: ProjectValidationReport, checked: set[str]) -> None:
    path = _asset_path(root, value)
    if path is None:
        return
    key = str(path)
    if key in checked:
        return
    checked.add(key)
    report.checked_files += 1
    if not path.is_file():
        report.add("error", category, "Arquivo referenciado não foi encontrado.", value, object_name)
    elif not _inside_project(root, path):
        report.add("error", category, "Arquivo está fora da pasta do projeto e não será exportado.", value, object_name)


def _asset_path(root: Path, value: Any) -> Path | None:
    text = str(value or "").strip().replace("\\", "/")
    if not text:
        return None
    path = Path(text)
    return path if path.is_absolute() else root / path


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _inside_project(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _validate_runtime_sources(root: Path, report: ProjectValidationReport) -> None:
    for relative in RUNTIME_SOURCES:
        path = root / relative
        report.checked_files += 1
        if not path.is_file():
            report.add("error", "Exportação", "Dependência do runtime não encontrada.", relative)

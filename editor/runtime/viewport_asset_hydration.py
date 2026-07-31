"""Asset hydration boundaries used by the isolated viewport runtime."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from engine.animation.clip_asset import animation_asset_to_clip, load_animation_asset
    from engine.animation.controller_asset import load_animator_controller
    from engine.behavior.controller_asset import load_behavior_controller
    from engine.logic.graph_asset import load_logic_graph
except ModuleNotFoundError:  # Runtime autocontido criado pelo exportador.
    from .clip_asset import animation_asset_to_clip, load_animation_asset
    from .controller_asset import load_animator_controller
    from .behavior_controller import load_behavior_controller
    from .logic_graph_asset import load_logic_graph


def hydrate_animation_asset_clips(
    objects: dict[str, dict[str, Any]], project_root: Path
) -> list[tuple[str, str, str]]:
    """Atualiza os caches de clips a partir dos arquivos ``.zanim`` antes do Play."""
    results: list[tuple[str, str, str]] = []
    for object_name, obj in objects.items():
        animator = obj.get("animator")
        clips = animator.get("clips") if isinstance(animator, dict) else None
        if not isinstance(clips, dict):
            continue
        for clip_name, clip in list(clips.items()):
            asset_path = str(clip.get("asset_path", "")) if isinstance(clip, dict) else ""
            if not asset_path:
                continue
            path = Path(asset_path)
            if not path.is_absolute():
                path = project_root / path
            try:
                asset = load_animation_asset(path)
                clips[clip_name] = animation_asset_to_clip(asset, asset_path)
                results.append(("INFO", object_name, f"animação atualizada: {path.name}"))
            except (OSError, ValueError) as exc:
                results.append(("ERROR", object_name, f"falha ao carregar animação {asset_path}: {exc}"))
    return results


def hydrate_animator_controllers(
    objects: dict[str, dict[str, Any]], project_root: Path
) -> list[tuple[str, str, str]]:
    """Carrega controllers e converte seus estados para os clips do runtime atual."""
    results: list[tuple[str, str, str]] = []
    for object_name, obj in objects.items():
        animator = obj.get("animator")
        if not isinstance(animator, dict):
            continue
        asset_path = str(animator.get("controller_path", ""))
        if not asset_path:
            continue
        path = Path(asset_path)
        if not path.is_absolute():
            path = project_root / path
        try:
            controller = load_animator_controller(path)
            animator["controller"] = controller
            clips = animator.setdefault("clips", {})
            if not isinstance(clips, dict):
                clips = {}
                animator["clips"] = clips
            loaded = 0
            for state_name, state in controller["states"].items():
                animation_path = str(state.get("animation", ""))
                if not animation_path:
                    continue
                clip_path = Path(animation_path)
                if not clip_path.is_absolute():
                    clip_path = project_root / clip_path
                asset = load_animation_asset(clip_path)
                clips[state_name] = animation_asset_to_clip(asset, animation_path)
                clips[state_name]["controller_speed"] = float(state.get("speed", 1.0))
                loaded += 1
            animator["active_clip"] = str(controller["initial_state"])
            results.append(("INFO", object_name, f"controller carregado: {path.name} ({loaded} estado(s))"))
        except (OSError, ValueError) as exc:
            results.append(("ERROR", object_name, f"falha ao carregar controller {asset_path}: {exc}"))
    return results


def hydrate_behavior_controllers(
    objects: dict[str, dict[str, Any]], project_root: Path
) -> list[tuple[str, str, str]]:
    """Carrega os assets ``.zbehavior`` usados pelos objetos da cena."""
    results: list[tuple[str, str, str]] = []
    for object_name, obj in objects.items():
        behavior = obj.get("behavior")
        if not isinstance(behavior, dict):
            continue
        asset_path = str(behavior.get("controller_path", ""))
        if not asset_path:
            continue
        path = Path(asset_path)
        if not path.is_absolute():
            path = project_root / path
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if (
                isinstance(raw, dict)
                and raw.get("format") == "zennity.generic_graph"
                and str(raw.get("category", "")).casefold() == "behavior tree"
            ):
                behavior["graph"] = raw
                behavior.pop("controller", None)
                count = len(raw.get("nodes", []))
                results.append(("INFO", object_name, f"Behavior Tree carregada: {path.name} ({count} nó(s))"))
                continue
            controller = load_behavior_controller(path)
            behavior["controller"] = controller
            behavior.pop("graph", None)
            behavior.setdefault("parameters", {})
            results.append(("INFO", object_name, f"behavior carregado: {path.name} ({len(controller['states'])} estado(s))"))
        except (OSError, ValueError) as exc:
            results.append(("ERROR", object_name, f"falha ao carregar behavior {asset_path}: {exc}"))
    return results


def hydrate_logic_graphs(
    objects: dict[str, dict[str, Any]], project_root: Path
) -> list[tuple[str, str, str]]:
    """Descobre automaticamente ``.zlogic`` e associa pelo nome ou Tag alvo."""
    results: list[tuple[str, str, str]] = []
    for obj in objects.values():
        obj.pop("logic_graphs", None)
    loaded_paths: set[Path] = set()
    for object_name, obj in objects.items():
        configured = obj.get("logic_assets", [])
        if not isinstance(configured, list):
            continue
        for asset_value in configured:
            path = Path(str(asset_value))
            path = path if path.is_absolute() else project_root / path
            try:
                resolved = path.resolve()
                graph = load_logic_graph(resolved)
                obj.setdefault("logic_graphs", []).append({
                    "path": resolved.relative_to(project_root.resolve()).as_posix(),
                    "graph": graph,
                })
                loaded_paths.add(resolved)
                results.append((
                    "INFO", object_name,
                    f"Logic Graph explícito carregado: {path.name}",
                ))
            except (OSError, ValueError) as exc:
                results.append((
                    "ERROR", object_name,
                    f"falha ao carregar Logic Graph explícito {asset_value}: {exc}",
                ))
    directory = project_root / "Assets" / "Logic"
    if not directory.is_dir():
        return results
    for path in sorted(directory.rglob("*.zlogic"), key=lambda item: str(item).lower()):
        if path.resolve() in loaded_paths:
            continue
        try:
            graph = load_logic_graph(path)
            if not bool(graph.get("enabled", True)):
                continue
            if any(node.get("type") == "subgraph_start" for node in graph.get("nodes", [])):
                continue
            target = graph.get("target", {})
            target_type = str(target.get("type", "name"))
            wanted = str(target.get("value", "Player")).casefold()
            matched = []
            for name, obj in objects.items():
                candidate = name if target_type == "name" else str(obj.get("tag", ""))
                if candidate.casefold() == wanted:
                    obj.setdefault("logic_graphs", []).append({"path": path.relative_to(project_root).as_posix(), "graph": graph})
                    matched.append(name)
            if matched:
                results.append(("INFO", ", ".join(matched), f"Logic Graph carregado: {path.name}"))
            else:
                results.append(("WARNING", wanted or "<sem alvo>", f"Logic Graph sem objeto alvo: {path.name}"))
        except (OSError, ValueError) as exc:
            results.append(("ERROR", path.stem, f"falha ao carregar Logic Graph: {exc}"))
    return results


def load_project_subgraph(asset_path: str, project_root: Path) -> dict[str, Any]:
    """Carrega somente subgrafos que pertencem ao projeto atual."""
    path = Path(str(asset_path))
    if not path.is_absolute():
        path = project_root / path
    resolved = path.resolve()
    root = project_root.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("O subgrafo precisa estar dentro do projeto.")
    graph = load_logic_graph(resolved)
    if not any(node.get("type") == "subgraph_start" for node in graph.get("nodes", [])):
        raise ValueError(f"'{resolved.name}' não possui Início do subgrafo.")
    return graph


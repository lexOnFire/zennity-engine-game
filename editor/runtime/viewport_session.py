"""Janela Pygame independente usada pelo experimento de viewport isolada."""
from __future__ import annotations

import math
import os
import sys
import time
import hashlib
import importlib.util
import uuid
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    from editor.runtime.audio_playback_state import set_channels_paused
    from editor.runtime.native_ui import NativeUIRenderer, normalize_ui
    from editor.runtime.sprite_rendering import prepare_scrolling_sprite_surface, prepare_sprite_surface
    from editor.runtime.viewport_systems import (
        AnimationPlaybackSystem,
        AudioPlaybackSystem,
        FixedStepScheduler,
        HudRuntimeSystem,
    )
    from editor.runtime.viewport_command_queue import ViewportCommandQueue
    from editor.runtime.viewport_control_commands import (
        ViewportAudioCommandHandler,
        ViewportControlCommandHandler,
        ViewportControlSettings,
    )
    from editor.runtime.viewport_edit_commands import ViewportEditCommandHandler
    from editor.runtime.viewport_play_commands import ViewportPlayCommandHandler, ViewportProcessState
    from editor.runtime.viewport_navigation_events import ViewportNavigationEventHandler, ViewportNavigationState
    from editor.runtime.viewport_transform_events import ViewportTransformEventHandler, ViewportTransformState
    from editor.runtime.viewport_overlay_renderer import ViewportOverlayRenderer
    from editor.runtime.viewport_sprite_renderer import ViewportSpriteRenderer
    from editor.runtime.viewport_physics_stepper import ViewportPhysicsStepper
    from editor.runtime.viewport_animation_updater import ViewportAnimationUpdater
    from editor.runtime.viewport_session_orchestrator import ViewportSessionOrchestrator
    from editor.runtime.viewport_script_updater import ViewportScriptUpdater
    from editor.runtime.viewport_contact_processor import ViewportContactProcessor
    from editor.runtime.viewport_runtime_initializer import ViewportRuntimeInitializer
    from engine.animation.clip_asset import animation_asset_to_clip, load_animation_asset
    from engine.animation.controller_asset import AnimatorControllerRuntime, load_animator_controller
    from engine.behavior.controller_asset import BehaviorControllerRunner, load_behavior_controller
    from engine.logic.graph_asset import load_logic_graph
    from engine.logic.runtime import LogicGraphRuntime
    from engine.runtime.runtime_world import RuntimeWorld
except ModuleNotFoundError:  # Runtime autocontido criado pelo exportador.
    from .audio_playback_state import set_channels_paused
    from .native_ui import NativeUIRenderer, normalize_ui
    from .sprite_rendering import prepare_scrolling_sprite_surface, prepare_sprite_surface
    from .viewport_systems import AnimationPlaybackSystem, AudioPlaybackSystem, FixedStepScheduler, HudRuntimeSystem
    from .viewport_command_queue import ViewportCommandQueue
    from .viewport_control_commands import ViewportAudioCommandHandler, ViewportControlCommandHandler, ViewportControlSettings
    from .viewport_edit_commands import ViewportEditCommandHandler
    from .viewport_play_commands import ViewportPlayCommandHandler, ViewportProcessState
    from .viewport_navigation_events import ViewportNavigationEventHandler, ViewportNavigationState
    from .viewport_transform_events import ViewportTransformEventHandler, ViewportTransformState
    from .viewport_overlay_renderer import ViewportOverlayRenderer
    from .viewport_sprite_renderer import ViewportSpriteRenderer
    from .viewport_physics_stepper import ViewportPhysicsStepper
    from .viewport_animation_updater import ViewportAnimationUpdater
    from .viewport_session_orchestrator import ViewportSessionOrchestrator
    from .viewport_script_updater import ViewportScriptUpdater
    from .viewport_contact_processor import ViewportContactProcessor
    from .viewport_runtime_initializer import ViewportRuntimeInitializer
    from .clip_asset import animation_asset_to_clip, load_animation_asset
    from .controller_asset import AnimatorControllerRuntime, load_animator_controller
    from .behavior_controller import BehaviorControllerRunner, load_behavior_controller
    from .logic_graph_asset import load_logic_graph
    from .logic_runtime import LogicGraphRuntime
    from .runtime_world import RuntimeWorld


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
            controller = load_behavior_controller(path)
            behavior["controller"] = controller
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
    directory = project_root / "Assets" / "Logic"
    if not directory.is_dir():
        return results
    for path in sorted(directory.rglob("*.zlogic"), key=lambda item: str(item).lower()):
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


class PlayAnimatorAPI:
    """Comandos simples expostos como ``game.animator`` nos scripts."""

    def __init__(self, obj: dict[str, Any]) -> None:
        self._obj = obj

    def _send(self, command: str, value: Any) -> None:
        self._obj.setdefault("script_instructions", []).append({"command": command, "value": value})

    def play(self, state: str) -> None:
        self._send("animator_play", str(state))

    def set_bool(self, parameter: str, value: bool) -> None:
        self._send("animator_set_bool", {"name": str(parameter), "value": bool(value)})

    def set_float(self, parameter: str, value: float) -> None:
        self._send("animator_set_float", {"name": str(parameter), "value": float(value)})

    def trigger(self, parameter: str) -> None:
        self._send("animator_trigger", str(parameter))

    @property
    def state(self) -> str:
        return str(self._obj.get("_animator_state", self._obj.get("_current_animation_name", "Nenhum")))


class PlayBehaviorAPI:
    """Controle simples do Behavior Controller disponível como ``game.behavior``."""

    def __init__(self, obj: dict[str, Any]) -> None:
        self._obj = obj
        self._runner: BehaviorControllerRunner | None = None
        self._game: PlayScriptAPI | None = None

    def bind(self, runner: BehaviorControllerRunner, game: PlayScriptAPI) -> None:
        self._runner = runner
        self._game = game

    def play(self, state: str) -> bool:
        return bool(self._runner and self._game and self._runner.play(str(state), self._game))

    def set_bool(self, parameter: str, value: bool) -> None:
        if self._runner:
            self._runner.set_bool(str(parameter), bool(value))

    def set_float(self, parameter: str, value: float) -> None:
        if self._runner:
            self._runner.set_float(str(parameter), float(value))

    def trigger(self, parameter: str) -> None:
        if self._runner:
            self._runner.trigger(str(parameter))

    @property
    def state(self) -> str:
        if self._runner:
            return self._runner.current_state
        return str(self._obj.get("_behavior_state", "Nenhum"))

    @property
    def parameters(self) -> dict[str, Any]:
        return dict(self._runner.parameters) if self._runner else {}


class PlayScriptAPI:
    """API pequena e estável entregue aos scripts no Play Mode."""

    _KEY_ALIASES = {
        "a": "left", "d": "right", "w": "up", "s": "down",
        "space": "jump", "r": "restart",
    }

    def __init__(self, name: str, obj: dict[str, Any], events: Any, world: dict[str, dict[str, Any]] | None = None, runtime_world: RuntimeWorld | None = None) -> None:
        self.name = name
        self.obj = obj
        self._events = events
        self._world = world if world is not None else {name: obj}
        self.runtime_world = runtime_world or RuntimeWorld(self._world)
        self._input: dict[str, bool] = {}
        self._previous_input: dict[str, bool] = {}
        self.animator = PlayAnimatorAPI(obj)
        self.behavior = PlayBehaviorAPI(obj)

    @property
    def x(self) -> float:
        return float(self.obj.get("x", 0.0))

    @x.setter
    def x(self, value: float) -> None:
        self.obj["x"] = float(value)

    @property
    def y(self) -> float:
        return float(self.obj.get("y", 0.0))

    @y.setter
    def y(self, value: float) -> None:
        self.obj["y"] = float(value)

    @property
    def rotation(self) -> float:
        return float(self.obj.get("rotation", 0.0))

    @rotation.setter
    def rotation(self, value: float) -> None:
        self.obj["rotation"] = float(value)

    @property
    def width(self) -> float:
        return float(self.obj.get("w", 1.0))

    @width.setter
    def width(self, value: float) -> None:
        self.obj["w"] = max(1.0, float(value))

    @property
    def height(self) -> float:
        return float(self.obj.get("h", 1.0))

    @height.setter
    def height(self, value: float) -> None:
        self.obj["h"] = max(1.0, float(value))

    @property
    def active(self) -> bool:
        return bool(self.obj.get("active", True))

    @active.setter
    def active(self, value: bool) -> None:
        self.obj["active"] = bool(value)

    @property
    def tag(self) -> str:
        return str(self.obj.get("tag", self.obj.get("name", "Untagged")))

    @property
    def state(self) -> dict[str, Any]:
        return self.obj.setdefault("_script_state", {})

    @property
    def grounded(self) -> bool:
        return bool(self.obj.get("_grounded", False))

    def begin_frame(self, input_state: dict[str, bool]) -> None:
        self._input = dict(input_state)

    def end_frame(self) -> None:
        self._previous_input = dict(self._input)

    def key(self, name: str) -> bool:
        key = self._KEY_ALIASES.get(name.lower(), name.lower())
        return bool(self._input.get(key, False))

    def key_pressed(self, name: str) -> bool:
        key = self._KEY_ALIASES.get(name.lower(), name.lower())
        return bool(self._input.get(key, False) and not self._previous_input.get(key, False))

    def axis(self, negative: str, positive: str) -> int:
        return int(self.key(positive)) - int(self.key(negative))

    def move(self, dx: float, dy: float = 0.0) -> None:
        self.x += float(dx)
        self.y += float(dy)

    def override_physics_axis(self, axis: str) -> None:
        """Evita que a gravidade desfaça um movimento visual controlado neste frame."""
        self.obj.setdefault("_logic_motion_axes", set()).add(str(axis).lower())

    def jump(self, force: float = 420.0) -> None:
        self.obj["_jump_requested"] = True
        self.obj["_jump_force"] = float(force)

    def find(self, tag: str) -> "PlayScriptAPI | None":
        wanted = str(tag).lower()
        for name, obj in self._world.items():
            if obj is self.obj:
                continue
            if str(obj.get("tag", obj.get("name", ""))).lower() == wanted:
                return PlayScriptAPI(name, obj, self._events, self._world, self.runtime_world)
        return None

    def create_object(
        self,
        name: str = "NovoObjeto",
        x: float = 0.0,
        y: float = 0.0,
        width: float = 64.0,
        height: float = 64.0,
        color: str = "#58a6ff",
        texture: str = "",
        tag: str = "Untagged",
    ) -> "PlayScriptAPI":
        """Cria um objeto temporário na cena atual e devolve sua referência."""
        obj = self.runtime_world.create_object(
            name=name, x=x, y=y, width=width, height=height,
            color=color, texture=texture, tag=tag,
        )
        self.log(f"objeto criado: {obj['name']}")
        return PlayScriptAPI(str(obj["name"]), obj, self._events, self._world, self.runtime_world)

    def create_object_from_pool(self, pool_key: str, **values: Any) -> "PlayScriptAPI":
        obj = self.runtime_world.create_object(pool_key=f"logic:{pool_key}", **values)
        self.log(f"objeto criado/reutilizado: {obj['name']}")
        return PlayScriptAPI(str(obj["name"]), obj, self._events, self._world, self.runtime_world)

    def create_prefab(
        self, path: str, x: float | None = None, y: float | None = None, **options: Any
    ) -> "PlayScriptAPI":
        obj = self.runtime_world.instantiate_prefab(path, x=x, y=y, **options)
        self.log(f"prefab criado: {obj['name']}")
        return PlayScriptAPI(str(obj["name"]), obj, self._events, self._world, self.runtime_world)

    def create_prefab_from_pool(
        self, path: str, x: float | None, y: float | None, pool_key: str, **options: Any
    ) -> "PlayScriptAPI":
        obj = self.runtime_world.instantiate_prefab(
            path, x=x, y=y, pool_key=f"logic:{pool_key}", **options
        )
        self.log(f"prefab criado/reutilizado: {obj['name']}")
        return PlayScriptAPI(str(obj["name"]), obj, self._events, self._world, self.runtime_world)

    def prefab_parameter(self, name: str, default: Any = None) -> Any:
        """Lê uma propriedade exposta recebida na criação desta instância."""
        values = self.obj.get("prefab_parameters")
        return deepcopy(values.get(str(name), default)) if isinstance(values, dict) else deepcopy(default)

    def clone_object(self, other: "PlayScriptAPI", name: str = "") -> "PlayScriptAPI":
        source = other.obj if isinstance(other, PlayScriptAPI) else self.obj
        obj = self.runtime_world.clone_object(source, name)
        return PlayScriptAPI(str(obj["name"]), obj, self._events, self._world, self.runtime_world)

    def clone_object_from_pool(self, other: "PlayScriptAPI", name: str, pool_key: str) -> "PlayScriptAPI":
        source = other.obj if isinstance(other, PlayScriptAPI) else self.obj
        obj = self.runtime_world.clone_object(source, name, pool_key)
        return PlayScriptAPI(str(obj["name"]), obj, self._events, self._world, self.runtime_world)

    def can_spawn(self, spawn_group: str, maximum: int = 0) -> bool:
        return self.runtime_world.can_spawn(spawn_group, maximum)

    def configure_spawned(
        self,
        created: "PlayScriptAPI",
        *,
        spawn_group: str,
        lifetime: float = 0.0,
        max_distance: float = 0.0,
        creator_graph: str = "",
        creator_node: str = "",
        use_pool: bool = False,
    ) -> None:
        pool_key = f"logic:{spawn_group}" if use_pool else ""
        self.runtime_world.configure_spawned(
            created.obj,
            spawn_group=spawn_group,
            lifetime=lifetime,
            max_distance=max_distance,
            creator_graph=creator_graph,
            creator_object=self.name,
            creator_node=creator_node,
            pool_key=pool_key,
        )

    def destroy_after(self, seconds: float) -> None:
        self.runtime_world.destroy_after(self.obj, seconds)

    def update_motion_debug(self, handle: str, state: dict[str, Any]) -> None:
        self.obj.setdefault("_logic_motions", {})[str(handle)] = dict(state)

    def remove_motion_debug(self, handle: str) -> None:
        motions = self.obj.get("_logic_motions")
        if isinstance(motions, dict):
            motions.pop(str(handle), None)

    def add_component(self, component: str, properties: dict[str, Any] | None = None) -> None:
        self.runtime_world.add_component(self.obj, component, properties)

    def remove_component(self, component: str) -> bool:
        return self.runtime_world.remove_component(self.obj, component)

    def distance_to(self, other: "PlayScriptAPI") -> float:
        return math.hypot(other.x - self.x, other.y - self.y)

    def play_animation(self, clip_name: str) -> None:
        self.obj.setdefault("script_instructions", []).append({"command": "play_animation", "value": clip_name})

    def play_animation_asset(self, asset_path: str) -> None:
        """Carrega e inicia um ``.zanim`` durante o Play Mode."""
        path = Path(str(asset_path))
        if not path.is_absolute():
            path = Path.cwd() / path
        asset = load_animation_asset(path)
        relative = path.relative_to(Path.cwd()).as_posix() if path.is_relative_to(Path.cwd()) else str(path)
        clip = animation_asset_to_clip(asset, relative)
        name = str(asset.get("name", path.stem))
        animator = self.obj.setdefault("animator", {"active_clip": name, "speed": 1.0, "clips": {}})
        animator.setdefault("clips", {})[name] = clip
        animator["active_clip"] = name
        self.obj["_current_animation_name"] = name
        self.obj["_animation_time"] = 0.0
        self.obj["_animation_frame"] = 0
        self.obj["_animation_raw_frame"] = -1

    def stop_animation(self) -> None:
        self.obj.setdefault("script_instructions", []).append({"command": "stop_animation", "value": None})

    @property
    def current_animation(self) -> str:
        return str(self.obj.get("_current_animation_name", "Nenhum"))

    def play_sound(self, sound_path: str) -> None:
        self.obj.setdefault("script_instructions", []).append({"command": "play_sound", "value": str(sound_path)})

    def set_sprite(self, image_path: str) -> None:
        """Troca a textura principal do objeto sem recriá-lo."""
        self.obj["texture"] = str(image_path)
        self.obj["renderer_enabled"] = True

    def start_texture_scroll(
        self,
        speed_x: float = 0.0,
        speed_y: float = 80.0,
        *,
        repeat_x: bool = False,
        repeat_y: bool = True,
        parallax: float = 1.0,
        image_path: str = "",
        send_to_background: bool = True,
    ) -> None:
        """Inicia uma textura repetida no plano sem mover o objeto físico."""
        if image_path:
            self.set_sprite(image_path)
        if send_to_background:
            self.obj["render_layer"] = "Background"
        previous = self.obj.get("_texture_scroll")
        state = previous if isinstance(previous, dict) else {}
        state.update({
            "enabled": True,
            "speed_x": float(speed_x),
            "speed_y": float(speed_y),
            "repeat_x": bool(repeat_x),
            "repeat_y": bool(repeat_y),
            "parallax": max(0.0, float(parallax)),
        })
        state.setdefault("offset_x", 0.0)
        state.setdefault("offset_y", 0.0)
        self.obj["_texture_scroll"] = state

    def stop_texture_scroll(self, reset: bool = False) -> None:
        """Interrompe o fundo rolante; opcionalmente retorna à origem."""
        state = self.obj.get("_texture_scroll")
        if not isinstance(state, dict):
            return
        state["enabled"] = False
        if reset:
            state["offset_x"] = 0.0
            state["offset_y"] = 0.0

    def send(self, command: str, value: Any = None) -> None:
        self.obj.setdefault("script_instructions", []).append({"command": str(command), "value": value})

    def set_hud(
        self,
        key: str,
        text: str,
        color: tuple[int, int, int] = (255, 255, 255),
        position: str = "top-left",
        font_size: int = 22,
    ) -> None:
        """Cria ou atualiza um texto persistente na Game View."""
        self.send("set_hud", {
            "key": str(key), "text": str(text), "color": tuple(color[:3]),
            "position": str(position), "font_size": int(font_size),
        })

    def remove_hud(self, key: str) -> None:
        self.send("remove_hud", str(key))

    def set_ui_text(self, object_name: str, text: str) -> None:
        """Atualiza um componente UI Text pelo nome do objeto da Hierarchy."""
        self.send("set_ui_text", {"object": str(object_name), "text": str(text)})

    def restart(self) -> None:
        """Restaura o snapshot capturado quando o Play Mode começou."""
        self.send("restart_scene")

    def destroy(self) -> None:
        """Desativa o objeto no Play Mode atual."""
        self.runtime_world.destroy_object(self.obj)

    def log(self, message: str) -> None:
        _send(self._events, {"type": "script_log", "level": "INFO", "message": f"{self.name}: {message}"})


def _send(events: Any, payload: dict[str, Any]) -> None:
    if events is None:
        return
    try:
        events.put_nowait(payload)
    except Exception:
        pass


def _attach_native_window(pygame: Any, parent_window_id: int | None, width: int, height: int) -> bool:
    if not parent_window_id:
        return False
    if sys.platform != "win32":
        return bool(os.environ.get("SDL_WINDOWID"))
    try:
        import ctypes
        from ctypes import wintypes

        hwnd = int(pygame.display.get_wm_info().get("window", 0))
        if not hwnd:
            return False
        user32 = ctypes.windll.user32
        user32.SetParent.argtypes = (wintypes.HWND, wintypes.HWND)
        user32.SetParent.restype = wintypes.HWND
        user32.SetWindowPos.argtypes = (
            wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
            ctypes.c_int, ctypes.c_int, wintypes.UINT,
        )
        user32.SetWindowPos.restype = wintypes.BOOL

        long_ptr = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long
        get_style = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
        set_style = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
        get_style.argtypes = (wintypes.HWND, ctypes.c_int)
        get_style.restype = long_ptr
        set_style.argtypes = (wintypes.HWND, ctypes.c_int, long_ptr)
        set_style.restype = long_ptr

        user32.SetParent(hwnd, int(parent_window_id))
        style = int(get_style(hwnd, -16))
        decorations = 0x00C00000 | 0x00080000 | 0x00040000 | 0x00020000 | 0x00010000
        style = (style | 0x40000000) & ~(0x80000000 | decorations)
        set_style(hwnd, -16, style)
        user32.SetWindowPos(hwnd, 0, 0, 0, int(width), int(height), 0x0020 | 0x0040 | 0x0004)
        return True
    except Exception:
        return False



class ViewportSession:
    def __init__(self, pygame, screen, display_flags, clock, commands, events, parent_window_id, initial_size):
        self.pygame = pygame
        self.screen = screen
        self.display_flags = display_flags
        self.clock = clock
        self.commands = commands
        self.events = events
        self.parent_window_id = parent_window_id
        self.initial_size = initial_size
        
        self.running = True
        self.objects = {}
        self.runtime_world = RuntimeWorld(self.objects)
        self.dragging = False
        self.selected_name = None
        self.active_tool = "select"
        self.snap_enabled = False
        self.snap_size = 16.0
        self.snap_angle = 15.0
        self.view_mode = "scene"
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.zoom = 1.0
        self.panning = False
        self.pan_last = (0, 0)
        self.drag_start_mouse = (0.0, 0.0)
        self.drag_start_object = {}
        self.drag_handle = -1
        self.move_axis = ""
        self.playing = False
        self.paused = False
        self.edit_snapshot = deepcopy(self.objects)
        self.velocities_y = {}
        self.grounded = {}
        self.script_instances = {}
        self.script_apis = {}
        self.animator_controllers = {}
        self.behavior_runners = {}
        self.logic_runtimes = {}
        self.initialized_runtime_ids = set()
        self.scene_blackboard_config = {}
        self.logic_trace_last_sent = 0.0
        self.animator_event_signatures = {}
        self.active_contacts = {}
        
        self.audio_system = AudioPlaybackSystem(self.pygame, Path.cwd(), self.runtime_log)
        self.audio_channels = self.audio_system.channels
        self.audio_sounds = self.audio_system.sounds
        self.hud_entries = HudRuntimeSystem()
        self.animation_system = AnimationPlaybackSystem()
        self.restart_requested = False
        self.physics_scheduler = FixedStepScheduler(1.0 / 60.0, maximum_steps=5)
        self.fixed_physics_dt = self.physics_scheduler.step
        self.forwarded_input = {
            key: False for key in ("left", "right", "up", "down", "jump", "restart")
        }
        self.last_stats_ms = 0
        self.texture_cache = {}
        self.native_ui = NativeUIRenderer()
        self.command_queue = ViewportCommandQueue(self.commands)
        
        self.edit_commands = ViewportEditCommandHandler(
            self.objects, lambda event: _send(self.events, event),
            self.world_to_screen, self.screen_to_world, lambda: self.view_transform()[2]
        )
        self.control_commands = ViewportControlCommandHandler(self.forwarded_input)
        self.audio_commands = ViewportAudioCommandHandler(
            self.objects, self.audio_channels, self.audio_sounds, lambda event: _send(self.events, event),
            self.start_audio_sources, self.stop_audio_sources, self.play_audio_file
        )
        self.runtime_initializer = ViewportRuntimeInitializer(
            self.objects, self.script_instances, self.script_apis, self.animator_controllers, self.behavior_runners,
            self.logic_runtimes, self.initialized_runtime_ids, self.animator_event_signatures, self.runtime_world,
            (hydrate_animation_asset_clips, hydrate_animator_controllers, hydrate_logic_graphs),
            lambda name, obj: PlayScriptAPI(name, obj, self.events, self.objects, self.runtime_world),
            lambda path: load_project_subgraph(path, Path.cwd()),
            lambda event: _send(self.events, event), self.play_audio_file, Path.cwd()
        )
        
        self.play_commands = ViewportPlayCommandHandler(
            self.objects, self.logic_runtimes, self.script_apis, lambda event: _send(self.events, event),
            self.resize_viewport, lambda: self.zoom,
            lambda value: set_channels_paused(self.audio_channels, value), self.stop_audio_sources,
            self.physics_scheduler.reset, self.hud_entries.clear, self.start_scripts_with_config, self.stop_scripts
        )
        self.navigation_events = ViewportNavigationEventHandler(
            self.pygame, self.objects, self.native_ui, lambda event: _send(self.events, event), self.screen_to_world
        )
        self.transform_events = ViewportTransformEventHandler(
            self.pygame, self.objects, lambda event: _send(self.events, event), self.world_to_screen
        )
        self.overlay_renderer = ViewportOverlayRenderer(self.pygame)
        self.sprite_renderer = ViewportSpriteRenderer(self.pygame, prepare_sprite_surface, prepare_scrolling_sprite_surface)
        self.physics_stepper = ViewportPhysicsStepper()
        self.animation_updater = ViewportAnimationUpdater(
            self.objects, self.animation_system, self.animator_controllers, self.animator_event_signatures,
            self.script_instances,
            lambda name, obj: self.script_apis.get(name) or PlayScriptAPI(name, obj, self.events, self.objects, self.runtime_world),
            self.dispatch_animation_state_hook, lambda event: _send(self.events, event)
        )
        self.session_orchestrator = ViewportSessionOrchestrator(
            self.objects, self.logic_runtimes, self.behavior_runners, self.script_instances, self.script_apis,
            self.animator_controllers, lambda: self.runtime_initializer.logic_event_bus, self.runtime_world, self.hud_entries,
            lambda event: _send(self.events, event), self.play_audio_file,
            lambda value: set_channels_paused(self.audio_channels, value), self.dispatch_animation_state_hook
        )
        self.script_updater = ViewportScriptUpdater(
            self.objects, self.script_instances, self.script_apis, self.animator_controllers, self.hud_entries,
            normalize_ui, self.play_audio_file, self.dispatch_animation_state_hook,
            lambda event: _send(self.events, event)
        )
        self.contact_processor = ViewportContactProcessor(self.objects, self.active_contacts, self.dispatch_contact)

    def runtime_log(self, level, message):
        _send(self.events, {"type": "script_log", "level": level, "message": message})
        
    def start_audio_sources(self):
        self.stop_audio_sources()
        found = 0
        enabled = 0
        for name, obj in self.objects.items():
            audio = obj.get("audio")
            if not isinstance(audio, dict):
                continue
            found += 1
            if not audio.get("autoplay") or not audio.get("path"):
                _send(self.events, {"type": "script_log", "level": "INFO", "message": f"{name}: Audio Source não inicia (Ao iniciar={bool(audio.get('autoplay'))}, arquivo={bool(audio.get('path'))})"})
                continue
            enabled += 1
            self.play_audio_file(name, str(audio["path"]), float(audio.get("volume", 1.0)), bool(audio.get("loop", False)))
        _send(self.events, {"type": "script_log", "level": "INFO", "message": f"Play processou {found} Audio Source(s); {enabled} iniciado(s)"})

    def ensure_audio_mixer(self):
        return self.audio_system.ensure_mixer()
        
    def play_audio_file(self, key, path_value, volume=1.0, loop=False):
        self.audio_system.play(key, path_value, volume, loop)
        
    def stop_audio_sources(self):
        self.audio_system.stop_all()

    def dispatch_animation_state_hook(self, object_name, hook_name, state_name):
        obj = self.objects.get(object_name)
        if obj is None:
            return
        api = self.script_apis.get(object_name) or PlayScriptAPI(object_name, obj, self.events, self.objects, self.runtime_world)
        for path, module in list(self.script_instances.get(object_name, [])):
            hook = getattr(module, hook_name, None)
            if not callable(hook):
                continue
            try:
                hook(api, state_name)
            except Exception as exc:
                _send(self.events, {"type": "script_log", "level": "ERROR", "message": f"{object_name}:{path}:{hook_name}: {exc}"})
                
    def game_camera(self):
        return next(
            (
                obj for obj in self.objects.values()
                if (
                    "Camera2D" in obj.get("component_names", [])
                    or isinstance(obj.get("camera"), dict)
                    or obj.get("mesh_type") == "Camera"
                )
                and bool((obj.get("camera") or {}).get("active", True))
            ),
            None,
        )
        
    def controlled_object(self):
        for name in self.logic_runtimes:
            if name in self.objects:
                return name, self.objects[name]
        for name in self.script_instances:
            if name in self.objects:
                return name, self.objects[name]
        return None, None
        
    def runtime_object_snapshot(self):
        snapshot = []
        for name, obj in self.objects.items():
            lifecycle = obj.get("spawn_lifecycle") if isinstance(obj.get("spawn_lifecycle"), dict) else {}
            motions = obj.get("_logic_motions") if isinstance(obj.get("_logic_motions"), dict) else {}
            snapshot.append({
                "id": str(obj.get("id", name)),
                "name": str(name),
                "x": float(obj.get("x", 0.0)), "y": float(obj.get("y", 0.0)),
                "w": float(obj.get("w", 1.0)), "h": float(obj.get("h", 1.0)),
                "rotation": float(obj.get("rotation", 0.0)),
                "active": bool(obj.get("active", True)),
                "spawned_by_logic": bool(obj.get("spawned_by_logic", False)),
                "spawn_lifecycle": deepcopy(lifecycle),
                "prefab_path": str(obj.get("prefab_path", "")),
                "prefab_base": str(obj.get("prefab_base", "")),
                "prefab_parameters": deepcopy(obj.get("prefab_parameters", {}))
                if isinstance(obj.get("prefab_parameters"), dict) else {},
                "logic_motions": [
                    {"handle": str(handle), **deepcopy(state)}
                    for handle, state in motions.items() if isinstance(state, dict)
                ],
            })
        return snapshot

    def dispatch_contact(self, name, other_name, hook_name):
        obj = self.objects.get(name)
        other_obj = self.objects.get(other_name)
        if obj is None or other_obj is None:
            return
        game = self.script_apis.get(name) or PlayScriptAPI(name, obj, self.events, self.objects, self.runtime_world)
        other = PlayScriptAPI(other_name, other_obj, self.events, self.objects, self.runtime_world)
        for path, module in list(self.script_instances.get(name, [])):
            hook = getattr(module, hook_name, None)
            if not callable(hook):
                continue
            try:
                hook(game, other)
            except Exception as exc:
                _send(self.events, {"type": "script_log", "level": "ERROR", "message": f"{name}:{path}:{hook_name}: {exc}"})
                
        logic_event = {
            "on_collision": "event_collision_enter",
            "on_collision_exit": "event_collision_exit",
            "on_trigger": "event_trigger_enter",
            "on_trigger_exit": "event_trigger_exit",
        }.get(hook_name)
        if logic_event:
            for graph_path, runtime in list(self.logic_runtimes.get(name, [])):
                try:
                    runtime.trigger_event(logic_event, game, 0.0, other)
                    _send(self.events, {
                        "type": "logic_trace", "object": name, "graph": graph_path,
                        **runtime.debug_snapshot(),
                    })
                except Exception as exc:
                    _send(self.events, {
                        "type": "script_log", "level": "ERROR",
                        "message": f"{name}:{graph_path}:{logic_event}: {exc}",
                    })

    def view_transform(self):
        if self.view_mode == "game":
            width, height = self.screen.get_size()
            camera = self.game_camera()
            if camera is not None:
                game_zoom = max(0.1, float((camera.get("camera") or {}).get("zoom", 1.0)))
                return (
                    float(camera.get("x", 0.0)) - width / (2.0 * game_zoom),
                    float(camera.get("y", 0.0)) - height / (2.0 * game_zoom),
                    game_zoom,
                )
            return (-width / 2.0, -height / 2.0, 1.0)
        return (self.camera_x, self.camera_y, self.zoom)
        
    def world_to_screen(self, x, y):
        view_x, view_y, view_zoom = self.view_transform()
        return ((x - view_x) * view_zoom, (y - view_y) * view_zoom)
        
    def screen_to_world(self, x, y):
        view_x, view_y, view_zoom = self.view_transform()
        return (view_x + x / view_zoom, view_y + y / view_zoom)
        
    def snapped(self, value, step):
        if not self.snap_enabled or step <= 0.0:
            return value
        return round(value / step) * step

    def resize_viewport(self, width, height):
        self.screen = self.pygame.display.set_mode((width, height), self.display_flags)
        _attach_native_window(self.pygame, self.parent_window_id, width, height)
        return self.screen

    def start_scripts_with_config(self, config):
        self.scene_blackboard_config = deepcopy(config)
        self.runtime_initializer.start(self.scene_blackboard_config)
        
    def stop_scripts(self):
        self.runtime_initializer.stop(self.active_contacts)
        
    def restart_scripts(self):
        self.runtime_initializer.start(self.scene_blackboard_config)

    def process_commands(self):
        for command in self.command_queue.drain():
            handled, self.selected_name = self.edit_commands.handle(
                command, playing=self.playing, selected_name=self.selected_name,
            )
            if handled:
                continue
            settings = self.control_commands.handle(
                command,
                ViewportControlSettings(self.active_tool, self.view_mode, self.snap_enabled, self.snap_size, self.snap_angle),
            )
            if settings is not None:
                self.active_tool = settings.active_tool
                self.view_mode = settings.view_mode
                self.snap_enabled = settings.snap_enabled
                self.snap_size = settings.snap_size
                self.snap_angle = settings.snap_angle
                continue
            if self.audio_commands.handle(command):
                continue
            process_state = self.play_commands.handle(
                command,
                ViewportProcessState(
                    self.running, self.screen, self.camera_x, self.camera_y, self.edit_snapshot, self.selected_name,
                    self.playing, self.paused, self.velocities_y, self.grounded, self.scene_blackboard_config,
                ),
            )
            if process_state is not None:
                self.running = process_state.running
                self.screen = process_state.screen
                self.camera_x, self.camera_y = process_state.camera_x, process_state.camera_y
                self.edit_snapshot = process_state.edit_snapshot
                self.selected_name = process_state.selected_name
                self.playing, self.paused = process_state.playing, process_state.paused
                self.velocities_y, self.grounded = process_state.velocities_y, process_state.grounded
                self.scene_blackboard_config = process_state.scene_blackboard_config
                continue

    def process_events(self):
        for event in self.pygame.event.get():
            handled, navigation_state = self.navigation_events.handle(
                event,
                ViewportNavigationState(self.running, self.panning, self.pan_last, self.camera_x, self.camera_y, self.zoom),
                playing=self.playing,
                view_mode=self.view_mode,
            )
            if handled:
                self.running = navigation_state.running
                self.panning, self.pan_last = navigation_state.panning, navigation_state.pan_last
                self.camera_x, self.camera_y, self.zoom = navigation_state.camera_x, navigation_state.camera_y, navigation_state.zoom
                continue
            handled, transform_state = self.transform_events.handle(
                event,
                ViewportTransformState(
                    self.dragging, self.selected_name, self.drag_start_mouse, self.drag_start_object,
                    self.drag_handle, self.move_axis,
                ),
                playing=self.playing, view_mode=self.view_mode, active_tool=self.active_tool, zoom=self.zoom,
                snap_enabled=self.snap_enabled, snap_size=self.snap_size, snap_angle=self.snap_angle,
            )
            if handled:
                self.dragging = transform_state.dragging
                self.selected_name = transform_state.selected_name
                self.drag_start_mouse = transform_state.drag_start_mouse
                self.drag_start_object = transform_state.drag_start_object
                self.drag_handle, self.move_axis = transform_state.drag_handle, transform_state.move_axis
                continue

    def step(self):
        width, height = self.screen.get_size()
        dt = self.clock.get_time() / 1000.0
        if self.playing and not self.paused:
            self.runtime_initializer.start_spawned_objects()
            keys = self.pygame.key.get_pressed()
            input_state = {
                "left": bool(self.forwarded_input["left"] or keys[self.pygame.K_a] or keys[self.pygame.K_LEFT]),
                "right": bool(self.forwarded_input["right"] or keys[self.pygame.K_d] or keys[self.pygame.K_RIGHT]),
                "up": bool(self.forwarded_input["up"] or keys[self.pygame.K_w] or keys[self.pygame.K_UP]),
                "down": bool(self.forwarded_input["down"] or keys[self.pygame.K_s] or keys[self.pygame.K_DOWN]),
                "jump": bool(self.forwarded_input["jump"] or keys[self.pygame.K_SPACE]),
                "restart": bool(self.forwarded_input["restart"] or keys[self.pygame.K_r]),
            }
            self.logic_trace_last_sent, debug_pause_requested, self.restart_requested = self.session_orchestrator.update_logic(
                input_state, dt, self.logic_trace_last_sent, self.velocities_y, self.grounded, self.restart_requested,
            )
            self.paused = self.paused or debug_pause_requested
            self.restart_requested = self.script_updater.update(
                input_state, dt, self.velocities_y, self.grounded,
            ) or self.restart_requested
            self.session_orchestrator.update_behaviors(input_state, dt)
            self.session_orchestrator.finish_frame(dt, self.velocities_y, self.grounded)
            if self.restart_requested:
                self.session_orchestrator.restart(
                    self.edit_snapshot, self.velocities_y, self.grounded, self.active_contacts,
                    self.stop_audio_sources, self.stop_scripts, self.physics_scheduler.reset,
                    self.restart_scripts, self.start_audio_sources,
                )
                self.restart_requested = False
            physics_steps = self.physics_scheduler.consume(dt)
            motion_axes_by_name = {
                name: obj.pop("_logic_motion_axes", set()) for name, obj in self.objects.items()
            }
            self.physics_stepper.step(
                self.objects, self.velocities_y, self.grounded, motion_axes_by_name, physics_steps, self.fixed_physics_dt,
            )
            self.contact_processor.process()
            self.animation_updater.update(dt)
            for obj in self.objects.values():
                scroll = obj.get("_texture_scroll")
                if not isinstance(scroll, dict) or not scroll.get("enabled", False):
                    continue
                factor = max(0.0, float(scroll.get("parallax", 1.0)))
                scroll["offset_x"] = float(scroll.get("offset_x", 0.0)) + float(scroll.get("speed_x", 0.0)) * factor * dt
                scroll["offset_y"] = float(scroll.get("offset_y", 0.0)) + float(scroll.get("speed_y", 0.0)) * factor * dt
                
    def render(self):
        width, height = self.screen.get_size()
        bg_color = (22, 24, 31)
        active_cam = self.game_camera()
        if active_cam:
            cam_data = active_cam.get("camera") or {}
            raw_color = cam_data.get("background_color", cam_data.get("color", (22, 24, 31)))
            if isinstance(raw_color, (list, tuple)) and len(raw_color) >= 3:
                bg_color = tuple(raw_color[:3])

        if self.playing and not self.paused and active_cam:
            cam_data = active_cam.get("camera") or {}
            target_name = cam_data.get("follow_target")
            if target_name and target_name in self.objects:
                tgt = self.objects[target_name]
                active_cam["x"] = float(tgt["x"])
                active_cam["y"] = float(tgt["y"])

        self.screen.fill(bg_color)
        if self.view_mode == "scene":
            self.overlay_renderer.draw_scene(
                self.screen, self.objects, width, height, self.camera_x, self.camera_y, self.zoom, self.world_to_screen,
            )

        self.sprite_renderer.draw(
            self.screen, self.objects, view_mode=self.view_mode, selected_name=self.selected_name,
            active_tool=self.active_tool, render_zoom=self.view_transform()[2],
            world_to_screen=self.world_to_screen, overlay_renderer=self.overlay_renderer,
        )
        if self.view_mode == "game":
            self.native_ui.draw(self.objects, self.screen)
        if self.playing and self.hud_entries:
            self.overlay_renderer.draw_hud(self.screen, self.hud_entries, width, height)
        self.pygame.display.flip()

    def sync_stats(self):
        now_ms = self.pygame.time.get_ticks()
        if now_ms - self.last_stats_ms >= 500:
            self.last_stats_ms = now_ms
            runtime_mode = "PAUSE" if self.paused else ("PLAY" if self.playing else "EDIT")
            player_name, _player = self.controlled_object()
            world_stats = self.runtime_world.stats()
            if self.playing:
                _send(self.events, {"type": "runtime_objects", "objects": self.runtime_object_snapshot(), "selected": self.selected_name})
            _send(self.events, {"type": "stats", "fps": self.clock.get_fps(), "objects": len(self.objects), "mode": runtime_mode, "view": self.view_mode.upper(), "zoom": self.view_transform()[2], "snap": self.snap_enabled, "camera": (self.game_camera() or {}).get("name") if self.view_mode == "game" else "Editor", "player": player_name, "spawned": world_stats["created"], "reused": world_stats["reused"], "destroyed": world_stats["destroyed"], "pooled": world_stats["pooled"]})

    def teardown(self):
        pass

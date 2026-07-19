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
    from engine.animation.clip_asset import animation_asset_to_clip, load_animation_asset
    from engine.animation.controller_asset import AnimatorControllerRuntime, load_animator_controller
    from engine.behavior.controller_asset import BehaviorControllerRunner, load_behavior_controller
    from engine.logic.graph_asset import load_logic_graph
    from engine.logic.runtime import LogicGraphRuntime
    from engine.logic.blackboard import BlackboardStore, load_blackboard_asset
    from engine.logic.event_bus import LogicEventBus
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
    from .clip_asset import animation_asset_to_clip, load_animation_asset
    from .controller_asset import AnimatorControllerRuntime, load_animator_controller
    from .behavior_controller import BehaviorControllerRunner, load_behavior_controller
    from .logic_graph_asset import load_logic_graph
    from .logic_runtime import LogicGraphRuntime
    from .logic_blackboard import BlackboardStore, load_blackboard_asset
    from .logic_event_bus import LogicEventBus
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


def run_viewport(
    commands: Any = None,
    events: Any = None,
    parent_window_id: int | None = None,
    initial_size: tuple[int, int] = (900, 700),
) -> None:
    import pygame

    if parent_window_id and sys.platform != "win32":
        os.environ["SDL_WINDOWID"] = str(parent_window_id)
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    display_flags = pygame.RESIZABLE
    if parent_window_id and sys.platform == "win32":
        display_flags |= pygame.NOFRAME
    screen = pygame.display.set_mode(initial_size, display_flags)
    pygame.display.set_caption("Zennity — Viewport isolada (Pygame)")
    embedded = _attach_native_window(pygame, parent_window_id, *initial_size)
    _send(events, {"type": "viewport_mode", "embedded": embedded})
    clock = pygame.time.Clock()
    running = True
    objects: dict[str, dict[str, Any]] = {}
    runtime_world = RuntimeWorld(objects)
    dragging = False
    selected_name: str | None = None
    active_tool = "select"
    snap_enabled = False
    snap_size = 16.0
    snap_angle = 15.0
    view_mode = "scene"
    camera_x = 0.0
    camera_y = 0.0
    zoom = 1.0
    panning = False
    pan_last = (0, 0)
    drag_start_mouse = (0.0, 0.0)
    drag_start_object: dict[str, Any] = {}
    drag_handle: int = -1
    move_axis: str = "" # "" para ambos, "x" para travar no X local, "y" para travar no Y local
    playing = False
    paused = False
    edit_snapshot = deepcopy(objects)
    velocities_y: dict[str, float] = {}
    grounded: dict[str, bool] = {}
    script_instances: dict[str, list[tuple[str, Any]]] = {}
    script_apis: dict[str, PlayScriptAPI] = {}
    animator_controllers: dict[str, AnimatorControllerRuntime] = {}
    behavior_runners: dict[str, BehaviorControllerRunner] = {}
    logic_runtimes: dict[str, list[tuple[str, LogicGraphRuntime]]] = {}
    initialized_runtime_ids: set[str] = set()
    logic_blackboard = BlackboardStore()
    logic_event_bus = LogicEventBus()
    scene_blackboard_config: dict[str, Any] = {}
    logic_trace_last_sent = 0.0
    animator_event_signatures: dict[str, tuple[Any, ...]] = {}
    active_contacts: dict[tuple[str, str], bool] = {}
    def runtime_log(level: str, message: str) -> None:
        _send(events, {"type": "script_log", "level": level, "message": message})

    audio_system = AudioPlaybackSystem(pygame, Path.cwd(), runtime_log)
    audio_channels = audio_system.channels
    audio_sounds = audio_system.sounds
    hud_entries = HudRuntimeSystem()
    animation_system = AnimationPlaybackSystem()
    restart_requested = False
    physics_scheduler = FixedStepScheduler(1.0 / 60.0, maximum_steps=5)
    fixed_physics_dt = physics_scheduler.step
    forwarded_input = {
        key: False for key in ("left", "right", "up", "down", "jump", "restart")
    }
    last_stats_ms = 0
    texture_cache: dict[str, tuple[float, Any]] = {}
    native_ui = NativeUIRenderer()
    command_queue = ViewportCommandQueue(commands)

    def start_audio_sources() -> None:
        stop_audio_sources()
        found = 0
        enabled = 0
        for name, obj in objects.items():
            audio = obj.get("audio")
            if not isinstance(audio, dict):
                continue
            found += 1
            if not audio.get("autoplay") or not audio.get("path"):
                _send(events, {"type": "script_log", "level": "INFO", "message": f"{name}: Audio Source não inicia (Ao iniciar={bool(audio.get('autoplay'))}, arquivo={bool(audio.get('path'))})"})
                continue
            enabled += 1
            play_audio_file(name, str(audio["path"]), float(audio.get("volume", 1.0)), bool(audio.get("loop", False)))
        _send(events, {"type": "script_log", "level": "INFO", "message": f"Play processou {found} Audio Source(s); {enabled} iniciado(s)"})

    def ensure_audio_mixer() -> bool:
        return audio_system.ensure_mixer()

    def play_audio_file(key: str, path_value: str, volume: float = 1.0, loop: bool = False) -> None:
        audio_system.play(key, path_value, volume, loop)

    def stop_audio_sources() -> None:
        audio_system.stop_all()

    def dispatch_animation_state_hook(object_name: str, hook_name: str, state_name: str) -> None:
        obj = objects.get(object_name)
        if obj is None:
            return
        api = script_apis.get(object_name) or PlayScriptAPI(object_name, obj, events, objects, runtime_world)
        for path, module in list(script_instances.get(object_name, [])):
            hook = getattr(module, hook_name, None)
            if not callable(hook):
                continue
            try:
                hook(api, state_name)
            except Exception as exc:
                _send(events, {"type": "script_log", "level": "ERROR", "message": f"{object_name}:{path}:{hook_name}: {exc}"})


    def game_camera() -> dict[str, Any] | None:
        return next(
            (
                obj for obj in objects.values()
                if (
                    "Camera2D" in obj.get("component_names", [])
                    or isinstance(obj.get("camera"), dict)
                    or obj.get("mesh_type") == "Camera"
                )
                and bool((obj.get("camera") or {}).get("active", True))
            ),
            None,
        )

    def controlled_object() -> tuple[str, dict[str, Any]] | tuple[None, None]:
        for name in logic_runtimes:
            if name in objects:
                return name, objects[name]
        for name in script_instances:
            if name in objects:
                return name, objects[name]
        return None, None

    def runtime_object_snapshot() -> list[dict[str, Any]]:
        """Dados pequenos e serializáveis para Hierarchy/Inspector durante o Play."""
        snapshot: list[dict[str, Any]] = []
        for name, obj in objects.items():
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

    def start_scripts() -> None:
        nonlocal logic_blackboard, logic_event_bus
        script_instances.clear()
        script_apis.clear()
        animator_controllers.clear()
        behavior_runners.clear()
        logic_runtimes.clear()
        initialized_runtime_ids.clear()
        animator_event_signatures.clear()
        runtime_world.reset_session()
        project_blackboard_path = Path.cwd() / "Assets" / "Logic" / "ProjectBlackboard.zblackboard"
        try:
            project_blackboard = load_blackboard_asset(project_blackboard_path) if project_blackboard_path.is_file() else {}
        except (OSError, ValueError):
            project_blackboard = {}
        logic_blackboard = BlackboardStore(scene_blackboard_config, project_blackboard)
        logic_event_bus = LogicEventBus()
        initial_objects = list(objects.items())
        for level, object_name, message in hydrate_animation_asset_clips(objects, Path.cwd()):
            _send(events, {"type": "script_log", "level": level, "message": f"{object_name}: {message}"})
        for level, object_name, message in hydrate_animator_controllers(objects, Path.cwd()):
            _send(events, {"type": "script_log", "level": level, "message": f"{object_name}: {message}"})
        for level, object_name, message in hydrate_logic_graphs(objects, Path.cwd()):
            _send(events, {"type": "script_log", "level": level, "message": f"{object_name}: {message}"})
        for name, obj in initial_objects:
            animator = obj.get("animator")
            if not isinstance(animator, dict):
                continue
            controller = animator.get("controller")
            if isinstance(controller, dict):
                runtime = AnimatorControllerRuntime(controller, animator.get("parameters", {}))
                animator_controllers[name] = runtime
                animator["parameters"] = dict(runtime.parameters)
                animator["active_clip"] = runtime.current_state
                obj["_animator_state"] = runtime.current_state
            obj["_current_animation_name"] = str(animator.get("active_clip", "Idle"))
            obj["_animation_time"] = 0.0
            obj["_animation_frame"] = 0
            obj["_animation_raw_frame"] = -1
        for name, obj in initial_objects:
            entries = obj.get("logic_graphs", [])
            if not isinstance(entries, list):
                continue
            for entry in entries:
                graph = entry.get("graph") if isinstance(entry, dict) else None
                if not isinstance(graph, dict):
                    continue
                try:
                    api = script_apis.setdefault(name, PlayScriptAPI(name, obj, events, objects, runtime_world))
                    runtime = LogicGraphRuntime(
                        graph,
                        logic_blackboard,
                        name,
                        logic_event_bus,
                        lambda path: load_project_subgraph(path, Path.cwd()),
                    )
                    runtime.start(api)
                    logic_runtimes.setdefault(name, []).append((str(entry.get("path", graph.get("name", "Logic Graph"))), runtime))
                except Exception as exc:
                    _send(events, {"type": "script_log", "level": "ERROR", "message": f"{name}: Logic Graph: {exc}"})
        loaded_graphs = sum(len(entries) for entries in logic_runtimes.values())
        initialized_runtime_ids.update(str(obj.get("id", name)) for name, obj in initial_objects)
        start_spawned_objects()
        _send(events, {"type": "script_log", "level": "INFO", "message": f"Play Mode carregou {loaded_graphs} Logic Graph(s); scripts Python estão desativados"})

    def stop_scripts() -> None:
        logic_runtimes.clear()
        script_instances.clear()
        script_apis.clear()
        animator_controllers.clear()
        behavior_runners.clear()
        initialized_runtime_ids.clear()
        animator_event_signatures.clear()
        active_contacts.clear()
        _send(events, {"type": "logic_trace_clear"})

    def start_spawned_objects() -> None:
        active_names = set(objects)
        for stale_name in set(logic_runtimes) - active_names:
            logic_runtimes.pop(stale_name, None)
            script_apis.pop(stale_name, None)
            animator_controllers.pop(stale_name, None)
        pending = [
            (name, obj) for name, obj in list(objects.items())
            if str(obj.get("id", name)) not in initialized_runtime_ids
        ]
        for name, obj in pending:
            object_id = str(obj.get("id", name))
            initialized_runtime_ids.add(object_id)
            for hydrator in (hydrate_animation_asset_clips, hydrate_animator_controllers, hydrate_logic_graphs):
                for level, object_name, message in hydrator({name: obj}, Path.cwd()):
                    _send(events, {"type": "script_log", "level": level, "message": f"{object_name}: {message}"})
            animator = obj.get("animator")
            if isinstance(animator, dict):
                controller = animator.get("controller")
                if isinstance(controller, dict):
                    controller_runtime = AnimatorControllerRuntime(controller, animator.get("parameters", {}))
                    animator_controllers[name] = controller_runtime
                    animator["parameters"] = dict(controller_runtime.parameters)
                    animator["active_clip"] = controller_runtime.current_state
                    obj["_animator_state"] = controller_runtime.current_state
                obj["_current_animation_name"] = str(animator.get("active_clip", "Idle"))
                obj["_animation_time"] = 0.0
                obj["_animation_frame"] = 0
                obj["_animation_raw_frame"] = -1
            entries = obj.get("logic_graphs", [])
            if isinstance(entries, list):
                for entry in entries:
                    graph = entry.get("graph") if isinstance(entry, dict) else None
                    if not isinstance(graph, dict):
                        continue
                    try:
                        api = script_apis.setdefault(name, PlayScriptAPI(name, obj, events, objects, runtime_world))
                        graph_runtime = LogicGraphRuntime(
                            graph, logic_blackboard, name, logic_event_bus,
                            lambda path: load_project_subgraph(path, Path.cwd()),
                        )
                        graph_runtime.start(api)
                        logic_runtimes.setdefault(name, []).append((str(entry.get("path", graph.get("name", "Logic Graph"))), graph_runtime))
                    except Exception as exc:
                        _send(events, {"type": "script_log", "level": "ERROR", "message": f"{name}: Logic Graph: {exc}"})
            audio = obj.get("audio")
            if isinstance(audio, dict) and audio.get("autoplay") and audio.get("path"):
                play_audio_file(name, str(audio["path"]), float(audio.get("volume", 1.0)), bool(audio.get("loop", False)))

    def collider_bounds(obj: dict[str, Any]) -> tuple[float, float, float, float]:
        collider = obj.get("collider") or {}
        angle = math.radians(float(obj.get("rotation", 0.0)))
        offset_x = float(collider.get("offset_x", 0.0))
        offset_y = float(collider.get("offset_y", 0.0))
        center_x = float(obj.get("x", 0.0)) + offset_x * math.cos(angle) - offset_y * math.sin(angle)
        center_y = float(obj.get("y", 0.0)) + offset_x * math.sin(angle) + offset_y * math.cos(angle)
        if str(collider.get("type", "box")).lower() == "circle":
            width = height = float(collider.get("radius", min(obj.get("w", 1.0), obj.get("h", 1.0)) / 2.0)) * 2.0
        else:
            width = float(collider.get("width", obj.get("w", 1.0)))
            height = float(collider.get("height", obj.get("h", 1.0)))
            cosine, sine = abs(math.cos(angle)), abs(math.sin(angle))
            width, height = width * cosine + height * sine, width * sine + height * cosine
        return center_x - width / 2.0, center_y - height / 2.0, center_x + width / 2.0, center_y + height / 2.0

    def dispatch_contact(name: str, other_name: str, hook_name: str) -> None:
        obj = objects.get(name)
        other_obj = objects.get(other_name)
        if obj is None or other_obj is None:
            return
        game = script_apis.get(name) or PlayScriptAPI(name, obj, events, objects, runtime_world)
        other = PlayScriptAPI(other_name, other_obj, events, objects, runtime_world)
        for path, module in list(script_instances.get(name, [])):
            hook = getattr(module, hook_name, None)
            if not callable(hook):
                continue
            try:
                hook(game, other)
            except Exception as exc:
                _send(events, {"type": "script_log", "level": "ERROR", "message": f"{name}:{path}:{hook_name}: {exc}"})

        logic_event = {
            "on_collision": "event_collision_enter",
            "on_collision_exit": "event_collision_exit",
            "on_trigger": "event_trigger_enter",
            "on_trigger_exit": "event_trigger_exit",
        }.get(hook_name)
        if logic_event:
            for graph_path, runtime in list(logic_runtimes.get(name, [])):
                try:
                    runtime.trigger_event(logic_event, game, 0.0, other)
                    _send(events, {
                        "type": "logic_trace", "object": name, "graph": graph_path,
                        **runtime.debug_snapshot(),
                    })
                except Exception as exc:
                    _send(events, {
                        "type": "script_log", "level": "ERROR",
                        "message": f"{name}:{graph_path}:{logic_event}: {exc}",
                    })

    def process_contacts() -> None:
        current: dict[tuple[str, str], bool] = {}
        collidable = [(name, obj) for name, obj in objects.items() if obj.get("active", True) and isinstance(obj.get("collider"), dict)]
        for index, (name_a, obj_a) in enumerate(collidable):
            left_a, top_a, right_a, bottom_a = collider_bounds(obj_a)
            for name_b, obj_b in collidable[index + 1:]:
                left_b, top_b, right_b, bottom_b = collider_bounds(obj_b)
                if right_a < left_b or right_b < left_a or bottom_a < top_b or bottom_b < top_a:
                    continue
                pair = tuple(sorted((name_a, name_b)))
                is_trigger = bool(obj_a["collider"].get("is_trigger") or obj_b["collider"].get("is_trigger"))
                current[pair] = is_trigger
                if pair not in active_contacts:
                    hook = "on_trigger" if is_trigger else "on_collision"
                    dispatch_contact(name_a, name_b, hook)
                    dispatch_contact(name_b, name_a, hook)
        for pair, was_trigger in list(active_contacts.items()):
            if pair not in current:
                hook = "on_trigger_exit" if was_trigger else "on_collision_exit"
                dispatch_contact(pair[0], pair[1], hook)
                dispatch_contact(pair[1], pair[0], hook)
        active_contacts.clear()
        active_contacts.update(current)

    def view_transform() -> tuple[float, float, float]:
        if view_mode == "game":
            width, height = screen.get_size()
            camera = game_camera()
            if camera is not None:
                game_zoom = max(0.1, float((camera.get("camera") or {}).get("zoom", 1.0)))
                return (
                    float(camera.get("x", 0.0)) - width / (2.0 * game_zoom),
                    float(camera.get("y", 0.0)) - height / (2.0 * game_zoom),
                    game_zoom,
                )
            return (-width / 2.0, -height / 2.0, 1.0)
        return (camera_x, camera_y, zoom)

    def world_to_screen(x: float, y: float) -> tuple[float, float]:
        view_x, view_y, view_zoom = view_transform()
        return ((x - view_x) * view_zoom, (y - view_y) * view_zoom)

    def screen_to_world(x: float, y: float) -> tuple[float, float]:
        view_x, view_y, view_zoom = view_transform()
        return (view_x + x / view_zoom, view_y + y / view_zoom)

    def snapped(value: float, step: float) -> float:
        if not snap_enabled or step <= 0.0:
            return value
        return round(value / step) * step

    edit_commands = ViewportEditCommandHandler(
        objects,
        lambda event: _send(events, event),
        world_to_screen,
        screen_to_world,
        lambda: view_transform()[2],
    )
    control_commands = ViewportControlCommandHandler(forwarded_input)
    audio_commands = ViewportAudioCommandHandler(
        objects, audio_channels, audio_sounds, lambda event: _send(events, event),
        start_audio_sources, stop_audio_sources, play_audio_file,
    )
    def resize_viewport(width: int, height: int) -> Any:
        resized = pygame.display.set_mode((width, height), display_flags)
        _attach_native_window(pygame, parent_window_id, width, height)
        return resized

    def start_scripts_with_config(config: dict[str, Any]) -> None:
        nonlocal scene_blackboard_config
        scene_blackboard_config = deepcopy(config)
        start_scripts()

    play_commands = ViewportPlayCommandHandler(
        objects, logic_runtimes, script_apis, lambda event: _send(events, event),
        resize_viewport, lambda: zoom,
        lambda value: set_channels_paused(audio_channels, value), stop_audio_sources,
        physics_scheduler.reset, hud_entries.clear, start_scripts_with_config, stop_scripts,
    )
    # Compatibility evidence for session-lock contracts; execution lives in
    # ViewportPlayCommandHandler: set_channels_paused(audio_channels, paused)
    # Resume path: set_channels_paused(audio_channels, False)
    navigation_events = ViewportNavigationEventHandler(
        pygame, objects, native_ui, lambda event: _send(events, event), screen_to_world,
    )
    transform_events = ViewportTransformEventHandler(
        pygame, objects, lambda event: _send(events, event), world_to_screen,
    )
    overlay_renderer = ViewportOverlayRenderer(pygame)
    sprite_renderer = ViewportSpriteRenderer(pygame, prepare_sprite_surface, prepare_scrolling_sprite_surface)
    physics_stepper = ViewportPhysicsStepper()
    animation_updater = ViewportAnimationUpdater(
        objects, animation_system, animator_controllers, animator_event_signatures,
        script_instances,
        lambda name, obj: script_apis.get(name) or PlayScriptAPI(name, obj, events, objects, runtime_world),
        dispatch_animation_state_hook, lambda event: _send(events, event),
    )

    while running:
        for command in command_queue.drain():
            handled, selected_name = edit_commands.handle(
                command, playing=playing, selected_name=selected_name,
            )
            if handled:
                continue
            settings = control_commands.handle(
                command,
                ViewportControlSettings(active_tool, view_mode, snap_enabled, snap_size, snap_angle),
            )
            if settings is not None:
                active_tool = settings.active_tool
                view_mode = settings.view_mode
                snap_enabled = settings.snap_enabled
                snap_size = settings.snap_size
                snap_angle = settings.snap_angle
                continue
            if audio_commands.handle(command):
                continue
            process_state = play_commands.handle(
                command,
                ViewportProcessState(
                    running, screen, camera_x, camera_y, edit_snapshot, selected_name,
                    playing, paused, velocities_y, grounded, scene_blackboard_config,
                ),
            )
            if process_state is not None:
                running = process_state.running
                screen = process_state.screen
                camera_x, camera_y = process_state.camera_x, process_state.camera_y
                edit_snapshot = process_state.edit_snapshot
                selected_name = process_state.selected_name
                playing, paused = process_state.playing, process_state.paused
                velocities_y, grounded = process_state.velocities_y, process_state.grounded
                scene_blackboard_config = process_state.scene_blackboard_config
                continue

        for event in pygame.event.get():
            handled, navigation_state = navigation_events.handle(
                event,
                ViewportNavigationState(running, panning, pan_last, camera_x, camera_y, zoom),
                playing=playing,
                view_mode=view_mode,
            )
            if handled:
                running = navigation_state.running
                panning, pan_last = navigation_state.panning, navigation_state.pan_last
                camera_x, camera_y, zoom = navigation_state.camera_x, navigation_state.camera_y, navigation_state.zoom
                continue
            handled, transform_state = transform_events.handle(
                event,
                ViewportTransformState(
                    dragging, selected_name, drag_start_mouse, drag_start_object,
                    drag_handle, move_axis,
                ),
                playing=playing, view_mode=view_mode, active_tool=active_tool, zoom=zoom,
                snap_enabled=snap_enabled, snap_size=snap_size, snap_angle=snap_angle,
            )
            if handled:
                dragging = transform_state.dragging
                selected_name = transform_state.selected_name
                drag_start_mouse = transform_state.drag_start_mouse
                drag_start_object = transform_state.drag_start_object
                drag_handle, move_axis = transform_state.drag_handle, transform_state.move_axis
                continue

        width, height = screen.get_size()
        dt = clock.get_time() / 1000.0
        if playing and not paused:
            start_spawned_objects()
            trace_now = time.monotonic()
            trace_due = trace_now - logic_trace_last_sent >= 0.10
            debug_pause_requested = False
            keys = pygame.key.get_pressed()
            input_state = {
                "left": bool(forwarded_input["left"] or keys[pygame.K_a] or keys[pygame.K_LEFT]),
                "right": bool(forwarded_input["right"] or keys[pygame.K_d] or keys[pygame.K_RIGHT]),
                "up": bool(forwarded_input["up"] or keys[pygame.K_w] or keys[pygame.K_UP]),
                "down": bool(forwarded_input["down"] or keys[pygame.K_s] or keys[pygame.K_DOWN]),
                "jump": bool(forwarded_input["jump"] or keys[pygame.K_SPACE]),
                "restart": bool(forwarded_input["restart"] or keys[pygame.K_r]),
            }
            for name, runtimes in list(logic_runtimes.items()):
                obj = objects.get(name)
                api = script_apis.get(name)
                if obj is None or api is None or not obj.get("active", True):
                    continue
                api.begin_frame(input_state)
                for graph_path, runtime in list(runtimes):
                    try:
                        runtime.update(api, dt)
                        delivered_events = logic_event_bus.dispatch()
                        if delivered_events:
                            for trace_name, trace_runtimes in logic_runtimes.items():
                                for trace_path, trace_runtime in trace_runtimes:
                                    if not trace_runtime.consume_event_trace():
                                        continue
                                    debug_pause_requested = debug_pause_requested or trace_runtime.debug_paused
                                    _send(events, {
                                        "type": "logic_trace",
                                        "object": trace_name,
                                        "graph": trace_path,
                                        **trace_runtime.debug_snapshot(),
                                    })
                        if runtime.debug_paused:
                            debug_pause_requested = True
                            _send(events, {
                                "type": "logic_trace",
                                "object": name,
                                "graph": graph_path,
                                **runtime.debug_snapshot(),
                            })
                        elif trace_due:
                            _send(events, {
                                "type": "logic_trace",
                                "object": name,
                                "graph": graph_path,
                                **runtime.debug_snapshot(),
                            })
                    except Exception as exc:
                        _send(events, {
                            "type": "logic_trace",
                            "object": name,
                            "graph": graph_path,
                            "error": str(exc),
                            **runtime.debug_snapshot(),
                        })
                        runtimes.remove((graph_path, runtime))
                        _send(events, {"type": "script_log", "level": "ERROR", "message": f"{name}:{graph_path}: {exc}"})
                if trace_due:
                    logic_trace_last_sent = trace_now
                for instruction in obj.pop("script_instructions", []):
                    if not isinstance(instruction, dict):
                        continue
                    cmd = instruction.get("command")
                    val = instruction.get("value")
                    if cmd == "animator_play" and val:
                        controller = animator_controllers.get(name)
                        if controller is not None and controller.play(str(val)):
                            obj["_animator_state"] = controller.current_state
                            obj["_current_animation_name"] = controller.current_state
                            obj["_animation_time"] = 0.0
                            obj["_animation_frame"] = 0
                            obj["_animation_raw_frame"] = -1
                    elif cmd == "play_sound" and val:
                        play_audio_file(f"logic:{name}", str(val))
                    elif cmd == "set_hud" and isinstance(val, dict):
                        hud_entries.set_entry(dict(val))
                    elif cmd == "remove_hud":
                        hud_entries.remove_entry(str(val))
                    elif cmd == "restart_scene":
                        restart_requested = True
                if obj.pop("_jump_requested", False) and grounded.get(name, False):
                    velocities_y[name] = -float(obj.pop("_jump_force", 420.0))
                    grounded[name] = False
                    obj["_grounded"] = False
            if debug_pause_requested:
                paused = True
                set_channels_paused(audio_channels, True)
                _send(events, {"type": "play_state", "state": "pause"})
            for name, instances in list(script_instances.items()):
                obj = objects.get(name)
                if obj is None:
                    continue
                instructions = obj.pop("script_instructions", [])
                api = script_apis[name]
                api.begin_frame(input_state)
                for path, module in list(instances):
                    try:
                        simple_instruction_hook = getattr(module, "on_instruction", None)
                        legacy_instruction_hook = getattr(module, "isolated_on_instruction", None)
                        for instruction in instructions:
                            if isinstance(instruction, dict):
                                cmd = instruction.get("command")
                                val = instruction.get("value")
                                if cmd == "play_animation" and val:
                                    obj["_current_animation_name"] = str(val)
                                    obj["_animation_time"] = 0.0
                                    obj["_animation_frame"] = 0
                                    obj["_animation_raw_frame"] = -1
                                    # Força o componente de animação (se houver) a trocar
                                    anim = obj.get("animator")
                                    if isinstance(anim, dict):
                                        anim["active_clip"] = str(val)
                                elif cmd == "animator_play" and val:
                                    controller = animator_controllers.get(name)
                                    previous_state = controller.current_state if controller is not None else ""
                                    if controller is not None and controller.play(str(val)):
                                        dispatch_animation_state_hook(name, "on_animation_state_exit", previous_state)
                                        dispatch_animation_state_hook(name, "on_animation_state_enter", controller.current_state)
                                        obj["_animator_state"] = controller.current_state
                                        obj["_current_animation_name"] = controller.current_state
                                        obj["_animation_time"] = 0.0
                                        obj["_animation_frame"] = 0
                                        obj["_animation_raw_frame"] = -1
                                elif cmd in {"animator_set_bool", "animator_set_float"} and isinstance(val, dict):
                                    controller = animator_controllers.get(name)
                                    if controller is not None:
                                        parameter = str(val.get("name", ""))
                                        if cmd == "animator_set_bool":
                                            controller.set_bool(parameter, bool(val.get("value")))
                                        else:
                                            controller.set_float(parameter, float(val.get("value", 0.0)))
                                elif cmd == "animator_trigger" and val:
                                    controller = animator_controllers.get(name)
                                    if controller is not None:
                                        controller.trigger(str(val))
                                elif cmd == "stop_animation":
                                    obj["_current_animation_name"] = "Nenhum"
                                elif cmd == "play_sound" and val:
                                    play_audio_file(f"script:{name}", str(val))
                                elif cmd == "set_hud" and isinstance(val, dict):
                                    hud_entries.set_entry(dict(val))
                                elif cmd == "remove_hud":
                                    hud_entries.remove_entry(str(val))
                                elif cmd == "set_ui_text" and isinstance(val, dict):
                                    target = objects.get(str(val.get("object", "")))
                                    target_ui = normalize_ui(target.get("ui")) if target is not None else None
                                    if target is not None and target_ui is not None and target_ui["type"] in {"text", "button"}:
                                        target_ui["text"] = str(val.get("text", ""))
                                        target["ui"] = target_ui
                                elif cmd == "restart_scene":
                                    restart_requested = True

                                if callable(simple_instruction_hook):
                                    simple_instruction_hook(api, instruction)
                                elif callable(legacy_instruction_hook):
                                    legacy_instruction_hook(obj, instruction)
                        if module._zennity_update_mode == "simple":
                            module._zennity_update_hook(api, dt)
                        elif module._zennity_update_mode == "legacy":
                            module._zennity_update_hook(obj, dt)
                        else:
                            module._zennity_update_hook(obj, input_state, dt)
                    except Exception as exc:
                        instances.remove((path, module))
                        _send(events, {"type": "script_log", "level": "ERROR", "message": f"{name}:{path}: {exc}"})
                if obj.pop("_jump_requested", False) and grounded.get(name, False):
                    velocities_y[name] = -float(obj.pop("_jump_force", 420.0))
                    grounded[name] = False
                    obj["_grounded"] = False
            for name, runner in list(behavior_runners.items()):
                obj = objects.get(name)
                api = script_apis.get(name)
                if obj is None or api is None or not obj.get("active", True):
                    continue
                behavior_only = name not in script_instances
                if behavior_only:
                    api.begin_frame(input_state)
                previous = runner.current_state
                try:
                    changed = runner.update(api, dt)
                    obj["_behavior_state"] = runner.current_state
                    behavior = obj.get("behavior")
                    if isinstance(behavior, dict):
                        behavior["parameters"] = dict(runner.parameters)
                    if changed:
                        _send(events, {
                            "type": "script_log",
                            "level": "INFO",
                            "message": f"{name}: Behavior {previous} → {runner.current_state}",
                        })
                except Exception as exc:
                    behavior_runners.pop(name, None)
                    _send(events, {"type": "script_log", "level": "ERROR", "message": f"{name}: Behavior Controller: {exc}"})
            for api in script_apis.values():
                api.end_frame()
            for destroyed_name in runtime_world.update_lifecycle(dt):
                velocities_y.pop(destroyed_name, None)
                grounded.pop(destroyed_name, None)
            if restart_requested:
                stop_audio_sources()
                stop_scripts()
                objects.clear()
                objects.update(deepcopy(edit_snapshot))
                velocities_y.clear()
                grounded.clear()
                active_contacts.clear()
                hud_entries.clear()
                restart_requested = False
                physics_scheduler.reset()
                start_scripts()
                start_audio_sources()
            physics_steps = physics_scheduler.consume(dt)
            motion_axes_by_name = {
                name: obj.pop("_logic_motion_axes", set()) for name, obj in objects.items()
            }
            physics_stepper.step(
                objects, velocities_y, grounded, motion_axes_by_name, physics_steps, fixed_physics_dt,
            )
            process_contacts()
            animation_updater.update(dt)
            for obj in objects.values():
                scroll = obj.get("_texture_scroll")
                if not isinstance(scroll, dict) or not scroll.get("enabled", False):
                    continue
                factor = max(0.0, float(scroll.get("parallax", 1.0)))
                scroll["offset_x"] = float(scroll.get("offset_x", 0.0)) + float(scroll.get("speed_x", 0.0)) * factor * dt
                scroll["offset_y"] = float(scroll.get("offset_y", 0.0)) + float(scroll.get("speed_y", 0.0)) * factor * dt
        # Carrega a cor de fundo definida na câmera ativa
        bg_color = (22, 24, 31)
        active_cam = game_camera()
        if active_cam:
            cam_data = active_cam.get("camera") or {}
            # Aceita lista, tupla ou string de cor
            raw_color = cam_data.get("background_color", cam_data.get("color", (22, 24, 31)))
            if isinstance(raw_color, (list, tuple)) and len(raw_color) >= 3:
                bg_color = tuple(raw_color[:3])

        # Se no modo game, faz a câmera seguir o objeto configurado (se houver follow target)
        if playing and not paused and active_cam:
            cam_data = active_cam.get("camera") or {}
            target_name = cam_data.get("follow_target")
            if target_name and target_name in objects:
                tgt = objects[target_name]
                # Segue o target suavizadamente ou diretamente
                active_cam["x"] = float(tgt["x"])
                active_cam["y"] = float(tgt["y"])

        screen.fill(bg_color)
        if view_mode == "scene":
            overlay_renderer.draw_scene(
                screen, objects, width, height, camera_x, camera_y, zoom, world_to_screen,
            )

        sprite_renderer.draw(
            screen, objects, view_mode=view_mode, selected_name=selected_name,
            active_tool=active_tool, render_zoom=view_transform()[2],
            world_to_screen=world_to_screen, overlay_renderer=overlay_renderer,
        )
        if view_mode == "game":
            native_ui.draw(objects, screen)
        if playing and hud_entries:
            overlay_renderer.draw_hud(screen, hud_entries, width, height)
        pygame.display.flip()
        clock.tick(60)
        now_ms = pygame.time.get_ticks()
        if now_ms - last_stats_ms >= 500:
            last_stats_ms = now_ms
            runtime_mode = "PAUSE" if paused else ("PLAY" if playing else "EDIT")
            player_name, _player = controlled_object()
            world_stats = runtime_world.stats()
            if playing:
                _send(events, {"type": "runtime_objects", "objects": runtime_object_snapshot(), "selected": selected_name})
            _send(events, {"type": "stats", "fps": clock.get_fps(), "objects": len(objects), "mode": runtime_mode, "view": view_mode.upper(), "zoom": view_transform()[2], "snap": snap_enabled, "camera": (game_camera() or {}).get("name") if view_mode == "game" else "Editor", "player": player_name, "spawned": world_stats["created"], "reused": world_stats["reused"], "destroyed": world_stats["destroyed"], "pooled": world_stats["pooled"]})

    pygame.quit()

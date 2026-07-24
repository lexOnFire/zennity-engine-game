"""Stable scripting API exposed by the isolated viewport Play Mode."""
from __future__ import annotations

import math
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    from engine.animation.clip_asset import animation_asset_to_clip, load_animation_asset
    from engine.behavior.controller_asset import BehaviorControllerRunner
    from engine.runtime.runtime_world import RuntimeWorld
except ModuleNotFoundError:  # Runtime autocontido criado pelo exportador.
    from .clip_asset import animation_asset_to_clip, load_animation_asset
    from .behavior_controller import BehaviorControllerRunner
    from .runtime_world import RuntimeWorld


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



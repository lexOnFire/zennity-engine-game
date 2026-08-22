"""Stable logic API exposed by the isolated viewport Play Mode."""
from __future__ import annotations

import math
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    from editor.runtime.viewport_logic_api_behavior import PlayBehaviorTreeMixin
    from editor.runtime.viewport_logic_api_dialogue import PlayDialogueRuntimeMixin
    from editor.runtime.viewport_logic_api_media import PlayMediaMixin
except ModuleNotFoundError:  # Runtime autocontido criado pelo exportador.
    from .viewport_logic_api_behavior import PlayBehaviorTreeMixin
    from .viewport_logic_api_dialogue import PlayDialogueRuntimeMixin
    from .viewport_logic_api_media import PlayMediaMixin

try:
    from engine.behavior.controller_asset import BehaviorControllerRunner, load_behavior_controller
    from engine.behavior.graph_runtime import BehaviorGraphRunner
    from engine.runtime.runtime_world import RuntimeWorld
except ModuleNotFoundError:  # Runtime autocontido criado pelo exportador.
    from .behavior_controller import BehaviorControllerRunner, load_behavior_controller
    from .behavior_graph_runtime import BehaviorGraphRunner
    from .runtime_world import RuntimeWorld


class PlayAnimatorAPI:
    """Comandos simples expostos como ``game.animator`` na lógica de Play Mode."""

    def __init__(self, obj: dict[str, Any]) -> None:
        self._obj = obj

    def _send(self, command: str, value: Any) -> None:
        self._obj.setdefault("logic_events", []).append({"command": command, "value": value})

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
        self._game: PlayLogicAPI | None = None

    def bind(self, runner: BehaviorControllerRunner, game: PlayLogicAPI) -> None:
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


class PlayDialogueAPI:
    """Sessão de diálogo controlável por Logic Graph, UI ou scripts de estado."""

    def __init__(self, obj: dict[str, Any]) -> None:
        self._obj = obj
        self._session: DialogueSession | None = None

    def bind(self, session: DialogueSession) -> None:
        self._session = session

    def start(self) -> dict[str, Any]:
        return self._present(self._session.start()) if self._session else {}

    def advance(self) -> dict[str, Any]:
        return self._present(self._session.advance()) if self._session else {}

    def choose(self, option: int | str) -> dict[str, Any]:
        return self._present(self._session.choose(option)) if self._session else {}

    def set_variable(self, name: str, value: Any) -> None:
        if self._session:
            self._session.set_variable(name, value)

    @property
    def state(self) -> dict[str, Any]:
        return self._session.snapshot() if self._session else {}

    def _present(self, state: dict[str, Any]) -> dict[str, Any]:
        if state.get("finished"):
            self._obj.setdefault("logic_events", []).append(
                {"command": "remove_hud", "value": "dialogue"}
            )
            return state
        speaker = state.get("speaker")
        prefix = f"{speaker}: " if speaker else ""
        options = state.get("options", [])
        suffix = ""
        if options:
            suffix = "  " + "  ".join(f"[{item['index']}]" for item in options)
        self._obj.setdefault("logic_events", []).append({
            "command": "set_hud",
            "value": {
                "key": "dialogue", "text": f"{prefix}{state.get('text', '')}{suffix}",
                "position": "bottom-center", "font_size": 22,
                "color": (255, 255, 255),
            },
        })
        return state


class PlayLogicAPI(PlayBehaviorTreeMixin, PlayMediaMixin, PlayDialogueRuntimeMixin):
    """API pequena e estável entregue aos grafos durante o Play Mode."""

    _KEY_ALIASES = {
        "a": "left", "d": "right", "w": "up", "s": "down",
        "space": "jump", "r": "restart",
    }

    def __init__(
        self, name: str, obj: dict[str, Any], events: Any,
        world: dict[str, dict[str, Any]] | None = None,
        runtime_world: RuntimeWorld | None = None,
        behavior_runners: dict[str, Any] | None = None,
        project_root: str | Path | None = None,
    ) -> None:
        self.name = name
        self.obj = obj
        self._events = events
        self._world = world if world is not None else {name: obj}
        self.runtime_world = runtime_world or RuntimeWorld(self._world)
        self._behavior_runners = behavior_runners
        self._project_root = Path(project_root or Path.cwd()).resolve()
        self._input: dict[str, bool] = {}
        self._previous_input: dict[str, bool] = {}
        self.animator = PlayAnimatorAPI(obj)
        self.behavior = PlayBehaviorAPI(obj)
        self.dialogue = PlayDialogueAPI(obj)

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
        return self.obj.setdefault("_logic_state", {})

    @property
    def grounded(self) -> bool:
        return bool(self.obj.get("_grounded", False))

    @property
    def value(self) -> float:
        try:
            ui = self.obj.get("ui")
            if isinstance(ui, dict) and "value" in ui and ui["value"] is not None:
                return float(ui["value"])
            if "value" in self.obj and self.obj["value"] is not None:
                return float(self.obj["value"])
            state_val = self.obj.get("_logic_state", {}).get("value")
            if state_val is not None:
                return float(state_val)
        except (TypeError, ValueError):
            pass
        return 100.0

    @value.setter
    def value(self, val: float) -> None:
        num = float(val)
        ui = self.obj.get("ui")
        if isinstance(ui, dict):
            ui["value"] = num
        self.obj["value"] = num
        self.obj.setdefault("_logic_state", {})["value"] = num

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

    def is_key_pressed(self, name: str) -> bool:
        """Check if key is currently pressed (same as key(), for compatibility)."""
        return self.key(name)

    def axis(self, negative: str, positive: str) -> int:
        return int(self.key(positive)) - int(self.key(negative))

    def get_touch_input(self) -> dict[str, Any]:
        """Return current touch input state (placeholder for mobile support)."""
        return self.obj.get("_touch_input", {})

    def get_swipe_input(self) -> dict[str, Any]:
        """Return current swipe gesture state (placeholder for mobile support)."""
        return self.obj.get("_swipe_input", {})

    def get_pinch_input(self) -> dict[str, Any]:
        """Return current pinch/zoom gesture state (placeholder for mobile support)."""
        return self.obj.get("_pinch_input", {})

    def move(self, dx: float, dy: float = 0.0) -> None:
        self.x += float(dx)
        self.y += float(dy)

    def move_y(self, dy: float) -> None:
        self.y += float(dy)

    def override_physics_axis(self, axis: str) -> None:
        """Evita que a gravidade desfaça um movimento visual controlado neste frame."""
        self.obj.setdefault("_logic_motion_axes", set()).add(str(axis).lower())

    def jump(self, force: float = 420.0) -> None:
        self.obj["_jump_requested"] = True
        self.obj["_jump_force"] = float(force)

    def find(self, tag: str) -> "PlayLogicAPI | None":
        wanted = str(tag).lower()
        for name, obj in self._world.items():
            if obj is self.obj or not bool(obj.get("active", True)):
                continue
            if str(obj.get("tag", obj.get("name", ""))).lower() == wanted or str(name).lower() == wanted:
                return PlayLogicAPI(name, obj, self._events, self._world, self.runtime_world, self._behavior_runners, self._project_root)
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
    ) -> "PlayLogicAPI":
        """Cria um objeto temporário na cena atual e devolve sua referência."""
        obj = self.runtime_world.create_object(
            name=name, x=x, y=y, width=width, height=height,
            color=color, texture=texture, tag=tag,
        )
        self.log(f"objeto criado: {obj['name']}")
        return PlayLogicAPI(str(obj["name"]), obj, self._events, self._world, self.runtime_world, self._behavior_runners, self._project_root)

    def create_object_from_pool(self, pool_key: str, **values: Any) -> "PlayLogicAPI":
        obj = self.runtime_world.create_object(pool_key=f"logic:{pool_key}", **values)
        self.log(f"objeto criado/reutilizado: {obj['name']}")
        return PlayLogicAPI(str(obj["name"]), obj, self._events, self._world, self.runtime_world, self._behavior_runners, self._project_root)

    def create_prefab(
        self, path: str, x: float | None = None, y: float | None = None, **options: Any
    ) -> "PlayLogicAPI":
        obj = self.runtime_world.instantiate_prefab(path, x=x, y=y, **options)
        self.log(f"prefab criado: {obj['name']}")
        return PlayLogicAPI(str(obj["name"]), obj, self._events, self._world, self.runtime_world, self._behavior_runners, self._project_root)

    def create_prefab_from_pool(
        self, path: str, x: float | None, y: float | None, pool_key: str, **options: Any
    ) -> "PlayLogicAPI":
        obj = self.runtime_world.instantiate_prefab(
            path, x=x, y=y, pool_key=f"logic:{pool_key}", **options
        )
        self.log(f"prefab criado/reutilizado: {obj['name']}")
        return PlayLogicAPI(str(obj["name"]), obj, self._events, self._world, self.runtime_world, self._behavior_runners, self._project_root)

    def prefab_parameter(self, name: str, default: Any = None) -> Any:
        """Lê uma propriedade exposta recebida na criação desta instância."""
        values = self.obj.get("prefab_parameters")
        return deepcopy(values.get(str(name), default)) if isinstance(values, dict) else deepcopy(default)

    def clone_object(self, other: "PlayLogicAPI", name: str = "") -> "PlayLogicAPI":
        source = other.obj if isinstance(other, PlayLogicAPI) else self.obj
        obj = self.runtime_world.clone_object(source, name)
        return PlayLogicAPI(str(obj["name"]), obj, self._events, self._world, self.runtime_world, self._behavior_runners, self._project_root)

    def clone_object_from_pool(self, other: "PlayLogicAPI", name: str, pool_key: str) -> "PlayLogicAPI":
        source = other.obj if isinstance(other, PlayLogicAPI) else self.obj
        obj = self.runtime_world.clone_object(source, name, pool_key)
        return PlayLogicAPI(str(obj["name"]), obj, self._events, self._world, self.runtime_world, self._behavior_runners, self._project_root)

    def can_spawn(self, spawn_group: str, maximum: int = 0) -> bool:
        return self.runtime_world.can_spawn(spawn_group, maximum)

    def configure_spawned(
        self,
        created: "PlayLogicAPI",
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

    def distance_to(self, other: "PlayLogicAPI") -> float:
        return math.hypot(other.x - self.x, other.y - self.y)

    def play_animation(self, clip_name: str) -> None:
        self.obj.setdefault("logic_events", []).append({"command": "play_animation", "value": clip_name})

    def stop_animation(self) -> None:
        self.obj.setdefault("logic_events", []).append({"command": "stop_animation", "value": None})

    @property
    def current_animation(self) -> str:
        return str(self.obj.get("_current_animation_name", "Nenhum"))

    def send(self, command: str, value: Any = None) -> None:
        self.obj.setdefault("logic_events", []).append({"command": str(command), "value": value})

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

    def set_ui_progress(self, object_name: str, value: float, maximum: float = 100.0) -> None:
        """Atualiza uma barra de progresso nativa pelo nome na Hierarchy."""
        self.send("set_ui_progress", {
            "object": str(object_name), "value": float(value), "max_value": float(maximum),
        })

    def restart(self) -> None:
        """Restaura o snapshot capturado quando o Play Mode começou."""
        self.send("restart_scene")

    def load_scene(self, scene_path: str) -> bool:
        """Load a new scene by path (e.g., 'Assets/Scenes/Level1.zscene')."""
        if not scene_path:
            return False
        self.send("load_scene", {"path": str(scene_path)})
        return True

    def change_scene(self, scene_path: str) -> bool:
        """Unload current scene and load new scene."""
        return self.load_scene(scene_path)

    def get_scene_name(self) -> str:
        """Get current scene name."""
        scene_data = self.obj.get("_scene", {})
        return str(scene_data.get("name", "Unknown"))

    def push_scene(self, scene_path: str) -> bool:
        """Push a new scene onto the stack (keep current scene paused)."""
        if not scene_path:
            return False
        self.send("push_scene", {"path": str(scene_path)})
        return True

    def pop_scene(self) -> bool:
        """Pop current scene and return to previous scene."""
        self.send("pop_scene")
        return True

    def save_game(self, slot_name: str) -> bool:
        """Save current game state to slot."""
        if not slot_name:
            return False
        self.send("save_game", {"slot_name": str(slot_name)})
        return True

    def load_game(self, slot_name: str) -> bool:
        """Load game state from slot."""
        if not slot_name:
            return False
        self.send("load_game", {"slot_name": str(slot_name)})
        return True

    def save_exists(self, slot_name: str) -> bool:
        """Check if save slot exists (pure getter)."""
        if not slot_name:
            return False
        from engine.core.save_manager import get_save_manager
        manager = get_save_manager()
        return manager.save_exists(str(slot_name))

    def delete_save(self, slot_name: str) -> bool:
        """Delete save slot."""
        if not slot_name:
            return False
        self.send("delete_save", {"slot_name": str(slot_name)})
        return True

    def destroy(self) -> None:
        """Desativa o objeto no Play Mode atual."""
        self.runtime_world.destroy_object(self.obj)

    def destroy_object(self, target_name: str) -> None:
        """Desativa um objeto pelo nome ou pela tag no Play Mode atual."""
        target = self.find(target_name)
        if target is not None:
            self.runtime_world.destroy_object(target.obj)
        else:
            obj = self._world.get(str(target_name))
            if obj is not None:
                self.runtime_world.destroy_object(obj)

    def camera_follow(self, target: str, smooth_time: float = 0.1) -> None:
        """Start camera following a target object."""
        self.obj.setdefault("_camera_state", {})["follow_target"] = str(target)
        self.obj["_camera_state"]["smooth_time"] = float(smooth_time)

    def camera_stop_follow(self) -> None:
        """Stop camera follow if active."""
        self.obj.setdefault("_camera_state", {})["follow_target"] = None

    def camera_shake(self, duration: float = 0.5, intensity: float = 0.1, frequency: float = 1.0) -> None:
        """Start camera shake animation."""
        self.obj.setdefault("_camera_state", {})["shake"] = {
            "duration": float(duration),
            "intensity": float(intensity),
            "frequency": float(frequency),
            "elapsed": 0.0,
        }

    def camera_set_zoom(self, zoom: float, duration: float = 0.0) -> None:
        """Set camera zoom level."""
        zoom = max(0.1, float(zoom))
        if duration > 0:
            self.obj.setdefault("_camera_state", {})["zoom_tween"] = {
                "target_zoom": zoom,
                "duration": float(duration),
                "elapsed": 0.0,
            }
        else:
            self.obj.setdefault("_camera_state", {})["zoom"] = zoom

    def camera_look_at(self, x: float, y: float, duration: float = 0.5) -> None:
        """Pan camera to look at a world position."""
        self.obj.setdefault("_camera_state", {})["look_at"] = {
            "target_x": float(x),
            "target_y": float(y),
            "duration": float(duration),
            "elapsed": 0.0,
        }

    def get_camera_position(self) -> tuple[float, float]:
        """Get current camera position (pure getter)."""
        state = self.obj.get("_camera_state", {})
        if "position" in state:
            return (float(state["position"][0]), float(state["position"][1]))
        return (0.0, 0.0)

    def get_camera_zoom(self) -> float:
        """Get current camera zoom level (pure getter)."""
        state = self.obj.get("_camera_state", {})
        return float(state.get("zoom", 1.0))

    def log(self, message: str) -> None:
        _send(self._events, {"type": "runtime_log", "level": "INFO", "message": f"{self.name}: {message}"})

    def _emit_runtime_log(self, level: str, message: str) -> None:
        _send(self._events, {"type": "runtime_log", "level": str(level), "message": str(message)})


def _send(events: Any, payload: dict[str, Any]) -> None:
    if events is None:
        return
    try:
        events.put_nowait(payload)
    except Exception:
        pass

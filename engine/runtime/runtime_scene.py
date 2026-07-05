from __future__ import annotations

from typing import Any

from engine.physics.physics import Physics
from engine.physics.physics_world import PhysicsWorld
from engine.runtime.clone import clone_game_object
from engine.runtime.script_runtime import ScriptRuntime


class RuntimeScene:
    """Isolated Play Mode scene built from an editor scene."""

    def __init__(self, editor_scene: Any) -> None:
        self.editor_scene = editor_scene
        self.scene = type(editor_scene)()
        self.scene.start()
        self.name = f"{getattr(editor_scene, 'name', 'Scene')} (Runtime)"
        self.playing = True
        self.script_runtime = ScriptRuntime(self)
        self.physics_world = PhysicsWorld(self)
        self._runtime_started = False
        self._runtime_started_components: list[Any] = []
        self.editor_to_runtime: dict[str, Any] = {}
        self.runtime_to_editor: dict[str, Any] = {}
        self._clear_started_scene()
        self._clone_editor_objects()
        self._copy_scene_state()

    def _clear_started_scene(self) -> None:
        for obj in list(getattr(self.scene, "editable_objects", [])):
            if hasattr(self.scene, "_remove_go"):
                self.scene._remove_go(obj)
            elif obj in getattr(self.scene, "game_objects", []):
                self.scene.game_objects.remove(obj)
                obj.scene = None
        if hasattr(self.scene, "editable_objects"):
            self.scene.editable_objects.clear()
        if hasattr(self.scene, "selected_index"):
            self.scene.selected_index = -1

    def _clone_editor_objects(self) -> None:
        for editor_obj in list(getattr(self.editor_scene, "editable_objects", [])):
            runtime_obj = clone_game_object(editor_obj)
            self.editor_to_runtime[str(editor_obj.id)] = runtime_obj
            self.runtime_to_editor[str(runtime_obj.id)] = editor_obj
            if hasattr(self.scene, "_add_go"):
                self.scene._add_go(runtime_obj)
            else:
                self.scene.game_objects.append(runtime_obj)
                runtime_obj.scene = self.scene
            self.scene.editable_objects.append(runtime_obj)

    def _copy_scene_state(self) -> None:
        self.scene.name = self.name
        self.scene.playing = True
        if hasattr(self.editor_scene, "selected_index"):
            self.scene.selected_index = int(getattr(self.editor_scene, "selected_index", -1))
        for attr in ("show_grid", "grid_size", "show_scale_handles"):
            if hasattr(self.editor_scene, attr):
                setattr(self.scene, attr, getattr(self.editor_scene, attr))

    @property
    def game_objects(self) -> list[Any]:
        return self.scene.game_objects

    @property
    def editable_objects(self) -> list[Any]:
        return self.scene.editable_objects

    @property
    def selected_index(self) -> int:
        return int(getattr(self.scene, "selected_index", -1))

    @selected_index.setter
    def selected_index(self, value: int) -> None:
        self.scene.selected_index = int(value)

    def runtime_for_editor(self, obj: Any) -> Any | None:
        if obj is None:
            return None
        return self.editor_to_runtime.get(str(getattr(obj, "id", "")))

    def editor_for_runtime(self, obj: Any) -> Any | None:
        if obj is None:
            return None
        return self.runtime_to_editor.get(str(getattr(obj, "id", "")))

    def _iter_runtime_objects(self) -> list[Any]:
        ordered: list[Any] = []

        def visit(obj: Any, parent_active: bool = True) -> None:
            inherited_active = parent_active and bool(getattr(obj, "active", True))
            ordered.append((obj, inherited_active))
            for child in getattr(obj, "children", []):
                visit(child, inherited_active)

        for obj in list(getattr(self.scene, "editable_objects", [])):
            visit(obj, True)
        return ordered

    def _iter_enabled_runtime_components(self) -> list[Any]:
        components: list[Any] = []
        for obj, active in self._iter_runtime_objects():
            if not active:
                continue
            for component in getattr(obj, "components", []):
                if bool(getattr(component, "enabled", True)):
                    components.append(component)
        return components

    def start_runtime(self) -> None:
        if self._runtime_started:
            return
        self._runtime_started = True
        self._runtime_started_components.clear()
        components = self._iter_enabled_runtime_components()
        self.physics_world.build_from_scene(self)
        Physics.bind_world(self.physics_world)
        self.script_runtime.start(components)
        for component in components:
            component.on_runtime_start()
            self._runtime_started_components.append(component)

    def update_runtime(self, delta_time: float) -> None:
        if not self._runtime_started:
            return
        for component in self._iter_enabled_runtime_components():
            if component in self._runtime_started_components:
                component.on_runtime_update(float(delta_time))
        self.script_runtime.update(float(delta_time))

    def stop_runtime(self) -> None:
        if not self._runtime_started:
            return
        for component in list(reversed(self._runtime_started_components)):
            component.on_runtime_stop()
        self.script_runtime.stop()
        self._runtime_started_components.clear()
        self._runtime_started = False

    def update(self, dt: float) -> None:
        self.update_runtime(dt)
        self.physics_world.step()
        self.scene.update(dt)

    def draw(self, screen: Any) -> None:
        self.scene.draw(screen)

    def handle_event(self, event: Any) -> None:
        self.scene.handle_event(event)

    def destroy(self) -> None:
        self.stop_runtime()
        for obj in list(getattr(self.scene, "editable_objects", [])):
            if hasattr(self.scene, "_remove_go"):
                self.scene._remove_go(obj)
            elif obj in getattr(self.scene, "game_objects", []):
                self.scene.game_objects.remove(obj)
                obj.scene = None
        self.scene.editable_objects.clear()
        Physics.unbind_world(self.physics_world)
        self.physics_world.clear()
        self.editor_to_runtime.clear()
        self.runtime_to_editor.clear()
        self.playing = False
        self.scene.playing = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self.scene, name)

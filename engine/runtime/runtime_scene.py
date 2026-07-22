from __future__ import annotations

from typing import Any

from engine.physics.physics import Physics
from engine.physics.physics_world import PhysicsWorld
from engine.runtime.clone import clone_game_object
from engine.runtime.lifecycle_scheduler import LifecycleEntry, LifecycleScheduler
from engine.runtime.script_runtime import ScriptRuntime
from engine.time import Time
from engine.ui.ui_renderer import UIRenderer


class RuntimeScene:
    """Isolated Play Mode scene built from an editor scene."""

    def __init__(self, editor_scene: Any) -> None:
        self.editor_scene = editor_scene
        self.scene = type(editor_scene)()
        self.scene.start()
        self.name = f"{getattr(editor_scene, 'name', 'Scene')} (Runtime)"
        self.playing = True
        self.lifecycle = LifecycleScheduler(fixed_delta_time=Time.fixed_delta_time)
        self.script_runtime = ScriptRuntime(self, scheduler=self.lifecycle)
        self.physics_world = PhysicsWorld(self)
        self.ui_renderer = UIRenderer()
        self._runtime_started = False
        self._runtime_started_components: list[Any] = []
        self.editor_to_runtime: dict[str, Any] = {}
        self.runtime_to_editor: dict[str, Any] = {}
        self._clear_started_scene()
        self._clone_editor_objects()
        self._copy_scene_state()

    def _clear_started_scene(self) -> None:
        objs = getattr(self.scene, "editable_objects", None)
        if objs is None:
            objs = getattr(self.scene, "game_objects", [])
        for obj in list(objs):
            try:
                obj.destroy()
            except Exception:
                pass
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
        objs = getattr(self.editor_scene, "editable_objects", None)
        if objs is None:
            objs = getattr(self.editor_scene, "game_objects", [])
        for editor_obj in list(objs):
            runtime_obj = clone_game_object(editor_obj)
            self.editor_to_runtime[str(editor_obj.id)] = runtime_obj
            self.runtime_to_editor[str(runtime_obj.id)] = editor_obj
            if hasattr(self.scene, "_add_go"):
                self.scene._add_go(runtime_obj)
            else:
                self.scene.game_objects.append(runtime_obj)
                runtime_obj.scene = self.scene
            if hasattr(self.scene, "editable_objects"):
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

        objs = getattr(self.scene, "editable_objects", None)
        if objs is None:
            objs = getattr(self.scene, "game_objects", [])
        for obj in list(objs):
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

    def _call_component_hook(self, component: Any, hook_name: str, *args: Any) -> bool:
        """Call a runtime lifecycle hook only when the component supports it."""
        hook = getattr(component, hook_name, None)
        if not callable(hook):
            return False
        hook(*args)
        return True

    def start_runtime(self) -> None:
        if self._runtime_started:
            return

        # Limpa o CameraManager antes do Play para isolar câmeras de edições ou execuções passadas
        from engine.graphics.camera_manager import CameraManager
        CameraManager.clear()

        # Limpa o AudioManager antes do Play para isolar áudio
        from engine.audio import AudioManager
        AudioManager.clear()

        self._runtime_started = True
        self._runtime_started_components.clear()
        components = self._iter_enabled_runtime_components()

        # Se não existir nenhuma câmera, cria uma câmera padrão no runtime
        from engine.graphics.camera import Camera
        has_camera = any(self._component_type_name(comp) == "Camera" for comp in components)
        if not has_camera:
            from engine.game_object import GameObject
            fallback_go = GameObject("Default Runtime Camera")
            fallback_go.runtime_hidden = True
            fallback_go.add_component(Camera())
            if hasattr(self.scene, "_add_go"):
                self.scene._add_go(fallback_go)
            else:
                self.scene.game_objects.append(fallback_go)
                fallback_go.scene = self.scene
            if hasattr(self.scene, "editable_objects"):
                self.scene.editable_objects.append(fallback_go)

            for comp in fallback_go.components:
                if comp not in components:
                    components.append(comp)

        # Se não existir nenhum AudioListener, cria um padrão em runtime
        from engine.audio import AudioListener
        has_listener = any(self._component_type_name(comp) == "AudioListener" for comp in components)
        if not has_listener:
            from engine.game_object import GameObject
            fallback_listener_go = GameObject("Default Audio Listener")
            fallback_listener_go.runtime_hidden = True
            fallback_listener_go.add_component(AudioListener())
            if hasattr(self.scene, "_add_go"):
                self.scene._add_go(fallback_listener_go)
            else:
                self.scene.game_objects.append(fallback_listener_go)
                fallback_listener_go.scene = self.scene
            if hasattr(self.scene, "editable_objects"):
                self.scene.editable_objects.append(fallback_listener_go)

            for comp in fallback_listener_go.components:
                if comp not in components:
                    components.append(comp)

        self.physics_world.build_from_scene(self)
        Physics.bind_world(self.physics_world)
        self.script_runtime.start(components)
        for component in components:
            self.lifecycle.register(
                LifecycleEntry(
                    key=("component", id(component)),
                    enabled=lambda component=component: bool(getattr(component, "enabled", True)),
                    start=lambda component=component: self._call_component_hook(component, "on_runtime_start"),
                    update=lambda dt, component=component: self._call_component_hook(
                        component, "on_runtime_update", dt
                    ),
                    fixed_update=lambda dt, component=component: self._call_component_hook(
                        component, "on_runtime_fixed_update", dt
                    ),
                    late_update=lambda dt, component=component: self._call_component_hook(
                        component, "on_runtime_late_update", dt
                    ),
                    stop=lambda component=component: self._call_component_hook(component, "on_runtime_stop"),
                )
            )
            self._runtime_started_components.append(component)
        self.lifecycle.start()
        AudioManager._sources = [comp for comp in components if comp.__class__.__name__ == "AudioSource"]
        AudioManager._listeners = [comp for comp in components if comp.__class__.__name__ == "AudioListener"]

    def update_runtime(self, delta_time: float) -> None:
        if not self._runtime_started:
            return
        self.lifecycle.update(float(delta_time))

    def stop_runtime(self) -> None:
        if not self._runtime_started:
            return
        self.lifecycle.stop()
        self.script_runtime.instances.clear()
        self.lifecycle.clear()
        self._runtime_started_components.clear()
        self._runtime_started = False
        from engine.graphics.camera_manager import CameraManager
        CameraManager.clear()
        from engine.audio import AudioManager
        AudioManager.clear()

    def _component_type_name(self, component: Any) -> str:
        return str(getattr(component, "type_name", getattr(component, "component_type", type(component).__name__)))

    def update(self, dt: float) -> None:
        dt = float(dt)
        self.update_runtime(dt)
        self.lifecycle.run_fixed_updates(dt, self.physics_world.step)
        self.lifecycle.late_update(dt)
        self.scene.update(dt)

    def draw(self, screen: Any) -> None:
        self.draw_background(screen)
        self.draw_content(screen)

    def _scene_supports_split_background(self) -> bool:
        """Só separa cenas que mantêm o contrato canônico ou o implementam."""
        from engine.core.scene import Scene
        scene_type = type(self.scene)
        return scene_type.draw is Scene.draw or "draw_content" in scene_type.__dict__

    def draw_background(self, screen: Any) -> None:
        from engine.graphics.camera import Camera
        main_cam = Camera.main
        if main_cam:
            screen.fill(main_cam.clear_color)
        else:
            screen.fill((30, 30, 30))
        if self._scene_supports_split_background():
            self.scene.draw_background(screen)

    def draw_content(self, screen: Any) -> None:
        """Desenha a cena sem limpar o framebuffer nem repetir seu fundo.

        Mantém ``draw()`` totalmente compatível e permite que uma pipeline
        externa assuma a responsabilidade pelo background. Cenas antigas que
        sobrescrevem apenas ``draw()`` continuam no caminho integral.
        """
        if self._scene_supports_split_background():
            self.scene.draw_content(screen)
        else:
            self.scene.draw(screen)
        self.ui_renderer.render(self, screen)

    def handle_event(self, event: Any) -> None:
        self.scene.handle_event(event)

    def destroy(self) -> None:
        self.stop_runtime()
        objs = getattr(self.scene, "editable_objects", None)
        if objs is None:
            objs = getattr(self.scene, "game_objects", [])
        for obj in list(objs):
            try:
                obj.destroy()
            except Exception:
                pass
            if hasattr(self.scene, "_remove_go"):
                self.scene._remove_go(obj)
            elif obj in getattr(self.scene, "game_objects", []):
                self.scene.game_objects.remove(obj)
                obj.scene = None
        if hasattr(self.scene, "editable_objects"):
            self.scene.editable_objects.clear()
        Physics.unbind_world(self.physics_world)
        self.physics_world.clear()
        self.editor_to_runtime.clear()
        self.runtime_to_editor.clear()
        self.playing = False
        self.scene.playing = False

    def __getattr__(self, name: str) -> Any:
        return getattr(self.scene, name)

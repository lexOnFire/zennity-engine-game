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
        self._compile_and_attach_ui()  # Phase 4C: Auto-compile Scene.ui if present
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

    def _compile_and_attach_ui(self) -> None:
        """Phase 4C: Load and compile Scene.ui if present.

        If editor_scene has a 'ui' field referencing a .zui asset:
        1. Load the .zui file with validation
        2. Compile authoring widgets to runtime components
        3. Create GameObjects for each compiled widget
        4. Attach to scene (will be cloned to runtime in _clone_editor_objects)
        """
        from pathlib import Path
        from engine.ui.asset_loader import UIAssetLoader, UIAssetLoaderError
        from engine.ui.runtime_compiler import UIRuntimeCompiler, UICompilerError
        from engine.ui.runtime_components import (
            ProgressBarComponent,
            LabelComponent,
            ImageComponent,
            ButtonComponent,
        )
        from engine.game_object import GameObject

        # Check if scene has UI asset reference
        ui_asset_path = getattr(self.editor_scene, "ui", None)
        if not ui_asset_path:
            return  # No UI asset - proceed normally

        ui_asset_path = str(ui_asset_path).strip()
        if not ui_asset_path:
            return  # Empty UI path - proceed normally

        try:
            import logging
            logger = logging.getLogger(__name__)

            logger.info(f"[UI] Loading scene.ui: {ui_asset_path}")

            # 1. Load .zui asset with validation
            loader = UIAssetLoader(project_root=Path.cwd())
            ui_document = loader.load(ui_asset_path)
            logger.info(f"[UI] Document loaded")

            # 2. Compile to runtime widgets
            compiler = UIRuntimeCompiler()
            compiled_widgets = compiler.compile(ui_document)
            logger.info(f"[UI] Compiled widgets: {len(compiled_widgets)}")
            for i, w in enumerate(compiled_widgets):
                logger.info(f"[UI]   [{i}] type={w.get('type')}, name={w.get('widget_name')}")

            # 3. Use existing Canvas container or create new one
            # CRITICAL: If scene already has MenuUI with Canvas, reuse it (preserves editor_data/logic_graphs)
            ui_canvas = None
            objs = getattr(self.scene, "editable_objects", getattr(self.scene, "game_objects", []))
            for obj in list(objs):
                if hasattr(obj, "name") and obj.name == "MenuUI":
                    # Found existing MenuUI - use it as UI container
                    ui_canvas = obj
                    logger.info(f"[UI] Using existing MenuUI as canvas container")
                    break

            if ui_canvas is None:
                # No existing canvas, create new one
                ui_canvas = GameObject("__UICanvas__")
                logger.info(f"[UI] Created new UICanvas")
                ui_canvas.runtime_hidden = True
                if hasattr(self.scene, "_add_go"):
                    self.scene._add_go(ui_canvas)
                else:
                    self.scene.game_objects.append(ui_canvas)
                    ui_canvas.scene = self.scene
                if hasattr(self.scene, "editable_objects"):
                    self.scene.editable_objects.append(ui_canvas)

            # 4. Create runtime components for each compiled widget
            created_count = 0
            for widget_def in compiled_widgets:
                if not widget_def:  # Panels return None
                    logger.debug(f"[UI] Skipping None widget (panel)")
                    continue

                widget_type = widget_def.get("type")
                widget_name = widget_def.get("widget_name")
                properties = widget_def.get("properties", {})
                logger.info(f"[UI] Creating widget: {widget_name} ({widget_type})")

                # Create GameObject to hold the UI component
                widget_go = GameObject(widget_name)
                component = None

                # Extract common properties
                x = float(properties.get("x", 0.0))
                y = float(properties.get("y", 0.0))
                width = float(properties.get("width", 100.0))
                height = float(properties.get("height", 100.0))
                visible = bool(properties.get("visible", True))
                z_order = int(properties.get("z_order", 0))

                if widget_type == "ProgressBarComponent":
                    component = ProgressBarComponent(
                        value=properties.get("value", 50.0),
                        max_value=properties.get("max_value", 100.0),
                        x=x, y=y, width=width, height=height,
                        visible=visible, z_order=z_order
                    )
                elif widget_type == "LabelComponent":
                    component = LabelComponent(
                        text=properties.get("text", ""),
                        x=x, y=y, width=width, height=height,
                        visible=visible, z_order=z_order
                    )
                elif widget_type == "ImageComponent":
                    component = ImageComponent(
                        sprite_path=properties.get("texture_path", ""),
                        x=x, y=y, width=width, height=height,
                        visible=visible, z_order=z_order
                    )
                elif widget_type == "ButtonComponent":
                    component = ButtonComponent(
                        text=properties.get("text", "Button"),
                        x=x, y=y, width=width, height=height,
                        visible=visible, z_order=z_order,
                        interactable=bool(properties.get("interactable", True))
                    )
                else:
                    # Unknown widget type - skip with warning
                    import logging
                    logging.warning(f"Unsupported widget type in UI: {widget_type}")
                    continue

                if component:
                    component.widget_name = widget_name
                    widget_go.add_component(component)
                    logger.info(f"[UI] Component attached: {widget_name}")
                    created_count += 1

                # Attach to UICanvas using canonical API
                ui_canvas.add_child(widget_go)
                if hasattr(self.scene, "_add_go"):
                    self.scene._add_go(widget_go)
                else:
                    self.scene.game_objects.append(widget_go)
                if hasattr(self.scene, "editable_objects"):
                    self.scene.editable_objects.append(widget_go)
                logger.info(f"[UI] Widget attached to scene: {widget_name}")

            logger.info(f"[UI] UI RENDER PIPELINE COMPLETE: {created_count}/{len(compiled_widgets)} widgets created")

        except (UIAssetLoaderError, UICompilerError) as e:
            # Diagnostic: Include scene context in error
            scene_name = getattr(self.editor_scene, "name", "Unknown")
            raise RuntimeError(
                f"Failed to compile UI for scene '{scene_name}':\n"
                f"Asset path: {ui_asset_path}\n"
                f"Error: {e}"
            )
        except Exception as e:
            scene_name = getattr(self.editor_scene, "name", "Unknown")
            raise RuntimeError(
                f"Unexpected error compiling UI for scene '{scene_name}':\n"
                f"Asset path: {ui_asset_path}\n"
                f"Error: {e}"
            )

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

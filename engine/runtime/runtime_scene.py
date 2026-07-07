from __future__ import annotations

import warnings
from typing import Any

from engine.physics.physics import Physics
from engine.physics.physics_world import PhysicsWorld
from engine.runtime.clone import clone_game_object
from engine.runtime.script_runtime import ScriptRuntime
from engine.ui.ui_renderer import UIRenderer


class RuntimeScene:
    """Isolated Play Mode scene built from an editor scene.

    Ciclo correto:
        __init__  → clona objetos do editor (sem start() antecipado)
        start_runtime() → dispara on_runtime_start nos componentes
        update_runtime() / draw() por frame
        stop_runtime() → on_runtime_stop + cleanup
        destroy()  → remove todos os objetos e desbinda física
    """

    def __init__(self, editor_scene: Any) -> None:
        self.editor_scene = editor_scene
        # Cria a cena runtime do mesmo tipo, porém SEM chamar start()
        # antecipado — evita efeitos colaterais de dupla inicialização.
        self.scene = type(editor_scene).__new__(type(editor_scene))
        # Inicializa os atributos mínimos sem executar start()
        type(editor_scene).__init__(self.scene)
        self.name = f"{getattr(editor_scene, 'name', 'Scene')} (Runtime)"
        self.playing = True
        self.script_runtime = ScriptRuntime(self)
        self.physics_world = PhysicsWorld(self)
        self.ui_renderer = UIRenderer()
        self._runtime_started = False
        self._runtime_started_components: list[Any] = []
        self.editor_to_runtime: dict[str, Any] = {}
        self.runtime_to_editor: dict[str, Any] = {}
        self._clear_started_scene()
        self._clone_editor_objects()
        self._copy_scene_state()

    # ------------------------------------------------------------------
    # Construção do mundo runtime
    # ------------------------------------------------------------------

    def _clear_started_scene(self) -> None:
        """Remove quaisquer objetos criados pelo __init__ da cena."""
        objs = getattr(self.scene, "editable_objects", None)
        if objs is None:
            objs = getattr(self.scene, "game_objects", [])
        for obj in list(objs):
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
        """Clona todos os objetos raiz do editor para o mundo runtime."""
        objs = getattr(self.editor_scene, "editable_objects", None)
        if objs is None:
            objs = getattr(self.editor_scene, "game_objects", [])
        for editor_obj in list(objs):
            # Sempre clona, independente de active=False no editor
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
            self.scene.selected_index = int(
                getattr(self.editor_scene, "selected_index", -1)
            )
        for attr in ("show_grid", "grid_size", "show_scale_handles"):
            if hasattr(self.editor_scene, attr):
                setattr(self.scene, attr, getattr(self.editor_scene, attr))

    # ------------------------------------------------------------------
    # Propriedades proxy
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Mapeamento editor ↔ runtime
    # ------------------------------------------------------------------

    def runtime_for_editor(self, obj: Any) -> Any | None:
        if obj is None:
            return None
        return self.editor_to_runtime.get(str(getattr(obj, "id", "")))

    def editor_for_runtime(self, obj: Any) -> Any | None:
        if obj is None:
            return None
        return self.runtime_to_editor.get(str(getattr(obj, "id", "")))

    # ------------------------------------------------------------------
    # Iteradores internos
    # ------------------------------------------------------------------

    def _iter_runtime_objects(self) -> list[Any]:
        """Percorre toda a árvore de objetos com flag de active herdado."""
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

    # ------------------------------------------------------------------
    # Ciclo de vida Play / Stop
    # ------------------------------------------------------------------

    def start_runtime(self) -> None:
        """Inicializa o mundo runtime: câmera padrão, áudio, física, scripts."""
        if self._runtime_started:
            return

        from engine.graphics.camera_manager import CameraManager
        CameraManager.clear()
        from engine.audio import AudioManager
        AudioManager.clear()

        self._runtime_started = True
        self._runtime_started_components.clear()
        components = self._iter_enabled_runtime_components()

        # Câmera padrão
        from engine.graphics.camera import Camera
        has_camera = any(
            self._component_type_name(comp) == "Camera" for comp in components
        )
        if not has_camera:
            from engine.game_object import GameObject
            fallback_go = GameObject("Default Runtime Camera")
            fallback_go.runtime_hidden = True
            fallback_go.add_component(Camera())
            self._add_runtime_go(fallback_go)
            for comp in fallback_go.components:
                if comp not in components:
                    components.append(comp)

        # AudioListener padrão
        from engine.audio import AudioListener
        has_listener = any(
            self._component_type_name(comp) == "AudioListener" for comp in components
        )
        if not has_listener:
            from engine.game_object import GameObject
            fallback_go = GameObject("Default Audio Listener")
            fallback_go.runtime_hidden = True
            fallback_go.add_component(AudioListener())
            self._add_runtime_go(fallback_go)
            for comp in fallback_go.components:
                if comp not in components:
                    components.append(comp)

        self.physics_world.build_from_scene(self)
        Physics.bind_world(self.physics_world)
        self.script_runtime.start(components)

        for component in components:
            try:
                component.on_runtime_start()
                self._runtime_started_components.append(component)
            except Exception as exc:  # pragma: no cover
                warnings.warn(
                    f"[RuntimeScene] on_runtime_start falhou em "
                    f"{getattr(component, 'type_name', type(component).__name__)}: {exc}",
                    RuntimeWarning,
                    stacklevel=1,
                )

        AudioManager._sources = [
            c for c in components if c.__class__.__name__ == "AudioSource"
        ]
        AudioManager._listeners = [
            c for c in components if c.__class__.__name__ == "AudioListener"
        ]

    def _add_runtime_go(self, go: Any) -> None:
        """Adiciona um GO interno (câmera/listener padrão) ao mundo runtime."""
        if hasattr(self.scene, "_add_go"):
            self.scene._add_go(go)
        else:
            self.scene.game_objects.append(go)
            go.scene = self.scene
        if hasattr(self.scene, "editable_objects"):
            self.scene.editable_objects.append(go)

    def update_runtime(self, delta_time: float) -> None:
        if not self._runtime_started:
            return
        started_set = set(id(c) for c in self._runtime_started_components)
        for component in self._iter_enabled_runtime_components():
            if id(component) in started_set:
                try:
                    component.on_runtime_update(float(delta_time))
                except Exception as exc:  # pragma: no cover
                    warnings.warn(
                        f"[RuntimeScene] on_runtime_update erro: {exc}",
                        RuntimeWarning,
                        stacklevel=1,
                    )
        self.script_runtime.update(float(delta_time))

    def stop_runtime(self) -> None:
        """Para o runtime e destrói recursos — idempotente."""
        if not self._runtime_started:
            return
        for component in list(reversed(self._runtime_started_components)):
            try:
                component.on_runtime_stop()
            except Exception as exc:  # pragma: no cover
                warnings.warn(
                    f"[RuntimeScene] on_runtime_stop erro: {exc}",
                    RuntimeWarning,
                    stacklevel=1,
                )
        self.script_runtime.stop()
        self._runtime_started_components.clear()
        self._runtime_started = False
        from engine.graphics.camera_manager import CameraManager
        CameraManager.clear()
        from engine.audio import AudioManager
        AudioManager.clear()

    # ------------------------------------------------------------------
    # Frame loop
    # ------------------------------------------------------------------

    def update(self, dt: float) -> None:
        self.update_runtime(dt)
        self.physics_world.step()
        self.scene.update(dt)

    def draw(self, screen: Any) -> None:
        from engine.graphics.camera import Camera
        main_cam = Camera.main
        if main_cam:
            screen.fill(main_cam.clear_color)
        else:
            screen.fill((30, 30, 30))
        self.scene.draw(screen)
        self.ui_renderer.render(self, screen)

    def handle_event(self, event: Any) -> None:
        self.scene.handle_event(event)

    # ------------------------------------------------------------------
    # Destruição
    # ------------------------------------------------------------------

    def destroy(self) -> None:
        """Para o runtime e limpa toda a memória do mundo runtime."""
        self.stop_runtime()
        objs = getattr(self.scene, "editable_objects", None)
        if objs is None:
            objs = getattr(self.scene, "game_objects", [])
        for obj in list(objs):
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _component_type_name(self, component: Any) -> str:
        return str(
            getattr(
                component,
                "type_name",
                getattr(component, "component_type", type(component).__name__),
            )
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self.scene, name)

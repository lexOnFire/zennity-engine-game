"""Janela Pygame independente usada pelo experimento de viewport isolada."""
from __future__ import annotations

import os
import sys
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
    from editor.runtime.viewport_editor_view_commands import (
        ViewportEditorViewCommandHandler,
        ViewportEditorViewState,
    )
    from editor.runtime.viewport_edit_commands import ViewportEditCommandHandler
    from editor.runtime.viewport_play_commands import ViewportPlayCommandHandler, ViewportProcessState
    from editor.runtime.viewport_navigation_events import ViewportNavigationEventHandler, ViewportNavigationState
    from editor.runtime.viewport_transform_events import ViewportTransformEventHandler, ViewportTransformState
    from editor.runtime.viewport_tool_shortcuts import ViewportToolShortcutHandler
    from editor.runtime.viewport_overlay_renderer import ViewportOverlayRenderer
    from editor.runtime.viewport_sprite_renderer import ViewportSpriteRenderer
    from editor.runtime.viewport_physics_stepper import ViewportPhysicsStepper
    from editor.runtime.viewport_animation_updater import ViewportAnimationUpdater
    from editor.runtime.viewport_session_orchestrator import ViewportSessionOrchestrator
    from editor.runtime.viewport_logic_event_updater import ViewportLogicEventUpdater
    from editor.runtime.viewport_contact_processor import ViewportContactProcessor
    from editor.runtime.viewport_runtime_initializer import ViewportRuntimeInitializer
    from editor.runtime.viewport_asset_hydration import (
        hydrate_animation_asset_clips,
        hydrate_animator_controllers,
        hydrate_behavior_controllers,
        hydrate_dialogues,
        hydrate_logic_graphs,
        load_project_subgraph,
    )
    from editor.runtime.viewport_logic_api import PlayLogicAPI, _send
    from engine.animation.controller_asset import AnimatorControllerRuntime
    from engine.behavior.controller_asset import BehaviorControllerRunner
    from engine.logic.runtime import LogicGraphRuntime
    from engine.runtime.runtime_world import RuntimeWorld
except ModuleNotFoundError:  # Runtime autocontido criado pelo exportador.
    from .audio_playback_state import set_channels_paused
    from .native_ui import NativeUIRenderer, normalize_ui
    from .sprite_rendering import prepare_scrolling_sprite_surface, prepare_sprite_surface
    from .viewport_systems import AnimationPlaybackSystem, AudioPlaybackSystem, FixedStepScheduler, HudRuntimeSystem
    from .viewport_command_queue import ViewportCommandQueue
    from .viewport_control_commands import ViewportAudioCommandHandler, ViewportControlCommandHandler, ViewportControlSettings
    from .viewport_editor_view_commands import ViewportEditorViewCommandHandler, ViewportEditorViewState
    from .viewport_edit_commands import ViewportEditCommandHandler
    from .viewport_play_commands import ViewportPlayCommandHandler, ViewportProcessState
    from .viewport_navigation_events import ViewportNavigationEventHandler, ViewportNavigationState
    from .viewport_transform_events import ViewportTransformEventHandler, ViewportTransformState
    from .viewport_tool_shortcuts import ViewportToolShortcutHandler
    from .viewport_overlay_renderer import ViewportOverlayRenderer
    from .viewport_sprite_renderer import ViewportSpriteRenderer
    from .viewport_physics_stepper import ViewportPhysicsStepper
    from .viewport_animation_updater import ViewportAnimationUpdater
    from .viewport_session_orchestrator import ViewportSessionOrchestrator
    from .viewport_logic_event_updater import ViewportLogicEventUpdater
    from .viewport_contact_processor import ViewportContactProcessor
    from .viewport_runtime_initializer import ViewportRuntimeInitializer
    from .viewport_asset_hydration import (
        hydrate_animation_asset_clips,
        hydrate_animator_controllers,
        hydrate_behavior_controllers,
        hydrate_dialogues,
        hydrate_logic_graphs,
        load_project_subgraph,
    )
    from .viewport_logic_api import PlayLogicAPI, _send
    from .controller_asset import AnimatorControllerRuntime
    from .behavior_controller import BehaviorControllerRunner
    from .logic_runtime import LogicGraphRuntime
    from .runtime_world import RuntimeWorld


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


try:
    from editor.runtime.viewport_session_lifecycle import ViewportSessionLifecycleMixin
except ImportError:  # Self-contained exported runtime.
    from .viewport_session_lifecycle import ViewportSessionLifecycleMixin


class ViewportSession(ViewportSessionLifecycleMixin):
    """Refactored ViewportSession using composable controllers."""
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
        self.show_grid = True
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
        self.logic_modules = {}
        self.logic_apis = {}
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
        self.last_runtime_sync_ms = 0
        self.texture_cache = {}
        self.native_ui = NativeUIRenderer()
        self.command_queue = ViewportCommandQueue(self.commands)
        
        self.edit_commands = ViewportEditCommandHandler(
            self.objects, lambda event: _send(self.events, event),
            self.world_to_screen, self.screen_to_world, lambda: self.view_transform()[2]
        )
        self.control_commands = ViewportControlCommandHandler(self.forwarded_input)
        self.editor_view_commands = ViewportEditorViewCommandHandler(
            self.objects, lambda: self.screen.get_size()
        )
        self.audio_commands = ViewportAudioCommandHandler(
            self.objects, self.audio_channels, self.audio_sounds, lambda event: _send(self.events, event),
            self.start_audio_sources, self.stop_audio_sources, self.play_audio_file
        )
        self.runtime_initializer = ViewportRuntimeInitializer(
            self.objects, self.logic_modules, self.logic_apis, self.animator_controllers, self.behavior_runners,
            self.logic_runtimes, self.initialized_runtime_ids, self.animator_event_signatures, self.runtime_world,
            (
                hydrate_animation_asset_clips, hydrate_animator_controllers,
                hydrate_behavior_controllers, hydrate_dialogues, hydrate_logic_graphs,
            ),
            lambda name, obj: PlayLogicAPI(name, obj, self.events, self.objects, self.runtime_world),
            lambda path: load_project_subgraph(path, Path.cwd()),
            lambda event: _send(self.events, event), self.play_audio_file, Path.cwd()
        )
        
        self.play_commands = ViewportPlayCommandHandler(
            self.objects, self.logic_runtimes, self.logic_apis, lambda event: _send(self.events, event),
            self.resize_viewport, lambda: self.zoom,
            lambda value: set_channels_paused(self.audio_channels, value), self.stop_audio_sources,
            self.physics_scheduler.reset, self.hud_entries.clear, self.start_logic_with_config, self.stop_logic
        )
        self.navigation_events = ViewportNavigationEventHandler(
            self.pygame, self.objects, self.native_ui, lambda event: _send(self.events, event), self.screen_to_world
        )
        self.tool_shortcuts = ViewportToolShortcutHandler(
            self.pygame, lambda event: _send(self.events, event)
        )
        self.transform_events = ViewportTransformEventHandler(
            self.pygame, self.objects, lambda event: _send(self.events, event), self.world_to_screen
        )
        self.overlay_renderer = ViewportOverlayRenderer(self.pygame)
        self.sprite_renderer = ViewportSpriteRenderer(self.pygame, prepare_sprite_surface, prepare_scrolling_sprite_surface)
        self.physics_stepper = ViewportPhysicsStepper()
        self.animation_updater = ViewportAnimationUpdater(
            self.objects, self.animation_system, self.animator_controllers, self.animator_event_signatures,
            self.logic_modules,
            lambda name, obj: self.logic_apis.get(name) or PlayLogicAPI(name, obj, self.events, self.objects, self.runtime_world),
            self.dispatch_animation_state_hook, lambda event: _send(self.events, event)
        )
        self.session_orchestrator = ViewportSessionOrchestrator(
            self.objects, self.logic_runtimes, self.behavior_runners, self.logic_modules, self.logic_apis,
            self.animator_controllers, lambda: self.runtime_initializer.logic_event_bus, self.runtime_world, self.hud_entries,
            lambda event: _send(self.events, event), self.play_audio_file,
            lambda value: set_channels_paused(self.audio_channels, value), self.dispatch_animation_state_hook
        )
        self.logic_event_updater = ViewportLogicEventUpdater(
            self.objects, self.logic_modules, self.logic_apis, self.animator_controllers, self.hud_entries,
            normalize_ui, self.play_audio_file, self.dispatch_animation_state_hook,
            lambda event: _send(self.events, event)
        )
        self.contact_processor = ViewportContactProcessor(self.objects, self.active_contacts, self.dispatch_contact)

    def runtime_log(self, level, message):
        _send(self.events, {"type": "runtime_log", "level": level, "message": message})
        
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
                _send(self.events, {"type": "runtime_log", "level": "INFO", "message": f"{name}: Audio Source não inicia (Ao iniciar={bool(audio.get('autoplay'))}, arquivo={bool(audio.get('path'))})"})
                continue
            enabled += 1
            self.play_audio_file(name, str(audio["path"]), float(audio.get("volume", 1.0)), bool(audio.get("loop", False)))
        _send(self.events, {"type": "runtime_log", "level": "INFO", "message": f"Play processou {found} Audio Source(s); {enabled} iniciado(s)"})

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
        api = self.logic_apis.get(object_name) or PlayLogicAPI(object_name, obj, self.events, self.objects, self.runtime_world)
        for path, module in list(self.logic_modules.get(object_name, [])):
            hook = getattr(module, hook_name, None)
            if not callable(hook):
                continue
            try:
                hook(api, state_name)
            except Exception as exc:
                _send(self.events, {"type": "runtime_log", "level": "ERROR", "message": f"{object_name}:{path}:{hook_name}: {exc}"})
                
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
        for name in self.logic_modules:
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
                "renderer_enabled": bool(obj.get("renderer_enabled", True)),
                "render_layer": str(obj.get("render_layer", "Default")),
                "sort_order": int(obj.get("sort_order", 0)),
                "color": deepcopy(obj.get("color", (180, 180, 180))),
                "texture": str(obj.get("texture", "")),
                "collider": deepcopy(obj.get("collider"))
                if isinstance(obj.get("collider"), dict) else None,
                "rigidbody": deepcopy(obj.get("rigidbody"))
                if isinstance(obj.get("rigidbody"), dict) else None,
                "velocity_y": float(self.velocities_y.get(name, 0.0)),
                "grounded": bool(self.grounded.get(name, False)),
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
        game = self.logic_apis.get(name) or PlayLogicAPI(name, obj, self.events, self.objects, self.runtime_world)
        other = PlayLogicAPI(other_name, other_obj, self.events, self.objects, self.runtime_world)
        for path, module in list(self.logic_modules.get(name, [])):
            hook = getattr(module, hook_name, None)
            if not callable(hook):
                continue
            try:
                hook(game, other)
            except Exception as exc:
                _send(self.events, {"type": "runtime_log", "level": "ERROR", "message": f"{name}:{path}:{hook_name}: {exc}"})
                
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
                        "type": "runtime_log", "level": "ERROR",
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

    def start_logic_with_config(self, config):
        self.scene_blackboard_config = deepcopy(config)
        self.runtime_initializer.start(self.scene_blackboard_config)
        
    def stop_logic(self):
        self.runtime_initializer.stop(self.active_contacts)
        
    def restart_logic(self):
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
            editor_view_state = self.editor_view_commands.handle(
                command,
                ViewportEditorViewState(
                    self.selected_name,
                    self.camera_x,
                    self.camera_y,
                    self.zoom,
                    self.show_grid,
                ),
            )
            if editor_view_state is not None:
                self.selected_name = editor_view_state.selected_name
                self.camera_x = editor_view_state.camera_x
                self.camera_y = editor_view_state.camera_y
                self.zoom = editor_view_state.zoom
                self.show_grid = editor_view_state.show_grid
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
            shortcut_tool = self.tool_shortcuts.handle(
                event, playing=self.playing, view_mode=self.view_mode
            )
            if shortcut_tool is not None:
                if shortcut_tool != "delete":
                    self.active_tool = shortcut_tool
                continue
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

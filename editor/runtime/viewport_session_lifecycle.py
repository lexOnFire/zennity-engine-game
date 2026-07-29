"""Mixin de ciclo de vida, execução e teardown para ViewportSession."""

from __future__ import annotations

from typing import Any


def _send(queue: Any, message: dict[str, Any]) -> None:
    queue.put(message)


class ViewportSessionLifecycleMixin:
    """Isola renderização, step, sync_stats e teardown da ViewportSession."""

    def step(self) -> None:
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
            self.logic_trace_last_sent, debug_pause_requested, self.restart_requested = (
                self.session_orchestrator.update_logic(
                    input_state,
                    dt,
                    self.logic_trace_last_sent,
                    self.velocities_y,
                    self.grounded,
                    self.restart_requested,
                )
            )
            self.paused = self.paused or debug_pause_requested
            self.restart_requested = (
                self.script_updater.update(
                    input_state,
                    dt,
                    self.velocities_y,
                    self.grounded,
                )
                or self.restart_requested
            )
            self.session_orchestrator.update_behaviors(input_state, dt)
            self.session_orchestrator.finish_frame(dt, self.velocities_y, self.grounded)
            if self.restart_requested:
                self.session_orchestrator.restart(
                    self.edit_snapshot,
                    self.velocities_y,
                    self.grounded,
                    self.active_contacts,
                    self.stop_audio_sources,
                    self.stop_scripts,
                    self.physics_scheduler.reset,
                    self.restart_scripts,
                    self.start_audio_sources,
                )
                self.restart_requested = False
            physics_steps = self.physics_scheduler.consume(dt)
            motion_axes_by_name = {
                name: obj.pop("_logic_motion_axes", set()) for name, obj in self.objects.items()
            }
            self.physics_stepper.step(
                self.objects,
                self.velocities_y,
                self.grounded,
                motion_axes_by_name,
                physics_steps,
                self.fixed_physics_dt,
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

    def render(self) -> None:
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
        if self.view_mode == "scene" and self.show_grid:
            self.overlay_renderer.draw_scene(
                self.screen,
                self.objects,
                width,
                height,
                self.camera_x,
                self.camera_y,
                self.zoom,
                self.world_to_screen,
            )

        self.sprite_renderer.draw(
            self.screen,
            self.objects,
            view_mode=self.view_mode,
            selected_name=self.selected_name,
            active_tool=self.active_tool,
            render_zoom=self.view_transform()[2],
            world_to_screen=self.world_to_screen,
            overlay_renderer=self.overlay_renderer,
        )
        if self.view_mode == "game":
            self.native_ui.draw(self.objects, self.screen)
        if self.playing and self.hud_entries:
            self.overlay_renderer.draw_hud(self.screen, self.hud_entries, width, height)
        self.pygame.display.flip()

    def sync_stats(self) -> None:
        now_ms = self.pygame.time.get_ticks()
        if self.playing and now_ms - self.last_runtime_sync_ms >= 33:
            self.last_runtime_sync_ms = now_ms
            _send(
                self.events,
                {
                    "type": "runtime_objects",
                    "objects": self.runtime_object_snapshot(),
                    "selected": self.selected_name,
                },
            )
        if now_ms - self.last_stats_ms >= 500:
            self.last_stats_ms = now_ms
            runtime_mode = "PAUSE" if self.paused else ("PLAY" if self.playing else "EDIT")
            player_name, _player = self.controlled_object()
            world_stats = self.runtime_world.stats()
            _send(
                self.events,
                {
                    "type": "stats",
                    "fps": self.clock.get_fps(),
                    "objects": len(self.objects),
                    "mode": runtime_mode,
                    "view": self.view_mode.upper(),
                    "zoom": self.view_transform()[2],
                    "snap": self.snap_enabled,
                    "camera": (self.game_camera() or {}).get("name") if self.view_mode == "game" else "Editor",
                    "player": player_name,
                    "spawned": world_stats["created"],
                    "reused": world_stats["reused"],
                    "destroyed": world_stats["destroyed"],
                    "pooled": world_stats["pooled"],
                },
            )

    def teardown(self) -> bool:
        """Libera deterministicamente todos os recursos pertencentes à sessão."""
        if getattr(self, "_teardown_complete", False):
            return False
        self._teardown_complete = True
        self.running = False

        self.stop_scripts()
        self.audio_system.shutdown()
        tuple(self.command_queue.drain())
        self.native_ui.clear_caches()

        for collection_name in (
            "objects",
            "edit_snapshot",
            "velocities_y",
            "grounded",
            "scene_blackboard_config",
            "animator_event_signatures",
            "active_contacts",
            "forwarded_input",
            "texture_cache",
            "hud_entries",
        ):
            collection = getattr(self, collection_name, None)
            if hasattr(collection, "clear"):
                collection.clear()

        self.screen = None
        self.clock = None
        return True

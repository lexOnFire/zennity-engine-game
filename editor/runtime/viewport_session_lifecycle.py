"""Mixin de ciclo de vida, execução e teardown para ViewportSession."""

from __future__ import annotations

from typing import Any


def _send(queue: Any, message: dict[str, Any]) -> None:
    queue.put(message)


class ViewportSessionLifecycleMixin:
    """Isola renderização, step, sync_stats e teardown da ViewportSession."""

    def step(self) -> None:
        import time
        t_start = time.perf_counter()
        if not hasattr(self, "frame_categories"):
            self.frame_categories = {"physics": 0.0, "scripts": 0.0, "animation": 0.0, "audio": 0.0, "rendering": 0.0, "overhead": 0.0}
            self.frame_accumulators = {"physics": 0.0, "scripts": 0.0, "animation": 0.0, "audio": 0.0, "rendering": 0.0, "overhead": 0.0, "count": 0}

        width, height = self.screen.get_size()
        dt = self.clock.get_time() / 1000.0
        t_scripts = time.perf_counter()
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
                self.logic_event_updater.update(
                    input_state,
                    dt,
                    self.velocities_y,
                    self.grounded,
                )
                or self.restart_requested
            )
            self.behavior_trace_last_sent, _ = self.session_orchestrator.update_behaviors(input_state, dt, self.behavior_trace_last_sent)
            self.session_orchestrator.finish_frame(dt, self.velocities_y, self.grounded)
            if self.restart_requested:
                self.session_orchestrator.restart(
                    self.edit_snapshot,
                    self.velocities_y,
                    self.grounded,
                    self.active_contacts,
                    self.stop_audio_sources,
                    self.stop_logic,
                    self.physics_scheduler.reset,
                    self.restart_logic,
                    self.start_audio_sources,
                )
                self.restart_requested = False
            
            self.frame_categories["scripts"] = (time.perf_counter() - t_scripts) * 1000.0
            t_physics = time.perf_counter()
            
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
            
            self.frame_categories["physics"] = (time.perf_counter() - t_physics) * 1000.0
            t_anim = time.perf_counter()
            
            self.animation_updater.update(dt)
            
            self.frame_categories["animation"] = (time.perf_counter() - t_anim) * 1000.0
            
        for obj in self.objects.values():
                scroll = obj.get("_texture_scroll")
                if not isinstance(scroll, dict) or not scroll.get("enabled", False):
                    continue
                factor = max(0.0, float(scroll.get("parallax", 1.0)))
                scroll["offset_x"] = float(scroll.get("offset_x", 0.0)) + float(scroll.get("speed_x", 0.0)) * factor * dt
                scroll["offset_y"] = float(scroll.get("offset_y", 0.0)) + float(scroll.get("speed_y", 0.0)) * factor * dt
                
        if hasattr(self, "frame_categories"):
            self.frame_categories["overhead"] = (time.perf_counter() - t_start) * 1000.0 - sum(self.frame_categories.values())

    def render(self) -> None:
        import time
        t_render = time.perf_counter()
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

        # 1. Momento do Clear
        self.screen.fill(bg_color)
        t_clear = time.perf_counter()

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

        # 2. Momento do Blit de Sprites
        t_blit_start = time.perf_counter()
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
        t_blit = time.perf_counter()

        # 3. Momento do UI Render (desenha em view_mode == "game" ou quando playing é True)
        t_ui_start = time.perf_counter()
        if self.view_mode == "game" or self.playing:
            self.native_ui.draw(self.objects, self.screen, world_to_screen=self.world_to_screen)
        if self.playing and self.hud_entries:
            self.overlay_renderer.draw_hud(self.screen, self.hud_entries, width, height)
        t_ui = time.perf_counter()

        # 4. Momento do Present / Update
        self.pygame.display.flip()
        
        if hasattr(self, "frame_categories"):
            self.frame_categories["rendering"] = (time.perf_counter() - t_render) * 1000.0
            for k, v in self.frame_categories.items():
                self.frame_accumulators[k] += v
            self.frame_accumulators["count"] += 1

    def sync_stats(self) -> None:
        now_ms = self.pygame.time.get_ticks()
        # A UI do editor não precisa receber uma cópia completa da cena a cada
        # frame. 10 Hz mantém Inspector/Hierarchy fluidos sem saturar o IPC/Qt.
        if self.playing and now_ms - self.last_runtime_sync_ms >= 100:
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
            
            if hasattr(self, "frame_accumulators") and self.frame_accumulators["count"] > 0:
                count = self.frame_accumulators["count"]
                avg_cats = {k: v / count for k, v in self.frame_accumulators.items() if k != "count"}
                frame_time_ms = sum(avg_cats.values())
                for k in self.frame_accumulators:
                    self.frame_accumulators[k] = 0.0 if k != "count" else 0
                _send(self.events, {
                    "type": "runtime_metrics",
                    "fps": self.clock.get_fps(),
                    "frame_time_ms": frame_time_ms,
                    "categories": avg_cats
                })

    def teardown(self) -> bool:
        """Libera deterministicamente todos os recursos pertencentes à sessão."""
        if getattr(self, "_teardown_complete", False):
            return False
        self._teardown_complete = True
        self.running = False

        self.stop_logic()
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

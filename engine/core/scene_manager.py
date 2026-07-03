"""
engine/core/scene_manager.py
────────────────────────────────────────────────────────────────
Fonte canônica do SceneManager.
O arquivo engine/scene_manager.py é agora um shim que importa daqui.

SceneManager — singleton que gerencia a pilha de cenas e transições.
"""
from __future__ import annotations

import importlib
import sys
import traceback
from typing import Callable, List, Optional

import pygame

from engine.transitions import Transition, TransitionPhase, FadeTransition  # noqa: F401


class SceneManager:
    _inst: Optional["SceneManager"] = None

    def __init__(self) -> None:
        self._engine = None
        self._stack: List = []
        self._transition: Optional[Transition] = None
        self._pending_scene = None
        self._pending_pop: bool = False
        self._pending_push: bool = False

        self.on_transition_start: Optional[Callable[[str], None]] = None
        self.on_transition_end: Optional[Callable[[str], None]] = None

    @classmethod
    def instance(cls) -> "SceneManager":
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    @classmethod
    def reset(cls) -> None:
        cls._inst = None

    def bind(self, engine) -> None:
        self._engine = engine
        bound_load = self.load
        self.load = bound_load
        engine.change_scene = bound_load

    def load(self, new_scene, transition: Optional[Transition] = None) -> None:
        if transition is None:
            self._do_swap_load(new_scene)
            return
        self._start_transition(transition, new_scene, pop=False)

    def push(self, new_scene, transition: Optional[Transition] = None) -> None:
        if transition is None:
            self._do_swap_push(new_scene)
            return
        self._start_transition(transition, new_scene, pop=False, is_push=True)

    def pop(self, transition: Optional[Transition] = None) -> None:
        if len(self._stack) <= 1:
            return

        prev_scene = self._stack[-2]
        if transition is None:
            self._stack.pop()
            self._reset_ui()
            if hasattr(prev_scene, "_ui_setup"):
                prev_scene._ui_setup()
            return

        self._start_transition(transition, prev_scene, pop=True)

    @property
    def current(self):
        return self._stack[-1] if self._stack else None

    @property
    def stack_depth(self) -> int:
        return len(self._stack)

    @property
    def is_transitioning(self) -> bool:
        return self._transition is not None and not self._transition.is_done

    def update(self, dt: float) -> None:
        tr = self._transition

        if tr is None or tr.is_done:
            if self.current:
                self.current.update(dt)
                self._run_physics()
            return

        tr.update(dt)

        if tr.should_swap:
            self._execute_pending_swap()

        if tr.phase in (TransitionPhase.IN, TransitionPhase.DONE):
            if self.current:
                self.current.update(dt)
                self._run_physics()

        if tr.is_done:
            self._transition = None
            if self.on_transition_end:
                self.on_transition_end(
                    self.current.__class__.__name__ if self.current else ""
                )

    def draw(self, screen: pygame.Surface) -> None:
        tr = self._transition

        if tr is None or tr.is_done:
            if self.current:
                self.current.draw(screen)
            return

        if tr.phase == TransitionPhase.OUT:
            if tr.snapshot_out is None and self.current:
                snap = pygame.Surface(screen.get_size())
                self.current.draw(snap)
                tr.snapshot_out = snap
            tr.draw(screen)

        elif tr.phase == TransitionPhase.SWAP:
            tr.draw(screen)

        elif tr.phase == TransitionPhase.IN:
            if tr.snapshot_in is None and self.current:
                snap = pygame.Surface(screen.get_size())
                self.current.draw(snap)
                tr.snapshot_in = snap
            tr.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.is_transitioning:
            return
        if self.current:
            self.current.handle_event(event)

    @staticmethod
    def _reset_ui() -> None:
        ui_module = importlib.import_module("engine.ui.ui_manager")
        ui_module.UIManager.reset()

    @staticmethod
    def _get_collider_classes():
        collider_module = sys.modules.get("engine.physics.collider")
        if collider_module is None:
            collider_module = importlib.import_module("engine.physics.collider")
        return collider_module.BoxCollider, collider_module.CircleCollider

    @staticmethod
    def _run_physics() -> None:
        try:
            BoxCollider, CircleCollider = SceneManager._get_collider_classes()
            BoxCollider.check_all()
            CircleCollider.check_all()
        except Exception:
            traceback.print_exc()

    def _start_transition(
        self,
        transition: Transition,
        target_scene,
        pop: bool = False,
        is_push: bool = False,
    ) -> None:
        self._transition = transition
        self._pending_scene = target_scene
        self._pending_pop = pop
        self._pending_push = is_push

        if self.on_transition_start:
            self.on_transition_start(target_scene.__class__.__name__)

    def _execute_pending_swap(self) -> None:
        if self._pending_pop:
            if len(self._stack) > 1:
                self._stack.pop()
            self._reset_ui()
        elif self._pending_push:
            self._reset_ui()
            scene = self._pending_scene
            scene.engine = self._engine
            scene.start()
            self._stack.append(scene)
        else:
            self._do_swap_load(self._pending_scene)

        self._pending_scene = None
        self._pending_pop = False
        self._pending_push = False

    def _do_swap_load(self, new_scene) -> None:
        self._reset_ui()
        self._stack.clear()
        try:
            BoxCollider, CircleCollider = self._get_collider_classes()
            BoxCollider._scene_tilemaps.clear()
            BoxCollider._scene_tilemap_components.clear()
            BoxCollider._registry.clear()
            CircleCollider._registry.clear()
        except Exception:
            pass
        try:
            from engine.audio import AudioManager
            AudioManager.stop_music()
            AudioManager.unload_cache()
        except Exception:
            pass
        new_scene.engine = self._engine
        new_scene.start()
        self._stack.append(new_scene)

    def _do_swap_push(self, new_scene) -> None:
        self._reset_ui()
        new_scene.engine = self._engine
        new_scene.start()
        self._stack.append(new_scene)

    def __repr__(self) -> str:
        current = self.current.__class__.__name__ if self.current else "None"
        return (
            f"<SceneManager current='{current}' "
            f"depth={self.stack_depth} "
            f"transitioning={self.is_transitioning}>"
        )

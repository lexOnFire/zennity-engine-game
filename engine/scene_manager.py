from __future__ import annotations
"""
engine/scene_manager.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SceneManager — singleton que gerencia a pilha de cenas e transições.

Funcionalidades:
  • load(scene, transition?)  — troca de cena com transição visual
  • push(scene, transition?)  — empilha cena (pausa a atual)
  • pop(transition?)          — desempilha e volta à cena anterior
  • Histórico de cenas (pilha)
  • Callbacks: on_transition_start, on_transition_end
  • Integração limpa com Engine existente via patch de change_scene()

Uso:
    sm = SceneManager.instance()
    sm.bind(engine)                     # uma vez, logo após Engine()

    sm.load(GameScene(),
            transition=FadeTransition(color=(0,0,0), duration_out=0.4))

    sm.push(PauseScene(),
            transition=SlideTransition(direction=SlideDirection.UP))

    sm.pop(transition=FadeTransition(duration_out=0.2))
"""

import pygame
from typing import Callable, List, Optional

from .transitions import Transition, TransitionPhase, FadeTransition
from .ui.ui_manager import UIManager


class SceneManager:
    _inst: Optional["SceneManager"] = None

    def __init__(self) -> None:
        self._engine = None
        self._stack:      List = []         # pilha de cenas ativas
        self._transition: Optional[Transition] = None
        self._pending_scene = None          # cena aguardando o swap
        self._pending_pop:  bool = False    # pop pendente

        self.on_transition_start: Optional[Callable[[str], None]] = None
        self.on_transition_end:   Optional[Callable[[str], None]] = None

    # ── Singleton ────────────────────────────────────────────────────

    @classmethod
    def instance(cls) -> "SceneManager":
        if cls._inst is None:
            cls._inst = cls()
        return cls._inst

    @classmethod
    def reset(cls) -> None:
        cls._inst = None

    # ── Bind ao Engine ───────────────────────────────────────────────

    def bind(self, engine) -> None:
        """
        Associa o SceneManager ao Engine.
        Faz patch de engine.change_scene → sm.load para compatibilidade
        com demos antigas.
        """
        self._engine = engine
        # Patch para retrocompatibilidade
        engine.change_scene = self.load

    # ── API pública ──────────────────────────────────────────────────

    def load(
        self,
        new_scene,
        transition: Optional[Transition] = None,
    ) -> None:
        """
        Substitui toda a pilha pela nova cena.
        Se transition=None, a troca é instantânea.
        """
        if transition is None:
            self._do_swap_load(new_scene)
            return

        self._start_transition(transition, new_scene, pop=False)

    def push(
        self,
        new_scene,
        transition: Optional[Transition] = None,
    ) -> None:
        """
        Empilha nova cena por cima (pausa a atual).
        A cena atual NÃO recebe update/draw enquanto a nova estiver ativa.
        """
        if transition is None:
            self._do_swap_push(new_scene)
            return
        self._start_transition(transition, new_scene, pop=False, is_push=True)

    def pop(
        self,
        transition: Optional[Transition] = None,
    ) -> None:
        """
        Remove a cena do topo e retorna à anterior.
        Sem efeito se a pilha tiver apenas uma cena.
        """
        if len(self._stack) <= 1:
            return

        prev_scene = self._stack[-2]  # cena que vai aparecer
        if transition is None:
            self._stack.pop()
            UIManager.reset()
            if hasattr(prev_scene, '_ui_setup'):
                prev_scene._ui_setup()
            return

        self._start_transition(transition, prev_scene, pop=True)

    # ── Propriedades ─────────────────────────────────────────────────

    @property
    def current(self):
        return self._stack[-1] if self._stack else None

    @property
    def stack_depth(self) -> int:
        return len(self._stack)

    @property
    def is_transitioning(self) -> bool:
        return self._transition is not None and not self._transition.is_done

    # ── Integração com Engine (chamado pelo loop) ─────────────────────

    def update(self, dt: float) -> None:
        tr = self._transition

        if tr is None or tr.is_done:
            # Comportamento normal
            if self.current:
                self.current.update(dt)
            return

        # Atualiza transição
        tr.update(dt)

        # Momento do swap
        if tr.should_swap:
            self._execute_pending_swap()

        # Cena de entrada também roda update (para animações de UI, etc.)
        if tr.phase in (TransitionPhase.IN, TransitionPhase.DONE):
            if self.current:
                self.current.update(dt)

        # Transição concluída
        if tr.is_done:
            self._transition = None
            if self.on_transition_end:
                self.on_transition_end(self.current.__class__.__name__ if self.current else "")

    def draw(self, screen: pygame.Surface) -> None:
        tr = self._transition

        if tr is None or tr.is_done:
            if self.current:
                self.current.draw(screen)
            return

        # Captura snapshots se necessário
        if tr.phase == TransitionPhase.OUT:
            if tr.snapshot_out is None and self.current:
                # Renderiza cena atual em snapshot limpo
                snap = pygame.Surface(screen.get_size())
                self.current.draw(snap)
                tr.snapshot_out = snap
            tr.draw(screen)

        elif tr.phase == TransitionPhase.SWAP:
            tr.draw(screen)  # frame de swap

        elif tr.phase == TransitionPhase.IN:
            if tr.snapshot_in is None and self.current:
                snap = pygame.Surface(screen.get_size())
                self.current.draw(snap)
                tr.snapshot_in = snap
            tr.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.is_transitioning:
            return   # bloqueia input durante transição
        if self.current:
            self.current.handle_event(event)

    # ── Internos ─────────────────────────────────────────────────────

    def _start_transition(
        self,
        transition: Transition,
        target_scene,
        pop:     bool = False,
        is_push: bool = False,
    ) -> None:
        self._transition   = transition
        self._pending_scene = target_scene
        self._pending_pop   = pop
        self._pending_push  = is_push

        if self.on_transition_start:
            self.on_transition_start(target_scene.__class__.__name__)

    def _execute_pending_swap(self) -> None:
        if self._pending_pop:
            if len(self._stack) > 1:
                self._stack.pop()
            UIManager.reset()
        elif getattr(self, '_pending_push', False):
            UIManager.reset()
            scene = self._pending_scene
            scene.engine = self._engine
            scene.start()
            self._stack.append(scene)
        else:
            self._do_swap_load(self._pending_scene)

        self._pending_scene = None
        self._pending_pop   = False
        self._pending_push  = False

    def _do_swap_load(self, new_scene) -> None:
        """Troca imediata — limpa pilha e inicia nova cena."""
        UIManager.reset()
        self._stack.clear()
        try:
            from engine.physics.collider import BoxCollider, CircleCollider
            BoxCollider._scene_tilemaps.clear()
            BoxCollider._scene_tilemap_components.clear()
            BoxCollider._registry.clear()
            CircleCollider._registry.clear()
        except Exception:
            pass
        new_scene.engine = self._engine
        new_scene.start()
        self._stack.append(new_scene)

    def _do_swap_push(self, new_scene) -> None:
        """Push imediato."""
        UIManager.reset()
        new_scene.engine = self._engine
        new_scene.start()
        self._stack.append(new_scene)

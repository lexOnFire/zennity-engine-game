import pygame
import sys
import traceback
from typing import Optional


class Scene:
    """Classe base para todas as cenas do jogo."""
    def __init__(self):
        self.engine: Optional['Engine'] = None

    def start(self) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, screen: pygame.Surface) -> None:
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        pass


class Engine:
    """Controlador principal do loop de jogo e gerenciamento de cenas."""

    def __init__(
        self,
        width:  int = 800,
        height: int = 600,
        title:  str = "Zennity Engine",
        fps:    int = 60,
    ) -> None:
        pygame.init()
        pygame.mixer.init()

        info = pygame.display.Info()
        desktop_w = info.current_w
        desktop_h = info.current_h

        if width >= desktop_w or height >= desktop_h:
            width  = int(desktop_w * 0.9)
            height = int(desktop_h * 0.85)

        self.width  = width
        self.height = height
        self.fps    = fps
        self.is_fullscreen = False
        self.saved_w = width
        self.saved_h = height

        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption(title)

        self.clock      = pygame.time.Clock()
        self.is_running = False

        # Retrocompatibilidade — SceneManager pode fazer patch aqui
        self._scene_manager = None
        self._current_scene: Optional[Scene] = None
        self._next_scene:    Optional[Scene] = None

    # ── Propriedade pública (retrocompat) ────────────────────────────

    @property
    def current_scene(self) -> Optional[Scene]:
        if self._scene_manager:
            return self._scene_manager.current
        return self._current_scene

    # ── SceneManager opt-in ──────────────────────────────────────────

    def use_scene_manager(self) -> "SceneManager":  # type: ignore[name-defined]
        """Ativa o SceneManager e retorna a instância."""
        from .scene_manager import SceneManager
        sm = SceneManager.instance()
        sm.bind(self)
        self._scene_manager = sm
        return sm

    # ── API de cena (retrocompat sem SceneManager) ───────────────────

    def change_scene(self, new_scene: Scene) -> None:
        """Troca de cena sem transição (retrocompatível)."""
        if self._scene_manager:
            self._scene_manager.load(new_scene)
        else:
            self._next_scene = new_scene

    def _perform_scene_change(self) -> None:
        if self._next_scene is not None:
            self._current_scene = self._next_scene
            self._current_scene.engine = self
            self._current_scene.start()
            self._next_scene = None

    # ── Fullscreen ───────────────────────────────────────────────────

    def toggle_fullscreen(self) -> None:
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.saved_w, self.saved_h = self.width, self.height
            info = pygame.display.Info()
            self.width, self.height = info.current_w, info.current_h
            self.screen = pygame.display.set_mode(
                (self.width, self.height), pygame.FULLSCREEN
            )
        else:
            self.width, self.height = self.saved_w, self.saved_h
            self.screen = pygame.display.set_mode(
                (self.width, self.height), pygame.RESIZABLE
            )

    # ── Loop principal ───────────────────────────────────────────────

    def run(self, initial_scene: Scene) -> None:
        """Inicia e executa o loop principal."""
        self.is_running = True

        if self._scene_manager:
            self._scene_manager.load(initial_scene)
        else:
            self.change_scene(initial_scene)
            self._perform_scene_change()

        from .input import Input

        while self.is_running:
            Input.update()
            dt = min(self.clock.tick(self.fps) / 1000.0, 0.1)

            sm = self._scene_manager

            # ── Eventos ──
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False

                if event.type == pygame.VIDEORESIZE and not self.is_fullscreen:
                    self.width, self.height = event.w, event.h
                    self.screen = pygame.display.set_mode(
                        (self.width, self.height), pygame.RESIZABLE
                    )

                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()

                try:
                    if sm:
                        sm.handle_event(event)
                    elif self._current_scene:
                        self._current_scene.handle_event(event)
                except Exception:
                    traceback.print_exc()

            # ── Update ──
            try:
                if sm:
                    sm.update(dt)
                else:
                    if self._next_scene:
                        self._perform_scene_change()
                    if self._current_scene:
                        self._current_scene.update(dt)
            except Exception:
                traceback.print_exc()

            # ── Draw ──
            try:
                if sm:
                    sm.draw(self.screen)
                elif self._current_scene:
                    self._current_scene.draw(self.screen)
            except Exception:
                traceback.print_exc()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

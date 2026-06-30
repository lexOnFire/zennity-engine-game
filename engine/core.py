import pygame
import sys
import traceback
from typing import Optional


class Scene:
    """Base class for all game scenes/states."""
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
    """The main engine controller that drives the game loop and scene transitions."""
    def __init__(self, width: int = 800, height: int = 600, title: str = "Pygame Engine", fps: int = 60):
        pygame.init()
        pygame.mixer.init()

        # Obter resolução do monitor e adaptar para caber perfeitamente na tela do usuário
        info = pygame.display.Info()
        desktop_w = info.current_w
        desktop_h = info.current_h
        
        if width >= desktop_w or height >= desktop_h:
            width = int(desktop_w * 0.9)
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

        self.current_scene: Optional[Scene] = None
        self.next_scene:    Optional[Scene] = None

    def toggle_fullscreen(self) -> None:
        """Alterna entre modo janela ressoável e tela cheia."""
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.saved_w, self.saved_h = self.width, self.height
            info = pygame.display.Info()
            self.width, self.height = info.current_w, info.current_h
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        else:
            self.width, self.height = self.saved_w, self.saved_h
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

    def change_scene(self, new_scene: Scene) -> None:
        """Schedules a scene transition for the end of the current frame."""
        self.next_scene = new_scene

    def _perform_scene_change(self) -> None:
        if self.next_scene is not None:
            self.current_scene = self.next_scene
            self.current_scene.engine = self
            self.current_scene.start()
            self.next_scene = None

    def run(self, initial_scene: Scene) -> None:
        """Starts and runs the main game loop."""
        self.is_running = True
        self.change_scene(initial_scene)
        self._perform_scene_change()

        from .input import Input

        while self.is_running:
            Input.update()
            dt = min(self.clock.tick(self.fps) / 1000.0, 0.1)

            # 1. Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False

                if event.type == pygame.VIDEORESIZE:
                    if not self.is_fullscreen:
                        self.width, self.height = event.w, event.h
                        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)

                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self.toggle_fullscreen()

                if self.current_scene:
                    try:
                        self.current_scene.handle_event(event)
                    except Exception:
                        traceback.print_exc()

            # 2. Update
            if self.current_scene:
                try:
                    self.current_scene.update(dt)
                except Exception:
                    traceback.print_exc()

            # 3. Scene change
            if self.next_scene:
                self._perform_scene_change()

            # 4. Rendering
            if self.current_scene:
                try:
                    self.current_scene.draw(self.screen)
                except Exception:
                    traceback.print_exc()

            pygame.display.flip()

        pygame.quit()
        sys.exit()

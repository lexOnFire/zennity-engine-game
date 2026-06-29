import pygame
import sys
from typing import Optional

class Scene:
    """Base class for all game scenes/states (e.g., MainMenu, Level1, GameOver)."""
    def __init__(self):
        self.engine: Optional['Engine'] = None

    def start(self) -> None:
        """Called when the scene starts."""
        pass

    def update(self, dt: float) -> None:
        """Called every frame to update scene logic. dt is delta time in seconds."""
        pass

    def draw(self, screen: pygame.Surface) -> None:
        """Called every frame to draw the scene graphics."""
        pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Called for every pygame event."""
        pass


class Engine:
    """The main engine controller that drives the game loop and scene transitions."""
    def __init__(self, width: int = 800, height: int = 600, title: str = "Pygame Engine", fps: int = 60):
        pygame.init()
        pygame.mixer.init()
        
        self.width = width
        self.height = height
        self.fps = fps
        
        # Set up window
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        
        self.clock = pygame.time.Clock()
        self.is_running = False
        
        # Scene Management
        self.current_scene: Optional[Scene] = None
        self.next_scene: Optional[Scene] = None

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
            # Update inputs
            Input.update()
            
            # Calculate delta time (dt) in seconds
            # Max dt capped to 0.1s to prevent huge jumps when dragging the window
            dt = min(self.clock.tick(self.fps) / 1000.0, 0.1)
            
            # 1. Event Handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.is_running = False
                
                # Let current scene handle events
                if self.current_scene:
                    self.current_scene.handle_event(event)
            
            # 2. Update logic
            if self.current_scene:
                self.current_scene.update(dt)
            
            # 3. Handle scheduled scene changes
            if self.next_scene:
                self._perform_scene_change()
            
            # 4. Rendering
            if self.current_scene:
                self.current_scene.draw(self.screen)
            
            pygame.display.flip()

        pygame.quit()
        sys.exit()

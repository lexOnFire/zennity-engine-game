import warnings
import pygame
from ..core.component import Component
from .camera2d import Camera2D
from ..assets import Assets
from typing import Tuple, List, Optional
import numpy as np
import random
from .renderer import SpriteRenderer

warnings.warn(
    "engine.graphics.renderer2d está deprecado. Use engine.graphics.renderer.",
    DeprecationWarning,
    stacklevel=2,
)

# SpriteRenderer é re-exportado de .renderer para retrocompatibilidade


class TextRenderer(Component):
    """Renders text. Can be drawn in World Space (moves with camera) or Screen Space (UI)."""
    def __init__(self, text: str, font_size: int = 24, color: Tuple[int, int, int] = (255, 255, 255), 
                 is_ui: bool = False, font_name: Optional[str] = None) -> None:
        super().__init__()
        self.text = text
        self.font_size = font_size
        self.color = color
        self.is_ui = is_ui
        self.font_name = font_name
        self._font = None
        self._rendered_surface = None

    def start(self) -> None:
        self._font = Assets.get_font(self.font_name, self.font_size)
        self._render_text()

    def _render_text(self) -> None:
        if self._font and self.text:
            self._rendered_surface = self._font.render(self.text, True, self.color)

    def set_text(self, text: str) -> None:
        """Updates the text content and re-renders the surface."""
        if self.text != text:
            self.text = text
            self._render_text()

    def draw(self, screen: pygame.Surface) -> None:
        if not self._rendered_surface:
            self._render_text()
            if not self._rendered_surface:
                return

        world_pos = self.transform.get_world_position()

        if self.is_ui:
            # Draw directly in screen coordinates
            screen_x, screen_y = world_pos[0], world_pos[1]
        else:
            # Draw using camera coordinates
            from engine.graphics.camera import Camera
            main_cam = Camera.main
            if main_cam:
                screen_x, screen_y = main_cam.world_to_screen(
                    world_pos, screen.get_width(), screen.get_height()
                )
            elif Camera2D.main:
                screen_x, screen_y = Camera2D.main.world_to_screen(
                    world_pos, screen.get_width(), screen.get_height()
                )
            else:
                screen_x, screen_y = world_pos[0], world_pos[1]

        rect = self._rendered_surface.get_rect()
        rect.center = (int(screen_x), int(screen_y))
        screen.blit(self._rendered_surface, rect)


class LegacyParticle:
    def __init__(self, x: float, y: float, vx: float, vy: float, 
                 color: Tuple[int, int, int], lifetime: float, size: float) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = size


class LegacyParticleSystem(Component):
    """Emits simple colored circle particles with velocity and gravity."""
    def __init__(self, color: Tuple[int, int, int] = (255, 100, 0),
                 emission_rate: float = 20, particle_lifetime: float = 1.0,
                 particle_speed: float = 100.0, gravity: float = 0.0) -> None:
        super().__init__()
        self.color = color
        self.emission_rate = emission_rate
        self.particle_lifetime = particle_lifetime
        self.particle_speed = particle_speed
        self.gravity = gravity
        
        self.particles: List[LegacyParticle] = []
        self._spawn_timer = 0.0

    def update(self, dt: float) -> None:
        # Update existing particles
        alive_particles = []
        for p in self.particles:
            p.lifetime -= dt
            if p.lifetime > 0:
                p.vy += self.gravity * dt
                p.x += p.vx * dt
                p.y += p.vy * dt
                alive_particles.append(p)
        self.particles = alive_particles

        # Emit new particles
        if self.emission_rate > 0:
            self._spawn_timer += dt
            spawn_interval = 1.0 / self.emission_rate
            world_pos = self.transform.get_world_position()

            while self._spawn_timer >= spawn_interval:
                # Emit particle
                angle = random.uniform(0, 2 * np.pi)
                speed = random.uniform(0.5, 1.0) * self.particle_speed
                vx = np.cos(angle) * speed
                vy = np.sin(angle) * speed
                
                lifetime = random.uniform(0.7, 1.3) * self.particle_lifetime
                size = random.uniform(2, 6)
                
                p = LegacyParticle(world_pos[0], world_pos[1], vx, vy, self.color, lifetime, size)
                self.particles.append(p)
                
                self._spawn_timer -= spawn_interval
        else:
            self._spawn_timer = 0.0

    def draw(self, screen: pygame.Surface) -> None:
        from engine.graphics.camera import Camera
        main_cam = Camera.main
        for p in self.particles:
            if main_cam:
                screen_x, screen_y = main_cam.world_to_screen(
                    np.array([p.x, p.y, 0]), screen.get_width(), screen.get_height()
                )
                zoom = main_cam.zoom
            elif Camera2D.main:
                screen_x, screen_y = Camera2D.main.world_to_screen(
                    np.array([p.x, p.y, 0]), screen.get_width(), screen.get_height()
                )
                zoom = Camera2D.main.zoom
            else:
                screen_x, screen_y = p.x, p.y
                zoom = 1.0

            size = max(1, int(p.size * zoom))
            # Fade out color based on lifetime
            alpha_ratio = p.lifetime / p.max_lifetime
            faded_color = (
                int(self.color[0] * alpha_ratio),
                int(self.color[1] * alpha_ratio),
                int(self.color[2] * alpha_ratio)
            )
            
            pygame.draw.circle(
                screen, faded_color, (int(screen_x), int(screen_y)), size
            )


Particle = LegacyParticle
ParticleSystem = LegacyParticleSystem

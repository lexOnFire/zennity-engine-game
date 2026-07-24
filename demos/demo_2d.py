import pygame
import sys
import os
import random
import numpy as np

# Adjust path to import engine from parent folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.core import Engine, Scene
from engine.game_object import GameObject
from engine.component import Component
from engine.input import Input
from engine.graphics.camera2d import Camera2D
from engine.graphics.renderer2d import SpriteRenderer, TextRenderer, ParticleSystem
from engine.physics.collision import BoxCollider2D
from engine.physics.rigidbody import Rigidbody2D


# ---------------------------------------------------------
# Procedural Sprite Generator
# ---------------------------------------------------------
def create_player_surface() -> pygame.Surface:
    """Creates a cute 2D character sprite procedurally."""
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)
    # Body (Rounded blue rectangle)
    pygame.draw.rect(surf, (0, 150, 255), (0, 0, 32, 32), border_radius=8)
    # Eyes
    pygame.draw.circle(surf, (255, 255, 255), (10, 10), 4)
    pygame.draw.circle(surf, (0, 0, 0), (10, 10), 2)
    pygame.draw.circle(surf, (255, 255, 255), (22, 10), 4)
    pygame.draw.circle(surf, (0, 0, 0), (22, 10), 2)
    # Smiling Mouth
    pygame.draw.arc(surf, (0, 0, 0), (8, 12, 16, 12), np.pi, 2 * np.pi, 2)
    return surf

def create_platform_surface(width: int, height: int, is_grass: bool = True) -> pygame.Surface:
    """Creates a textured tile surface procedurally."""
    surf = pygame.Surface((width, height))
    if is_grass:
        # Grass (green top) and dirt (brown bottom)
        surf.fill((120, 70, 30))  # Brown dirt
        pygame.draw.rect(surf, (40, 180, 70), (0, 0, width, max(4, height // 4)))  # Green grass
        # Draw grass strands
        for x in range(0, width, 8):
            pygame.draw.line(surf, (30, 150, 50), (x, 0), (x + random.randint(-2, 2), random.randint(3, 8)))
    else:
        # Stone block
        surf.fill((100, 100, 100))
        # Draw brick pattern
        for y in range(0, height, 16):
            pygame.draw.line(surf, (60, 60, 60), (0, y), (width, y), 2)
            offset = 8 if (y // 16) % 2 == 0 else 0
            for x in range(offset, width, 16):
                pygame.draw.line(surf, (60, 60, 60), (x, y), (x, y + 16), 2)
    return surf


# ---------------------------------------------------------
# Custom Components
# ---------------------------------------------------------
class PlayerController(Component):
    """Component that controls character movement, jumping, and triggers particles."""
    def __init__(self, speed: float = 250.0, jump_force: float = 480.0) -> None:
        super().__init__()
        self.speed = speed
        self.jump_force = jump_force
        self.rb: Rigidbody2D = None
        self.particles: ParticleSystem = None

    def start(self) -> None:
        self.rb = self.game_object.get_component(Rigidbody2D)
        self.particles = self.game_object.get_component(ParticleSystem)

    def update(self, dt: float) -> None:
        if not self.rb:
            return
            
        # Horizontal Movement
        h_axis = Input.get_axis_horizontal()
        self.rb.velocity[0] = h_axis * self.speed
        
        # Animate sprite rotation slightly based on horizontal movement
        if h_axis != 0.0:
            target_rot = -h_axis * 10.0
            # Slerp/Lerp rotation
            self.transform.rz += (target_rot - self.transform.rz) * 10.0 * dt
        else:
            self.transform.rz += (0.0 - self.transform.rz) * 10.0 * dt

        # Jump
        if Input.get_key_down(pygame.K_SPACE) or Input.get_key_down(pygame.K_w) or Input.get_key_down(pygame.K_UP):
            if self.rb.is_grounded:
                self.rb.velocity[1] = -self.jump_force
                # Emit jump burst particles
                if self.particles:
                    self.particles.emission_rate = 80
                    # Reset back to lower rate after a short delay
                    self.game_object.scene.engine.clock.tick()  # Ensure timer reference
            
        # Dynamically adjust particle emission rate
        if self.particles:
            if not self.rb.is_grounded:
                # Fewer particles in air
                self.particles.emission_rate = 3.0
            elif abs(self.rb.velocity[0]) > 10.0:
                # Normal running particle trail
                self.particles.emission_rate = 25.0
            else:
                # Idle particle rate
                self.particles.emission_rate = 0.0


class CameraFollow2D(Component):
    """Lerps camera transform to follow a target Transform smoothly."""
    def __init__(self, target_transform: 'Transform', lerp_speed: float = 6.0) -> None:
        super().__init__()
        self.target = target_transform
        self.lerp_speed = lerp_speed

    def update(self, dt: float) -> None:
        if not self.target:
            return
        
        # Lerp camera position
        tx = self.target.x
        ty = self.target.y - 50.0  # Offset camera slightly upwards
        
        self.transform.x += (tx - self.transform.x) * self.lerp_speed * dt
        self.transform.y += (ty - self.transform.y) * self.lerp_speed * dt


# ---------------------------------------------------------
# Demo 2D Game Scene
# ---------------------------------------------------------
class Game2DScene(Scene):
    def __init__(self) -> None:
        super().__init__()
        self.game_objects: List[GameObject] = []

    def start(self) -> None:
        print("2D Demo Scene Started!")
        
        # 1. Create Ground and Platforms
        self.create_platform(0, 200, 1000, 40, is_grass=True)      # Ground
        self.create_platform(-250, 80, 200, 30, is_grass=False)    # Left Floating Platform
        self.create_platform(250, 80, 200, 30, is_grass=False)     # Right Floating Platform
        self.create_platform(0, -60, 250, 30, is_grass=True)       # Top Grass Platform
        
        # 2. Create Player Character
        player = GameObject("Player")
        player.transform.x = 0.0
        player.transform.y = 100.0  # Spawn above ground
        
        # Render component
        player_surf = create_player_surface()
        player.add_component(SpriteRenderer(player_surf))
        
        # Collider and Physics
        player.add_component(BoxCollider2D(32, 32))
        player.add_component(Rigidbody2D(gravity=1200.0))
        
        # Particle System (trail behind feet)
        particles = player.add_component(ParticleSystem(
            color=(0, 200, 255), 
            emission_rate=0, 
            particle_lifetime=0.5,
            particle_speed=50.0, 
            gravity=80.0
        ))
        
        # Player controller logic
        player.add_component(PlayerController(speed=240.0, jump_force=500.0))
        
        self.add_game_object(player)
        
        # 3. Setup Camera
        camera_obj = GameObject("MainCamera")
        camera_comp = camera_obj.add_component(Camera2D(zoom=1.5))
        camera_comp.make_main()
        camera_obj.add_component(CameraFollow2D(player.transform))
        self.add_game_object(camera_obj)

        # 4. Instructions UI Text (Fixed in Screen Space)
        ui_text = GameObject("UI_Instructions")
        ui_text.transform.x = 400.0  # Center X on screen
        ui_text.transform.y = 35.0   # Top of screen
        ui_text.add_component(TextRenderer(
            text="A / D or Arrow Keys: Move  |  SPACE: Jump  |  Mouse Scroll: Zoom",
            font_size=20,
            color=(255, 255, 255),
            is_ui=True
        ))
        self.add_game_object(ui_text)
        
        ui_title = GameObject("UI_Title")
        ui_title.transform.x = 400.0
        ui_title.transform.y = 570.0
        self.title_text = ui_title.add_component(TextRenderer(
            text="ZenithEngine 2D Sandbox",
            font_size=18,
            color=(0, 180, 255),
            is_ui=True
        ))
        self.add_game_object(ui_title)

    def create_platform(self, x: float, y: float, w: int, h: int, is_grass: bool) -> GameObject:
        platform = GameObject(f"Platform_{x}_{y}")
        platform.transform.x = x
        platform.transform.y = y
        
        surf = create_platform_surface(w, h, is_grass)
        platform.add_component(SpriteRenderer(surf))
        platform.add_component(BoxCollider2D(w, h))
        
        self.add_game_object(platform)
        return platform

    def add_game_object(self, go: GameObject) -> None:
        go.scene = self
        self.game_objects.append(go)
        # Propagate scene to start existing components
        go._propagate_scene(self)

    def update(self, dt: float) -> None:
        # Update title FPS readout
        fps = int(self.engine.clock.get_fps())
        self.title_text.set_text(f"ZenithEngine 2D Sandbox - FPS: {fps} - Zoom: {Camera2D.main.zoom:.1f}x")
        
        for go in self.game_objects:
            go.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        # Clear screen with a nice sky gradient blue
        screen.fill((20, 25, 45))
        
        # Draw all scene game objects
        for go in self.game_objects:
            go.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> None:
        # Camera zoom handler
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll Up
                Camera2D.main.zoom = min(3.0, Camera2D.main.zoom + 0.1)
            elif event.button == 5:  # Scroll Down
                Camera2D.main.zoom = max(0.5, Camera2D.main.zoom - 0.1)


if __name__ == '__main__':
    # Initialize Engine and run 2D Scene
    engine = Engine(width=800, height=600, title="ZenithEngine 2D Sandbox")
    scene = Game2DScene()
    engine.run(scene)

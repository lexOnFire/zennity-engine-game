import pygame
import sys
import os
import numpy as np

# Adjust path to import engine from parent folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.core import Engine, Scene
from engine.game_object import GameObject
from engine.component import Component
from engine.input import Input
from engine.graphics.renderer3d import Camera3D, MeshRenderer3D
from engine.graphics.renderer2d import TextRenderer
from engine.assets import Assets

# ---------------------------------------------------------
# Helper: Create pyramid.obj procedurally if not present
# ---------------------------------------------------------
def ensure_pyramid_obj() -> str:
    """Writes a simple pyramid .obj file if it doesn't already exist."""
    path = os.path.join(os.path.dirname(__file__), "pyramid.obj")
    if not os.path.exists(path):
        obj_content = """# Simple Pyramid Mesh
v -1.0 0.0 -1.0
v 1.0 0.0 -1.0
v 1.0 0.0 1.0
v -1.0 0.0 1.0
v 0.0 1.8 0.0

f 1 2 5
f 2 3 5
f 3 4 5
f 4 1 5
f 4 3 2 1
"""
        with open(path, "w") as f:
            f.write(obj_content)
    return path


# ---------------------------------------------------------
# Custom 3D Components
# ---------------------------------------------------------
class Spinner3D(Component):
    """Component that rotates a 3D GameObject over time."""
    def __init__(self, speed_x: float = 0.0, speed_y: float = 40.0, speed_z: float = 0.0) -> None:
        super().__init__()
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.speed_z = speed_z

    def update(self, dt: float) -> None:
        self.transform.rotate(self.speed_x * dt, self.speed_y * dt, self.speed_z * dt)


class FreeCameraController3D(Component):
    """First-Person flight controls using WASD + Arrow Keys."""
    def __init__(self, speed: float = 4.0, rot_speed: float = 80.0) -> None:
        super().__init__()
        self.speed = speed
        self.rot_speed = rot_speed

    def update(self, dt: float) -> None:
        # 1. Rotation (Arrow Keys)
        rot_input_y = 0.0  # Yaw
        if Input.get_key(pygame.K_LEFT):
            rot_input_y -= 1.0
        if Input.get_key(pygame.K_RIGHT):
            rot_input_y += 1.0
            
        rot_input_x = 0.0  # Pitch
        if Input.get_key(pygame.K_UP):
            rot_input_x -= 1.0
        if Input.get_key(pygame.K_DOWN):
            rot_input_x += 1.0
            
        # Apply Yaw (Y rotation)
        self.transform.ry += rot_input_y * self.rot_speed * dt
        
        # Apply Pitch (X rotation) with clamping to avoid flipping upside down
        new_rx = self.transform.rx + rot_input_x * self.rot_speed * dt
        self.transform.rx = max(-85.0, min(85.0, new_rx))

        # 2. Movement relative to camera angle (Yaw)
        yaw_rad = np.radians(self.transform.ry)
        
        # Direction vectors in horizontal XZ plane
        forward = np.array([np.sin(yaw_rad), 0.0, np.cos(yaw_rad)], dtype=np.float32)
        right = np.array([np.cos(yaw_rad), 0.0, -np.sin(yaw_rad)], dtype=np.float32)
        
        move_dir = np.zeros(3, dtype=np.float32)
        
        if Input.get_key(pygame.K_w):
            move_dir += forward
        if Input.get_key(pygame.K_s):
            move_dir -= forward
        if Input.get_key(pygame.K_d):
            move_dir += right
        if Input.get_key(pygame.K_a):
            move_dir -= right
            
        # Vertical movement (Fly up/down)
        if Input.get_key(pygame.K_e) or Input.get_key(pygame.K_SPACE):
            move_dir[1] += 1.0
        if Input.get_key(pygame.K_q) or Input.get_key(pygame.K_LCTRL):
            move_dir[1] -= 1.0
            
        # Normalize and apply
        norm = np.linalg.norm(move_dir)
        if norm > 0:
            move_dir = (move_dir / norm) * self.speed * dt
            self.transform.translate(move_dir[0], move_dir[1], move_dir[2])


# ---------------------------------------------------------
# Demo 3D Scene
# ---------------------------------------------------------
class Game3DScene(Scene):
    def __init__(self) -> None:
        super().__init__()
        self.game_objects = []

    def start(self) -> None:
        print("3D Demo Scene Started!")
        
        # 1. Ensure our test assets exist
        pyramid_path = ensure_pyramid_obj()
        
        # 2. Setup central rotating Pyramid model loaded from OBJ file
        pyramid = GameObject("Pyramid")
        pyramid.transform.position = np.array([0.0, -0.5, 5.0])
        pyramid.transform.scale = np.array([1.2, 1.2, 1.2])
        
        pyramid_mesh = Assets.get_mesh(pyramid_path)
        pyramid.add_component(MeshRenderer3D(pyramid_mesh, color=(0, 255, 150), wireframe=False))
        pyramid.add_component(Spinner3D(speed_x=0, speed_y=35.0, speed_z=0))
        self.add_game_object(pyramid)
        
        # 3. Setup multiple surrounding Cubes (Procedural meshes)
        cube_mesh = Assets.create_cube_mesh(1.0)
        
        # Red Cube (Left)
        cube_l = GameObject("RedCube")
        cube_l.transform.position = np.array([-3.0, 0.0, 5.0])
        cube_l.add_component(MeshRenderer3D(cube_mesh, color=(255, 50, 50), wireframe=False))
        cube_l.add_component(Spinner3D(speed_x=20.0, speed_y=25.0, speed_z=10.0))
        self.add_game_object(cube_l)
        
        # Blue Cube (Right)
        cube_r = GameObject("BlueCube")
        cube_r.transform.position = np.array([3.0, 0.0, 5.0])
        cube_r.add_component(MeshRenderer3D(cube_mesh, color=(50, 100, 255), wireframe=False))
        cube_r.add_component(Spinner3D(speed_x=15.0, speed_y=45.0, speed_z=30.0))
        self.add_game_object(cube_r)
        
        # Yellow Cube Wireframe (Back floating)
        cube_back = GameObject("WireframeCube")
        cube_back.transform.position = np.array([0.0, 2.5, 7.0])
        cube_back.transform.scale = np.array([0.7, 0.7, 0.7])
        cube_back.add_component(MeshRenderer3D(cube_mesh, color=(255, 220, 50), wireframe=True))
        cube_back.add_component(Spinner3D(speed_x=10.0, speed_y=15.0, speed_z=40.0))
        self.add_game_object(cube_back)
        
        # 4. Setup First-Person camera
        camera_obj = GameObject("PlayerCamera")
        # Position: slightly up (Y=0.8), looking forward (Z=0)
        camera_obj.transform.position = np.array([0.0, 0.8, 0.0])
        camera_obj.add_component(Camera3D(fov=65.0, near=0.1, far=100.0))
        camera_obj.add_component(FreeCameraController3D(speed=5.0, rot_speed=90.0))
        self.add_game_object(camera_obj)

        # 5. Instructions UI Overlay (using 2D TextRenderer in screen-space)
        instructions = GameObject("UI_Instructions")
        instructions.transform.x = 400.0
        instructions.transform.y = 35.0
        instructions.add_component(TextRenderer(
            text="WASD: Walk  |  SPACE/E: Up  |  CTRL/Q: Down  |  Arrow Keys: Look",
            font_size=20,
            color=(255, 255, 255),
            is_ui=True
        ))
        self.add_game_object(instructions)
        
        ui_title = GameObject("UI_Title")
        ui_title.transform.x = 400.0
        ui_title.transform.y = 570.0
        self.title_text = ui_title.add_component(TextRenderer(
            text="ZenithEngine 3D Software Rasterizer",
            font_size=18,
            color=(0, 255, 150),
            is_ui=True
        ))
        self.add_game_object(ui_title)

    def add_game_object(self, go: GameObject) -> None:
        go.scene = self
        self.game_objects.append(go)
        go._propagate_scene(self)

    def update(self, dt: float) -> None:
        # FPS tracker
        fps = int(self.engine.clock.get_fps())
        cam_pos = Camera3D.main.transform.position
        self.title_text.set_text(
            f"ZenithEngine 3D Software Rasterizer - FPS: {fps} - Cam Pos: [{cam_pos[0]:.1f}, {cam_pos[1]:.1f}, {cam_pos[2]:.1f}]"
        )
        
        for go in self.game_objects:
            go.update(dt)

    def draw(self, screen: pygame.Surface) -> None:
        # Dark space grey background
        screen.fill((15, 17, 20))
        
        # Draw all 3D mesh components (internally sorted by Painter's Algorithm in depth)
        for go in self.game_objects:
            go.draw(screen)

    def handle_event(self, event: pygame.event.Event) -> None:
        pass


if __name__ == '__main__':
    # Run 3D demo scene
    engine = Engine(width=800, height=600, title="ZenithEngine 3D Demo")
    scene = Game3DScene()
    engine.run(scene)

import pygame
import numpy as np

from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider
from engine.graphics.camera2d import Camera2D
from editor_legacy.editor_2d import Editor2DScene
from editor.runtime.legacy_scene_adapter import LegacySceneAdapter

pygame.init()
pygame.display.set_mode((800, 600))
surface = pygame.Surface((800, 600), pygame.SRCALPHA)
surface.fill((28, 29, 36, 255))

scene = Editor2DScene()
scene.start()

# Enable debug_draw for all box colliders
for obj in scene.game_objects:
    bc = obj.get_component(BoxCollider)
    if bc:
        bc.debug_draw = True

Camera2D.main.transform.position[0] = 500.0
Camera2D.main.transform.position[1] = 400.0
Camera2D.main.zoom = 0.5

LegacySceneAdapter.draw(scene, surface)

pygame.image.save(surface, "test_output_box.png")
print("Saved to test_output_box.png")

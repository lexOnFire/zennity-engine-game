import pygame
import numpy as np

from engine.game_object import GameObject
from engine.physics.rigidbody import RigidBody
from engine.physics.collider import BoxCollider
from engine.graphics.camera2d import Camera2D
from engine.graphics.camera import Camera
from editor_legacy.editor_2d import Editor2DScene
from editor.runtime.legacy_scene_adapter import LegacySceneAdapter

pygame.init()
pygame.display.set_mode((800, 600))
surface = pygame.Surface((800, 600), pygame.SRCALPHA)

# Preencher fundo com alfa = 255
surface.fill((28, 29, 36, 255))

scene = Editor2DScene()
scene.start()

LegacySceneAdapter.draw(scene, surface)

pixels = pygame.surfarray.pixels_alpha(surface)
non_opaque = 0
for x in range(800):
    for y in range(600):
        if pixels[x, y] != 255:
            non_opaque += 1

print(f"Non-opaque pixels: {non_opaque}")

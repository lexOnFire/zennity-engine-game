# Script Pronto: Pular com Espaço
# Pressione ESPAÇO para pular. Requer 'Simular Gravidade' ativado.
from engine.physics.rigidbody3d import RigidBody3D
import pygame

JUMP_FORCE = 5.0

def start(obj):
    obj._jump_pressed_last = False

def update(obj, dt):
    pressed = pygame.key.get_pressed()[pygame.K_SPACE]
    if pressed and not obj._jump_pressed_last:
        rb = obj.get_component(RigidBody3D)
        if rb:
            rb._sleeping = False
            rb.add_impulse(0, JUMP_FORCE, 0)
    obj._jump_pressed_last = pressed

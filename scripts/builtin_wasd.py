# Script Pronto: Andar com WASD
# Mova o objeto com as teclas W/A/S/D no modo Play.
import pygame

SPEED = 3.0

def start(obj):
    pass

def update(obj, dt):
    keys = pygame.key.get_pressed()
    if keys[pygame.K_d]: obj.transform.position[0] += SPEED * dt
    if keys[pygame.K_a]: obj.transform.position[0] -= SPEED * dt
    if keys[pygame.K_w]: obj.transform.position[2] -= SPEED * dt
    if keys[pygame.K_s]: obj.transform.position[2] += SPEED * dt

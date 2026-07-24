# Script de Comportamento: Bloco_1
import numpy as np

def start(obj):
    obj.script_time = 0.0

def update(obj, dt):
    obj.script_time = getattr(obj, 'script_time', 0.0) + dt
    # Exemplo: rotação suave no eixo Y
    obj.transform.rotation[1] = (obj.transform.rotation[1] + 45.0 * dt) % 360

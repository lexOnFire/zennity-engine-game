# Script Pronto: Desaparecer ao Colidir
# Quando este objeto colidir com outro de tag 'perigoso', ele some da cena.
# Troque TARGET_TAG pela tag do objeto que causa a colisão.
import numpy as np

TARGET_TAG  = "perigoso"
COLLISION_D = 1.2  # distância mínima para contar como colisão

def start(obj):
    pass

def update(obj, dt):
    scene = getattr(obj, 'scene', None)
    if scene is None:
        return
    for other in getattr(scene, 'editable_objects', []):
        if other is obj:
            continue
        if getattr(other, 'tag', '') != TARGET_TAG:
            continue
        dist = float(np.linalg.norm(other.transform.position - obj.transform.position))
        if dist < COLLISION_D:
            # esconde o objeto da cena imediatamente
            obj.transform.position[1] = -999.0
            obj.active = False
            break

# Script Pronto: Seguir o Jogador
# Coloque a tag 'player' no objeto que vai ser seguido.
# Este objeto seguirá o jogador suavemente.
SPEED  = 2.5
TAG    = "player"

def start(obj):
    obj._follow_target = None

def update(obj, dt):
    # busca o alvo pela tag uma vez
    if obj._follow_target is None:
        scene = getattr(obj, 'scene', None)
        if scene:
            for other in getattr(scene, 'editable_objects', []):
                if getattr(other, 'tag', '') == TAG and other is not obj:
                    obj._follow_target = other
                    break
    target = obj._follow_target
    if target is None:
        return
    import numpy as np
    diff = target.transform.position - obj.transform.position
    dist = float(np.linalg.norm(diff))
    if dist > 0.05:
        obj.transform.position += (diff / dist) * min(SPEED * dt, dist)

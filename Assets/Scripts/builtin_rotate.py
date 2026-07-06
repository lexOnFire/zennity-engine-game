# Script Pronto: Rotação Contínua
# O objeto gira automaticamente no eixo Y.
SPEED = 60.0  # graus por segundo

def start(obj):
    pass

def update(obj, dt):
    obj.transform.rotation[1] = (obj.transform.rotation[1] + SPEED * dt) % 360

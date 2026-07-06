import math

def update(obj, dt):
    if not hasattr(obj, "time"):
        obj.time = 0.0
        obj.initial_y = obj.transform.position[1]
    obj.time += dt
    obj.transform.position[1] = obj.initial_y + math.sin(obj.time * 3.0) * 0.4

import math
import numpy as np

def update(obj, dt):
    if not hasattr(obj, "scale_time"):
        obj.scale_time = 0.0
    obj.scale_time += dt
    s = 1.0 + math.sin(obj.scale_time * 4.0) * 0.25
    obj.transform.scale = np.array([s, s, s], dtype=np.float32)

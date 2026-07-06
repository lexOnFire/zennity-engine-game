def update(obj, dt):
    obj.transform.rotation[1] = (obj.transform.rotation[1] + 45.0 * dt) % 360

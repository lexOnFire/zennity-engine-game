from engine.runtime import Input, ScriptBehaviour


class PlayerController(ScriptBehaviour):
    def on_start(self):
        pass

    def on_update(self, delta_time):
        speed = 120.0
        

        if Input.is_key_down("a"):
            self.transform.position[0] -= speed * delta_time

        if Input.is_key_down("d"):
            self.transform.position[0] += speed * delta_time

        if Input.is_key_down("space"):
            self.transform.position[1] = speed * delta_time

    def on_destroy(self):
        pass

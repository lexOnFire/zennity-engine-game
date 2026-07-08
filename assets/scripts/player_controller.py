from engine.runtime import Input, ScriptBehaviour


class PlayerController(ScriptBehaviour):
    def on_start(self):
        print(f"[GettingStarted] {self.game_object.name} started")

    def on_update(self, delta_time):
        speed = 120.0

        if Input.is_key_down("d"):
            self.transform.position[0] += speed * delta_time
        
        if Input.is_key_down("a"):
            self.transform.position[0] -= speed * delta_time
        
    
        if Input.is_key_down("space"):
            rb = obj.get_component(RigidBody3D)
            if rb:
                rb._sleeping = False
                rb.add_impulse(0, JUMP_FORCE, 0)
                obj._jump_pressed_last = pressed

        if Input.is_mouse_pressed("left"):
            print(f"[GettingStarted] mouse pressed at {Input.mouse_position()}")

    def on_destroy(self):
        print(f"[GettingStarted] {self.game_object.name} stopped")

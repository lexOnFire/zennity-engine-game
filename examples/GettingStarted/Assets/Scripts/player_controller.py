from engine.runtime import Input, ScriptBehaviour
from engine.audio import AudioSource
from engine.graphics.camera import Camera


class PlayerController(ScriptBehaviour):
    def on_start(self):
        print(f"[GettingStarted] {self.game_object.name} started")
        # Mostra informações da câmera principal
        if Camera.main:
            print(f"[GettingStarted] Main Camera encontrada com zoom {Camera.main.zoom}")
        # Toca som inicial se houver AudioSource
        source = self.get_component(AudioSource)
        if source:
            print("[GettingStarted] Tocando som inicial do AudioSource")
            source.play()

    def on_update(self, delta_time):
        speed = 120.0

        if Input.is_key_down("Space"):
            self.transform.position[0] += speed * delta_time
            # Toca som ao mover
            source = self.get_component(AudioSource)
            if source and not source.is_playing():
                source.play()

        if Input.is_mouse_pressed("left"):
            print(f"[GettingStarted] mouse pressed at {Input.mouse_position()}")

    def on_destroy(self):
        print(f"[GettingStarted] {self.game_object.name} stopped")

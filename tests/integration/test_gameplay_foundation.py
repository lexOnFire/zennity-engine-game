import pytest
from unittest.mock import MagicMock
import numpy as np
import pygame
import tempfile
from pathlib import Path

from engine.core import Scene, GameObject, Transform, Component
from engine.components.script_component import ScriptComponent
from engine.runtime import RuntimeScene, ScriptBehaviour, Input, RuntimeManager
from engine.graphics.camera import Camera
from engine.physics.collider import BoxCollider
from editor.gizmos.gizmo_registry import GizmoRegistry


def test_full_gameplay_foundation_integration():
    """
    Testa o fluxo de integração completo da Gameplay Foundation (v0.2.0-alpha):
    Cena -> GameObject -> Componentes -> Script -> Input -> Time -> Physics -> Camera -> Audio -> Play -> Stop.
    """
    # Cria script temporário
    from engine.audio import AudioManager, AudioSource, AudioListener

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "test_script.py"
        events_path = Path(tmpdir) / "events.txt"
        
        script_code = f"""from engine.runtime import ScriptBehaviour, Input

class IntegrationTestScript(ScriptBehaviour):
    def on_start(self):
        with open({str(events_path)!r}, 'a') as f:
            f.write("start\\n")

    def on_update(self, delta_time):
        with open({str(events_path)!r}, 'a') as f:
            f.write(f"update:{{delta_time}}\\n")
        if Input.is_key_down("Space"):
            with open({str(events_path)!r}, 'a') as f:
                f.write("space_pressed\\n")
"""
        script_path.write_text(script_code, encoding="utf-8")

        # 1. Criação da cena editor
        editor_scene = Scene("EditorScene")

        # 2. Configuração de Câmera
        cam_go = GameObject("MainCam")
        cam = cam_go.add_component(Camera(zoom=1.5))
        editor_scene.add_game_object(cam_go)

        # 3. Configuração de Áudio
        listener_go = GameObject("MyListener")
        listener = listener_go.add_component(AudioListener())
        editor_scene.add_game_object(listener_go)

        # 4. Configuração de Player com BoxCollider, AudioSource (play_on_awake) e Script
        player_go = GameObject("Player")
        collider = player_go.add_component(BoxCollider(width=32, height=32))
        audio_source = player_go.add_component(AudioSource(audio_clip="dummy.wav", play_on_awake=True))
        
        # Mock do AudioManager.play_sfx para retornar um canal ativo simulado
        mock_channel = MagicMock()
        mock_channel.get_busy.return_value = True
        orig_play_sfx = AudioManager.play_sfx
        AudioManager.play_sfx = MagicMock(return_value=mock_channel)

        player_go.add_component(ScriptComponent(str(script_path)))
        editor_scene.add_game_object(player_go)

        # 5. Inicializa o RuntimeManager (Play Mode)
        AudioManager.clear()
        manager = RuntimeManager()
        scene = manager.start_play(editor_scene)

        # Validações pós-Play:
        # Camera principal foi definida (pega a câmera de runtime correspondente)
        runtime_cam = scene.runtime_for_editor(cam_go).get_component(Camera)
        assert Camera.main is runtime_cam

        # AudioListener ativo (pega o listener correspondente de runtime)
        runtime_listener = scene.runtime_for_editor(listener_go).get_component(AudioListener)
        active_listener = AudioManager.get_active_listener()
        assert active_listener is not None
        assert active_listener is not listener
        assert active_listener.game_object.name == runtime_listener.game_object.name
        assert active_listener.game_object.scene is scene.scene

        # AudioSource play_on_awake disparado
        runtime_audio = scene.runtime_for_editor(player_go).get_component(AudioSource)
        assert runtime_audio.play_on_awake is True
        assert runtime_audio._playing is True

        # Verifica se o script do runtime gravou 'start'
        assert events_path.exists()
        assert events_path.read_text().splitlines()[0] == "start"

        # 6. Time e Input
        manager.input.key_down("Space")
        
        # Simula um tick de física, scripts e lógica no runtime
        manager.tick(0.016)

        # Verifica se o script recebeu o delta_time no update e detectou o Input
        lines = events_path.read_text().splitlines()
        assert "update:0.016" in lines
        assert "space_pressed" in lines

        # 7. Gizmos não alteram objetos (roda no editor_scene)
        draw_box_gizmo = GizmoRegistry.get_gizmo("BoxCollider")
        assert draw_box_gizmo is not None
        
        surface = pygame.Surface((100, 100))
        # Executa o Gizmo
        draw_box_gizmo(collider, surface, MagicMock())
        
        # Propriedades do colisor intactas no editor
        assert collider.width == 32
        assert collider.height == 32
        assert player_go.transform.position[0] == 0.0

        # 8. Stop Mode (stop_play)
        manager.stop_play()

        # Limpeza e reset do AudioManager e do Camera.main
        assert Camera.main is None
        assert AudioManager.get_active_listener() is None
        
        # Restaura AudioManager.play_sfx
        AudioManager.play_sfx = orig_play_sfx

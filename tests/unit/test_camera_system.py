import pytest
import json
from engine.core import GameObject, Scene, component_registry
from engine.graphics.camera import Camera
from engine.graphics.camera_manager import CameraManager
from engine.runtime.runtime_scene import RuntimeScene


@pytest.fixture(autouse=True)
def clean_camera_manager():
    """Limpa o CameraManager antes e depois de cada teste para garantir isolamento."""
    CameraManager.clear()
    yield
    CameraManager.clear()


def test_camera_component_initialization():
    """Verifica a inicialização dos atributos padrão da Câmera."""
    cam = Camera(zoom=2.0, clear_color=(10, 20, 30), viewport_rect=(0.1, 0.1, 0.8, 0.8), priority=10, active=True)
    assert cam.zoom == 2.0
    assert cam.clear_color == (10, 20, 30)
    assert cam.background_color == (10, 20, 30)
    assert cam.viewport_rect == (0.1, 0.1, 0.8, 0.8)
    assert cam.priority == 10
    assert cam.active is True
    assert cam.enabled is True

    # Testando setters e pseudônimos
    cam.background_color = (40, 50, 60)
    assert cam.clear_color == (40, 50, 60)
    cam.active = False
    assert cam.active is False


def test_camera_registration_and_removal():
    """Garante que as câmeras se registram no CameraManager ao iniciar e se removem ao serem destruídas."""
    scene = Scene("TestScene")
    go = GameObject("CamObj")
    cam = go.add_component(Camera(priority=5))

    # Registro ocorre quando o GameObject ganha uma cena e inicia os componentes
    assert cam not in CameraManager.get_all_cameras()
    scene.add_game_object(go)
    assert cam in CameraManager.get_all_cameras()

    # Remoção ocorre no destroy()
    go.destroy()
    assert cam not in CameraManager.get_all_cameras()


def test_main_camera_static_shortcut():
    """Verifica que Camera.main retorna a câmera principal ativa sem expor o CameraManager diretamente."""
    scene = Scene("TestScene")
    go1 = GameObject("Cam1")
    cam1 = go1.add_component(Camera(priority=5, active=True))
    scene.add_game_object(go1)
    
    go2 = GameObject("Cam2")
    cam2 = go2.add_component(Camera(priority=10, active=True))
    scene.add_game_object(go2)

    scene.start()

    # A de maior prioridade (cam2 com priority=10) deve ser a Camera.main
    assert Camera.main is cam2

    # Desativa cam2, agora cam1 deve ser a Camera.main
    cam2.active = False
    assert Camera.main is cam1


def test_camera_manager_set_main_camera():
    """Garante que definir uma câmera como principal desativa as demais."""
    scene = Scene("TestScene")
    go1 = GameObject("Cam1")
    cam1 = go1.add_component(Camera(priority=1, active=True))
    scene.add_game_object(go1)
    
    go2 = GameObject("Cam2")
    cam2 = go2.add_component(Camera(priority=2, active=True))
    scene.add_game_object(go2)

    scene.start()

    CameraManager.set_main_camera(cam1)
    assert cam1.active is True
    assert cam2.active is False
    assert Camera.main is cam1


def test_camera_serialization_deserialization():
    """Garante que a Câmera é serializada e desserializada corretamente de forma compatível com cenas e prefabs."""
    go = GameObject("SerializedCamera")
    cam = go.add_component(Camera(zoom=1.5, clear_color=(100, 150, 200), viewport_rect=(0.0, 0.0, 0.5, 0.5), priority=99, active=False))
    
    data = cam.serialize()
    assert data["type"] == "Camera"
    assert data["properties"]["zoom"] == 1.5
    assert data["properties"]["clear_color"] == [100, 150, 200]
    assert data["properties"]["viewport_rect"] == [0.0, 0.0, 0.5, 0.5]
    assert data["properties"]["priority"] == 99
    assert data["properties"]["active"] is False

    # Desserialização pelo component_registry
    cloned_cam = component_registry.create(data)
    assert cloned_cam.zoom == 1.5
    assert cloned_cam.clear_color == (100, 150, 200)
    assert cloned_cam.viewport_rect == (0.0, 0.0, 0.5, 0.5)
    assert cloned_cam.priority == 99
    assert cloned_cam.active is False


def test_runtime_scene_camera_isolation_and_fallback():
    """Valida o isolamento de câmeras no RuntimeScene e a criação da câmera de runtime padrão se não houver Main Camera."""
    scene = Scene("TestScene")
    
    # Criamos o RuntimeScene a partir de uma cena sem câmera
    runtime_scene = RuntimeScene(scene)
    
    # Antes de iniciar, o CameraManager deve ser limpo/inativo
    assert CameraManager.get_main_camera() is None

    # Inicia o Runtime. Deve criar a câmera padrão ('Default Runtime Camera')
    runtime_scene.start_runtime()
    
    main_cam = CameraManager.get_main_camera()
    assert main_cam is not None
    assert main_cam.game_object.name == "Default Runtime Camera"
    
    # Renderização usa a cor limpa da câmera
    import pygame
    surface = pygame.Surface((100, 100))
    runtime_scene.draw(surface)
    # A cor padrão da câmera (30, 30, 30) deve ser usada para limpar a tela
    color = surface.get_at((10, 10))
    assert (color.r, color.g, color.b) == (30, 30, 30)

    # Parando o runtime, o CameraManager é limpo de novo
    runtime_scene.stop_runtime()
    assert CameraManager.get_main_camera() is None


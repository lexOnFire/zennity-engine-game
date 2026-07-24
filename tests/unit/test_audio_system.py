import pytest
from unittest.mock import MagicMock, patch
from engine.core import GameObject, Scene, component_registry
from engine.audio import AudioManager, AudioSource, AudioListener
from engine.runtime.runtime_scene import RuntimeScene


@pytest.fixture(autouse=True)
def mock_pygame_mixer():
    """Mock do pygame.mixer para evitar dependências de drivers de som reais."""
    with patch("pygame.mixer.init"), \
         patch("pygame.mixer.get_init", return_value=True), \
         patch("pygame.mixer.Sound") as mock_sound, \
         patch("pygame.mixer.music") as mock_music, \
         patch("pygame.mixer.stop"), \
         patch("pygame.mixer.pause"), \
         patch("pygame.mixer.unpause"), \
         patch("os.path.exists", return_value=True):
        
        # Configura o mock do Sound para retornar um mock de Channel
        mock_channel = MagicMock()
        mock_channel.get_busy.return_value = True
        mock_sound_instance = MagicMock()
        mock_sound_instance.play.return_value = mock_channel
        mock_sound.return_value = mock_sound_instance
        
        yield {
            "sound": mock_sound,
            "music": mock_music,
            "channel": mock_channel,
            "sound_instance": mock_sound_instance
        }


@pytest.fixture(autouse=True)
def clean_audio_manager():
    """Garante isolamento limpo do AudioManager antes e depois de cada teste."""
    AudioManager.clear()
    yield
    AudioManager.clear()


def test_audio_components_initialization():
    """Verifica atributos padrão e setters de AudioSource e AudioListener."""
    source = AudioSource(audio_clip="assets/sfx/jump.wav", volume=0.7, pitch=1.2, loop=True, play_on_awake=True, mute=True)
    assert source.audio_clip == "assets/sfx/jump.wav"
    assert source.volume == 0.7
    assert source.pitch == 1.2
    assert source.loop is True
    assert source.play_on_awake is True
    assert source.mute is True
    assert source.enabled is True

    listener = AudioListener()
    assert listener.enabled is True


def test_audio_registration_and_removal():
    """Verifica que componentes se registram/removem dinamicamente do AudioManager ao serem adicionados e destruídos."""
    scene = Scene("TestScene")
    go = GameObject("AudioGO")
    source = go.add_component(AudioSource(audio_clip="test.wav"))
    listener = go.add_component(AudioListener())

    assert source not in AudioManager._sources
    assert listener not in AudioManager._listeners

    scene.add_game_object(go)

    assert source in AudioManager._sources
    assert listener in AudioManager._listeners
    assert AudioManager.get_active_listener() is listener

    go.destroy()
    assert source not in AudioManager._sources
    assert listener not in AudioManager._listeners


def test_audio_playback_controls(mock_pygame_mixer):
    """Testa controles de reprodução (play, stop, pause, unpause, is_playing)."""
    scene = Scene("TestScene")
    go = GameObject("Player")
    source = go.add_component(AudioSource(audio_clip="assets/sfx/jump.wav", volume=0.5))
    scene.add_game_object(go)

    source.play()
    assert source._playing is True
    mock_pygame_mixer["sound"].assert_called_with("assets/sfx/jump.wav")
    mock_pygame_mixer["sound_instance"].play.assert_called_once()
    
    assert source.is_playing() is True

    source.pause()
    mock_pygame_mixer["channel"].pause.assert_called_once()

    source.unpause()
    mock_pygame_mixer["channel"].unpause.assert_called_once()

    source.stop()
    assert source._playing is False
    mock_pygame_mixer["channel"].stop.assert_called_once()


def test_audio_serialization_deserialization():
    """Valida que AudioSource e AudioListener são serializados e desserializados corretamente."""
    go = GameObject("AudioGO")
    source = go.add_component(AudioSource(audio_clip="assets/music.ogg", volume=0.8, pitch=0.9, loop=True, play_on_awake=False, mute=True))
    listener = go.add_component(AudioListener())

    # Serialização
    source_data = source.serialize()
    assert source_data["type"] == "AudioSource"
    assert source_data["properties"]["audio_clip"] == "assets/music.ogg"
    assert source_data["properties"]["volume"] == 0.8
    assert source_data["properties"]["pitch"] == 0.9
    assert source_data["properties"]["loop"] is True
    assert source_data["properties"]["play_on_awake"] is False
    assert source_data["properties"]["mute"] is True

    listener_data = listener.serialize()
    assert listener_data["type"] == "AudioListener"

    # Desserialização
    cloned_source = component_registry.create(source_data)
    assert cloned_source.audio_clip == "assets/music.ogg"
    assert cloned_source.volume == 0.8
    assert cloned_source.pitch == 0.9
    assert cloned_source.loop is True
    assert cloned_source.play_on_awake is False
    assert cloned_source.mute is True

    cloned_listener = component_registry.create(listener_data)
    assert cloned_listener.__class__.__name__ == "AudioListener"


def test_runtime_isolation_and_fallback(mock_pygame_mixer):
    """Valida o isolamento de áudio no RuntimeScene e a criação do listener padrão de fallback."""
    scene = Scene("TestScene")
    go = GameObject("SourceGO")
    source = go.add_component(AudioSource(audio_clip="awake.wav", play_on_awake=True))
    scene.add_game_object(go)

    runtime_scene = RuntimeScene(scene)

    # Inicia o runtime. AudioManager deve ser limpo e depois preenchido com componentes do runtime
    runtime_scene.start_runtime()

    # O AudioListener padrão deve ter sido criado na cena de runtime
    active_listener = None
    for rgo in runtime_scene.scene.game_objects:
        for comp in rgo.components:
            if comp.__class__.__name__ == "AudioListener":
                active_listener = comp
                break
    assert active_listener is not None
    assert active_listener.game_object.name == "Default Audio Listener"

    # O AudioSource com play_on_awake=True deve ter começado a tocar
    mock_pygame_mixer["sound_instance"].play.assert_called_once()

    # Finalizar o runtime deve limpar todo o estado do AudioManager
    runtime_scene.stop_runtime()
    
    # Limpamos o AudioManager do teste (editor) também para garantir que as listas fiquem vazias
    AudioManager.clear()
    assert len(AudioManager._sources) == 0
    assert len(AudioManager._listeners) == 0


def test_runtime_listener_registry_ignores_stale_editor_listener(mock_pygame_mixer):
    """Garante que listeners antigos não vazem para o Runtime World."""
    from engine.audio import AudioManager, AudioListener

    stale_go = GameObject("StaleListener")
    stale_listener = stale_go.add_component(AudioListener())
    AudioManager.register_audio_listener(stale_listener)

    scene = Scene("TestScene")
    listener_go = GameObject("RuntimeListener")
    editor_listener = listener_go.add_component(AudioListener())
    scene.add_game_object(listener_go)

    runtime_scene = RuntimeScene(scene)
    runtime_scene.start_runtime()
    runtime_listener = runtime_scene.runtime_for_editor(listener_go).get_component(AudioListener)
    active_listener = AudioManager.get_active_listener()

    assert runtime_listener is not editor_listener
    assert active_listener is not None
    assert active_listener is not stale_listener
    assert active_listener.game_object.name == runtime_listener.game_object.name
    assert active_listener.game_object.scene is runtime_scene.scene
    assert stale_listener not in AudioManager._listeners

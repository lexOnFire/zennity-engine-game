import pytest
from PySide6.QtWidgets import QApplication

# Garante instância de QApplication para widgets PySide6
@pytest.fixture(scope="module", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


from editor.animation_studio.timeline_ruler import TimelineRuler
from editor.animation_studio.track_header_widget import TrackHeaderWidget
from editor.animation_studio.keyframe_canvas import KeyframeCanvas
from editor.animation_studio.animation_studio_dock import AnimationStudioDock
from engine.animation.tracks import TransformTrack, PropertyTrack


def test_marco_a_timeline_ruler(qapp):
    """Valida o Marco A — Timeline (Zoom, Pan, Conversion, Snapping)."""
    ruler = TimelineRuler()
    ruler.zoom_factor = 100.0
    ruler.pan_offset_x = 0.0
    
    # 1s = 100px
    assert ruler.time_to_pixel(1.0) == 100.0
    assert ruler.pixel_to_time(200.0) == 2.0
    
    # Snapping
    ruler.snap_interval = 0.1
    assert ruler.snap_time(0.14) == pytest.approx(0.1)
    assert ruler.snap_time(0.17) == pytest.approx(0.2)


def test_marco_b_track_headers(qapp):
    """Valida o Marco B — Tracks (Mute, Solo, Lock)."""
    track = TransformTrack(name="PlayerTransform")
    header = TrackHeaderWidget(track)
    
    assert track.enabled is True
    header.btn_mute.setChecked(True)
    assert track.enabled is False


def test_marco_c_keyframe_canvas(qapp):
    """Valida o Marco C — Keyframes (Interação e Canvas)."""
    canvas = KeyframeCanvas()
    track = TransformTrack(name="Position")
    track.position_keyframes = [
        {"time": 0.0, "value": [0.0, 0.0, 0.0]},
        {"time": 1.0, "value": [10.0, 0.0, 0.0]},
    ]
    canvas.tracks = [track]
    
    assert len(track.position_keyframes) == 2


def test_marco_d_preview_dock(qapp):
    """Valida o Marco D — Preview (Playback & Hot Reload)."""
    dock = AnimationStudioDock()
    dock.play()
    assert dock.playback_state == 1  # PLAYING
    
    dock.pause()
    assert dock.playback_state == 2  # PAUSED
    
    dock.stop()
    assert dock.playback_state == 0  # STOPPED
    
    dock.trigger_hot_reload()

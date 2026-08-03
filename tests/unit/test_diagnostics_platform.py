import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="module", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


from engine.core.bootstrap import EngineBootstrap
from engine.diagnostics.service import DiagnosticsService, PerformanceCounter
from editor.profiler.profiler_dock import ProfilerDock


def test_diagnostics_service():
    """Valida o serviço central de estatísticas de performance."""
    service = DiagnosticsService()
    service.initialize()

    fps = service.get_counter("fps")
    assert fps is not None
    assert fps.unit == "FPS"

    service.record_counter("fps", 60.0)
    service.record_counter("fps", 58.5)
    assert fps.current_value == 58.5
    assert len(fps.history) == 2

    summary = service.get_summary()
    assert "fps" in summary
    assert "frame_time" in summary


def test_diagnostics_provider_boots_metadata(qapp):
    """Valida a inicialização automática do DiagnosticsProvider pelo EngineBootstrap."""
    context = EngineBootstrap.boot()
    diag_service = context.services.get_optional(DiagnosticsService)
    assert diag_service is not None
    assert diag_service.get_counter("fps") is not None


def test_profiler_dock_client(qapp):
    """Valida o ProfilerDock como cliente da Diagnostics Platform."""
    context = EngineBootstrap.boot()
    dock = ProfilerDock()
    assert dock.lbl_fps.text().startswith("FPS:")
    dock._on_refresh()

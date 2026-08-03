import pytest
import time
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="module", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


from engine.core.bootstrap import EngineBootstrap
from engine.metadata.manager import MetadataManager
from engine.core.metadata.asset import AssetTypeDefinition
from engine.diagnostics.service import DiagnosticsService
from engine.extension.metadata import ExtensionPackageDefinition, ExtensionType
from editor.extension_manager.extension_dock import ExtensionManagerDock


def test_diagnostics_scoped_measurement():
    """Valida a medição por subsistemas (with diagnostics.measure("Physics"): ...)."""
    service = DiagnosticsService()
    service.initialize()

    with service.measure("Physics"):
        time.sleep(0.01)

    with service.measure("Renderer"):
        time.sleep(0.005)

    physics_ms = service.get_scope_time("Physics")
    renderer_ms = service.get_scope_time("Renderer")

    assert physics_ms > 0.0
    assert renderer_ms > 0.0
    assert "scope.Physics" in service.get_summary()


def test_extension_provider_boots_metadata(qapp):
    """Valida o registro automático das extensões e pacotes pelo ExtensionProvider."""
    context = EngineBootstrap.boot()
    manager = context.services.get(MetadataManager)

    asset_def = manager.get(AssetTypeDefinition, "extension_package")
    assert asset_def is not None
    assert ".zext" in asset_def.extensions

    exts = manager.get_all(ExtensionPackageDefinition)
    ext_ids = {e.id for e in exts}
    assert "ext.2d_physics" in ext_ids
    assert "ext.dark_theme" in ext_ids
    assert "ext.rpg_nodes" in ext_ids
    assert "ext.platformer_template" in ext_ids


def test_extension_manager_dock_client(qapp):
    """Valida o ExtensionManagerDock como cliente do Plugin Ecosystem."""
    context = EngineBootstrap.boot()
    dock = ExtensionManagerDock()
    assert dock.tree_ext.topLevelItemCount() >= 4

    dock.combo_filter.setCurrentText("Theme")
    assert dock.tree_ext.topLevelItemCount() >= 1

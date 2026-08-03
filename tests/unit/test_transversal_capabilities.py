import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="module", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


from engine.core.bootstrap import EngineBootstrap
from engine.assets.capabilities import AssetCapabilityDefinition, AssetCapabilitiesRegistry
from engine.assets.dependency_graph import AssetDependencyGraph
from engine.build.pipeline import BuildProfile, BuildPipeline
from engine.prefab.system import PrefabAsset
from editor.tools.dependency_viewer_dock import DependencyViewerDock
from editor.tools.build_report_dock import BuildReportDock
from editor.tools.asset_auditor_dock import AssetAuditorDock


def test_asset_transversal_capabilities():
    """Valida o registro de capacidades transversais de assets."""
    cap = AssetCapabilityDefinition(id="ui_layout", is_searchable=True, is_previewable=True)
    AssetCapabilitiesRegistry.register("ui_layout", cap)

    retrieved = AssetCapabilitiesRegistry.get("ui_layout")
    assert retrieved.is_searchable is True
    assert retrieved.is_previewable is True


def test_asset_dependency_graph():
    """Valida o grafo de dependências cruzadas entre assets."""
    graph = AssetDependencyGraph()
    graph.register_asset("Scene.zscene", "scene")
    graph.register_asset("Player.zbehavior", "behavior_tree")

    graph.add_dependency("Scene.zscene", "Player.zbehavior")
    assert graph.get_dependencies("Scene.zscene") == ["Player.zbehavior"]
    assert graph.get_references("Player.zbehavior") == ["Scene.zscene"]

    gdata = graph.to_graph_data()
    assert len(gdata["nodes"]) == 2
    assert len(gdata["connections"]) == 1


def test_build_pipeline():
    """Valida a infraestrutura de Build Pipeline e Exportação."""
    profile = BuildProfile(name="Release", target_platform="Windows", scenes=["Main.zscene", "Level1.zscene"])
    report = BuildPipeline.execute_build(profile)

    assert report.success is True
    assert report.total_assets_bundled > 0
    assert report.total_bytes_written > 0


def test_advanced_prefab_system():
    """Valida herança e overrides do sistema de prefabs avançado."""
    base_prefab = PrefabAsset("BaseEnemy")
    base_prefab.set_property("health", 100)
    base_prefab.set_property("speed", 5.0)

    variant = PrefabAsset("BossEnemy", parent_prefab=base_prefab)
    variant.set_property("health", 500)  # Override

    props = variant.get_resolved_properties()
    assert props["health"] == 500
    assert props["speed"] == 5.0


def test_production_tools_docks(qapp):
    """Valida os docks das ferramentas de produção."""
    context = EngineBootstrap.boot()

    dep_dock = DependencyViewerDock()
    assert dep_dock.graph_editor is not None

    build_dock = BuildReportDock()
    build_dock.run_build()
    assert "BUILD REPORT" in build_dock.txt_log.toPlainText()

    audit_dock = AssetAuditorDock()
    assert audit_dock.tree_audit.topLevelItemCount() >= 1

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="module", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


from engine.core.bootstrap import EngineBootstrap
from engine.metadata.manager import MetadataManager
from engine.core.metadata import NodeDefinition
from engine.core.metadata.asset import AssetTypeDefinition
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget
from editor.behavior_tree.behavior_tree_dock import BehaviorTreeEditorDock


def test_ai_provider_boots_metadata(qapp):
    """Valida o registro automático dos metadados de Behavior Tree via AIProvider."""
    context = EngineBootstrap.boot()
    manager = context.services.get(MetadataManager)

    asset_def = manager.get(AssetTypeDefinition, "behavior_tree")
    assert asset_def is not None
    assert ".zbehavior" in asset_def.extensions

    nodes = manager.get_all(NodeDefinition)
    node_ids = {n.id for n in nodes}
    assert "bt.selector" in node_ids
    assert "bt.sequence" in node_ids
    assert "bt.inverter" in node_ids
    assert "bt.wait" in node_ids
    assert "bt.move_to" in node_ids
    assert {
        "bt.repeat", "bt.cooldown", "bt.target_in_range",
        "bt.parameter_condition", "bt.chase", "bt.patrol",
        "bt.attack", "bt.play_animation",
    } <= node_ids


def test_generic_graph_editor_widget(qapp):
    """Valida a inicialização do editor de grafos genérico."""
    context = EngineBootstrap.boot()
    editor = GenericGraphEditorWidget(graph_category_filter="Behavior Tree")
    assert editor.category_filter == "Behavior Tree"
    assert editor.node_palette.topLevelItemCount() >= 1
    assert editor.inspector_tabs.tabText(0) == "Propriedades"
    assert editor.inspector_tabs.tabText(1) == "Ajuda"
    assert "Behavior Tree" in editor.help_browser.toPlainText()


def test_behavior_tree_library_is_localized_searchable_and_filterable(qapp):
    EngineBootstrap.boot()
    editor = GenericGraphEditorWidget(graph_category_filter="Behavior Tree")

    categories = {
        editor.node_palette.topLevelItem(index).text(0)
        for index in range(editor.node_palette.topLevelItemCount())
    }
    assert {"Composição", "Decoradores", "Condições", "Ações"} <= categories

    editor.search_edit.setText("perseguição")
    visible_nodes = [
        editor.node_palette.topLevelItem(index).child(child).text(0)
        for index in range(editor.node_palette.topLevelItemCount())
        for child in range(editor.node_palette.topLevelItem(index).childCount())
    ]
    assert visible_nodes == ["Mover até"]

    editor.search_edit.clear()
    editor.palette_category.setCurrentText("Decoradores")
    assert editor.node_palette.topLevelItemCount() == 1
    assert editor.node_palette.topLevelItem(0).text(0) == "Decoradores"


def test_palette_selection_updates_contextual_help(qapp):
    EngineBootstrap.boot()
    editor = GenericGraphEditorWidget(graph_category_filter="Behavior Tree")
    actions = next(
        editor.node_palette.topLevelItem(index)
        for index in range(editor.node_palette.topLevelItemCount())
        if editor.node_palette.topLevelItem(index).text(0) == "Ações"
    )
    chase = next(
        actions.child(index)
        for index in range(actions.childCount())
        if actions.child(index).text(0) == "Perseguir alvo"
    )

    editor.node_palette.itemClicked.emit(chase, 0)

    assert "Perseguir alvo" in editor.help_browser.toPlainText()
    assert "distância de parada" in editor.help_browser.toPlainText()


def test_delete_removes_selected_behavior_node_and_marks_document_dirty(qapp):
    EngineBootstrap.boot()
    editor = GenericGraphEditorWidget(graph_category_filter="Behavior Tree")
    changed = []
    editor.canvas.asset_changed.connect(lambda: changed.append(True))
    editor.canvas._spawn_node("bt.chase")
    node = next(iter(editor.canvas.scene.nodes.values()))
    node.setSelected(True)

    assert editor.canvas.delete_selection() is True
    assert editor.canvas.scene.nodes == {}
    assert changed
    assert editor.canvas.delete_shortcut.context() == Qt.WidgetWithChildrenShortcut


def test_behavior_tree_editor_dock_specialization(qapp):
    """Valida que o BehaviorTreeEditorDock reutiliza o GenericGraphEditorWidget sem código duplicado."""
    context = EngineBootstrap.boot()
    dock = BehaviorTreeEditorDock()
    assert dock.graph_editor.category_filter == "Behavior Tree"

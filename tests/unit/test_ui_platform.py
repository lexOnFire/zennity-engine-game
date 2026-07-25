import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="module", autouse=True)
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


from engine.core.bootstrap import EngineBootstrap
from engine.metadata.manager import MetadataManager
from engine.core.metadata.asset import AssetTypeDefinition, PreviewDefinition
from engine.ui.metadata import WidgetDefinition
from engine.ui.runtime import (
    UICanvas,
    UIPanel,
    UIButton,
    UILabel,
    UIImage,
    UIScrollView,
    UIInput,
    UIContainer,
)
from engine.ui.preview_provider import UIPreviewProvider
from editor.ui_builder.ui_builder_dock import UIBuilderDock


def test_fase_1_and_3_and_4_ui_provider_boots_metadata(qapp):
    """Valida o registro automático dos metadados de UI (Assets, Widgets e Preview)."""
    context = EngineBootstrap.boot()
    manager = context.services.get(MetadataManager)

    # 1. Assets (Fase 1)
    layout_def = manager.get(AssetTypeDefinition, "ui_layout")
    assert layout_def is not None
    assert ".zui" in layout_def.extensions

    theme_def = manager.get(AssetTypeDefinition, "ui_theme")
    assert theme_def is not None
    assert ".theme" in theme_def.extensions

    # 2. Widgets Metadata (Fase 3)
    btn_def = manager.get(WidgetDefinition, "ui.button")
    assert btn_def is not None
    assert btn_def.widget_type == "Button"

    # 3. Preview Definition (Fase 4)
    prev_def = manager.get(PreviewDefinition, "ui_preview")
    assert prev_def is not None


def test_fase_2_ui_runtime_hierarchy():
    """Valida a hierarquia runtime de UI e serialização."""
    canvas = UICanvas("MainCanvas")
    panel = UIPanel("HeaderPanel")
    button = UIButton("SubmitBtn")
    label = UILabel("TitleLabel")

    panel.add_child(button)
    panel.add_child(label)
    canvas.add_child(panel)

    assert len(canvas.children) == 1
    assert len(panel.children) == 2
    assert button.parent == panel

    serialized = canvas.serialize()
    assert serialized["type"] == "UICanvas"
    assert len(serialized["children"]) == 1


def test_fase_5_ui_builder_dock(qapp):
    """Valida o UI Builder Dock interagindo com a UI Platform."""
    context = EngineBootstrap.boot()
    dock = UIBuilderDock()

    # Adiciona botão e verifica a árvore de hierarquia
    dock.add_widget(UIButton("PlayButton"))
    assert len(dock.preview_canvas.canvas_runtime.children) == 1
    assert dock.tree_hierarchy.topLevelItemCount() == 1

from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtWidgets import QApplication, QTextEdit

from engine.core.bootstrap import EngineBootstrap
from engine.core.context import EngineContext
from editor.visual_scripting.visual_scripting_dock import VisualScriptingEditorDock
from editor.widgets.generic_graph_editor import GenericGraphEditorWidget


def test_specialized_palette_does_not_mix_unrelated_graph_domains() -> None:
    app = QApplication.instance() or QApplication([])
    if EngineContext.current() is None:
        EngineBootstrap.boot()
    editor = GenericGraphEditorWidget("Dialogue")
    try:
        categories = [
            editor.node_palette.topLevelItem(index).text(0)
            for index in range(editor.node_palette.topLevelItemCount())
        ]
        assert categories
        assert all(category.casefold().startswith("dialogue") for category in categories)
    finally:
        editor.deleteLater()
        app.processEvents()


def test_specialized_starter_creates_real_nodes() -> None:
    app = QApplication.instance() or QApplication([])
    if EngineContext.current() is None:
        EngineBootstrap.boot()
    editor = GenericGraphEditorWidget("Dialogue")
    try:
        editor.create_starter_graph()
        assert len(editor.canvas.scene.nodes) == 2
        assert editor.is_dirty
    finally:
        editor.deleteLater()
        app.processEvents()


def test_validation_uses_current_canvas_document(monkeypatch) -> None:
    app = QApplication.instance() or QApplication([])
    editor = GenericGraphEditorWidget("Dialogue")
    captured = {}
    service = SimpleNamespace(
        validate_graph=lambda nodes, edges: captured.update(
            nodes=nodes, edges=edges
        ) or []
    )
    context = SimpleNamespace(
        services=SimpleNamespace(get_optional=lambda _type: service)
    )
    monkeypatch.setattr(
        "editor.widgets.generic_graph_editor.EngineContext.current",
        lambda: context,
    )
    monkeypatch.setattr(
        editor.canvas,
        "graph_data",
        lambda: {
            "nodes": [{"id": "speech"}],
            "edges": [{
                "source_node": "speech",
                "target_node": "end",
                "source_port": "out",
                "target_port": "in",
            }],
        },
    )
    try:
        assert editor.validate_graph() == []
        assert captured["nodes"] == [{"id": "speech"}]
        assert captured["edges"][0]["from_node"] == "speech"
        assert captured["edges"][0]["to_node"] == "end"
        assert editor.document_status.text() == "Validação • grafo pronto"
    finally:
        editor.deleteLater()
        app.processEvents()


def test_runtime_profiler_displays_live_measurements() -> None:
    profiler = QTextEdit()
    dock = SimpleNamespace(profiler_text=profiler)
    VisualScriptingEditorDock.update_runtime_stats(
        dock, fps=50.0, object_count=12
    )
    text = profiler.toPlainText()
    assert "50.0" in text
    assert "20.00 ms" in text
    assert "12" in text
    profiler.deleteLater()

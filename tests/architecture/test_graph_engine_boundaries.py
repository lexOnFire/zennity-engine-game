"""Contrato da decisão arquitetural sobre os dois motores de Graph."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _python_sources(relative_dir: str) -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / relative_dir).rglob("*.py"))
    )


def test_specialized_logic_canvas_does_not_depend_on_generic_graph_engine() -> None:
    source = _python_sources("editor/widgets/logic_graph")
    assert "engine.graphs" not in source
    assert "editor.widgets.graph_editor" not in source


def test_generic_canvas_does_not_depend_on_logic_graph_engine() -> None:
    source = _python_sources("editor/widgets/graph_editor")
    assert "engine.logic" not in source
    assert "editor.widgets.logic_graph" not in source


def test_architecture_documents_the_intentional_split() -> None:
    architecture = (ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "Por que existem dois motores de Graph" in architecture
    assert "manter permanentemente dois motores de canvas separados por domínio" in architecture

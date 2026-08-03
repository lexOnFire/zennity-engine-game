"""Gate das classes monitoradas na auditoria estrutural pré-v1."""
from __future__ import annotations

import ast
from pathlib import Path


AUDIT = Path("docs/architecture/PRE_V1_FINAL_AUDIT.md")
MONITORED_CLASSES = {
    "editor/phase1_editor.py": "ZennityPhase1Editor",
    "engine/logic/runtime/core.py": "LogicGraphRuntime",
    "editor/widgets/phase1_viewport.py": "Phase1ViewportWidget",
    "editor/windows/main_window.py": "MainWindow",
    "editor/widgets/viewport_widget.py": "ViewportWidget",
}


def _class_size(path: str, class_name: str) -> int:
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    node = next(
        item
        for item in tree.body
        if isinstance(item, ast.ClassDef) and item.name == class_name
    )
    return node.end_lineno - node.lineno + 1


def test_monitored_classes_remain_below_release_budget() -> None:
    sizes = {
        class_name: _class_size(path, class_name)
        for path, class_name in MONITORED_CLASSES.items()
    }
    assert all(size < 500 for size in sizes.values()), sizes


def test_audit_reports_current_ast_measurements() -> None:
    audit = AUDIT.read_text(encoding="utf-8")
    for path, class_name in MONITORED_CLASSES.items():
        size = _class_size(path, class_name)
        assert f"{class_name}` | {size} |" in audit

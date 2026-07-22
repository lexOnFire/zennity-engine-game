from __future__ import annotations

import ast
from pathlib import Path

from editor.entrypoints import CANONICAL_ENTRYPOINT, LEGACY_ENTRYPOINTS


def test_phase1_is_the_only_public_editor_entrypoint() -> None:
    assert CANONICAL_ENTRYPOINT == "editor.phase1_main"
    assert len(LEGACY_ENTRYPOINTS) == 5


def test_legacy_launchers_are_thin_redirects_without_qt_bootstraps() -> None:
    for module_name in LEGACY_ENTRYPOINTS:
        path = Path(*module_name.split(".")).with_suffix(".py")
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]

        assert "QApplication" not in source
        assert "run_deprecated_entrypoint" in source
        redirect_calls = [
            call for call in calls
            if isinstance(call.func, ast.Name) and call.func.id == "run_deprecated_entrypoint"
        ]
        assert len(redirect_calls) == 1

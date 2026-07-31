"""Official Phase 1 editor application entrypoint."""
from __future__ import annotations

import sys

from editor.editor_app.bootstrap import run_isolated_editor


def main(argv: list[str] | None = None) -> None:
    """Start the single official editor shell."""
    run_isolated_editor()

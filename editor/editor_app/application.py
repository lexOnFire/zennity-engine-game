"""Official Phase 1 editor application entrypoint."""
from __future__ import annotations

import sys

from editor.editor_app.bootstrap import run_isolated_editor, run_legacy_embedded_editor


def main(argv: list[str] | None = None) -> None:
    """Start the single official editor shell."""
    args = list(sys.argv if argv is None else argv)
    if "--legacy-embedded" in args:
        run_legacy_embedded_editor(args)
        return
    run_isolated_editor()

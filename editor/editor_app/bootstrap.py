"""Bootstrap boundaries for the official Phase 1 editor."""
from __future__ import annotations


def run_isolated_editor() -> None:
    """Run the modern isolated viewport editor."""
    from editor.isolated_editor_main import main as isolated_main

    isolated_main()

"""Entrypoint oficial do Zennity Phase 1."""
from __future__ import annotations


def main() -> None:
    from editor.editor_app.application import main as run_editor

    run_editor()


if __name__ == "__main__":
    main()

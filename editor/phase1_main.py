"""Entrypoint oficial do Zennity Phase 1."""
from __future__ import annotations

import os
os.environ["PYGAME_PARACHUTE"] = "0"
os.environ["SDL_FORCE_EXIT"] = "0"


def main() -> None:
    from editor.editor_app.application import main as run_editor

    run_editor()


if __name__ == "__main__":
    main()

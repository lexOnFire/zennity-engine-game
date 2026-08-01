"""Compatibility launcher; use editor.phase1_main."""
from __future__ import annotations

from editor.entrypoints import run_deprecated_entrypoint


def main() -> None:
    run_deprecated_entrypoint("editor.studio_main")


if __name__ == "__main__":
    main()

"""Public editor entrypoint policy and compatibility redirects."""
from __future__ import annotations

import warnings
from typing import NoReturn

CANONICAL_ENTRYPOINT = "editor.phase1_main"
LEGACY_ENTRYPOINTS = (
    "editor.main",
    "editor.premium_main",
    "editor.studio_main",
    "editor.mvp_main",
    "editor.fixed_studio_main",
)


def run_deprecated_entrypoint(module_name: str) -> NoReturn:
    """Redirect a legacy launcher to the canonical editor bootstrap."""
    warnings.warn(
        f"{module_name} is deprecated; use python -m {CANONICAL_ENTRYPOINT}",
        FutureWarning,
        stacklevel=2,
    )
    from editor.phase1_main import main

    main()
    raise SystemExit(0)

"""Registro explícito dos entrypoints suportados e de compatibilidade."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EditorEntrypoint:
    module: str
    status: str
    description: str


OFFICIAL_ENTRYPOINT = EditorEntrypoint(
    module="editor.phase1_main",
    status="official",
    description="Shell PySide6 com viewport Pygame em processo isolado.",
)

COMPATIBILITY_ENTRYPOINTS = (
    EditorEntrypoint("editor.phase1_main --legacy-embedded", "compatibility", "Phase 1 embutido."),
    EditorEntrypoint("editor.main", "deprecated", "Launcher histórico."),
    EditorEntrypoint("editor.studio_main", "deprecated", "Protótipo Studio."),
    EditorEntrypoint("editor.mvp_main", "deprecated", "Protótipo MVP."),
    EditorEntrypoint("editor.premium_main", "deprecated", "Protótipo Premium."),
)


def supported_entrypoints() -> tuple[EditorEntrypoint, ...]:
    return (OFFICIAL_ENTRYPOINT, *COMPATIBILITY_ENTRYPOINTS)

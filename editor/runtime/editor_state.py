from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EditorState:
    """Estado compartilhado do editor que nao pertence a nenhum widget."""

    is_playing: bool = False
    camera_mode: str = "2D"
    grid_visible: bool = True
    grid_size: int = 32
    snap_enabled: bool = False
    snap_size: int = 16
    snap_angle: int = 15  # graus — usado pela Rotate Tool quando snap esta ativo

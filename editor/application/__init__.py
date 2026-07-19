"""Application-layer services for the Zennity editor.

This package keeps editor state and use cases independent from Qt and Pygame so
UI classes can gradually become thin adapters without a risky rewrite.
"""

from .editor_state import EditorState
from .scene_manager import SceneManager

__all__ = ["EditorState", "SceneManager"]

"""Canonical Transform import.

Transform remains implemented beside Component because both types share the
same ownership and lifecycle. This module provides the focused public path
``engine.core.transform.Transform`` without duplicating the implementation.
"""

from engine.core.component import Transform

__all__ = ["Transform"]

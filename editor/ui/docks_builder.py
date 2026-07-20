"""Composition root for the editor navigation, inspector, and bottom panels."""
from editor.ui.bottom_panels_builder import build_bottom_panels
from editor.ui.inspector_builder import build_inspector_dock
from editor.ui.navigation_builder import build_navigation_panels


def build_docks_layout(window):
    left = build_navigation_panels(window)
    build_inspector_dock(window)
    build_bottom_panels(window, left)

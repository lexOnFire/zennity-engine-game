"""
Phase 4B: UIRuntimeCompiler - Convert .zui authoring widgets to runtime components

Responsabilidade única: Transformar estruturas de authoring em runtime components.
"""
from __future__ import annotations

from typing import Any, Callable
import logging

logger = logging.getLogger(__name__)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    if not isinstance(hex_color, str):
        return (255, 255, 255)

    hex_color = hex_color.strip().lstrip("#")
    if len(hex_color) != 6:
        return (255, 255, 255)

    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return (r, g, b)
    except ValueError:
        return (255, 255, 255)


def rgb_to_hex(rgb: tuple[int, int, int] | list[int]) -> str:
    """Convert RGB tuple/list to hex color string."""
    try:
        r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        return f"#{r:02x}{g:02x}{b:02x}"
    except (IndexError, ValueError, TypeError):
        return "#ffffff"


class UICompilerError(Exception):
    """Base exception for UI compilation errors."""
    pass


class UICompilerWidgetError(UICompilerError):
    """Raised when a widget fails to compile."""
    pass


class UIRuntimeCompiler:
    """Compile .zui authoring widgets into runtime components."""

    # Registry of widget compilers
    WIDGET_COMPILERS: dict[str, Callable] = {}

    def __init__(self):
        """Initialize compiler with default widget handlers."""
        self._register_default_compilers()

    def _register_default_compilers(self):
        """Register built-in widget compilers."""
        self.register_compiler("uilabel", self._compile_label)
        self.register_compiler("label", self._compile_label)
        self.register_compiler("text", self._compile_label)

        self.register_compiler("uiimage", self._compile_image)
        self.register_compiler("image", self._compile_image)

        self.register_compiler("uibutton", self._compile_button)
        self.register_compiler("button", self._compile_button)

        self.register_compiler("uiprogressbar", self._compile_progress_bar)
        self.register_compiler("progressbar", self._compile_progress_bar)
        self.register_compiler("progress_bar", self._compile_progress_bar)
        self.register_compiler("progress", self._compile_progress_bar)

        self.register_compiler("uipanel", self._compile_panel)
        self.register_compiler("panel", self._compile_panel)

    def register_compiler(self, widget_type: str, compiler_func: Callable):
        """Register a custom compiler function for a widget type."""
        self.WIDGET_COMPILERS[widget_type.lower().strip()] = compiler_func

    def compile(self, ui_document: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Compile a UI document into a list of runtime widget definitions.

        Args:
            ui_document: Validated UI document from UIAssetLoader

        Returns:
            List of compiled widget definitions ready for instantiation

        Raises:
            UICompilerError: If compilation fails
        """
        if not isinstance(ui_document, dict):
            raise UICompilerError("UI document must be a dictionary")

        canvas = ui_document.get("canvas") or ui_document
        widgets = []

        # Compile canvas children recursively
        self._compile_widgets_recursive(canvas, widgets, parent_name=None)

        return widgets

    def _compile_widgets_recursive(
        self,
        widget: Any,
        result: list[dict[str, Any]],
        parent_name: str | None = None,
        z_order: int = 0,
    ) -> None:
        """Recursively compile widgets."""
        if not isinstance(widget, dict):
            return

        widget_type = str(widget.get("type", "")).lower().strip()

        # Canvas container - compile children
        if widget_type in ("canvas", "panel", "uipanel") or not widget_type:
            for child in widget.get("children", []):
                self._compile_widgets_recursive(child, result, parent_name, z_order)
            return

        # Try to compile this widget
        try:
            compiled = self._compile_widget(widget, widget_type, parent_name, z_order)
            if compiled:
                result.append(compiled)
                # Compile children of this widget
                for child in widget.get("children", []):
                    widget_name = str(widget.get("name", "")).strip()
                    self._compile_widgets_recursive(child, result, widget_name, z_order + 1)
        except UICompilerWidgetError as e:
            logger.error(f"Failed to compile widget: {e}")
            raise

    def _compile_widget(
        self,
        widget: dict[str, Any],
        widget_type: str,
        parent_name: str | None = None,
        z_order: int = 0,
    ) -> dict[str, Any] | None:
        """Compile a single widget using registered compiler."""
        compiler_func = self.WIDGET_COMPILERS.get(widget_type)
        if not compiler_func:
            raise UICompilerWidgetError(
                f"Unsupported widget type: {widget_type}"
            )

        try:
            return compiler_func(widget, parent_name, z_order)
        except Exception as e:
            widget_name = widget.get("name", "unnamed")
            raise UICompilerWidgetError(
                f"Widget '{widget_name}' (type: {widget_type}): {e}"
            )

    # ========== Widget Compilers ==========

    @staticmethod
    def _compile_label(
        widget: dict[str, Any],
        parent_name: str | None = None,
        z_order: int = 0,
    ) -> dict[str, Any]:
        """Compile a label/text widget to runtime component."""
        widget_name = str(widget.get("name", "Label")).strip()

        # Color handling
        color = widget.get("text_color") or widget.get("color")
        if isinstance(color, str):
            color = hex_to_rgb(color)
        elif isinstance(color, (list, tuple)) and len(color) >= 3:
            color = tuple(int(c) for c in color[:3])
        else:
            color = (255, 255, 255)

        return {
            "type": "LabelComponent",
            "widget_name": widget_name,
            "properties": {
                "text": str(widget.get("text", "")),
                "font_size": int(widget.get("font_size", 24)),
                "color": color,
                "x": float(widget.get("x", 0.0)),
                "y": float(widget.get("y", 0.0)),
                "width": float(widget.get("width", 200.0)),
                "height": float(widget.get("height", 30.0)),
                "visible": bool(widget.get("visible", True)),
                "alpha": int(widget.get("alpha", 255)),
                "z_order": z_order,
            }
        }

    @staticmethod
    def _compile_image(
        widget: dict[str, Any],
        parent_name: str | None = None,
        z_order: int = 0,
    ) -> dict[str, Any]:
        """Compile an image widget to runtime component."""
        widget_name = str(widget.get("name", "Image")).strip()

        return {
            "type": "ImageComponent",
            "widget_name": widget_name,
            "properties": {
                "texture_path": str(widget.get("texture_path", widget.get("path", ""))),
                "x": float(widget.get("x", 0.0)),
                "y": float(widget.get("y", 0.0)),
                "width": float(widget.get("width", 100.0)),
                "height": float(widget.get("height", 100.0)),
                "visible": bool(widget.get("visible", True)),
                "alpha": int(widget.get("alpha", 255)),
                "z_order": z_order,
            }
        }

    @staticmethod
    def _compile_button(
        widget: dict[str, Any],
        parent_name: str | None = None,
        z_order: int = 0,
    ) -> dict[str, Any]:
        """Compile a button widget to runtime component."""
        widget_name = str(widget.get("name", "Button")).strip()

        color = widget.get("color")
        if isinstance(color, str):
            color = hex_to_rgb(color)
        elif isinstance(color, (list, tuple)) and len(color) >= 3:
            color = tuple(int(c) for c in color[:3])
        else:
            color = (100, 100, 100)

        return {
            "type": "ButtonComponent",
            "widget_name": widget_name,
            "properties": {
                "text": str(widget.get("text", "Button")),
                "x": float(widget.get("x", 0.0)),
                "y": float(widget.get("y", 0.0)),
                "width": float(widget.get("width", 120.0)),
                "height": float(widget.get("height", 40.0)),
                "color": color,
                "visible": bool(widget.get("visible", True)),
                "interactable": bool(widget.get("interactable", True)),
                "z_order": z_order,
            }
        }

    @staticmethod
    def _compile_progress_bar(
        widget: dict[str, Any],
        parent_name: str | None = None,
        z_order: int = 0,
    ) -> dict[str, Any]:
        """Compile a progress bar widget to ProgressBarComponent."""
        widget_name = str(widget.get("name", "ProgressBar")).strip()

        # Color handling for fill_color
        fill_color = widget.get("fill_color")
        if isinstance(fill_color, str):
            fill_color = hex_to_rgb(fill_color)
        elif isinstance(fill_color, (list, tuple)) and len(fill_color) >= 3:
            fill_color = tuple(int(c) for c in fill_color[:3])
        else:
            fill_color = (46, 204, 113)  # Default green

        # Color handling for bg_color
        bg_color = widget.get("bg_color")
        if isinstance(bg_color, str):
            bg_color = hex_to_rgb(bg_color)
        elif isinstance(bg_color, (list, tuple)) and len(bg_color) >= 3:
            bg_color = tuple(int(c) for c in bg_color[:3])
        else:
            bg_color = (28, 35, 48)  # Default dark

        # Ensure value doesn't exceed max_value
        value = float(widget.get("value", 50.0))
        max_value = float(widget.get("max_value", 100.0))
        if value > max_value:
            value = max_value

        return {
            "type": "ProgressBarComponent",
            "widget_name": widget_name,
            "properties": {
                "value": value,
                "max_value": max_value,
                "x": float(widget.get("x", 0.0)),
                "y": float(widget.get("y", 0.0)),
                "width": float(widget.get("width", 200.0)),
                "height": float(widget.get("height", 20.0)),
                "fill_color": fill_color,
                "bg_color": bg_color,
                "visible": bool(widget.get("visible", True)),
                "alpha": int(widget.get("alpha", 255)),
                "z_order": z_order,
            }
        }

    @staticmethod
    def _compile_panel(
        widget: dict[str, Any],
        parent_name: str | None = None,
        z_order: int = 0,
    ) -> dict[str, Any] | None:
        """Panels are containers - don't create a component, children are compiled instead."""
        # Panels are purely structural; children will be compiled
        # This returns None because panels themselves don't become components
        return None

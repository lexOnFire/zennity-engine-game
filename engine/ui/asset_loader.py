"""
Phase 4B: UIAssetLoader - Load and validate .zui files

Responsabilidade única: Ler e validar arquivos .zui do disco.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class UIAssetLoaderError(Exception):
    """Base exception for UI asset loading errors."""
    pass


class UIAssetValidationError(UIAssetLoaderError):
    """Raised when a .zui asset fails validation."""
    pass


class UIAssetNotFoundError(UIAssetLoaderError):
    """Raised when a .zui asset file cannot be found."""
    pass


class UIAssetLoader:
    """Load and validate .zui (UI layout) assets from disk."""

    def __init__(self, project_root: str | Path | None = None):
        """Initialize loader with optional project root for relative paths."""
        self.project_root = Path(project_root or Path.cwd())

    def load(self, path: str | Path) -> dict[str, Any]:
        """
        Load a .zui file and return validated UI document.

        Args:
            path: File path (relative or absolute)

        Returns:
            Validated UI document dict

        Raises:
            UIAssetNotFoundError: If file doesn't exist
            UIAssetValidationError: If file is invalid
        """
        file_path = self._resolve_path(path)

        if not file_path.is_file():
            raise UIAssetNotFoundError(
                f"UI asset not found: {path}\n"
                f"Resolved path: {file_path}"
            )

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise UIAssetValidationError(
                f"Invalid JSON in UI asset: {path}\n"
                f"Error: {e}"
            )
        except Exception as e:
            raise UIAssetValidationError(
                f"Failed to read UI asset: {path}\n"
                f"Error: {e}"
            )

        # Validate the document
        self.validate(data)

        return data

    def validate(self, document: dict[str, Any]) -> None:
        """
        Validate a UI document structure.

        Raises:
            UIAssetValidationError: If validation fails
        """
        if not isinstance(document, dict):
            raise UIAssetValidationError(
                f"UI asset must be a JSON object, got {type(document).__name__}"
            )

        # Extract canvas (can be in root or under "canvas" key)
        canvas = document.get("canvas") or document

        if not isinstance(canvas, dict):
            raise UIAssetValidationError(
                "Canvas must be a dictionary"
            )

        # Validate canvas type
        canvas_type = str(canvas.get("type", "")).lower().strip()
        if canvas_type not in ("canvas", "panel", ""):
            raise UIAssetValidationError(
                f"Invalid canvas type: {canvas_type}"
            )

        # Validate children
        children = canvas.get("children", [])
        if not isinstance(children, list):
            raise UIAssetValidationError(
                "Canvas children must be a list"
            )

        # Check for duplicate widget names
        widget_names = set()
        self._validate_widgets_recursive(canvas, widget_names)

    def _validate_widgets_recursive(self, widget: Any, seen_names: set[str]) -> None:
        """Recursively validate widgets and track names for duplicates."""
        if not isinstance(widget, dict):
            return

        widget_type = str(widget.get("type", "")).lower().strip()
        if not widget_type or widget_type == "canvas":
            # Canvas container - process children
            for child in widget.get("children", []):
                self._validate_widgets_recursive(child, seen_names)
            return

        # This is a widget
        widget_name = str(widget.get("name", "")).strip()
        if widget_name:
            if widget_name in seen_names:
                raise UIAssetValidationError(
                    f"Duplicate widget name: {widget_name}\n"
                    f"Widget names must be unique within a .zui asset"
                )
            seen_names.add(widget_name)

        # Validate widget type
        if not self._is_valid_widget_type(widget_type):
            raise UIAssetValidationError(
                f"Unknown widget type: {widget_type}"
            )

        # Validate required properties based on type
        self._validate_widget_properties(widget, widget_type)

        # Recursively validate children
        for child in widget.get("children", []):
            self._validate_widgets_recursive(child, seen_names)

    @staticmethod
    def _is_valid_widget_type(widget_type: str) -> bool:
        """Check if widget type is recognized."""
        valid_types = {
            "uilabel", "label", "text",
            "uiimage", "image",
            "uibutton", "button",
            "uiprogressbar", "progressbar", "progress_bar",
            "uipanel", "panel",
        }
        return widget_type in valid_types

    @staticmethod
    def _validate_widget_properties(widget: dict[str, Any], widget_type: str) -> None:
        """Validate type-specific properties."""
        if widget_type in ("uilabel", "label", "text"):
            # Label/Text validation
            if "text" in widget and not isinstance(widget["text"], (str, type(None))):
                raise UIAssetValidationError(
                    f"Label 'text' must be a string, got {type(widget['text']).__name__}"
                )
            if "font_size" in widget:
                try:
                    size = int(widget["font_size"])
                    if size <= 0:
                        raise UIAssetValidationError(
                            f"Label 'font_size' must be > 0, got {size}"
                        )
                except (ValueError, TypeError):
                    raise UIAssetValidationError(
                        f"Label 'font_size' must be an integer, got {widget['font_size']}"
                    )

        elif widget_type in ("uiprogressbar", "progressbar", "progress_bar"):
            # ProgressBar validation
            if "value" in widget:
                try:
                    value = float(widget["value"])
                    if value < 0:
                        raise UIAssetValidationError(
                            f"ProgressBar 'value' must be >= 0, got {value}"
                        )
                except (ValueError, TypeError):
                    raise UIAssetValidationError(
                        f"ProgressBar 'value' must be a number, got {widget['value']}"
                    )

            if "max_value" in widget:
                try:
                    max_val = float(widget["max_value"])
                    if max_val <= 0:
                        raise UIAssetValidationError(
                            f"ProgressBar 'max_value' must be > 0, got {max_val}"
                        )
                except (ValueError, TypeError):
                    raise UIAssetValidationError(
                        f"ProgressBar 'max_value' must be a number > 0, got {widget['max_value']}"
                    )

            # Validate value is not greater than max_value
            try:
                if "value" in widget and "max_value" in widget:
                    value = float(widget["value"])
                    max_val = float(widget["max_value"])
                    if value > max_val:
                        raise UIAssetValidationError(
                            f"ProgressBar 'value' ({value}) cannot exceed 'max_value' ({max_val})"
                        )
            except (ValueError, TypeError):
                pass  # Already validated above

        elif widget_type in ("uiimage", "image"):
            # Image validation
            if "texture_path" in widget and not isinstance(widget["texture_path"], (str, type(None))):
                raise UIAssetValidationError(
                    f"Image 'texture_path' must be a string, got {type(widget['texture_path']).__name__}"
                )

        elif widget_type in ("uibutton", "button"):
            # Button validation
            if "text" in widget and not isinstance(widget["text"], (str, type(None))):
                raise UIAssetValidationError(
                    f"Button 'text' must be a string, got {type(widget['text']).__name__}"
                )

    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve path relative to project root if not absolute."""
        file_path = Path(path)
        if file_path.is_absolute():
            return file_path
        return self.project_root / file_path

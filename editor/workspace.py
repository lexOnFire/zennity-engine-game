from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DEFAULT_LAYOUT = "Default"
COMPACT_LAYOUT = "Compact"
ANIMATION_LAYOUT = "Animation"


@dataclass
class WorkspaceLayout:
    """Serializable editor workspace layout.

    This is intentionally independent from PySide widgets so the editor can test
    workspace behavior without opening a UI window.
    """

    name: str = DEFAULT_LAYOUT
    visible_panels: dict[str, bool] = field(default_factory=dict)
    splitter_sizes: dict[str, list[int]] = field(default_factory=dict)
    active_tabs: dict[str, str] = field(default_factory=dict)

    def normalized_name(self) -> str:
        value = str(self.name or DEFAULT_LAYOUT).strip()
        return value or DEFAULT_LAYOUT

    def set_panel_visible(self, panel_name: str, visible: bool) -> None:
        key = str(panel_name or "").strip()
        if key:
            self.visible_panels[key] = bool(visible)

    def is_panel_visible(self, panel_name: str, default: bool = True) -> bool:
        key = str(panel_name or "").strip()
        return bool(self.visible_panels.get(key, default))

    def set_splitter_sizes(self, splitter_name: str, sizes: list[int] | tuple[int, ...]) -> None:
        key = str(splitter_name or "").strip()
        if key:
            self.splitter_sizes[key] = [max(0, int(size)) for size in sizes]

    def set_active_tab(self, tab_group: str, tab_name: str) -> None:
        key = str(tab_group or "").strip()
        value = str(tab_name or "").strip()
        if key and value:
            self.active_tabs[key] = value

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.normalized_name(),
            "visible_panels": dict(self.visible_panels),
            "splitter_sizes": {key: list(value) for key, value in self.splitter_sizes.items()},
            "active_tabs": dict(self.active_tabs),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "WorkspaceLayout":
        if not data:
            return cls()
        layout = cls(name=str(data.get("name", DEFAULT_LAYOUT) or DEFAULT_LAYOUT))
        for key, value in dict(data.get("visible_panels", {})).items():
            layout.set_panel_visible(str(key), bool(value))
        for key, value in dict(data.get("splitter_sizes", {})).items():
            if type(value) in (list, tuple):
                layout.set_splitter_sizes(str(key), value)
        for key, value in dict(data.get("active_tabs", {})).items():
            layout.set_active_tab(str(key), str(value))
        return layout


def default_workspace_layout() -> WorkspaceLayout:
    layout = WorkspaceLayout(name=DEFAULT_LAYOUT)
    for panel in ("Hierarchy", "Assets", "Inspector", "Console", "Preview", "Profiler"):
        layout.set_panel_visible(panel, True)
    layout.set_splitter_sizes("main", [260, 850, 300])
    layout.set_splitter_sizes("left", [380, 360])
    layout.set_splitter_sizes("center", [560, 150, 170])
    layout.set_active_tab("viewport", "Scene")
    layout.set_active_tab("hierarchy", "Hierarchy")
    layout.set_active_tab("assets", "Assets")
    return layout


def compact_workspace_layout() -> WorkspaceLayout:
    layout = default_workspace_layout()
    layout.name = COMPACT_LAYOUT
    layout.set_panel_visible("Profiler", False)
    layout.set_panel_visible("Preview", False)
    layout.set_splitter_sizes("main", [220, 780, 260])
    layout.set_splitter_sizes("center", [720, 160, 0])
    return layout


def animation_workspace_layout() -> WorkspaceLayout:
    layout = default_workspace_layout()
    layout.name = ANIMATION_LAYOUT
    layout.set_panel_visible("Preview", True)
    layout.set_panel_visible("Console", True)
    layout.set_splitter_sizes("main", [240, 900, 320])
    layout.set_splitter_sizes("center", [500, 180, 240])
    layout.set_active_tab("viewport", "Scene")
    return layout


class WorkspaceManager:
    """Small registry for editor workspace presets and current layout."""

    def __init__(self) -> None:
        self._layouts: dict[str, WorkspaceLayout] = {}
        self.current = default_workspace_layout()
        self.register(self.current)
        self.register(compact_workspace_layout())
        self.register(animation_workspace_layout())

    def register(self, layout: WorkspaceLayout) -> None:
        self._layouts[layout.normalized_name()] = WorkspaceLayout.from_dict(layout.to_dict())

    def available_layouts(self) -> list[str]:
        return sorted(self._layouts.keys())

    def apply(self, name: str) -> WorkspaceLayout:
        key = str(name or DEFAULT_LAYOUT).strip() or DEFAULT_LAYOUT
        layout = self._layouts.get(key, self._layouts[DEFAULT_LAYOUT])
        self.current = WorkspaceLayout.from_dict(layout.to_dict())
        return self.current

    def capture(self, layout: WorkspaceLayout) -> None:
        self.current = WorkspaceLayout.from_dict(layout.to_dict())
        self.register(self.current)

    def reset(self) -> WorkspaceLayout:
        return self.apply(DEFAULT_LAYOUT)

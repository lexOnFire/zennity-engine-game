"""Serializable workspace presets kept independent from Qt widgets."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


DEFAULT_LAYOUT = "Default"
COMPACT_LAYOUT = "Compact"
ANIMATION_LAYOUT = "Animation"


@dataclass
class WorkspaceLayout:
    name: str = DEFAULT_LAYOUT
    visible_panels: dict[str, bool] = field(default_factory=dict)
    splitter_sizes: dict[str, list[int]] = field(default_factory=dict)
    active_tabs: dict[str, str] = field(default_factory=dict)

    def normalized_name(self) -> str:
        return str(self.name or DEFAULT_LAYOUT).strip() or DEFAULT_LAYOUT

    def set_panel_visible(self, panel_name: str, visible: bool) -> None:
        if key := str(panel_name or "").strip():
            self.visible_panels[key] = bool(visible)

    def is_panel_visible(self, panel_name: str, default: bool = True) -> bool:
        return bool(self.visible_panels.get(str(panel_name or "").strip(), default))

    def set_splitter_sizes(self, splitter_name: str, sizes) -> None:
        if key := str(splitter_name or "").strip():
            self.splitter_sizes[key] = [max(0, int(size)) for size in sizes]

    def set_active_tab(self, tab_group: str, tab_name: str) -> None:
        key, value = str(tab_group or "").strip(), str(tab_name or "").strip()
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
        layout = cls(name=str((data or {}).get("name", DEFAULT_LAYOUT) or DEFAULT_LAYOUT))
        for key, value in dict((data or {}).get("visible_panels", {})).items():
            layout.set_panel_visible(key, value)
        for key, value in dict((data or {}).get("splitter_sizes", {})).items():
            if isinstance(value, (list, tuple)):
                layout.set_splitter_sizes(key, value)
        for key, value in dict((data or {}).get("active_tabs", {})).items():
            layout.set_active_tab(key, value)
        return layout


def default_workspace_layout() -> WorkspaceLayout:
    layout = WorkspaceLayout()
    for panel in ("Hierarchy", "Assets", "Inspector", "Console", "Preview", "Profiler"):
        layout.set_panel_visible(panel, True)
    layout.set_splitter_sizes("main", [260, 850, 300])
    layout.set_splitter_sizes("left", [380, 360])
    layout.set_splitter_sizes("center", [560, 150, 170])
    layout.set_active_tab("viewport", "Scene")
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
    layout.set_splitter_sizes("main", [240, 900, 320])
    layout.set_splitter_sizes("center", [500, 180, 240])
    return layout


class WorkspaceLayoutManager:
    def __init__(self) -> None:
        self._layouts = {
            layout.name: layout for layout in (
                default_workspace_layout(),
                compact_workspace_layout(),
                animation_workspace_layout(),
            )
        }
        self.current = WorkspaceLayout.from_dict(self._layouts[DEFAULT_LAYOUT].to_dict())

    def available_layouts(self) -> list[str]:
        return sorted(self._layouts)

    def apply(self, name: str) -> WorkspaceLayout:
        source = self._layouts.get(str(name), self._layouts[DEFAULT_LAYOUT])
        self.current = WorkspaceLayout.from_dict(source.to_dict())
        return self.current

    def reset(self) -> WorkspaceLayout:
        return self.apply(DEFAULT_LAYOUT)

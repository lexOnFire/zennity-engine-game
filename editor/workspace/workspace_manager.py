from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Callable

from PySide6.QtCore import QObject, QSettings, Qt, Signal
from PySide6.QtWidgets import QDockWidget, QMainWindow

if TYPE_CHECKING:
    from editor.runtime.editor_context import EditorContext


class WorkspacePreset(str, Enum):
    """Presets de layout predefinidos para fluxos de trabalho do Zennity Studio."""

    DEFAULT = "Default Workspace"
    VISUAL_SCRIPTING = "Lógica Visual & Grafos"
    ANIMATION = "Animation Studio"
    UI_DESIGN = "UI Builder & Interfaces"
    PRODUCTION_BUILD = "Build & Produção"


class WindowRegistry:
    """Registro central de janelas e referências de nível superior do editor."""

    def __init__(self) -> None:
        self._main_window: QMainWindow | None = None

    def set_main_window(self, window: QMainWindow) -> None:
        self._main_window = window

    @property
    def main_window(self) -> QMainWindow | None:
        return self._main_window


class PanelRegistry:
    """Registro centralizado de todas as docks e painéis disponíveis no editor."""

    def __init__(self) -> None:
        self._docks: dict[str, QDockWidget] = {}
        self._categories: dict[str, str] = {}

    def register_dock(self, panel_id: str, dock: QDockWidget, category: str = "Geral") -> None:
        self._docks[panel_id] = dock
        self._categories[panel_id] = category

    def get_dock(self, panel_id: str) -> QDockWidget | None:
        return self._docks.get(panel_id)

    def all_docks(self) -> dict[str, QDockWidget]:
        return dict(self._docks)

    def docks_by_category(self, category: str) -> list[QDockWidget]:
        return [dock for pid, dock in self._docks.items() if self._categories.get(pid) == category]


class WorkspaceManager(QObject):
    """Gerenciador central do layout do editor, integrando registrador de painéis e presets."""

    layout_changed = Signal(str)

    def __init__(self, main_window: QMainWindow, context: EditorContext | None = None) -> None:
        super().__init__()
        self.main_window = main_window
        self.context = context
        self.window_registry = WindowRegistry()
        self.window_registry.set_main_window(main_window)
        self.panel_registry = PanelRegistry()
        self.current_preset: WorkspacePreset = WorkspacePreset.DEFAULT
        self.settings = QSettings("ZennityEngine", "EditorFramework2")

    def register_panel(self, panel_id: str, dock: QDockWidget, category: str = "Geral") -> None:
        self.panel_registry.register_dock(panel_id, dock, category)

    def show_panel(self, panel_id: str) -> None:
        dock = self.panel_registry.get_dock(panel_id)
        if dock:
            dock.show()
            dock.raise_()
            dock.activateWindow()

    def hide_panel(self, panel_id: str) -> None:
        dock = self.panel_registry.get_dock(panel_id)
        if dock:
            dock.hide()

    def apply_preset(self, preset: WorkspacePreset) -> None:
        """Aplica uma reconfiguração de layout para acomodar ferramentas específicas."""
        docks = self.panel_registry.all_docks()
        if not docks or not self.main_window:
            return

        # Oculta todas as docks secundárias/especializadas inicialmente
        for pid, dock in docks.items():
            if pid not in ("hierarchy", "inspector", "assets", "console", "profiler"):
                dock.hide()

        if preset == WorkspacePreset.DEFAULT:
            self._apply_default_preset(docks)
        elif preset == WorkspacePreset.VISUAL_SCRIPTING:
            self._apply_visual_scripting_preset(docks)
        elif preset == WorkspacePreset.ANIMATION:
            self._apply_animation_preset(docks)
        elif preset == WorkspacePreset.UI_DESIGN:
            self._apply_ui_design_preset(docks)
        elif preset == WorkspacePreset.PRODUCTION_BUILD:
            self._apply_production_build_preset(docks)

        self.current_preset = preset
        self.layout_changed.emit(preset.value)

        # Emite no EventBus global se disponível
        try:
            from editor.core.event_bus import EventBus
            EventBus.emit("EVENT_WORKSPACE_CHANGED", layout_name=preset.value)
        except Exception:
            pass

    def _apply_default_preset(self, docks: dict[str, QDockWidget]) -> None:
        h = docks.get("hierarchy")
        i = docks.get("inspector")
        a = docks.get("assets")
        c = docks.get("console")
        p = docks.get("profiler")

        if h:
            self.main_window.addDockWidget(Qt.LeftDockWidgetArea, h)
            h.show()
        if i:
            self.main_window.addDockWidget(Qt.RightDockWidgetArea, i)
            i.show()
        if a:
            self.main_window.addDockWidget(Qt.BottomDockWidgetArea, a)
            a.show()
        if c:
            self.main_window.addDockWidget(Qt.BottomDockWidgetArea, c)
            c.show()
        if p:
            self.main_window.addDockWidget(Qt.BottomDockWidgetArea, p)
            p.show()
            if c:
                self.main_window.tabifyDockWidget(c, p)

    def _apply_visual_scripting_preset(self, docks: dict[str, QDockWidget]) -> None:
        self._apply_default_preset(docks)
        vs = docks.get("visual_scripting") or docks.get("logic_graph")
        if vs:
            self.main_window.addDockWidget(Qt.BottomDockWidgetArea, vs)
            vs.show()
            vs.raise_()
            vs.activateWindow()

    def _apply_animation_preset(self, docks: dict[str, QDockWidget]) -> None:
        self._apply_default_preset(docks)
        anim = docks.get("animation_studio")
        if anim:
            self.main_window.addDockWidget(Qt.BottomDockWidgetArea, anim)
            anim.show()
            anim.raise_()
            anim.activateWindow()

    def _apply_ui_design_preset(self, docks: dict[str, QDockWidget]) -> None:
        self._apply_default_preset(docks)
        ui = docks.get("ui_builder")
        if ui:
            self.main_window.addDockWidget(Qt.BottomDockWidgetArea, ui)
            ui.show()
            ui.raise_()
            ui.activateWindow()

    def _apply_production_build_preset(self, docks: dict[str, QDockWidget]) -> None:
        self._apply_default_preset(docks)
        bw = docks.get("build_wizard")
        br = docks.get("build_report")
        aud = docks.get("asset_auditor")
        dep = docks.get("dependency_viewer")

        if bw:
            self.main_window.addDockWidget(Qt.BottomDockWidgetArea, bw)
            bw.show()
        if br:
            self.main_window.addDockWidget(Qt.BottomDockWidgetArea, br)
            br.show()
            if bw:
                self.main_window.tabifyDockWidget(bw, br)
        if dep:
            self.main_window.addDockWidget(Qt.LeftDockWidgetArea, dep)
            dep.show()
        if aud:
            self.main_window.addDockWidget(Qt.RightDockWidgetArea, aud)
            aud.show()

    def save_layout(self, name: str = "current_layout") -> None:
        if self.main_window:
            self.settings.setValue(f"layout_{name}_geometry", self.main_window.saveGeometry())
            self.settings.setValue(f"layout_{name}_state", self.main_window.saveState())

    def restore_layout(self, name: str = "current_layout") -> bool:
        if not self.main_window:
            return False
        geom = self.settings.value(f"layout_{name}_geometry")
        state = self.settings.value(f"layout_{name}_state")
        if geom and state:
            self.main_window.restoreGeometry(geom)
            self.main_window.restoreState(state)
            return True
        return False

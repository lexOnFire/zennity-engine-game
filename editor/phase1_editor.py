from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter

from editor.premium_editor import (
    ConsolePanel,
    CreatePanel,
    ResourcesPanel,
    SimplePanel,
    ZennityPremiumEditor,
)
from editor.premium_panels import RealHierarchyPanel, RealInspectorPanel
from editor.selection_runtime import install_viewport_selection_api
from editor.widgets.phase1_viewport import Phase1ViewportWidget

install_viewport_selection_api()


class ZennityPhase1Editor(ZennityPremiumEditor):
    """Editor Premium com Fase 1 ativada.

    Primeira entrega funcional:
    - Hierarchy usa objetos reais da Viewport.
    - Inspector mostra Transform real.
    - Criar objeto sincroniza Viewport, Hierarchy e Inspector.
    - Selecionar na Hierarchy seleciona o objeto real na cena.
    """

    def _build_layout(self) -> None:
        self.hierarchy = RealHierarchyPanel()
        self.resources = ResourcesPanel()
        self.create_panel = CreatePanel()
        self.inspector = RealInspectorPanel()
        self.console = ConsolePanel()
        self.preview = SimplePanel("Asset Preview", "Preview de assets")
        self.profiler = SimplePanel("Profiler", "FPS, CPU, memoria")

        self.viewport = Phase1ViewportWidget(self)
        self.viewport.setObjectName("ViewportCanvas")
        self.viewport.set_viewmodel(self.scene_view_model)

        left = QSplitter(Qt.Vertical)
        left.addWidget(self.hierarchy)
        left.addWidget(self.resources)
        left.addWidget(self.create_panel)
        left.setSizes([320, 260, 220])

        center = QSplitter(Qt.Vertical)
        center.addWidget(self.viewport)
        bottom = QSplitter(Qt.Horizontal)
        bottom.addWidget(self.console)
        bottom.addWidget(self.preview)
        bottom.addWidget(self.profiler)
        bottom.setSizes([520, 260, 260])
        center.addWidget(bottom)
        center.setSizes([560, 240])

        main = QSplitter(Qt.Horizontal)
        main.addWidget(left)
        main.addWidget(center)
        main.addWidget(self.inspector)
        main.setSizes([260, 850, 300])
        self.setCentralWidget(main)

        self.refresh_hierarchy_from_viewport()

    def _connect(self) -> None:
        self.hierarchy.selected.connect(self.select_object)
        self.create_panel.create_requested.connect(self.create_object)
        self.scene_view_model.selection_changed.connect(self.on_viewport_selection_changed)

    def scene_objects(self) -> list[Any]:
        scene = getattr(self.viewport, "active_scene", None)
        if scene is None:
            return []
        return list(getattr(scene, "editable_objects", []))

    def refresh_hierarchy_from_viewport(self) -> None:
        objects = self.scene_objects()
        self.object_count = len(objects)
        self.hierarchy.refresh_objects(objects)
        if hasattr(self, "stats"):
            self.stats.setText(f"FPS: 60 | Memoria: 512 MB | Objetos: {self.object_count}")

    def select_object(self, obj: Any) -> None:
        self.viewport.select_object(obj)
        selected = self.viewport.selected_object()
        self.inspector.load_object(selected)
        self.hierarchy.select_object(selected)

    def on_viewport_selection_changed(self, obj: Any) -> None:
        self.inspector.load_object(obj)
        self.hierarchy.select_object(obj)

    def create_object(self, name: str) -> None:
        mapping = {
            "Sprite 2D": "Quadrado",
            "Cube 3D": "Cube",
            "Plane 3D": "Plane",
            "Plataforma 2D": "Plataforma",
            "Top-down 2D": "Player",
        }
        value = mapping.get(name, name)
        self.viewport.create_object(value)

        objects = self.scene_objects()
        created = objects[-1] if objects else None
        self.refresh_hierarchy_from_viewport()
        if created is not None:
            self.select_object(created)

        self.console.add("INFO", f"Objeto criado: {name}")

"""Painel opt-in das métricas do RenderPipeline da Scene View."""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from editor.premium_editor import Panel


class RenderPipelineProfilerPanel(Panel):
    """Exibe métricas por passe sem habilitar profiling automaticamente."""

    def __init__(self) -> None:
        super().__init__("Profiler")
        self._viewports: dict[str, Any] = {}

        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        self.enabled_checkbox = QCheckBox("Medir Render Pipeline")
        self.viewport_combo = QComboBox()
        self.viewport_combo.addItems(["Scene", "Game"])
        self.reset_button = QPushButton("Reset")
        controls_layout.addWidget(self.enabled_checkbox)
        controls_layout.addWidget(self.viewport_combo)
        controls_layout.addWidget(self.reset_button)
        self.layout.addWidget(controls)

        self.status_label = QLabel("Coleta desativada")
        self.layout.addWidget(self.status_label)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Pass", "Último", "Média", "Máximo", "Exec."])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for column in range(1, 5):
            self.table.horizontalHeader().setSectionResizeMode(column, QHeaderView.ResizeToContents)
        self.layout.addWidget(self.table)

        self.enabled_checkbox.toggled.connect(self._set_enabled)
        self.viewport_combo.currentTextChanged.connect(lambda _text: self.refresh())
        self.reset_button.clicked.connect(self.reset_metrics)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(250)

    def set_viewports(self, scene_viewport: Any, game_viewport: Any) -> None:
        self._viewports = {"Scene": scene_viewport, "Game": game_viewport}

    def _pipelines(self) -> list[Any]:
        return [
            viewport.render_pipeline
            for viewport in self._viewports.values()
            if getattr(viewport, "render_pipeline", None) is not None
        ]

    def _current_pipeline(self) -> Any | None:
        viewport = self._viewports.get(self.viewport_combo.currentText())
        return getattr(viewport, "render_pipeline", None)

    def _set_enabled(self, enabled: bool) -> None:
        for pipeline in self._pipelines():
            pipeline.set_profiling_enabled(enabled)
        self.status_label.setText("Coletando métricas" if enabled else "Coleta desativada")
        if not enabled:
            self.table.setRowCount(0)

    def reset_metrics(self) -> None:
        for pipeline in self._pipelines():
            pipeline.reset_metrics()
        self.refresh()

    def refresh(self) -> None:
        if not self.enabled_checkbox.isChecked():
            return
        pipeline = self._current_pipeline()
        metrics = pipeline.metrics if pipeline is not None else ()
        self.table.setRowCount(len(metrics))
        for row, metric in enumerate(metrics):
            values = (
                metric.pass_name,
                f"{metric.last_ms:.3f} ms",
                f"{metric.average_ms:.3f} ms",
                f"{metric.max_ms:.3f} ms",
                str(metric.executions),
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))

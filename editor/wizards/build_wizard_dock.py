"""Assistente de Exportação e Build (Build Wizard Dock) consumindo o PipelineEngine."""
from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QProgressBar,
    QTextEdit,
)
from engine.pipeline.stage import PipelineEngine, PipelineTask
from engine.build.cooking import AssetValidationStage, AssetCookingStage


class BuildWizardDock(QDockWidget):
    """Dock do Assistente de Build & Export (Build Wizard)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("🧙 Build & Export Wizard", parent)
        self.setObjectName("BuildWizardDock")

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        toolbar = QHBoxLayout()
        btn_start_wizard = QPushButton("⚡ Execute Operational Build", self)
        btn_start_wizard.clicked.connect(self.run_pipeline_wizard)

        toolbar.addWidget(QLabel("Pipeline Wizard:", self))
        toolbar.addWidget(btn_start_wizard)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.txt_log = QTextEdit(self)
        self.txt_log.setReadOnly(True)
        layout.addWidget(self.txt_log, 1)

        self.setWidget(container)

    def run_pipeline_wizard(self) -> None:
        # Instancia o motor de pipeline padronizado
        pipeline = PipelineEngine("BuildWizardPipeline")
        pipeline.add_stage(AssetValidationStage())
        pipeline.add_stage(AssetCookingStage())

        task = PipelineTask("GamePackage", input_data="MainScene.zscene")
        result_task = pipeline.run(task)

        self.progress_bar.setValue(100)
        self.txt_log.setText("\n".join(result_task.logs) + f"\n\nResultado Final: {result_task.output_data}")

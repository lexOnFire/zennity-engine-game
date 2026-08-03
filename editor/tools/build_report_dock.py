"""Dock do Relatório e Configuração de Build (Build Report Dock)."""
from __future__ import annotations
from typing import Optional
from PySide6.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox, QTextEdit
from engine.build.pipeline import BuildPipeline, BuildProfile


class BuildReportDock(QDockWidget):
    """Dock de Build Pipeline e Exportação do Projeto."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("🚀 Build Pipeline & Export", parent)
        self.setObjectName("BuildReportDock")

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)

        toolbar = QHBoxLayout()
        self.combo_platform = QComboBox(self)
        self.combo_platform.addItems(["Windows", "Linux", "macOS", "Web (WASM)"])

        btn_build = QPushButton("▶ Build Game", self)
        btn_build.clicked.connect(self.run_build)

        toolbar.addWidget(QLabel("Platform:", self))
        toolbar.addWidget(self.combo_platform)
        toolbar.addWidget(btn_build)
        toolbar.addStretch(1)
        layout.addLayout(toolbar)

        self.txt_log = QTextEdit(self)
        self.txt_log.setReadOnly(True)
        layout.addWidget(self.txt_log, 1)

        self.setWidget(container)

    def run_build(self) -> None:
        profile = BuildProfile(name="Release", target_platform=self.combo_platform.currentText(), scenes=["MainScene.zscene"])
        report = BuildPipeline.execute_build(profile)
        self.txt_log.setText(f"=== BUILD REPORT ({profile.target_platform}) ===\n"
                             f"Status: {'SUCCESS' if report.success else 'FAILED'}\n"
                             f"Bundled Assets: {report.total_assets_bundled}\n"
                             f"Total Size: {report.total_bytes_written / 1024:.1f} KB\n"
                             f"Time Elapsed: {report.duration_seconds}s\n")

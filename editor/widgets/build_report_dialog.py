from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from engine.build import BuildReport


def _human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024.0 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024.0
    return f"{size} B"


class BuildReportDialog(QDialog):
    """Apresenta o resultado do build sem executar lógica de exportação."""

    def __init__(self, report: BuildReport, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.report = report
        self.setWindowTitle("Relatório de Build")
        self.resize(760, 540)
        self.setMinimumSize(620, 420)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        summary = QFrame()
        summary.setObjectName("BuildSummary")
        summary.setStyleSheet(
            "#BuildSummary { background: #20232b; border: 1px solid #343945; border-radius: 8px; }"
        )
        summary_layout = QVBoxLayout(summary)
        status = "Build concluído" if self.report.success else "Build não concluído"
        status_color = "#65d17a" if self.report.success else "#ff6b6b"
        status_label = QLabel(("✓  " if self.report.success else "✕  ") + status)
        status_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {status_color};")
        summary_layout.addWidget(status_label)
        destination = QLabel(self.report.destination)
        destination.setTextInteractionFlags(Qt.TextSelectableByMouse)
        destination.setStyleSheet("color: #aab2c5;")
        summary_layout.addWidget(destination)
        details = QLabel(
            f"{self.report.file_count} arquivos  •  {_human_size(self.report.total_size_bytes)}  •  "
            f"{self.report.duration_seconds:.2f}s  •  {len(self.report.warnings)} avisos  •  "
            f"{len(self.report.errors)} erros"
        )
        details.setStyleSheet("color: #8f96a8;")
        summary_layout.addWidget(details)
        layout.addWidget(summary)

        tabs = QTabWidget()
        issues = QTreeWidget()
        issues.setHeaderLabels(["Tipo", "Mensagem", "Arquivo"])
        issues.setColumnWidth(0, 80)
        issues.setColumnWidth(1, 390)
        if not self.report.issues:
            item = QTreeWidgetItem(["OK", "Nenhum problema encontrado.", ""])
            item.setForeground(0, QColor("#65d17a"))
            issues.addTopLevelItem(item)
        for issue in self.report.issues:
            label = "ERRO" if issue.severity == "error" else "AVISO"
            item = QTreeWidgetItem([label, issue.message, issue.path])
            item.setForeground(0, QColor("#ff6b6b" if issue.severity == "error" else "#f2c14e"))
            item.setToolTip(2, issue.path)
            issues.addTopLevelItem(item)
        tabs.addTab(issues, f"Diagnóstico ({len(self.report.issues)})")

        files = QPlainTextEdit()
        files.setReadOnly(True)
        files.setPlainText("\n".join(self.report.files) or "Nenhum arquivo foi gerado.")
        tabs.addTab(files, f"Arquivos ({self.report.file_count})")
        layout.addWidget(tabs, 1)

        actions = QHBoxLayout()
        open_button = QPushButton("Abrir pasta do build")
        open_button.setEnabled(Path(self.report.destination).is_dir())
        open_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(self.report.destination))
        )
        close_button = QPushButton("Fechar")
        close_button.setDefault(True)
        close_button.clicked.connect(self.accept)
        actions.addWidget(open_button)
        actions.addStretch(1)
        actions.addWidget(close_button)
        layout.addLayout(actions)


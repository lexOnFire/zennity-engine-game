from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog, QFrame, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from engine.build import ProjectValidationReport
from editor.ui.tokens import DEFAULT_TOKENS


class ProjectValidationDialog(QDialog):
    def __init__(self, report: ProjectValidationReport, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("ProjectValidationDialog")
        self.report = report
        self.setWindowTitle("Validação do Projeto")
        self.resize(880, 560)
        self.setMinimumSize(700, 440)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        summary = QFrame()
        summary.setObjectName("ValidationSummary")
        summary_layout = QVBoxLayout(summary)
        title = "Projeto pronto para exportar" if self.report.valid else "O projeto precisa de correções"
        status = QLabel(("✓  " if self.report.valid else "✕  ") + title)
        status.setObjectName("ValidationStatus")
        status.setProperty("uiState", "success" if self.report.valid else "error")
        summary_layout.addWidget(status)
        details = QLabel(
            f"Cena: {self.report.scene_name or '—'}  •  {self.report.object_count} objetos  •  "
            f"{self.report.checked_files} arquivos verificados  •  {len(self.report.warnings)} avisos  •  "
            f"{len(self.report.errors)} erros  •  {self.report.duration_seconds:.2f}s"
        )
        details.setObjectName("ValidationDetails")
        details.setWordWrap(True)
        summary_layout.addWidget(details)
        layout.addWidget(summary)

        tree = QTreeWidget()
        tree.setObjectName("ValidationIssues")
        tree.setHeaderLabels(["Tipo", "Categoria", "Objeto", "Mensagem", "Arquivo"])
        tree.setColumnWidth(0, 75)
        tree.setColumnWidth(1, 110)
        tree.setColumnWidth(2, 130)
        tree.setColumnWidth(3, 330)
        if not self.report.issues:
            item = QTreeWidgetItem(["OK", "Projeto", "", "Nenhum problema encontrado.", ""])
            item.setForeground(0, QColor(DEFAULT_TOKENS.success))
            tree.addTopLevelItem(item)
        for issue in self.report.issues:
            label = "ERRO" if issue.severity == "error" else "AVISO"
            item = QTreeWidgetItem([label, issue.category, issue.object_name, issue.message, issue.path])
            item.setForeground(0, QColor(
                DEFAULT_TOKENS.danger if issue.severity == "error" else DEFAULT_TOKENS.warning
            ))
            item.setToolTip(4, issue.path)
            tree.addTopLevelItem(item)
        layout.addWidget(tree, 1)

        actions = QHBoxLayout()
        close_button = QPushButton("Fechar")
        close_button.setDefault(True)
        close_button.clicked.connect(self.accept)
        actions.addStretch(1)
        actions.addWidget(close_button)
        layout.addLayout(actions)

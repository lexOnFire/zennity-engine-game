"""Diálogo Read-Only para visualização do código-fonte real dos nós do Logic Graph."""
import importlib
import inspect
from pathlib import Path
from typing import Any, Mapping

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from engine.logic.node_definitions.catalogue import (
    ensure_catalogue_loaded,
    resolve_node_id,
)
from engine.logic.node_definitions.registry import get_registry
from engine.logic.runtime.registry import registry


def extract_node_source_info(node_type: str) -> dict[str, Any]:
    """Extrai informações de código real (Definition, Executor, Evaluator) para um tipo de nó."""
    ensure_catalogue_loaded()
    canonical_id = resolve_node_id(node_type)
    
    definition_info = None
    reg = get_registry()
    owner_mod_name = reg.definition_owner(canonical_id)
    if owner_mod_name:
        try:
            mod = importlib.import_module(f"engine.logic.node_definitions.{owner_mod_name}")
            for attr_name in dir(mod):
                val = getattr(mod, attr_name)
                if isinstance(val, type) and getattr(val, "__node_definition__", None):
                    node_def = val.__node_definition__
                    if getattr(node_def, "id", None) == canonical_id:
                        file_path = inspect.getsourcefile(val)
                        lines, start_line = inspect.getsourcelines(val)
                        definition_info = {
                            "file": file_path,
                            "line": start_line,
                            "code": "".join(lines),
                            "class_name": attr_name,
                        }
                        break
        except Exception:
            pass

    executor_info = None
    executor_fn = registry.executors.get(canonical_id) or registry.executors.get(node_type)
    if executor_fn:
        try:
            file_path = inspect.getsourcefile(executor_fn)
            lines, start_line = inspect.getsourcelines(executor_fn)
            executor_info = {
                "file": file_path,
                "line": start_line,
                "code": "".join(lines),
                "name": executor_fn.__name__,
            }
        except Exception:
            pass

    evaluator_info = None
    evaluator_fn = registry.evaluators.get(canonical_id) or registry.evaluators.get(node_type)
    if evaluator_fn:
        try:
            file_path = inspect.getsourcefile(evaluator_fn)
            lines, start_line = inspect.getsourcelines(evaluator_fn)
            evaluator_info = {
                "file": file_path,
                "line": start_line,
                "code": "".join(lines),
                "name": evaluator_fn.__name__,
            }
        except Exception:
            pass

    return {
        "node_type": node_type,
        "canonical_id": canonical_id,
        "definition": definition_info,
        "executor": executor_info,
        "evaluator": evaluator_info,
    }


class NodeCodeViewDialog(QDialog):
    """Janela modal para exibição do código-fonte dos nós."""

    def __init__(self, node: Mapping[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.node = node
        self.node_type = str(node.get("type", ""))
        self.node_title = str(node.get("title", self.node_type))
        self.category = str(node.get("category", "Logic"))

        self.setWindowTitle(f"Código do Nó: {self.node_title} ({self.node_type})")
        self.resize(780, 560)
        self.setMinimumSize(540, 380)
        self.setStyleSheet(
            "QDialog { background-color: #0f121a; color: #f1f5f9; }"
            "QLabel { color: #cbd5e1; }"
            "QTabBar::tab { background: #181c28; color: #94a3b8; padding: 6px 14px; font-weight: bold; border-top-left-radius: 4px; border-top-right-radius: 4px; font-size: 11px; }"
            "QTabBar::tab:selected { background: #232a3b; color: #f8fafc; border-bottom: 2px solid #3b82f6; }"
            "QTabBar::tab:disabled { color: #475569; background: #11141c; }"
            "QTabWidget::pane { border: 1px solid #1e2430; background: #141720; border-radius: 4px; }"
            "QPushButton { background-color: #1e293b; color: #f8fafc; border: 1px solid #334155; padding: 6px 16px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #334155; border-color: #475569; }"
            "QPushButton#CopyButton { background-color: #2563eb; border-color: #3b82f6; }"
            "QPushButton#CopyButton:hover { background-color: #1d4ed8; }"
        )

        self._setup_ui()
        self._load_sources()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header com Nome, Categoria e Badge Read-Only
        header_layout = QHBoxLayout()
        title_label = QLabel(self.node_title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f8fafc;")
        
        type_badge = QLabel(f"id: {self.node_type}")
        type_badge.setStyleSheet("font-size: 11px; color: #94a3b8; background: #1e2430; padding: 2px 8px; border-radius: 4px;")
        
        category_badge = QLabel(self.category)
        category_badge.setStyleSheet("font-size: 11px; color: #60a5fa; background: #172554; padding: 2px 8px; border-radius: 4px; font-weight: bold;")

        readonly_badge = QLabel("🔒 READ-ONLY")
        readonly_badge.setStyleSheet("font-size: 11px; color: #34d399; background: #064e3b; padding: 2px 8px; border-radius: 4px; font-weight: bold;")

        header_layout.addWidget(title_label)
        header_layout.addWidget(type_badge)
        header_layout.addWidget(category_badge)
        header_layout.addStretch(1)
        header_layout.addWidget(readonly_badge)
        layout.addLayout(header_layout)

        # File & line location label
        self.location_label = QLabel("Localização: —")
        self.location_label.setStyleSheet("font-size: 11px; color: #64748b; font-family: Consolas, monospace;")
        layout.addWidget(self.location_label)

        # Tabs para Definition, Executor, Evaluator
        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs, 1)

        # Editor de Código Read-Only por Aba
        self.definition_edit = self._create_code_viewer()
        self.executor_edit = self._create_code_viewer()
        self.evaluator_edit = self._create_code_viewer()

        self.tabs.addTab(self.definition_edit, "NodeDefinition (Declaração)")
        self.tabs.addTab(self.executor_edit, "Executor (Fluxo)")
        self.tabs.addTab(self.evaluator_edit, "Evaluator (Dados)")

        # Rodapé de Ações
        footer_layout = QHBoxLayout()
        self.copy_btn = QPushButton("Copiar Código")
        self.copy_btn.setObjectName("CopyButton")
        self.copy_btn.clicked.connect(self._copy_current_code)
        
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.accept)

        footer_layout.addWidget(self.copy_btn)
        footer_layout.addStretch(1)
        footer_layout.addWidget(close_btn)
        layout.addLayout(footer_layout)

    def _create_code_viewer(self) -> QPlainTextEdit:
        editor = QPlainTextEdit()
        editor.setReadOnly(True)
        editor.setStyleSheet(
            "QPlainTextEdit { background-color: #0b0d14; color: #38bdf8; font-family: Consolas, 'Courier New', monospace; "
            "font-size: 12px; line-height: 1.4; border: none; padding: 10px; selection-background-color: #1e3a8a; }"
        )
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        editor.setFont(font)
        return editor

    def _load_sources(self) -> None:
        self.info = extract_node_source_info(self.node_type)

        # Aba Definição
        def_info = self.info.get("definition")
        if def_info:
            self.definition_edit.setPlainText(def_info["code"])
            self.tabs.setTabEnabled(0, True)
        else:
            self.definition_edit.setPlainText("# Nenhuma classe NodeDefinition estática localizada para este nó.")
            self.tabs.setTabEnabled(0, False)

        # Aba Executor
        exec_info = self.info.get("executor")
        if exec_info:
            self.executor_edit.setPlainText(exec_info["code"])
            self.tabs.setTabEnabled(1, True)
        else:
            self.executor_edit.setPlainText("# Este nó não possui Executor de fluxo registrado (nó puramente de dados ou dinâmico).")
            self.tabs.setTabEnabled(1, False)

        # Aba Evaluator
        eval_info = self.info.get("evaluator")
        if eval_info:
            self.evaluator_edit.setPlainText(eval_info["code"])
            self.tabs.setTabEnabled(2, True)
        else:
            self.evaluator_edit.setPlainText("# Este nó não possui Evaluator de dados registrado (nó de ação pura).")
            self.tabs.setTabEnabled(2, False)

        # Seleciona a primeira aba disponível
        for idx in range(3):
            if self.tabs.isTabEnabled(idx):
                self.tabs.setCurrentIndex(idx)
                break
        self._update_location_label()

    def _on_tab_changed(self, index: int) -> None:
        self._update_location_label()

    def _update_location_label(self) -> None:
        idx = self.tabs.currentIndex()
        key = ("definition", "executor", "evaluator")[idx] if 0 <= idx < 3 else None
        item = self.info.get(key) if key else None
        if item and item.get("file"):
            p = Path(item["file"])
            try:
                rel = p.relative_to(Path.cwd())
            except ValueError:
                rel = p
            self.location_label.setText(f"Arquivo: {rel} • Linha: {item.get('line', 1)}")
        else:
            self.location_label.setText("Arquivo: —")

    def _copy_current_code(self) -> None:
        idx = self.tabs.currentIndex()
        text = ""
        if idx == 0:
            text = self.definition_edit.toPlainText()
        elif idx == 1:
            text = self.executor_edit.toPlainText()
        elif idx == 2:
            text = self.evaluator_edit.toPlainText()
        
        if text:
            from PySide6.QtGui import QGuiApplication
            clipboard = QGuiApplication.clipboard()
            if clipboard:
                clipboard.setText(text)
                self.copy_btn.setText("Copiado! ✓")
                from PySide6.QtCore import QTimer
                QTimer.singleShot(1500, lambda: self.copy_btn.setText("Copiar Código"))

"""Assistente de Exportação e Build (Build Wizard Dock) consumindo o PipelineEngine."""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtWidgets import (
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)
from engine.pipeline.stage import PipelineEngine, PipelineTask
from engine.build.cooking import AssetValidationStage, AssetCookingStage
from engine.build.project_validator import validate_project
from engine.build.export_profile import debug_profile, release_profile


class _ValidationWorker(QObject):
    """Roda a validação em background thread para não travar a UI."""
    finished = Signal(object)

    def __init__(self, project_root: str, scene_path: str) -> None:
        super().__init__()
        self._root = project_root
        self._scene = scene_path

    def run(self) -> None:
        report = validate_project(self._root, self._scene)
        self.finished.emit(report)


class BuildWizardDock(QDockWidget):
    """Dock do Assistente de Build & Export com validação pré-build integrada."""

    # ── Perfis disponíveis ──────────────────────────────────────────────────
    _PROFILES = {
        "🐛 Debug  (desenvolvimento)": debug_profile,
        "🚀 Release  (distribuição)": release_profile,
    }

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__("🧙 Build & Export Wizard", parent)
        self.setObjectName("BuildWizardDock")
        self._validation_thread: QThread | None = None
        self._project_root = str(Path.cwd())

        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── Seleção de Perfil ───────────────────────────────────────────────
        profile_row = QHBoxLayout()
        profile_row.addWidget(QLabel("Perfil:"))
        self.combo_profile = QComboBox()
        self.combo_profile.addItems(list(self._PROFILES.keys()))
        profile_row.addWidget(self.combo_profile, 1)
        layout.addLayout(profile_row)

        # ── Linha de cena principal ─────────────────────────────────────────
        scene_row = QHBoxLayout()
        scene_row.addWidget(QLabel("Cena:"))
        self.lbl_scene = QLabel("(nenhuma cena salva)")
        self.lbl_scene.setObjectName("BuildScenePath")
        self.lbl_scene.setTextInteractionFlags(Qt.TextSelectableByMouse)
        scene_row.addWidget(self.lbl_scene, 1)
        layout.addLayout(scene_row)

        # ── Botões de ação ──────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self.btn_validate = QPushButton("🔍 Validar Projeto")
        self.btn_validate.setToolTip("Executa a validação pré-build: verifica assets, scripts, câmera, prefabs e logic graphs.")
        self.btn_validate.clicked.connect(self._run_validation)

        self.btn_build = QPushButton("⚡ Build & Export")
        self.btn_build.setToolTip("Executa o pipeline completo: validação → cozimento de assets → empacotamento.")
        self.btn_build.clicked.connect(self._run_build)
        self.btn_build.setEnabled(False)  # Habilitado somente após validação limpa

        btn_row.addWidget(self.btn_validate)
        btn_row.addWidget(self.btn_build)
        layout.addLayout(btn_row)

        # ── Barra de progresso ──────────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # ── Log de saída ────────────────────────────────────────────────────
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setObjectName("BuildLog")
        self.txt_log.setPlaceholderText("Os resultados do build aparecerão aqui…")
        layout.addWidget(self.txt_log, 1)

        self.setWidget(container)

    def set_project_root(self, root: str | Path) -> None:
        """Atualiza o diretório raiz do projeto (chamado ao abrir/salvar um projeto)."""
        self._project_root = str(Path(root).resolve())

    def set_active_scene(self, scene_path: str | Path) -> None:
        """Atualiza a cena principal exibida no dock."""
        p = Path(scene_path)
        self.lbl_scene.setText(p.name)
        self.lbl_scene.setToolTip(str(p))

    # ── Validação Pré-Build ─────────────────────────────────────────────────

    def _run_validation(self) -> None:
        """Executa a validação de pré-build em background e exibe o relatório."""
        scene_path = self.lbl_scene.toolTip() or str(Path(self._project_root) / "Assets" / "Scenes" / "MainScene.zscene")
        self._log("", clear=True)
        self._log("🔍 Iniciando validação pré-build…")
        self.btn_validate.setEnabled(False)
        self.btn_build.setEnabled(False)
        self.progress_bar.setRange(0, 0)  # Animação indeterminada

        worker = _ValidationWorker(self._project_root, scene_path)
        thread = QThread(self)
        self._validation_thread = thread
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._on_validation_finished)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.start()

    def _on_validation_finished(self, report) -> None:
        self.progress_bar.setRange(0, 100)
        self.btn_validate.setEnabled(True)

        if report.valid:
            self.progress_bar.setValue(100)
            self._log(f"✅ Validação concluída em {report.duration_seconds:.2f}s — {report.object_count} objetos, {report.checked_files} arquivos verificados.")
            if report.warnings:
                for w in report.warnings:
                    self._log(f"  ⚠ [{w.category}] {w.message}" + (f" ({w.object_name})" if w.object_name else ""))
            self.btn_build.setEnabled(True)
            self._log("✔ Sem erros críticos. Você pode executar o Build.")
        else:
            self.progress_bar.setValue(0)
            self._log(f"❌ Validação falhou — {len(report.errors)} erro(s), {len(report.warnings)} aviso(s).")
            for issue in report.issues:
                icon = "✕" if issue.severity == "error" else "⚠"
                self._log(f"  {icon} [{issue.category}] {issue.message}" + (f" → {issue.object_name}" if issue.object_name else ""))
            self.btn_build.setEnabled(False)
            self._log("⛔ Corrija os erros antes de exportar.")

    # ── Build Pipeline ──────────────────────────────────────────────────────

    def _run_build(self) -> None:
        selected_label = self.combo_profile.currentText()
        profile_factory = self._PROFILES.get(selected_label, debug_profile)
        profile = profile_factory()

        self._log(f"\n⚡ Executando Build: {profile.normalized_name()}…")
        self.btn_build.setEnabled(False)
        self.btn_validate.setEnabled(False)
        self.progress_bar.setRange(0, 0)

        try:
            pipeline = PipelineEngine(f"Build_{profile.normalized_name()}")
            pipeline.add_stage(AssetValidationStage())
            pipeline.add_stage(AssetCookingStage())
            task = PipelineTask("GamePackage", input_data=self.lbl_scene.toolTip() or "MainScene.zscene")
            result_task = pipeline.run(task)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            for line in result_task.logs:
                self._log(f"  {line}")
            self._log(f"\n✅ Build concluído → {result_task.output_data}")
            self._log(f"Resultado Final: {result_task.output_data}")
        except Exception as exc:  # noqa: BLE001
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self._log(f"❌ Build falhou: {exc}")
        finally:
            self.btn_validate.setEnabled(True)
            self.btn_build.setEnabled(True)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _log(self, msg: str, *, clear: bool = False) -> None:
        if clear:
            self.txt_log.clear()
        self.txt_log.append(msg)

    # ── Compatibilidade retroativa ──────────────────────────────────────────
    def run_pipeline_wizard(self) -> None:
        """Alias de compatibilidade para testes legados — delega ao _run_build."""
        self._run_build()


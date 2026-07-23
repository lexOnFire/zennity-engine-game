"""Scene persistence, project validation and export workflow orchestration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QFileDialog, QInputDialog

from editor.widgets.build_report_dialog import BuildReportDialog
from editor.widgets.project_validation_dialog import ProjectValidationDialog
from editor.runtime.diagnostics import EditorDiagnostic
from engine.build import export_development_project_with_report, validate_project


class ProjectWorkflowController:
    """Owns user-facing scene and build workflows."""

    SCENE_FILTER = "Zennity Scene (*.zscene);;Cena JSON (*.json)"

    def __init__(self, host: Any, project_root: Path | None = None) -> None:
        self.host = host
        self.project_root = (project_root or Path.cwd()).resolve()

    def save_scene(self) -> bool:
        h = self.host
        filename, _ = QFileDialog.getSaveFileName(
            h,
            "Salvar cena",
            str(h._current_scene_path or "Untitled.zscene"),
            self.SCENE_FILTER,
        )
        if not filename:
            return False
        path = Path(filename)
        try:
            prefab_workspace = getattr(h, "_prefab_workspace", None)
            if prefab_workspace is not None:
                prefab_workspace.sync_scene_instances()
            payload = h._scene_persistence.save(
                path, h._scene_snapshot, h._scene_document
            )
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            self._report_failure(
                "Falha ao salvar cena",
                exc,
                action="Verifique a pasta de destino e tente Salvar como.",
                path=path,
            )
            return False
        h._scene_document = payload
        h._current_scene_path = path
        h.statusBar().showMessage(f"Cena salva: {filename}")
        h._log("INFO", f"Cena salva: {filename}")
        return True

    def collect_logic_variables(self, scope: str) -> dict[str, dict[str, Any]]:
        return self.host._scene_persistence.collect_logic_variables(scope)

    def load_scene(self, scene_path: Path | None = None) -> bool:
        h = self.host
        if scene_path is not None:
            filename = str(scene_path)
        else:
            filename, _ = QFileDialog.getOpenFileName(
                h, "Abrir cena", "", self.SCENE_FILTER
            )
        if not filename:
            return False
        try:
            payload, snapshots, typed = h._scene_persistence.load(Path(filename))
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            self._report_failure(
                "Falha ao abrir cena",
                exc,
                action="Confira o formato do arquivo ou restaure uma cópia válida.",
                path=Path(filename),
            )
            return False
        h._record_history()
        h._scene_snapshot = snapshots
        h._objects_by_name = {item["name"]: item for item in snapshots}
        h._scene_document = payload if typed else None
        h._current_scene_path = Path(filename)
        h._selected_name = None
        h._refresh_hierarchy()
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        h.statusBar().showMessage(f"Cena aberta: {filename}")
        h._log("INFO", f"Cena aberta: {filename}")
        return True

    def export_project(self) -> None:
        h = self.host
        h._save_scene_snapshot()
        if h._current_scene_path is None:
            return
        validation = validate_project(self.project_root, h._current_scene_path)
        h._last_validation_report = validation
        if not validation.valid:
            h._log(
                "ERROR",
                f"Exportação bloqueada por {len(validation.errors)} erro(s) de validação",
            )
            h.statusBar().showMessage("Corrija os erros de validação antes de exportar")
            ProjectValidationDialog(validation, h).exec()
            return
        output = QFileDialog.getExistingDirectory(
            h, "Pasta para exportar", str(self.project_root / "Builds")
        )
        if not output:
            return
        default_name = str((h._scene_document or {}).get("scene_name", "ZennityGame"))
        project_name, accepted = QInputDialog.getText(
            h, "Exportar projeto", "Nome do jogo:", text=default_name
        )
        if not accepted or not project_name.strip():
            return
        report = export_development_project_with_report(
            self.project_root, h._current_scene_path, Path(output), project_name
        )
        h._last_build_report = report
        h._build_report_action.setEnabled(True)
        if report.success:
            h._log(
                "INFO",
                f"Projeto exportado: {report.destination} "
                f"({report.file_count} arquivos, {len(report.warnings)} aviso(s))",
            )
            h.statusBar().showMessage(f"Build criado em {report.destination}")
        else:
            h._log("ERROR", f"Build não concluído: {len(report.errors)} erro(s)")
            h.statusBar().showMessage("Build não concluído — consulte o relatório")
        self.show_last_build_report()

    def validate_current_project(self) -> None:
        h = self.host
        h._save_scene_snapshot()
        if h._current_scene_path is None:
            return
        report = validate_project(self.project_root, h._current_scene_path)
        h._last_validation_report = report
        if report.valid:
            h._log(
                "INFO", f"Projeto validado: {len(report.warnings)} aviso(s), nenhum erro"
            )
            h.statusBar().showMessage("Projeto pronto para exportar")
        else:
            h._log(
                "ERROR",
                f"Validação encontrou {len(report.errors)} erro(s) e "
                f"{len(report.warnings)} aviso(s)",
            )
            h.statusBar().showMessage("Projeto precisa de correções antes da exportação")
        ProjectValidationDialog(report, h).exec()

    def show_last_build_report(self) -> None:
        h = self.host
        if h._last_build_report is not None:
            BuildReportDialog(h._last_build_report, h).exec()

    def _report_failure(
        self, title: str, error: Exception, *, action: str, path: Path | None = None,
    ) -> None:
        h = self.host
        diagnostic = EditorDiagnostic(
            severity="ERROR",
            title=title,
            message=str(error),
            action=action,
            path=path,
        )
        center = getattr(h, "_diagnostics", None)
        if center is not None:
            diagnostic = center.report(diagnostic)
        h._log(diagnostic.severity, diagnostic.console_message())
        h.statusBar().showMessage(f"{title}. {action}")

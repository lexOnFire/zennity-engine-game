"""Scene persistence, project validation and export workflow orchestration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QFileDialog, QInputDialog

from editor.widgets.build_report_dialog import BuildReportDialog
from editor.widgets.project_validation_dialog import ProjectValidationDialog
from engine.build import export_development_project_with_report, validate_project


class ProjectWorkflowController:
    """Owns user-facing scene and build workflows."""

    SCENE_FILTER = "Zennity Scene (*.zscene);;Cena JSON (*.json)"

    def __init__(self, host: Any, project_root: Path | None = None) -> None:
        self.host = host
        self.project_root = (project_root or Path.cwd()).resolve()

    def save_scene(self, *, save_as: bool = False) -> bool:
        h = self.host
        path = Path(h._current_scene_path) if h._current_scene_path else None
        if save_as or path is None:
            filename, _ = QFileDialog.getSaveFileName(
                h,
                "Salvar cena como" if save_as else "Salvar cena",
                str(path or self.project_root / "Untitled.zscene"),
                self.SCENE_FILTER,
            )
            if not filename:
                return False
            path = Path(filename)
        try:
            payload = h._scene_persistence.save(
                path, h._scene_snapshot, h._scene_document
            )
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            h.statusBar().showMessage(f"Falha ao salvar cena: {exc}")
            return False
        h._scene_document = payload
        h._current_scene_path = path
        h.statusBar().showMessage(f"Cena salva: {path}")
        h._log("INFO", f"Cena salva: {path}")
        return True

    def save_scene_as(self) -> bool:
        """Always ask for a destination, preserving Save for in-place updates."""
        return self.save_scene(save_as=True)

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
            h.statusBar().showMessage(f"Falha ao abrir cena: {exc}")
            return False
        h._record_history()
        h._scene_snapshot = snapshots
        h._objects_by_name = {item["name"]: item for item in snapshots}
        h._scene_document = payload if typed else None
        h._current_scene_path = Path(filename)
        h._selected_name = None
        h._refresh_hierarchy()
        h._scene_controller.publish_snapshot(h._scene_snapshot)
        dock = getattr(h, "_dock_visual_scripting", None)
        if dock is not None and hasattr(dock, "sync_from_host"):
            dock.sync_from_host()
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

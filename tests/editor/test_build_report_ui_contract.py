from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_build_menu_exposes_export_and_last_report() -> None:
    source = (ROOT / "editor" / "isolated_editor_main.py").read_text(encoding="utf-8")

    assert 'addAction("Exportar projeto...")' in source
    assert 'addAction("Último relatório...")' in source
    assert "export_development_project_with_report" in source
    assert "BuildReportDialog" in source


def test_report_dialog_exposes_diagnostics_files_and_output_folder() -> None:
    source = (ROOT / "editor" / "widgets" / "build_report_dialog.py").read_text(encoding="utf-8")

    assert 'tabs.addTab(issues, f"Diagnóstico' in source
    assert 'tabs.addTab(files, f"Arquivos' in source
    assert 'QPushButton("Abrir pasta do build")' in source

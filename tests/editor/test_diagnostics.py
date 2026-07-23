from pathlib import Path

from editor.runtime.diagnostics import DiagnosticCenter, EditorDiagnostic


def test_diagnostics_are_bounded_and_deduplicate_adjacent_failures() -> None:
    center = DiagnosticCenter(maximum_records=2)
    failure = EditorDiagnostic(
        "error", "Falha ao salvar", "Acesso negado",
        action="Escolha outra pasta", path=Path("Level.zscene"),
    )

    first = center.report(failure)
    repeated = center.report(failure)
    center.report(EditorDiagnostic("warning", "Asset ausente", "player.png"))
    center.report(EditorDiagnostic("error", "Build falhou", "Cena inválida"))

    assert first.severity == "ERROR"
    assert repeated.occurrences == 2
    assert len(center.records) == 2
    assert center.records[-1].title == "Build falhou"


def test_diagnostic_console_message_includes_recovery_action() -> None:
    diagnostic = EditorDiagnostic(
        "ERROR", "Falha ao abrir cena", "JSON inválido",
        action="Restaure uma cópia válida",
    )

    assert "Próxima ação: Restaure uma cópia válida" in diagnostic.console_message()

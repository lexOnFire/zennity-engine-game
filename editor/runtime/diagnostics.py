"""Structured, bounded editor diagnostics with recovery guidance."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class EditorDiagnostic:
    severity: str
    title: str
    message: str
    action: str = ""
    path: Path | None = None
    occurrences: int = 1

    def console_message(self) -> str:
        location = f" [{self.path}]" if self.path is not None else ""
        recovery = f" Próxima ação: {self.action}" if self.action else ""
        repeated = f" (repetido {self.occurrences}x)" if self.occurrences > 1 else ""
        return f"{self.title}: {self.message}{location}.{recovery}{repeated}"


class DiagnosticCenter:
    """Keep recent failures useful without allowing unbounded console growth."""

    def __init__(self, maximum_records: int = 200) -> None:
        if maximum_records < 1:
            raise ValueError("maximum_records must be positive")
        self._records: deque[EditorDiagnostic] = deque(maxlen=maximum_records)

    @property
    def records(self) -> tuple[EditorDiagnostic, ...]:
        return tuple(self._records)

    def report(self, diagnostic: EditorDiagnostic) -> EditorDiagnostic:
        normalized = replace(
            diagnostic,
            severity=str(diagnostic.severity or "ERROR").upper(),
            title=str(diagnostic.title).strip() or "Erro do editor",
            message=str(diagnostic.message).strip(),
        )
        if self._records and self._same_problem(self._records[-1], normalized):
            previous = self._records.pop()
            normalized = replace(previous, occurrences=previous.occurrences + 1)
        self._records.append(normalized)
        return normalized

    @staticmethod
    def _same_problem(left: EditorDiagnostic, right: EditorDiagnostic) -> bool:
        return (
            left.severity,
            left.title,
            left.message,
            left.action,
            left.path,
        ) == (
            right.severity,
            right.title,
            right.message,
            right.action,
            right.path,
        )

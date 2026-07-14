from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BuildIssue:
    """Aviso ou erro encontrado durante a validação/exportação."""

    severity: str
    message: str
    path: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class BuildReport:
    """Resultado serializável de uma exportação da Zennity."""

    project_name: str
    destination: str
    success: bool = False
    duration_seconds: float = 0.0
    total_size_bytes: int = 0
    file_count: int = 0
    files: list[str] = field(default_factory=list)
    issues: list[BuildIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[BuildIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[BuildIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    def add_error(self, message: str, path: str | Path = "") -> None:
        self.issues.append(BuildIssue("error", message, str(path)))

    def add_warning(self, message: str, path: str | Path = "") -> None:
        self.issues.append(BuildIssue("warning", message, str(path)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "destination": self.destination,
            "success": self.success,
            "duration_seconds": round(self.duration_seconds, 4),
            "total_size_bytes": self.total_size_bytes,
            "file_count": self.file_count,
            "files": list(self.files),
            "issues": [issue.to_dict() for issue in self.issues],
        }


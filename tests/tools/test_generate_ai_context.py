"""Regressões de segurança para o gerador de contexto de IA."""
from __future__ import annotations

import subprocess
from unittest.mock import patch

from tools import generate_ai_context


def test_run_invokes_subprocess_without_shell() -> None:
    with patch.object(subprocess, "check_output", return_value="ok") as check_output:
        result = generate_ai_context.run(["git", "status", "--short"])

    assert result == "ok"
    check_output.assert_called_once_with(
        ["git", "status", "--short"],
        cwd=generate_ai_context.ROOT,
        text=True,
        encoding="utf-8",
        errors="ignore",
    )


def test_run_preserves_non_raising_error_fallback() -> None:
    failure = subprocess.CalledProcessError(1, ["git", "status"])
    with patch.object(subprocess, "check_output", side_effect=failure):
        result = generate_ai_context.run(["git", "status"])

    assert "returned non-zero exit status 1" in result

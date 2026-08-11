"""Session fixtures for the PHASE 9.5B Stage 2 node system tests."""

from __future__ import annotations

import json

import pytest

from ._probe import BASELINE_PATH


@pytest.fixture(scope="session")
def baseline() -> dict:
    """The pre-Stage-2 snapshot Stage 2 must remain compatible with."""
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

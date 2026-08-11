"""Running the test suite must not modify the repository working tree.

PHASE 9.5B Stage 2.1.

``AssetDatabase`` defaults ``project_root`` to ``Path.cwd()``.  That is right for
the shipping editor, where the working directory *is* the project -- but under
pytest the working directory is the repository, so a service-lifecycle test that
constructed ``AssetDatabase()`` and called ``initialize_all()`` ran a full
``scan()`` over the repository's own ``Assets/`` and rewrote 314 ``.meta`` files.

The churn is persistent because 29 of the committed ``.meta`` files carry hashes
that no longer match their committed asset.  The database recomputes the correct
hash every run, so the diff reappears after every suite and never settles.

These tests fail loudly rather than letting that come back silently.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        pytest.skip(f"git unavailable or not a repository: {result.stderr.strip()}")
    return result.stdout


def _tracked_asset_changes() -> list[str]:
    """Tracked files under Assets/ that differ from HEAD."""
    return [
        line[3:].strip().strip('"')
        for line in _git("status", "--porcelain", "--", "Assets/").splitlines()
        if line and not line.startswith("??")
    ]


def test_asset_database_defaults_to_cwd_and_must_be_given_a_project_root():
    """Documents the sharp edge that caused the churn, so it stays visible."""
    from engine.assets.asset_database import AssetDatabase

    scoped = AssetDatabase(REPO_ROOT / "does-not-exist")
    assert scoped.project_root == (REPO_ROOT / "does-not-exist").resolve()

    # The no-argument form silently binds to the current working directory.
    # Nothing scans here -- constructing is harmless, initialize()/scan() is not.
    defaulted = AssetDatabase()
    assert defaulted.project_root == Path.cwd().resolve()


def test_no_test_constructs_an_unscoped_asset_database():
    """A scan from an unscoped database writes into the real Assets/ tree."""
    offenders: list[str] = []
    for path in sorted((REPO_ROOT / "tests").rglob("test_*.py")):
        if path.resolve() == Path(__file__).resolve():
            continue  # this file names the pattern in order to document it
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "AssetDatabase()" in text:
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert not offenders, (
        "these tests build an AssetDatabase bound to the current working "
        f"directory and will rewrite the repository's Assets/: {offenders}. "
        "Pass an explicit project_root (pytest's tmp_path)."
    )


def test_scanning_a_temporary_project_never_touches_the_repository(tmp_path):
    """The positive case: a scoped database writes only inside its own root."""
    from engine.assets.asset_database import AssetDatabase

    assets = tmp_path / "Assets"
    assets.mkdir()
    (assets / "sample.zscene").write_text('{"objects": []}', encoding="utf-8")

    before = _tracked_asset_changes()

    database = AssetDatabase(tmp_path)
    database.initialize()
    assert (assets / "sample.zscene.meta").is_file(), "the scan did not run"

    assert _tracked_asset_changes() == before, (
        "a scan scoped to a temporary project still modified tracked repository assets"
    )


def test_committed_meta_hashes_match_their_assets():
    """The 29 stale hashes are why the churn never settles.

    Marked xfail rather than skipped: the repository genuinely carries stale
    metadata, and this test is the record of it.  Committing the regenerated
    .meta files -- a deliberate, reviewable change -- is what turns it green.
    """
    stale: list[str] = []
    for relative in _git("ls-files", "Assets/").split("\n"):
        relative = relative.strip()
        if not relative.endswith(".meta"):
            continue
        committed = _git("show", f"HEAD:{relative}")
        try:
            data = json.loads(committed)
        except json.JSONDecodeError:
            continue
        source = REPO_ROOT / str(data.get("source_path", ""))
        if not source.is_file():
            continue
        actual = hashlib.sha256(source.read_bytes()).hexdigest()
        if data.get("hash") and data["hash"] != actual:
            stale.append(relative)

    if stale:
        pytest.xfail(
            f"{len(stale)} committed .meta files carry a hash that does not match "
            f"their asset, so every scan rewrites them: {stale[:5]}"
        )

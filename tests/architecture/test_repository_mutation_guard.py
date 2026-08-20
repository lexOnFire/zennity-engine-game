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

import ast
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


#: Source trees the suite must never leave modified. ``Assets/`` is covered by
#: its own helper below; everything here is code and configuration.
SOURCE_TREES = ("engine/", "editor/", "tests/", "tools/", "scripts/")

#: Modules that deliberately rewrite a file *outside* ``Assets/`` and are
#: required to restore it byte for byte.  ``test_projection_fidelity`` mutates
#: ``engine/logic/node_definitions/catalogue.py`` to prove its own guard can go
#: red; that is legitimate, restoring it as CRLF was not.
SOURCE_MUTATING_MODULES = (
    "tests/logic/test_projection_fidelity.py",
)


def _porcelain(*pathspecs: str) -> list[str]:
    """Tracked files under ``pathspecs`` that differ from HEAD.

    Untracked entries are dropped: ``__pycache__``, ``.pytest_cache`` and every
    other build artefact is either ignored by git or shows up as ``??``, and
    neither is a repository mutation.
    """
    return [
        line[3:].strip().strip('"')
        for line in _git("status", "--porcelain", "--", *pathspecs).splitlines()
        if line and not line.startswith("??")
    ]


def _tracked_source_changes() -> list[str]:
    """Tracked code/config files that differ from HEAD."""
    return _porcelain(*SOURCE_TREES)


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


#: Modules that build a project root and persist to it.  A static scan for
#: ``Path.cwd()`` alone is useless here -- many tests legitimately *read*
#: reference assets from the repository and write into tmp_path -- so these are
#: executed for real and the working tree is checked afterwards.
ASSET_WRITING_MODULES = (
    "tests/test_phase8b_checkpoint_a.py",
    "tests/test_phase8b_checkpoint_b.py",
    "tests/unit/test_asset_handle.py",
    "tests/editor/test_project_exporter.py",
    "tests/integration/test_phase8a_editor_scene_opening.py",
)


def test_running_the_asset_writing_modules_leaves_the_tree_untouched():
    """Record the tree, run the modules that persist assets, compare.

    This is the contract that matters, and it is checked by execution rather
    than by pattern-matching source: two Phase 8B checkpoints used to rewrite
    Assets/Logic/PlayerMovement.zlogic and
    Assets/Scenes/CanonicalGameplayTest.zscene on every run.
    """
    import os
    import sys

    before = sorted(_tracked_asset_changes())

    environment = dict(os.environ)
    environment.update(
        SDL_VIDEODRIVER="dummy",
        SDL_AUDIODRIVER="dummy",
        PYGAME_HIDE_SUPPORT_PROMPT="1",
        QT_QPA_PLATFORM="offscreen",
    )
    existing = [name for name in ASSET_WRITING_MODULES if (REPO_ROOT / name).is_file()]
    assert existing, "no asset-writing modules found; this guard would be vacuous"

    subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=no", *existing],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=environment,
        timeout=900,
    )

    after = sorted(_tracked_asset_changes())
    newly_dirty = sorted(set(after) - set(before))
    assert not newly_dirty, (
        "running the asset-writing test modules modified tracked repository "
        f"assets: {newly_dirty}"
    )


def test_running_the_source_mutating_modules_restores_every_byte():
    """The same contract as the asset guard, for code instead of assets.

    ``_tracked_asset_changes`` scopes ``git status`` to ``Assets/``, so a test
    that rewrote a *source* file passed through it unseen.  That is exactly what
    happened: ``test_projection_fidelity`` restored
    ``engine/logic/node_definitions/catalogue.py`` through ``Path.write_text``,
    which re-encodes newlines with ``os.linesep`` and turned a LF file into CRLF
    on Windows.  Same content, whole file rewritten, tree dirty after every run.

    Differential rather than absolute: a developer's own edits are already dirty
    before this runs, so only files that become dirty *because of* the subprocess
    are reported.
    """
    import os
    import sys

    before = set(_tracked_source_changes())

    environment = dict(os.environ)
    environment.update(
        SDL_VIDEODRIVER="dummy",
        SDL_AUDIODRIVER="dummy",
        PYGAME_HIDE_SUPPORT_PROMPT="1",
        QT_QPA_PLATFORM="offscreen",
    )
    existing = [name for name in SOURCE_MUTATING_MODULES if (REPO_ROOT / name).is_file()]
    assert existing, "no source-mutating modules found; this guard would be vacuous"

    subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=no", *existing],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=environment,
        timeout=900,
    )

    newly_dirty = sorted(set(_tracked_source_changes()) - before)
    assert not newly_dirty, (
        "running the source-mutating test modules left tracked code modified: "
        f"{newly_dirty}. A test may rewrite a source file to prove a guard "
        "works, but it must restore the exact bytes it read -- use "
        "read_bytes()/write_bytes(), not read_text()/write_text()."
    )


#: Roots a test uses to address the checkout itself.
_REPOSITORY_ROOTS = {"REPO_ROOT", "ROOT", "PROJECT_ROOT", "project_root"}
_SOURCE_TREE_NAMES = {tree.rstrip("/") for tree in SOURCE_TREES} - {"tests"}
_MUTATING_METHODS = {"write_text", "write_bytes", "unlink", "rename", "touch", "chmod"}


def _addresses_a_source_file(node: ast.AST) -> bool:
    """True for ``REPO_ROOT / "engine" / ...`` and any longer chain from it.

    Matching the expression rather than the file's text is what separates a test
    that rewrites the checkout from one that merely reads a reference file and
    writes its output into ``tmp_path`` -- the majority, and the reason a plain
    substring scan reports them all.
    """
    root_seen = False
    tree_seen = False
    while isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        right = node.right
        if isinstance(right, ast.Constant) and right.value in _SOURCE_TREE_NAMES:
            tree_seen = True
        node = node.left
        if isinstance(node, ast.Name) and node.id in _REPOSITORY_ROOTS:
            root_seen = True
    return root_seen and tree_seen


def test_a_test_that_writes_into_a_source_tree_is_declared():
    """Keep the executed guard above from going stale as tests are added.

    The differential check only covers the modules it is told about.  This finds
    the ones it should be told about: a module that calls a mutating method on a
    path built from the repository root into a source tree, whether written
    inline or bound to a module constant first.
    """
    undeclared: list[str] = []
    for path in sorted((REPO_ROOT / "tests").rglob("test_*.py")):
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative == Path(__file__).relative_to(REPO_ROOT).as_posix():
            continue  # this file names the pattern in order to document it
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue

        bound: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and _addresses_a_source_file(node.value):
                bound.update(
                    target.id for target in node.targets if isinstance(target, ast.Name)
                )

        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)):
                continue
            if node.func.attr not in _MUTATING_METHODS:
                continue
            receiver = node.func.value
            hits_source = _addresses_a_source_file(receiver) or (
                isinstance(receiver, ast.Name) and receiver.id in bound
            )
            if hits_source and relative not in SOURCE_MUTATING_MODULES:
                undeclared.append(relative)
                break

    assert not undeclared, (
        "these test modules call a mutating method on a path inside a source "
        f"tree but are not listed in SOURCE_MUTATING_MODULES: {undeclared}. Add "
        "them so the executed guard covers them, or stop writing into the checkout."
    )


def test_no_tracked_asset_file_is_modified_outside_metadata():
    """Only .meta may ever differ; a changed .zlogic/.zscene is a test writing home."""
    non_metadata = [
        path
        for path in _tracked_asset_changes()
        if not path.endswith(".meta")
    ]
    assert not non_metadata, (
        f"tracked non-metadata assets have been modified: {non_metadata}. "
        "Something wrote into the repository's Assets/ tree."
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

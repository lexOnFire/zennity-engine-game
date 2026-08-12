"""Editor state files must not survive a test run inside the repository.

PHASE 9 recovery item 9B. Stage 2.1 stopped tests writing *assets*; it never
covered the editor's own state, and that turned out to be the worse half,
because the editor reads it back on the next construction:

    .zennity/last_graph_<category>.json   GenericGraphEditorWidget
    .zennity/last_ui.json                 UIBuilderDock
    .zennity/recovery/*.autosave.zlogic   LogicGraphPersistenceMixin
    .zennity_autosave.json + manifest     AutosaveManager

The symptom was a test that passed alone and failed after the suite:
``test_delete_removes_selected_behavior_node_and_marks_document_dirty``
asserted an empty canvas and found three nodes restored from a graph a previous
test had opened. That is not a flaky test; it is a shared mutable file in the
checkout.

The guard below is empirical -- it runs the workflows that produce this state in
a subprocess and looks at the repository afterwards -- because a static scan
cannot tell a legitimate read of a repository asset from a write.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Everything the editor may drop into a project root, relative to it.
STATE_ARTIFACTS = (
    ".zennity",
    ".zennity_autosave.json",
    ".zennity_autosave_manifest.json",
    ".zennity_session.lock",
)

#: Modules proven (by bisecting the suite) to create editor state.
STATE_PRODUCING_MODULES = (
    "tests/editor/test_all_tabs_demo.py",
    "tests/editor/test_isolated_editor_startup.py",
    "tests/editor/test_visual_logic_window_isolation.py",
    "tests/editor/test_visual_scripting_productivity_tabs.py",
    "tests/unit/test_behavior_tree_platform.py",
)


def _repository_state_artifacts() -> set[str]:
    return {name for name in STATE_ARTIFACTS if (REPO_ROOT / name).exists()}


def _run_pytest(*targets: str, timeout: int = 900) -> subprocess.CompletedProcess:
    environment = dict(os.environ)
    environment.update(
        SDL_VIDEODRIVER="dummy",
        SDL_AUDIODRIVER="dummy",
        PYGAME_HIDE_SUPPORT_PROMPT="1",
        QT_QPA_PLATFORM="offscreen",
    )
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--tb=no", *targets],
        cwd=REPO_ROOT, capture_output=True, text=True, env=environment, timeout=timeout,
    )


@pytest.fixture(scope="module")
def state_producing_run():
    """Run the state-producing modules once and report what they left behind."""
    existing = [name for name in STATE_PRODUCING_MODULES if (REPO_ROOT / name).is_file()]
    assert existing, "no state-producing modules found; this guard would be vacuous"
    before = _repository_state_artifacts()
    result = _run_pytest(*existing)
    return {"before": before, "after": _repository_state_artifacts(), "result": result}


def test_the_state_producing_modules_still_pass(state_producing_run):
    """Isolation must not be achieved by breaking the tests it isolates."""
    result = state_producing_run["result"]
    assert result.returncode == 0, f"{result.stdout[-3000:]}\n{result.stderr[-2000:]}"


def test_no_editor_state_is_left_in_the_repository(state_producing_run):
    leaked = sorted(state_producing_run["after"] - state_producing_run["before"])
    assert not leaked, (
        f"the suite left editor state in the checkout: {leaked}. These files are "
        "read back by the next editor built in the same working directory, which "
        "makes test results depend on execution order."
    )


def test_the_isolation_fixture_is_active_repository_wide():
    """It has to come from tests/conftest.py, not from one directory's conftest."""
    conftest = (REPO_ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")
    assert "_isolated_project_state" in conftest
    assert (REPO_ROOT / "tests" / "_isolated_project_state.py").is_file()


def test_a_test_chosen_temporary_root_is_not_hijacked(tmp_path):
    """Only a root inside the checkout is redirected; tmp_path stays tmp_path."""
    from editor.autosave_manager import AutosaveManager

    manager = AutosaveManager(tmp_path, snapshot_fn=lambda: {"scene": {}})
    manager.flush()
    assert (tmp_path / AutosaveManager.RECOVERY_FILENAME).is_file(), (
        "the guard redirected a root the test chose itself"
    )


def test_a_repository_root_is_redirected_away():
    from editor.autosave_manager import AutosaveManager

    manager = AutosaveManager(REPO_ROOT, snapshot_fn=lambda: {"scene": {}})
    manager.flush()
    assert not (REPO_ROOT / AutosaveManager.RECOVERY_FILENAME).exists(), (
        "an autosave rooted at the repository still wrote into it"
    )


# ---------------------------------------------------------------------------
# Order independence -- the property the isolation exists to provide
# ---------------------------------------------------------------------------

ORDER_VICTIM = (
    "tests/unit/test_behavior_tree_platform.py"
    "::test_delete_removes_selected_behavior_node_and_marks_document_dirty"
)
ORDER_CONTAMINATOR = "tests/editor/test_visual_logic_window_isolation.py"


def test_the_victim_passes_alone_and_after_the_contaminator():
    """The historical failure, reproduced as a contract.

    Before the fix these two runs disagreed: alone it passed, after the module
    that opens a graph it failed, because the canvas restored that graph from
    ``.zennity/last_graph_behavior_tree.json``.
    """
    if not (REPO_ROOT / ORDER_CONTAMINATOR).is_file():
        pytest.skip(f"{ORDER_CONTAMINATOR} is not in this checkout")

    alone = _run_pytest(ORDER_VICTIM)
    after = _run_pytest(ORDER_CONTAMINATOR, ORDER_VICTIM)

    assert alone.returncode == 0, f"the victim fails even alone:\n{alone.stdout[-2000:]}"
    assert after.returncode == alone.returncode, (
        "the result depends on what ran before it:\n"
        f"alone: rc={alone.returncode}\nafter contaminator: rc={after.returncode}\n"
        f"{after.stdout[-3000:]}"
    )

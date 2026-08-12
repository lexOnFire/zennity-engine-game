# PHASE 9 Recovery — Stage 2.1 test infrastructure

Branch: `integration/phase9-recovery`
Base: `bbced37`

---

## 1. Why this came before rebuilding Items 1–8

The `integration/phase9-stabilization` lineage carrying Items 1–8 was lost with
its container: it was never pushed, because `git push` returns 403 for this
session and the GitHub App cannot create refs either. Rebuilding those items is
the larger job, and it is the job that most needs a trustworthy suite — Item 8
burned a full cycle chasing a "new regression" that turned out to be leftover
state from a previous run. So the infrastructure comes first, and every
checkpoint gets pushed off the container from here on.

## 2. Audit of the Stage 2.1 commits

All four are already **ancestors of `bbced37`**:

```
bbced37  (base)
  e4e091e  fix(assets): synchronize canonical asset metadata hashes
  7d2f7e2  test: real_dialog opt-out, QMenu/QApplication, stop asset writes
  179ed3c  test: repository-wide headless dialog contract, drop an import cycle
  8e3ab31  test(editor): headless-safe suite, stop mutating repository Assets
```

There was nothing to cherry-pick. That includes `e4e091e`, which the brief said
never to apply: on the old `fix/executor-port-contract` lineage it would have
imported metadata belonging elsewhere, but here it is already part of the base
and its result is verified consistent (section 8). No metadata commit is needed
or made.

| Commit | Change | Status on `bbced37` |
|---|---|---|
| 8e3ab31 | `tests/editor/conftest.py` seam | **OBSOLETE** — replaced by 179ed3c |
| 8e3ab31 | `tests/editor/__init__.py` | **ALREADY PRESENT** |
| 8e3ab31 | `test_repository_mutation_guard.py` | **ALREADY PRESENT**, extended here |
| 8e3ab31 | `tests/unit/test_asset_handle.py` → tmp_path | **ALREADY PRESENT**, verified |
| 8e3ab31 | `pytest.ini`, `requirements-dev.txt` | **ALREADY PRESENT** |
| 179ed3c | `tests/_headless_dialogs.py` | **ALREADY PRESENT**, one real gap fixed here |
| 179ed3c | `tests/conftest.py` | **ALREADY PRESENT**, extended here |
| 179ed3c | registry cycle removal | **ALREADY PRESENT** |
| 7d2f7e2 | `real_dialog` opt-out | **ALREADY PRESENT**, now tested |
| 7d2f7e2 | QMenu / QApplication coverage | **PRESENT BUT BROKEN** — see section 4 |
| 7d2f7e2 | checkpoint A/B tmp_path | **ALREADY PRESENT**, verified |
| e4e091e | metadata hashes | **ALREADY PRESENT**, idempotent |

So the work in this item is the two things Stage 2.1 did *not* do: fix the QMenu
seam, which never worked, and isolate editor state, which it never covered.

## 3. Qt blocking-call inventory (current, `bbced37`)

| API | production call sites |
|---|---|
| `QFileDialog.*` | 22 |
| `QMessageBox.*` | 58 |
| `QMenu.exec` / `exec_` | 9 |
| `QApplication.exec` / `exec_` | 4 |
| `QDialog.exec` on instances | 5 (`dialog.exec(`) |
| `QEventLoop` | 0 |

## 4. The QMenu seam never worked

Stage 2.1 neutralised QMenu with

```python
monkeypatch.setattr(QMenu, "exec", replacement, raising=False)
```

and that **looks** correct — after it runs, `type(QMenu.exec).__name__` really is
`function`. But Shiboken resolves the method on the *instance* through its own
metaobject, so `menu.exec()` still reaches the C++ slot and still opens a
blocking loop:

```
before: builtin_function_or_method
after : function          <- the class attribute did change
resolved (m.exec): builtin_function_or_method   <- and is ignored
```

No test ever called it, so nothing failed and the gap stayed invisible for three
commits. The first test written against it hung the run immediately.

`QDialog.exec` does **not** have this problem — patching it works, verified —
which is why the difference went unnoticed.

The fix installs a Python subclass (virtual dispatch through Shiboken does
work for those) and rebinds the name in two directions: in `PySide6.QtWidgets`
itself, covering modules that import `QMenu` after the fixture runs, and in the
`editor`/`engine` modules that imported it before. Production writes
`menu = QMenu(self)`, which resolves the module global, so it gets the safe one.

## 5. Editor state contamination — new work

Stage 2.1 stopped tests writing *assets*. It never covered the editor's own
state files, and those are worse, because the editor **reads them back**:

| File | Written by |
|---|---|
| `.zennity/last_graph_<category>.json` | `generic_graph_editor.py:554`, `Path.cwd()` |
| `.zennity/last_ui.json` | `ui_builder_dock.py:250`, `project_root` |
| `.zennity/recovery/UntitledLogic.autosave.zlogic` | `persistence_mixin.py:370` |
| `.zennity_autosave.json` + manifest + lockfile | `autosave_manager.py`, `project_root` |

`EditorContext.project_root` defaults to `Path.cwd()`, which under pytest is the
checkout. The consequence is an order-dependent suite:
`test_delete_removes_selected_behavior_node_and_marks_document_dirty` asserts an
empty canvas after deleting its only node, and found three nodes (`wait`,
`move`, …) restored from a graph a *previous* test had opened. It passed alone
and failed after the suite — proven both ways, and now pinned as a test.

`tests/_isolated_project_state.py` redirects this state, with a deliberately
narrow rule: **only a root that resolves inside the checkout is redirected**.
`tests/editor/test_scene_autosave_controller.py` passes its own `tmp_path` and
asserts the recovery file lands there; that keeps working untouched. No
production code changed. Opt out with `@pytest.mark.real_project_state`.

Each test gets a *fresh* directory, created lazily on first use — a shared one
would isolate the repository but not the tests from each other, which is half
the bug. Lazily, because ~4000 eager temp directories cost more than the
isolation is worth when almost no test touches editor state.

The recovery path was the last one found: it is written by a deferred autosave
timer, so it lands after the test that armed it has torn down. It never appeared
when a file was run alone — only at the end of a whole-directory run.

## 6. The three historical hangs

All terminate naturally, no timeout, no SIGKILL:

| Test | Result | Duration |
|---|---|---|
| `tests/editor/test_phase1_editor_context.py` | 40 passed | 3.52 s |
| `tests/editor/test_phase1_scale_tool.py` | 6 passed | 0.67 s |
| `tests/integration/test_memory_leak.py` | 1 passed | 12.10 s |

`test_memory_leak` drives 500 Play/Stop cycles; historically it hung for >2400 s.

## 7. Full suite

Both runs completed with no exclusions — `tests/editor` and `test_memory_leak`
included.

| | run 1 (before) | run 2 (after) |
|---|---|---|
| collected | 4113 | 4133 |
| passed | 3982 | 4004 |
| failed | 127 | 125 |
| skipped | 3 | 3 |
| xfailed | 1 | 1 |
| duration | 459.5 s | 459.9 s |
| tracked tree after | clean | clean |
| state artifacts left | `.zennity/`, `.zennity_autosave.json`, manifest | **none** |

**Fixed: 2. New regressions: 0.** Both fixed tests were order-dependent victims
of the state contamination:
`test_visual_scripting_productivity_tabs.py::test_specialized_starter_creates_real_nodes`
and `test_behavior_tree_platform.py::test_delete_...`.

The remaining 125 failures are pre-existing on `bbced37` and untouched here.
They include the node-semantics differences (`move.speed` 100 vs 200,
`move_by` `x/y` vs `delta_x/delta_y`) that belong to a later item, and everything
that Items 1–8 used to fix — this base predates that work.

## 8. Metadata

Canonical scan (`AssetDatabase(REPO_ROOT).initialize()`), run twice:

```
first scan:   modified=0  new=0  non-meta=0
second scan:  modified=0  new=0  non-meta=0
```

Idempotent, and already consistent — `e4e091e` is in the base. The previously
`xfail`ed `test_committed_meta_hashes_match_their_assets` now passes. **No
metadata commit was made or is needed.**

## 9. Differences from the original Stage 2.1

1. QMenu is neutralised by subclass rebinding rather than `setattr`, because
   `setattr` silently does not work.
2. `QApplication.exec` raises instead of answering — answering would be a lie,
   since a test that calls it wants the loop.
3. The headless seam now has tests of its own. Its failure mode is a hang, not a
   red test, so nothing would have reported a regression in it.
4. Editor state isolation is entirely new.
5. The mutation guard is joined by a state guard that reproduces the historical
   order-dependency as an executable contract.

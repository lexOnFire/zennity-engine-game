# PHASE 9 — Recovery Item 16D: case-colliding script paths

Base: `7ce562a4` · Case collisions: **10 groups → 0** · Assets functionally modified: **0**

Ten files existed twice, differing only in the case of their path:

```
Assets/Scripts/animator.py
assets/scripts/animator.py
```

All ten pairs are **byte identical** — same size, same SHA-256. Classification
**A — BYTE IDENTICAL DUPLICATE** for every group, with no divergence to
reconcile and nothing to merge.

## Why it mattered

Linux treats the two paths as different files and keeps both. Windows and macOS
cannot: on a fresh clone git prints

```
warning: the following paths have collided ... and only one from the same
colliding group is in the working tree
```

and silently drops one side. Which side survives is not something the project
controls.

That is also the answer to a puzzle from item 16B.1: on Windows the
`Assets/Scripts/*.meta` hashes looked stale. They were not — the recorded hashes
matched the repository content exactly. The file *on disk* was the other copy of
the pair, so the hash of what was there did not match the hash of what was
recorded. The metadata was right; the checkout was ambiguous.

## The decision was already made, and already documented

This item chose nothing. `docs/architecture/ASSETS_CASING_MIGRATION.md` states
it plainly:

> O repositório da engine usa exclusivamente a raiz canônica `Assets/`.
> A antiga árvore `assets/scripts` foi removida...
> Um gate de arquitetura impede que a raiz minúscula volte a ser versionada.

Two of those three sentences were true. The lowercase tree had **not** been
removed — all ten files were still tracked — and the gate,
`tests/architecture/test_canonical_assets_root.py::test_repository_has_only_canonical_root_assets_tree`,
had been failing continuously ever since, recording the gap it was written to
catch.

So item 16D finished a migration that was declared complete, rather than making
a call of its own.

## Evidence gathered before removing anything

| question | answer |
|---|---|
| content differs? | no — all 10 pairs byte identical |
| which side carries `.meta`? | `Assets/Scripts` has all 10; `assets/scripts` has none |
| production code reading `assets/scripts`? | **none** |
| tests referencing it? | 3, all string literals against `tmp_path` fixtures exercising `AssetPathResolver`, none reading the repository tree |
| history | `Assets/Scripts` traces back through `cd8365a5` *"resolve conflito de caminhos do Animator no Windows"*; `assets/scripts` through `459b894f`. The Windows-conflict commit is on the canonical side. |

External projects keep working: `AssetPathResolver` accepts any casing of the
root, matches path components case-insensitively, and re-serializes with the
`Assets/` prefix. That compatibility lives in the resolver, which is why no
symlink, copy or fallback loader was added here — section 10's rule, and the
right one.

## What changed

- `git rm -r assets/scripts` — 10 files, byte-identical duplicates.
- Three tests in `tests/architecture/test_repository_hygiene.py`:
  a repository-wide casefold gate, an anti-vacuity check proving the detector
  detects, and an assertion that no tracked path starts with `assets/`.

No `.zlogic`, `.zscene`, `.zprfb` or `.meta` was touched. No import changed,
because nothing imported the lowercase path.

## The gate is repository-wide

Checking only `Assets/Scripts` would have missed the next collision. The gate
casefolds **every tracked path** and fails on any group with more than one
member, so a collision introduced anywhere is caught where it appears.

Its anti-vacuity companion proves the detector works on a synthetic pair and
that the real sweep covers more than a thousand paths — a gate that cannot fail
would be worse than none.

## Results

| | before | after |
|---|---|---|
| case collisions | 10 groups / 20 files | **0** |
| tracked files | 2035 | 2025 |
| `test_canonical_assets_root` | **failing** | **passing** |
| assets functionally modified | — | **0** |

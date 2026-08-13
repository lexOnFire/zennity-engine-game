# PHASE 9 — Recovery Item 14F: `move_by.velocity` cleanup

Base: `3cd7dfe7` · **Assets modified: 0**

`move_by` no longer declares a `velocity` input. This is a contract change only:
the executor was not touched, and `x`/`y` mean exactly what they meant before.

## Where the pin came from

`b19f603e` — *"fix(logic): resolve validator errors in PlayerMovementLogic and
register port definitions"*. It was added to `graph_asset.py`'s hand-maintained
port table alongside a mass rewrite of `PlayerMovementLogic.zlogic`, i.e. to
make a validator stop complaining. `b3a24b71` later moved that table into
`catalogue.py` as `_EXPLICIT_PORT_CONTRACTS`, where `move_by` was declared
**twice** with different pins and the second won — the same duplicate that put
`delta_x`/`delta_y` in the palette, which item 9 removed.

`git log -S'"velocity"' -- engine/logic/runtime/nodes/movement_nodes.py` returns
nothing: **no commit in the repository's history ever made an executor read it.**
There is no lost runtime to restore.

Critically, the *declarative* `MoveByNode` never had the pin. It declares
`exec`, `x`, `y` → `exec_done` and always did. `velocity` existed only in the
projection table, which is why that table was the correct — and only — place to
remove it. Nothing had to be hidden behind an Inspector filter.

## Why it looked necessary, and why it stopped being

Item 9 found the field authorable and unread, and could not remove it:
`BossAILogic` and `EnemyAILogic` wired `multiply_number.value` into
`move_by.velocity`, so deleting the pin would have orphaned two shipping edges.
Reading it instead would have started moving two enemies that had stood still —
a gameplay decision item 9 was not authorized to take. It was recorded as debt
and carved out of the generic "no authorable field is ignored" gate.

Item 14E reauthored both graphs onto `move_by.x` / `move_by.y`. That removed the
last producer, and with the executor never having been a consumer, the pin
became a field the Inspector offered that moved nothing.

## Current usage, measured

Measured on **normalized** graphs — raw files hide aliases and seeded defaults.

| question | answer |
|---|---|
| `move_by` instances in shipping assets | 24, across 11 graphs |
| edges into `velocity` | **0** |
| non-default `velocity` values | **0** |
| executor reads `velocity` | **NO** (reads `x`, `y`, `target`) |
| any commit ever read it | **NO** |
| plugins / templates / recipes requiring it | **none** |

### One honest wrinkle

Three graphs — `BossAILogic`, `BossHealthLogic`, `EnemyAILogic` — still carry a
`velocity` **property** after normalization, on their "stop" nodes. It comes from
the raw legacy `config` (`physics.set_velocity` with `[0, 0]`, the legacy idiom
for "stop"), and the migration preserves unknown authored data verbatim. So the
property outlives the pin.

That is harmless and was left alone: every survivor is the zero vector, each of
those nodes also has `x`/`y` at zero, and nothing reads either. Removing the pin
discarded no authored value. The assets were **not** edited to tidy this, and
the unknown-property policy was not changed.

## Classification

**C — DEAD AUTHORING PROPERTY.** Not B (no legacy port alias maps onto it), not
D (no runtime ever consumed it), not E (no plugin declares it).

## What changed

- `engine/logic/node_definitions/catalogue.py` — `velocity` dropped from
  `_EXPLICIT_PORT_CONTRACTS["move_by"]`. `in`, `target`, `x`, `y`, `next` kept.
- The generic gate `test_no_authorable_property_is_ignored_by_the_executor` lost
  its `- {"velocity"}` carve-out. It is now unconditional and names no node —
  section 15's ask, achieved by deleting an exemption rather than adding a rule.
- Recorded assertions inverted, not deleted: the item 9 "declared but unread"
  test, and the item 14C "move_by offers a `vector2` socket" find.
- `registration_baseline.json` — the pre-Stage-2 snapshot drops the pin, with
  provenance and the previous value kept in `_provenance_item_14F`. It is the
  single deliberate divergence from that contract; every other entry is intact.

**No alias was created.** Mapping `velocity` onto `x`, or onto a synthesized
pair, would invent a semantics no commit implemented, on a pin that fed nothing.
Removing is better than lying.

## Legacy graph behaviour (documented, not changed)

A hand-made legacy document wiring into `move_by.velocity` — the case that no
longer exists in the repository — is loaded like this:

- the node id still migrates (`physics.set_velocity` → `move_by`);
- **the edge is preserved verbatim**, not dropped, rewritten or rejected;
- `velocity` is not in the declared inputs, so the edge surfaces as an unknown
  port and is visible to the orphan-edge gate;
- the graph still loads and builds a runtime — an unknown port is not fatal.

This is the pre-existing policy for unknown ports. Item 14F did not modify it.

## Regression results

| | before | after |
|---|---|---|
| orphan edges | 50 | **50** |
| phantom ids | 29 | **29** |
| phantom instances | 57 | **57** |
| `audit --ci` | PASS | **PASS** |
| Assets modified | — | **0** |

`tests/logic`: 10 failures, identical to the `3cd7dfe7` baseline — 0 new.
Boss and Enemy chase revalidated (not re-edited): still driven through `x`/`y`,
no `velocity`, chase intact.

All gates were mutation-tested: reintroducing the pin fails both the dedicated
suite **and** the now-unconditional generic gate; removing `x` fails too, so the
suite defends the live pins as well as the dead one's absence.

# PHASE 9 — Recovery Item 15.1: Player movement test reconciliation

Base: `6ee7e3f3` · **Assets modified: 0** · Classification: **F — MIXED**

Two tests in `tests/logic/test_logic_graph_asset.py` now describe the Player
graph the game actually loads. No asset was touched.

> Base note: the item spec named `e8e7e774`. The branch was one commit ahead —
> `6ee7e3f3`, the documentation-only commit recording the item 14E playtest,
> authored and pushed after the spec was written. One `.md` file, no code.

## The two assets are not the same file

| | |
|---|---|
| what the game loads | `Assets/Logic/PlayerMovementLogic.zlogic` — 4 nodes, bound by `Player.zprfb` and `Level1.zscene` |
| what the tests loaded | `Assets/Logic/PlayerMovement.zlogic` — 3 nodes, bound by `CanonicalGameplayTest.zscene` |

Different graphs at similar paths. Treating them as interchangeable is what made
this look like a stale test for so long.

## The test was not obsolete — it was born orphaned

This corrects an earlier diagnosis of mine, which said the assertion described a
shape the asset "no longer has". The history says otherwise.

At `0d2ba5f8`, the commit that **introduced** these tests, the file at
`Assets/Logic/PlayerMovement.zlogic` was **already** the three-node stub it is
today. The test was written verbatim as it stands. It could never have passed on
this branch.

And the shape it asserts is not invented. It matches a real graph exactly:

```
6a88b9ee  feat(logic): add visual logic graph workspace
  Assets/Logic/PlayerMovement.zlogic — 8 nodes / 7 edges
  types: event_update, input_axis, if_else, move,
         key_pressed, is_grounded, jump, play_animation
  move.speed = 220.0   ->  1 x 220 x 0.5 = 110.0   (the expected x)
  jump.force = 440.0                               (the expected jumps)
```

Every number in the assertion comes from that graph. **`6a88b9ee` is not an
ancestor of this branch.**

This is the third time this lineage pattern has appeared in Phase 9. Item 11
found definitions that arrived while their executors did not. Item 14C found
assets authored against an API that never shipped here. This time **the test
arrived and its asset did not**.

## Why F — MIXED

| question | answer |
|---|---|
| Is the test wrong? | No — it describes a real, coherent graph |
| Is the asset wrong? | No — the 3-node stub is valid: 0 phantom, 0 orphan, `validate_logic_graph` clean |
| Is the runtime wrong? | No — it produces `0.5`, correct for a 3-node graph |
| Is there a gameplay bug? | No — the Player uses the other asset and works (manual playtest PASS) |

No single category A–E covers it: a valid test, a valid asset, and a path they
happen to share.

## What changed

`test_player_movement_demo_contains_expected_visual_flow` and
`test_player_movement_demo_executes_move_and_jump_nodes` were replaced by three
tests against `PlayerMovementLogic.zlogic`:

| old assertion | why invalid here | new assertion |
|---|---|---|
| 7 node types incl. `jump`, `is_grounded`, `key_pressed` | those nodes exist only in the `6a88b9ee` graph, absent from this lineage | the graph the game binds contains `event_update`, `input_axis`, `if_else`, `move`, and validates clean |
| `len(edges) == 7` | layout of a graph this branch never had; a count is brittle even when right | every edge names a **declared port**, every node exists in the catalogue — the same rule the shipping-asset gate uses |
| `x == 110.0` from `move.speed 220` | correct number, wrong asset — coincidentally the shipped graph authors 220 too | `+1.0 → +110.0`, `-1.0 → -110.0`, `0.0 → no movement and no `move` execution` |
| `jumps == [440.0]` | no jump node exists in this lineage's Player graph | **not replaced** — recorded as debt below |

The binding itself is now asserted (`Player.zprfb` and `Level1.zscene` reference
the asset), because a behavioural test pointed at the wrong graph is precisely
the failure this item untangled.

### Overlap with item 15, kept deliberate and small

`test_numeric_condition_coercion.py` already drives this asset to prove
`_condition` handles numbers. The test here proves something different: that the
**shipped graph** turns an axis into displacement at the speed it authors. It
would still fail if the asset were rewired or its speed changed.

## Debt this item does NOT pay

**Jump and animation coverage.** The 8-node demo at `6a88b9ee` covered `jump`,
`is_grounded`, `key_pressed` and `play_animation`. Nothing covers them now.

Restoring it is **not** a test fix: it would change what
`CanonicalGameplayTest.zscene` loads and would reintroduce an asset from a
non-ancestor lineage. That is a content and design decision deserving its own
playtest.

> ### Future item — PlayerMovement Demo Asset Restoration
>
> Decide, deliberately, whether `Assets/Logic/PlayerMovement.zlogic` should be
> restored to the `6a88b9ee` 8-node version — recovering `jump`,
> `is_grounded` and `play_animation` coverage and changing what
> `CanonicalGameplayTest.zscene` runs — or whether that demo should be retired.
> Either way the outcome should be explicit, not the result of a test edit.
>
> Everything needed to make that call is recorded above: the commit, the node
> count, the edge count, the types, and both authored values.

## Mutation proof

| mutation | result |
|---|---|
| remove `_condition`'s numeric branch | **1 failed** — the behavioural test goes red |
| neutralize the `move` executor | **1 failed** — same |

Both restored; nothing mutated was committed.

## Results

| | |
|---|---|
| Player `+1.0` | `x = +110.0` |
| Player `-1.0` | `x = -110.0` |
| Player `0.0` | no movement, `move` not executed |
| Player graph phantom | **0** |
| Player graph orphan | **0** |
| manual playtest (items 14E/15) | **PASS** |
| orphan edges / phantom ids / instances | 50 / 29 / 57 — unchanged |
| Assets modified | **0** |

`FIXED`: the two repointed tests were among the 124 baseline failures and are
now green.

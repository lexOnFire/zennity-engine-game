# PHASE 9 Recovery — Item 8: `set_variable` ownership and contract

Branch: `integration/phase9-recovery`
Base: `fca53da`

---

## 1. Every split at once

One node carried all of them:

| | |
|---|---|
| definitions | 1 real (`misc_nodes`) |
| executors | **2** (`misc_nodes`, `scene_nodes`) — winner by load order |
| effective contract | `_EXPLICIT_PORT_CONTRACTS` overriding the declaration |
| runtime returns | `["done", "next"]` — `done` undeclared |
| asset node ids | **3** spellings, one of which resolved nowhere |

## 2. The item's premise was too small

The brief said "approximately 10 instances". There are **24, across 17 shipping
assets**, under three ids: `set_variable` (10), `variable.set` (10),
`variables.set` (4).

Output ports used by assets: `next` **12**, `done` **0**, `exec_done` **0**.
Inputs: `in` 14 flow, `value` 7 data.

## 3. The silent one

`variable.set` — 10 nodes across 8 shipping assets — had **no alias, no
contract and no executor**. It sits in `LEGACY_NODE_TYPES`, and `all_aliases()`
merges that table, so diagnostics reported it as a known alias. But
`resolve_node_id`, which the normalizer actually calls, reads only
`NODE_ID_ALIASES`.

So the graph loaded, `_execute` found no executor, fell through to its default
`return ["next"]` — and the flow continued while **the variable was never
written**. It failed silently, in `BossAILogic`, `BossCombatLogic`,
`BossHealthLogic`, `CoinCollectionLogic`, `DoorLogic`, `EnemyAILogic`,
`GuardInteractionLogic` and `KeyCollectionLogic`.

One line fixed it. The reason it needed confirming first is that it changes what
8 shipping graphs do — but as the user put it, those assets already express the
intent by using a node called `variable.set`; they were inert from a resolution
defect, not a design choice.

## 4. Not a semantic split — measured, not assumed

Two executors could have meant two behaviours. They do not. Running both against
the same node:

| | `misc_nodes` | `scene_nodes` (winner) |
|---|---|---|
| blackboard write | `hp = 42.0` | `hp = 42.0` |
| `game.set_variable` hook | — | `hp = 42` |
| returns | `["next"]` | `["done", "next"]` |

`scene_nodes` is a strict superset, and the host hook is pinned by an existing
public-contract test (`test_set_variable_uses_the_authored_name`). Picking the
other body would have dropped it. `done` is not a second event: undeclared, in
no asset, asserted by no test.

## 5. What the override was really carrying

Removing `_EXPLICIT_PORT_CONTRACTS["set_variable"]` broke a shipping asset:
`EnergyCell.zlogic` feeds a number into `value`, and the declaration typed that
pin `STRING` while the override said `any`.

The override was not redundant — it was carrying a truth **the declaration could
not express**, because `PinType` had no member for "accepts anything". So the
fix was to give the vocabulary the missing word (`PinType.ANY`) rather than keep
two sources of truth. A variable's value genuinely is any type; the type system
simply could not say so.

The regenerated contract is byte-identical to what the override provided, except
the input pin is now spelled `exec` instead of `in` — the declarative spelling,
which the contract-relative normalizer resolves for the 14 asset edges.

## 6. Surfaced, not decided

Removing the duplicate executor made a latent divergence visible: the
`misc_nodes` fallback for `name` was `"value"` and matched the declared default,
which had been masking the `scene_nodes` fallbacks (`name` `""`, `value` `0`).

Both entered `property_default_mismatch_baseline.json` (63 → 65) with that
reason. They are the same class the baseline exists for and defers by design:
writing a variable literally called `value`, or writing `""` where the executor
writes `0`, are behaviour decisions. Latent as ever — the catalogue seeds both
properties on creation, so the fallbacks only apply to a graph omitting them.

## 7. The counters closed

| | before | after |
|---|---|---|
| definitions / owners | 1 / 1 | 1 / 1 |
| executors | **2** | **1** |
| effective contract sources | **2** | **1** |
| undeclared runtime outputs | `done` | **none** |
| known duplicate debt | `executor:set_variable` | **removed** |
| executor output contract debt | **1** | **0** |
| node ids resolving nowhere | `variable.set` | **none** |

`executor_port_mismatch_baseline.json` is now empty and deliberately kept: the
gate fails on a new entry, on a fixed entry left behind, and on changed ports,
so an empty file is the strongest statement — enforced by the same check that
carried the debt down from 45.

## 8. Results

| | |
|---|---|
| new tests | 28 |
| recovery items 1–7 | still green |
| `tests/logic` | identical failure set |
| `audit --ci` | exit 0 |
| orphan edges | 71 → 71, per-asset sets unchanged |
| assets touched | **0** |

Untouched as instructed: `move.speed`, `move_by`, `find_nearest_object`,
`get_object_name`, the 71 orphan edges, and the broader unification of the two
alias tables — recorded, deliberately not attempted here.

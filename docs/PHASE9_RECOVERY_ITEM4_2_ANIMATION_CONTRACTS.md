# PHASE 9 Recovery — Item 4.2: animation contract reconciliation

Branch: `integration/phase9-recovery`
Base: `c14a4dd`

---

## 1. What was wrong

`play_animation` and `stop_animation` were each declared twice — in
`actions_nodes` and in `animation_nodes` — with different pins, and each had two
executors. Measured on a real shipping asset before any change:

```
saved node properties after normalize: {'state': 'PlayerAttack',
                                        'animation_name': 'idle', ...}
executor that wins:  engine.logic.runtime.nodes.animation_nodes
returned ports:      ['failure']
declared outputs:    [('next', 'flow')]
```

Three failures in a row: the author saved `state='PlayerAttack'`, normalization
seeded `animation_name='idle'` from the *losing* declaration's default, the
winning executor read `animation_name` and ignored the author entirely — then
returned `failure`, a port the resolved contract did not declare, so the flow
after the node stopped dead.

`play_animation` did not work in shipping content. That is not the `in`/`exec`
port question; it is the split brain.

## 2. The resolution

`animation_nodes` owns both nodes. It resolves the real `Animator` component
through `target` and has a failure path; what `actions_nodes` held was a thinner
parallel implementation (`game.animator.play(state)`) that assumed the game
object *was* the animator. Definitions and executors were removed from
`actions_nodes`.

| | before | after |
|---|---|---|
| duplicate conflicts | 2 | **0** |
| `KNOWN_DUPLICATE_DEFINITIONS` | 2 | **empty** |
| `play_animation` owner | `actions_nodes` (first claimant) | `animation_nodes` |
| `stop_animation` owner | `actions_nodes` | `animation_nodes` |

### Canonical contracts

| node | inputs | outputs |
|---|---|---|
| `play_animation` | `exec`, `target`, `state`, `force` | `next`, `exec_failure`, `animation` |
| `stop_animation` | `exec`, `target` | `next`, `exec_failure`, `stopped` |

The executors were aligned to them: they returned `success`/`failure`, which the
contract never declared. `stopped` and `animation` were already being stored by
the runtime and simply had no declared pin.

### Stale overrides removed

`_EXPLICIT_PORT_CONTRACTS` held `in`/`state` → `next` for `play_animation` and
`in` → `next` for `stop_animation`. Those entries were deleted rather than
rewritten: the declaration in `animation_nodes` is the source of truth, and
copying the correct contract into a second table is the failure this phase keeps
undoing.

## 3. `state` is the authoring property

Recounted on this branch: 4 saved `play_animation` nodes, all using `state`
(`Idle`, `Jump`, `Run`, `PlayerAttack`), **0** using `animation_name`.

`animation_name` is now load-time compatibility only, migrated by
`_RENAMED_NODE_PROPERTIES` — the mechanism `log_message` already used — not a
second authorable field. The executor keeps reading it defensively for a graph
that reaches the runtime without passing the normalizer, and that read is
recorded in `LEGACY_PROPERTY_FALLBACKS` so it is not mistaken for a missing
Inspector field.

**The historical default bug is pinned by a test.** The `state` pin's default is
deliberately empty: it used to be `"idle"`, and normalization seeded that over a
legacy graph's real animation name. A legacy graph with
`animation_name='Run'` now normalizes to `state='Run'` — not `''`, not
`'Idle'`, and `animation_name` does not survive to shadow it.

## 4. Runtime roundtrip

Driven through the real executor and a real `Animator`:

| | result |
|---|---|
| `state='Run'`, valid target | animator plays `Run`, returns `next` |
| legacy `animation_name='Run'` | animator plays `Run`, returns `next` |
| `force=True` | passed through to `animator.play` |
| missing animator | `exec_failure`, nothing played |
| unknown clip | `exec_failure` |
| empty `state` | `exec_failure` |
| `stop_animation`, valid target | animator stops, returns `next` |
| `stop_animation`, missing animator | `exec_failure` |

## 5. Expected blocker — recovery item 5

The canonical entry pin is `exec`; the four saved edges name it `in`:

```
PlayerCombatLogic.zlogic            play_animation.in   1
Assets/Logic/ZennityRun/PlayerMovement.zlogic   play_animation.in   3
```

Orphan edges: **72 → 76**. Those four are the entire delta, and they are the
`in` → `exec` incompatibility that **port normalization** resolves. The contract
is correct and no asset was edited. There are no edges *out* of
`play_animation` in any asset, so changing the output ports broke nothing.

**Status: contracts complete, blocked only by port normalization.**

## 6. A fixture keying bug found on the way

`orphan_edge_baseline.json` was keyed by file name, and three different assets
are called `PlayerMovement.zlogic`. All three read the same recorded list —
harmless while all three had zero orphans, wrong the moment one differed. Keys
are repo-relative paths from here on, and the test ids match.

## 7. Baselines regenerated, with reasons

| fixture | change |
|---|---|
| `stage2/registration_baseline.json` | `play_animation` / `stop_animation` port schema — held the stale explicit snapshot that was just removed |
| `stage2/orphan_edge_baseline.json` | +4 `play_animation.in`, rekeyed by path |
| `stage4/property_default_mismatch_baseline.json` | `play_animation.animation_name` and `.state` left it because the mismatch is **fixed**, not relaxed |

## 8. Results

| | |
|---|---|
| `tests/logic` | 10 before, 10 after — 0 new |
| new tests | 31 |
| items 1, 2, 3, 4.1 | 131 tests, still green |
| `audit --ci` | exit 0, duplicate definitions 0 |
| assets touched | 0 |

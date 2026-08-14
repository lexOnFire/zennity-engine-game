# PHASE 9 — Recovery Item 14E: AI chase asset reauthoring

Base: `4abc267e` · Assets modified: `Assets/Logic/BossAILogic.zlogic`, `Assets/Logic/EnemyAILogic.zlogic` — **and no others**.

Item 14D.2 proved a full 2D chase runs on nodes the engine already has. This item
applies that chain to the two shipping AI graphs. It does not redesign the AI, does
not add nodes to the palette, does not introduce a vector API, and does not
implement `move_by.velocity`.

## What was actually wrong

The graphs are legacy `zennity.generic_graph` documents; what earlier items
inventoried was the *migrated* output. Three defects stacked:

1. **Phantom nodes.** `math.distance`, `vector2` and `normalize_vector` — the
   engine has none of them, and the migration map leaves them untranslated.
2. **Phantom pins.** Positions were read through `get_position.object` /
   `.position`, and comparisons made through `if_else.value` / `.compare_value`.
   `get_position` declares `target` → `x`, `y`; `if_else` declares only
   `condition`. Nine distinct orphan kinds per asset.
3. **No flow reached the chase at all.** No edge entered any branch node.
   `frame_loop` reached only `find_player` and the position nodes, so
   `calc_direction` → `normalize` → `set_velocity` never executed. There was no
   prior behaviour to preserve — the chase had never run.

A fourth fact shaped the design: neither object carries a RigidBody in any scene,
so `move_by` takes the `target.move(dx, dy)` path. `move_by(0, 0)` therefore moves
nothing **and cancels nothing** — a "stop" wired in parallel with the chase is a
no-op.

## The chain that replaced it

```
dx = player.x - self.x                    subtract_number
dy = player.y - self.y                    subtract_number
distance = distance_to_point(self.x, self.y, player.x, player.y)
if distance > threshold:                  subtract_number -> compare_number
  if distance > 0:                        compare_number   (the division guard)
    move_by.x = (dx / distance) * move_speed
    move_by.y = (dy / distance) * move_speed
```

Two shapes carry the design:

- **Self** is "no `target` edge". `_read_target` falls back to
  `_implicit_target or game`, and the host passes a per-object API as `game`.
- **Dynamic thresholds.** `compare_number` takes its right operand from a
  property, so it cannot see `detection_range`. Subtracting first and comparing
  the remainder against zero says the same thing with existing nodes.

The `distance > 0` guard sits on the **flow**, not on a value: `divide_number`
raises on a zero divisor, so gating the branch means the normalization nodes are
never evaluated when the AI stands on the player.

## Decisions taken (both confirmed with the author)

| Question | Decision |
|---|---|
| Stop wired in parallel with chase (a no-op) | **Exclusive**: `check_*_attack_range.true` → stop, `.false` → chase. The only arrangement where the stop has an effect. |
| Boss `check_phase2`: `compare_value: 250` vs the `max_health` edge | **Honour the edge** (`health ≤ max_health`). The authored data edges are the structural source; no invented number. |

## Boss — before / after

| | before | after |
|---|---|---|
| nodes | 21 | 28 |
| edges | 23 | 42 |
| phantom instances | 4 | **1** |
| orphan kinds | 9 | **0** |
| unresolved edges | 16 / 23 | **1 / 42** |

**Removed:** `calc_direction` (`vector2`), `normalize_dir` (`normalize_vector`).
**Retyped in place, keeping id, position and config:** `calc_distance` →
`distance_to_point`; `check_detected`, `check_attack_range`, `check_phase2` →
`compare_number` (`condition: "less_equal"` → `operator: "<="`, since `_compare`
only accepts symbolic operators and `"less_equal"` silently returned `False`).
**Added:** `margin_detection`, `margin_attack`, `margin_phase`, `chase_guard`,
`boss_dx`, `boss_dy`, `boss_nx`, `boss_ny`, `boss_vy`. `apply_speed` kept its id
and became the x component.
**Preserved:** all `get_variable` configs, the phase branch, `stop_boss`,
`set_speed_param`, every node id and position outside the chase.

## Enemy — before / after

| | before | after |
|---|---|---|
| nodes | 24 | 31 |
| edges | 25 | 45 |
| phantom instances | 8 | **5** |
| orphan kinds | 9 | **0** |
| unresolved edges | 20 / 25 | **5 / 45** |

Same transformation, adapted rather than copied: no phase logic, and the
attack-cooldown branch is preserved and given the flow edges it never had
(`get_attack_cooldown` → `get_cooldown_timer` → `check_can_attack`, which had no
incoming flow either). `check_can_attack` compares the other way round
(`cooldown_timer ≥ attack_cooldown`), so its margin is `>= 0`.

## Runtime measurements

Harness mirrors `PlayLogicAPI` (the per-object API), with scene variables.

| | Boss (speed 80, detect 500, attack 72) | Enemy (speed 100, detect 300, attack 48) |
|---|---|---|
| 8 directions, cosine to player | **1.000000 in all 8** | **1.000000 in all 8** |
| distance before → after (1 frame) | 400.00 → 398.67 | 200.00 → 198.33 |
| step vs authored speed | 1.333 = 80/60 | 1.667 = 100/60 |
| undetected player | does not move | does not move |
| inside attack range | does not move | does not move |
| standing on player | no move, no NaN/inf, no divide | same |
| speed 0 | does not move | same |
| 600 frames | monotonic, settles at 70.67 (≤ 72) | monotonic, settles at 46.67 (≤ 48) |

## Global delta

| metric | before | after |
|---|---|---|
| phantom ids | 32 | **29** |
| phantom instances | 63 | **57** |
| orphan edges (distinct kinds) | 68 | **50** |
| new orphans | — | **0** |

`math.distance`, `vector2` and `normalize_vector` existed only in these two
assets, so all three ids disappear entirely.

## Animation debt — unchanged, and not pretended otherwise

**Before:** `set_animator_parameter` (Boss ×1, Enemy ×3), `animator.set_trigger`
(Enemy ×1), `variable.increment` (Enemy ×1) — all phantom, none implemented.
**After:** identical. Every animation edge was preserved verbatim, including
`check_detected.false → idle_state` and `check_detected.true → set_speed_parameter`.
**Remaining:** the same 6 instances. Animation still does nothing. Item 14E
proved only that it does not block movement.

`run_state` (Enemy) remains unconnected, exactly as authored.

### The debt is not visual-only, and the Boss playtest is what showed it

Item 16A classified this debt ANIMATION/VISUAL ONLY on the evidence that the
chase works without it. That holds for movement and is wrong in general.

The author played the Boss and could not tell whether the attacks were
happening. They were right not to guess: **there is nothing to observe.** The
attack branch runs five nodes and three of them are phantom.

| node | type | effect |
|---|---|---|
| `set_normal_attack` | `animator.set_trigger` | **nothing** |
| `set_heavy_attack` | `animator.set_trigger` | **nothing** |
| `increment_count` | `variable.increment` | **nothing** |
| `reset_count` | `set_variable` | works |
| `reset_timer` | `set_variable` | works |

The consequence goes past appearance. `increment_count` never runs, so
`attack_count` never increases, so `check_heavy` (`attack_count == 3`) can never
be true: **the heavy attack is unreachable**. Not because of item 16B -- its
comparison is correct -- but because the counter feeding it does not exist.

So `variable.increment` breaks *state logic*, not just visuals, and belongs in a
different bucket from `set_animator_parameter` and `animator.set_trigger`.
Whoever takes the animation item should reclassify it rather than inherit the
16A label.

## Remaining phantom ids in these two assets

| id | why it remains | scope |
|---|---|---|
| `set_animator_parameter` | animation not implemented | out (declared debt) |
| `animator.set_trigger` | animation not implemented | out (declared debt) |
| `variable.increment` | no canonical increment node; cooldown logic | out |

## Manual acceptance — Enemy PASSED, Boss PASSED

Played by the author in `Level1.zscene`. Result, in their words: the enemies
follow when they see the player, stop following once the player leaves the
detection field, stop on reaching the player, and do not push or jitter.

| step | result |
|---|---|
| starts moving inside `detection_range` (300) | **PASS** |
| moves towards the player | **PASS** |
| stops once outside detection | **PASS** |
| stops inside `attack_range` (48) | **PASS** |
| no pushing, no jitter at the boundary | **PASS** |

The last row was the open risk. The automated test only proves the chase settles
at 46.67 against a 48 limit; whether a step of 1.67 px looks like a stable stop
or a one-frame tremor is not something a test can answer. It stops cleanly.

Worth recording plainly: this chase had **never run**. No flow edge reached any
branch node, and the chain went through three node types the engine does not
have. This playtest is the first time it executed at all.

### Boss, played later

Confirmed by the author after item 16B: the Boss chases, stops on reaching the
player, and does not push. Same three behaviours as the Enemy, at its own
thresholds (speed 80, detection 500, attack 72).

What could **not** be observed is the attack rhythm, and that turned out not to
be a gap in the testing -- see the animation debt section above. The
comparisons item 16B reauthored fire correctly, proven against the real asset
including boundaries; what they trigger is not implemented.

Still unconfirmed: **Stop → Play** repeat from a clean state.

Expect **no animation change**: enemies chase without a run/idle transition.
That is the declared debt above, not a regression from this item.

Player movement is a separate matter and was broken for an unrelated reason —
see item 15, which restored it after this item shipped.

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

## Remaining phantom ids in these two assets

| id | why it remains | scope |
|---|---|---|
| `set_animator_parameter` | animation not implemented | out (declared debt) |
| `animator.set_trigger` | animation not implemented | out (declared debt) |
| `variable.increment` | no canonical increment node; cooldown logic | out |

## Manual acceptance — required

Automated status is complete; gameplay is not signed off. Steps:

1. Open `Assets/Scenes/Level1.zscene` (three Enemies).
2. Press Play.
3. Walk the Player towards an Enemy until inside `detection_range` (300).
4. Confirm it starts moving and moves **towards** the Player.
5. Walk away — confirm it follows, and stops once outside detection.
6. Approach until inside `attack_range` (48) — confirm it stops.
7. Confirm it does not push through or jitter on the Player.
8. Confirm the speed looks like ~100 px/s.
9. Open `Assets/Scenes/Level2.zscene` and repeat for the Boss (speed 80,
   detection 500, attack 72).
10. Stop, then Play again — confirm behaviour repeats from a clean state.

Expect **no animation change**: enemies will chase without a run/idle
transition. That is the declared debt above, not a regression from this item.

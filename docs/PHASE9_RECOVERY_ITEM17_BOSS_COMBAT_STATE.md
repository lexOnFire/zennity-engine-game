# PHASE 9 — Recovery Item 17: boss combat state progression

Base: `0e0fb6c1` · Boss assets modified: **3** · Phantom ids: 27 → 26 · Phantom instances: 53 → 47

## The premise was right about the classification and wrong about the cause

Item 16A filed the boss debt as *animation/visual only*. Item 14E had already
contradicted that, and this item started from the correction: `variable.increment`
is the node that writes `attack_count`, so a phantom there stops **state**.

Measurement then moved the counter from first place to fourth. Driving
`BossCombatLogic` through a runtime harness executed **two of its eighteen nodes**:

```
frame_loop -> get_cooldown_timer -> (nothing)
```

The edge leaving `get_cooldown_timer` left the node's *data* port (`value`) and
arrived at a flow port, and `_follow` only walks `next`. Everything downstream —
the cooldown check, both branches, both animator triggers, the counter, the timer
reset — was unreachable. `increment_count` was never even reached, so it could not
be the reason `attack_count` stayed at zero.

`BossHealthLogic` had the same shape. `check_dead` received health on a data edge
and no flow edge ever reached it, so **the boss could not die**, and
`update_boss_hud` never ran either, so its health bar never moved.

Four defects, each hiding the next:

| # | defect | effect |
|---|---|---|
| 1 | flow chain stopped two nodes in, in both graphs | nothing after node 2 ran |
| 2 | `cooldown_timer` authored as a countdown, compared as a count-up | one attack, ever |
| 3 | `variable.increment` and `animator.set_trigger` phantom | counter frozen, no animation |
| 4 | phase 2 compared `health <= max_health` | phase 2 at full health, on tick 1 |

## Gate A — classification

| node / debt | assets | status before | historical evidence | gameplay impact | class | canonical replacement |
|---|---|---|---|---|---|---|
| flow chain break | BossCombat, BossHealth | 2/18 and 3/12 nodes reachable | authoring error, no history to recover | **total**: no attack, no death | **A — state logic blocker** | rewire `next → in` |
| `variable.increment` | BossCombat ×2, EnemyAI ×1 | phantom | **D — never implemented**: no commit in the whole history defines a node with `increment` in its id | counter frozen | **A — state logic blocker** | `get_variable → add_number / subtract_number → set_variable` |
| `animator.set_trigger` | BossCombat ×2, BossHealth ×1, EnemyAI ×1 | phantom | **B — alias gap**: `animator_set_trigger` has a definition *and* an executor, both predating this item; only the `LEGACY_NODE_TYPES` entry was missing | **D — animation/state coupling** (see below) | `animator_set_trigger`, one map line |
| `set_animator_parameter` | BossAI ×1, EnemyAI ×3 | phantom | **F — authoring error in the map itself**: `animator.set_parameter` is mapped to `set_animator_parameter`, an id that **does not exist** in `NODE_DEFINITIONS`. The canonical node is `animator_parameter`, with a different property set (`parameter_name` / `parameter_type` / `value`) that the assets do not supply | **C — visual only** | not taken: remapping would produce a node that fails at runtime for want of properties. Still debt. |

**ATTACK_COUNT ROOT CAUSE** — the counter node was unreachable; the phantom was
downstream of a flow break. Both had to be fixed, in that order.
**HEAVY_ATTACK ROOT CAUSE** — same break, plus a threshold hardcoded as `== 3`
while the scene declared `heavy_attack_interval: 3` and was ignored.
**PHASE2 BLOCKED?** — no: it fired *always*, which is worse than never.
**DEATH BLOCKED?** — yes, completely: `check_dead` was unreachable.
**ANIMATION BLOCKED?** — yes, and it was coupled to state; see below.

## The coupling that decided the layout

`animator_set_trigger` returns `exec_failure` when the object has no
`AnimationController`, and a failed flow port continues nothing. The asset had
both triggers *in the middle* of the chain:

```
check_heavy --false--> set_normal_attack --> increment_count --> reset_timer
```

Mapping the alias without moving anything would have made the boss's counter and
cooldown depend on its animator existing. So state is written first and the
trigger is a leaf:

```
check_heavy --false--> increment_count --> set_normal_attack
check_heavy --true --> reset_count     --> set_heavy_attack
```

`test_the_counter_still_advances_without_an_animator` holds that line.

## Decisions taken, and by whom

Four readings were genuinely ambiguous and were put to the author rather than
guessed:

1. **Cooldown = countdown.** Level2 seeds `cooldown_timer` at 1.5, the same value
   as `attack_cooldown` — what a countdown looks like at rest. `decrease_timer`
   decrements and `clamp_timer` clamps at 0. Against that, the check compared
   `timer - cooldown >= 0` and the reset wrote 0, which is count-up. Under
   count-up the boss attacked once and never again, because the reset moved the
   timer *away* from the threshold. The check is now `timer <= 0` and the reset
   writes `attack_cooldown`.
2. **Threshold from the scene.** `heavy_attack_interval` was declared and ignored.
   `compare_number` takes its right operand from a property, so a wired threshold
   needs the margin trick: subtract, compare the remainder against zero.
3. **Animator connected, flow decoupled** — above.
4. **Phase 2 trigger fixed, phase 2 *effect* left as debt.** `phase2_threshold: 0.5`
   is now honoured, so phase 2 begins at half health instead of immediately. What
   phase 2 *does* is still nothing: `get_phase2_cooldown` and `calc_phase2_cooldown`
   carry no edges at all, and `check_phase2` branches to nothing. Wiring an effect
   is design, not recovery, so it stays recorded.

## Off-by-one worth naming

With interval 3 and the comparison on the *stored* count, the sequence runs
0→1→2→3 and the heavy attack lands on the **fourth** attack. The comparison is on
`attack_count + 1` — the ordinal of the attack about to happen — so it lands on the
third. `>=` rather than `==`, so a count that somehow overshoots still fires
instead of locking the heavy attack out for the rest of the fight.

## What this item did *not* fix

**The boss deals no damage, and cannot.** No boss graph contains a
damage-dealing node, and the engine has **no node of any kind** whose id mentions
damage — the whole "attack" is an animator trigger. `attack_damage: 20` and
`heavy_attack_damage: 35` sit in Level2 unread by anything. Restoring the counter
restores a working state machine that selects between two animations; it does not
make the boss hurt the player. That needs a damage node, which is new design.

Also still open, all recorded rather than fixed: `set_animator_parameter`'s broken
map target; `component.set_property` and `scene.load` in `BossHealthLogic`
(so death disables no collider and loads no victory scene); `variable.increment`'s
last instance in `EnemyAILogic`; and phase 2's missing effect.

## Results

| | before | after |
|---|---|---|
| BossCombatLogic nodes reached per tick | 2 of 18 | 8–10 of 21 |
| BossHealthLogic `check_dead` reachable | no | yes |
| `attack_count` after 20 attacks | 0 | cycles 1,2,0 |
| heavy attack reachable | **never** | every 3rd attack |
| phase 2 at full health | **yes** | no — at ≤ 50% |
| boss can die | **no** | yes, at health ≤ 0 |
| phantom ids / instances | 27 / 53 | 26 / 47 |
| orphan edges in the three boss graphs | 0 | 0 |

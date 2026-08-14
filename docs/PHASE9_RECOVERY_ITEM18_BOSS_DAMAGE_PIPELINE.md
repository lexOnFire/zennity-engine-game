# PHASE 9 — Recovery Item 18: boss damage pipeline

Base: `3dcacfb4` · New nodes created: **0** · Assets modified: **3** · Phantom instances: 47 → 46

Item 17 left the boss with a working state machine that hit nothing.
`attack_damage: 20` and `heavy_attack_damage: 35` sat in `Level2.zscene` with no
reader, and no boss graph applied damage to anything.

The item deliberately did not start by proposing a `damage` node. It started by
asking how this project already represents a change of health.

## Gate A

| question | answer |
|---|---|
| **PLAYER HEALTH SOURCE OF TRUTH** | the shared `BlackboardStore`, object scope, key `Player`. The viewport builds **one** store and passes it to every runtime, so `object_values["Player"]["health"]` is visible to the whole scene. |
| **CURRENT HEALTH WRITE PATH** | none. Nothing wrote it. |
| **BOSS TARGET AVAILABLE** | not in `BossCombatLogic` — it had no target node and no range check at all; the attack fired on cooldown alone, at any distance. |
| **NORMAL / HEAVY DAMAGE VALUE** | 20 / 35, authored in Level2, confirmed on the current tree. |
| **EXISTING NODES CAN EXPRESS DAMAGE** | **yes** — see below. |
| **HISTORICAL DAMAGE IMPLEMENTATION** | no. |
| **ENEMY DAMAGE CURRENTLY WORKS** | **no.** `EnemyAttackLogic` executes **zero** nodes: its only event is `animation.on_event`, phantom, so nothing ever starts it. |
| **NEW NODE REQUIRED** | **no.** |
| **ROOT CAUSE** | **B — LOST ASSET WIRING**, twice over, not a missing runtime. |

### Two authored damage designs, one of them unrunnable

`EnemyAttackLogic` spells out the intended pipeline in full — raycast, hit test,
read health, subtract, clamp, write back — using `object.get_variable` and
`object.set_variable` for the cross-object access. A search across **every commit
in the repository** found no Python definition for either id, ever. That route
was never runnable, and building it would be new design, not recovery.

`PlayerHealthLogic` used `event.custom` for its death signal, so custom events
were this project's cross-object channel from the start. `emit_event` and
`event_custom` both exist, both have executors, `graph_validator` already
requires a `name` on both, and the `LogicEventBus` is shared across every object
in the scene — the same way the blackboard is.

So the damage was expressible today:

```
Boss:   ... -> emit_event(name="player_damage", payload=attack_damage)
Player: event_custom("player_damage") -> get_variable(health)
        -> subtract_number -> clamp_number -> set_variable(health)
```

The player mutates its own health. No node writes another object's state, and
health keeps exactly one source of truth.

## PlayerHealthLogic had to be authored, not merely wired

It shipped with **8 nodes and 0 edges**, every `properties` block empty — so even
the variable names were gone. `4ed6c6cd` (*"100% visual state management"*)
stripped the wiring that `0d2ba5f8` had; both are ancestors of this branch. It
was also **absent from the Player in Level2**, so a correct graph would never
have loaded.

Restoring `0d2ba5f8` verbatim would not have been enough: its flow chain had the
same defect item 17 found in `BossHealthLogic` — `frame_loop` fanning out to two
`get_variable` nodes with nothing reaching `check_dead`. The graph was authored
with that corrected, plus the damage receiver.

## Targeting: the guard that was missing, and the one that was nearly missing

`BossCombatLogic` gained the scalar range chain `BossAILogic` already uses:
`find_tag → get_position → distance_to_point → subtract_number(attack_range) →
compare_number`.

The first version of that guard had a hole worth recording. `find_tag` has no
failure port, and `get_position` on a null target falls back to the boss's own
position — so with no player in the scene the distance collapses to **0**, which
`distance <= attack_range` happily accepts. `BossAILogic` had already solved this
with its `chase_guard` (`distance > 0`), and the combat graph now carries the
same guard rather than a new node. `test_the_target_guard_is_what_makes_that_true`
mutates the operator to prove the guard is load-bearing.

## Ordering

State first, damage second, animation last — extending item 17's rule. The
animator triggers stay leaves, so a boss with no `AnimationController` still
counts its attacks *and* still deals damage.

```
check_heavy --false--> increment_count --> emit_normal_damage --> set_normal_attack
check_heavy --true --> reset_count     --> emit_heavy_damage  --> set_heavy_attack
```

## Dispatch is not automatic

`LogicEventBus.emit` only queues. The viewport calls `dispatch()` after **every**
`runtime.update`, and the test harness does the same, in the same order — a
harness that dispatched differently would prove nothing about the game. This is
the one detail that made the first end-to-end measurement read as a total
failure when the graphs were already correct.

## Results

| | before | after |
|---|---|---|
| normal attack | no effect | −20 |
| heavy attack | no effect | −35, every 3rd attack |
| out of attack_range | attacked anyway | no damage |
| at exactly `attack_range` | — | hit lands (`<= 0` margin, inclusive) |
| no player in scene | attacked the origin | no attack |
| damage per attack | — | exactly one, 95 frames apart |
| health floor | — | clamped at 0 |
| player death branch | unreachable | reached at health ≤ 0 |
| HUD | never updated | follows the same health |
| `PlayerHealthLogic` edges | **0** | 16 |
| new nodes created | — | **0** |

## Still open

- **`EnemyAttackLogic` cannot reuse this yet.** Its blocker is upstream of
  damage: `animation.on_event` is phantom, so the graph never starts, and its
  `set_player_health` has no incoming flow edge either. Once it has a working
  trigger, the same `emit_event` → `event_custom` pipeline serves it unchanged —
  the player-side receiver is already generic.
- `component.set_property` and `scene.load` in `BossHealthLogic`: the boss dies
  but keeps its collider, and the victory scene does not load.
- `variable.increment` in `EnemyAILogic`.
- `set_animator_parameter`'s alias target still does not exist.
- The phase-2 effect is still wired to nothing.

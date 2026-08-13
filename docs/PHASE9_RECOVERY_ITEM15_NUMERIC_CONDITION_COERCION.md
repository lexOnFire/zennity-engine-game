# PHASE 9 — Recovery Item 15: numeric condition coercion

Base: `4c984b8f` · **Assets modified: 0** · Classification: **A — NUMERIC COERCION BUG**

`LogicGraphRuntime._condition` now decides numbers by their value. Two lines,
placed after the `bool` branch and before anything becomes text.

## The bug

`_condition` had no numeric branch at all. A number fell through to a string
path built for literals (`true`/`verdadeiro`), tokens (`axis != 0`) and variable
names, ending at `variables.get(str(value), False)`.

Measured before the fix:

| value | type | result | why |
|---|---|---|---|
| `1` | int | True | `str(1)` == `"1"`, a recognized literal — **by accident** |
| `0` | int | False | same accident |
| `2` | int | **False** | `"2"` is not a literal, not a variable |
| `-1` | int | **False** | same |
| `1.0` | float | **False** | `str(1.0)` == `"1.0"` |
| `-1.0`, `0.5`, `-0.5` | float | **False** | same |
| `0.0` | float | False | correct, also by accident |

So only the literals `1` and `0` worked, and only because of how they print.

## The consequence

`PlayerMovementLogic.zlogic` is `event_update → if_else → move`, with
`input_axis.value` feeding `if_else.condition`. `input_axis` returns
`float(game.axis(...))` — always `1.0`, never `1`. The condition read as the
variable named `"1.0"`, found nothing, and took the false branch **in every
direction**. `move` never executed; the player never moved.

An analog stick could never have worked either, which is the whole reason the
axis is a float.

This predates recovery items 14E and 14F: verified identical at `66f46056`.

## Scope, measured before touching anything

| | |
|---|---|
| `_condition` callers | **2**, both `if_else` (executor + evaluator) |
| other `condition` pins | `add_transition.condition` — a string (`"always"`/`"on_key"`), never routed through `_condition` |
| conditions fed by an edge, all shipping assets | **1** — `PlayerMovementLogic`, `input_axis.value` (number) |
| conditions from properties | **19** — 6 `bool:False`, 13 strings. **None numeric** |
| variables with a numeric name | **none** |

## The fix

```python
if isinstance(value, bool):      # already there: bool is an int subclass
    return value
if isinstance(value, (int, float)):
    return value != 0
text = str(value).strip()...     # unchanged from here down
```

Dispatch is on **type**, not spelling. The *string* `"1.0"` is untouched and
still resolves through the text path, so a variable spelled like a number keeps
its meaning. That distinction is what makes the change safe rather than clever.

`input_axis` was not changed: returning a float is correct (section 14).

## Asset impact audit

Every `if_else` in every shipping asset, old logic vs new:

| | |
|---|---|
| property conditions re-evaluated | 19 |
| **changed** | **0** |
| connected conditions | 1 — `PlayerMovementLogic`, `1.0`: False → **True** |

The only behavioural change in the repository is the intended fix.

## Player movement, after

| axis | condition | `move` ran | x after one frame at 60fps |
|---|---|---|---|
| `+1.0` | True | yes | `+3.667` (= 220/60) |
| `-1.0` | True | yes | `-3.667` |
| `0.0` | False | **no** | `0.0` |
| `+0.5` | True | yes | `+1.833` — half, as an analog stick should |
| `+0.25` | True | yes | `+0.917` |

Direction and magnitude both correct.

## The pre-existing test that is still red

`test_player_movement_demo_executes_move_and_jump_nodes` still fails, and **not
because of this bug**. It exercises a different asset — `PlayerMovement.zlogic`,
not `PlayerMovementLogic.zlogic` — which contains no `if_else` and no jump node
at all: it is `event_update → input_axis → move_by`. With `axis` returning `1`
and `dt=0.5`, `move_by` displaces `0.5`, exactly what the test observes. The
graph is right; the test asserts a shape (`x == 110.0`, `jumps == [440.0]`) that
the asset no longer has.

That is a stale-test problem with its own cause, out of scope here (section 29),
and left untouched.

## Regression results

| | before | after |
|---|---|---|
| orphan edges | 50 | **50** |
| phantom ids | 29 | **29** |
| phantom instances | 57 | **57** |
| `audit --ci` | PASS | **PASS** |
| Assets modified | — | **0** |

`tests/logic`: 10 failures, identical to the `4c984b8f` baseline — 0 new.
Full suite: 124 failed / 4858 passed; failure set identical to baseline
(124 / 4807), **0 new regressions**, +51 passed = the new tests.

Recovery suites for items 14D.1, 14D.2, 14E and 14F: 130 passed. Boss and Enemy
are unaffected by design — item 14E moved them onto `compare_number`, and a test
asserts they contain no `if_else` so a future edit cannot silently make them
depend on this helper again.

Mutation-tested: removing the two numeric lines turns 19 of the 51 tests red.

## Manual playtest — required

**Player**
1. Open a scene with the Player → Play
2. Move right — the player should move right
3. Move left — the player should move left
4. Release — the player should stop
5. If a gamepad is available, push the stick partway: movement should be
   proportionally slower
6. Jump, if the scene's graph has one
7. Stop → Play again

**Enemy / Boss** — confirm the item 14E chase still works. It does not go
through `_condition`, so nothing should differ; worth one pass to be sure.

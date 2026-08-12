# PHASE 9 Recovery — Item 2: canonical node ids, aliases and palette rescue

Branch: `integration/phase9-recovery`
Base: `52e765f`

---

## 1. The evidence

Recounted on this branch rather than taken from the lost integration. Node
occurrences across every shipping `.zlogic`:

| canonical (dotted) | uses | legacy (flat) | uses |
|---|---|---|---|
| `scene.load_scene` | 5 | `load_scene` | 0 |
| `ui.button_clicked` | 5 | `button_clicked` | 0 |
| `app.quit` | 1 | `quit_game` | 0 |
| `ui.set_widget_enabled` | 1 | `set_ui_enabled` | 0 |

Identical to the historical measurement. The dotted spelling is what authors
actually saved, so it owns the definition, the palette entry and the port
contract; the flat spelling is a load-time alias. Renaming ids that assets
already carry buys nothing.

The table used to point the other way — dotted resolving onto flat — which sent
every one of those 12 saved nodes to an id no asset uses.

## 2. One table

`NODE_ID_ALIASES` in `node_definitions/catalogue.py` is the only node-id alias
mapping in the engine, read-only, one-way, legacy → canonical:

```
load_scene      open_scene       -> scene.load_scene
quit_game       exit_game        -> app.quit
button_clicked  on_ui_click      -> ui.button_clicked
set_ui_enabled                   -> ui.set_widget_enabled
variables.set                    -> set_variable
game.load_game                   -> load_game
game.has_save                    -> has_save
```

API: `resolve_node_id`, `get_node_aliases`, `get_aliases_for`,
`validate_node_id_aliases`. `canonical_node_id` and `RUNTIME_ID_ALIASES` remain
as the previous spellings so existing importers keep working.

`validate_node_id_aliases()` rejects self-aliases, chains, cycles and targets
with no definition. No target is also a key, which is what makes one-step
resolution converge; a test pins that property rather than trusting it.

Node-id aliases and **port** aliases stay separate concepts: `load_scene →
scene.load_scene` maps node identity, `in → exec` maps pin names. Conflating
them is how two disagreeing tables appeared the first time.

## 3. Where resolution happens

`graph_normalizer` resolves node ids once, at load. Before this item **nothing
did** — `canonical_node_id` existed but was called only by validation, so a
graph containing `load_scene` stayed `load_scene` all the way into the runtime.
Now everything downstream, and anything saved afterwards, sees only canonical
ids.

## 4. Palette rescue

The four canonical ids had a port contract and an executor but **no definition**
— an author could not place `scene.load_scene` at all, though five graphs use
it. Item 1 parked Stage 1's declarations for exactly these ids in
`ALIASED_DECLARATIVE_DEFINITIONS`; this item consumes them.

Metadata only: title, category, description, and property defaults added with
`setdefault`. **The declaration's pins are deliberately not written.** A
declarative definition carrying no pins was once written straight over the port
schema and turned a working contract into an empty one; the pins keep coming
from the port schema, and a test asserts the contract survived the rescue.

| id | title | inputs | outputs |
|---|---|---|---|
| `scene.load_scene` | Carregar Cena | `in`, `scene_path` | `next`, `success` |
| `ui.button_clicked` | Botão Clicado | `in`, `widget_name` | `next`, `clicked`, `exec` |
| `app.quit` | Sair do Jogo | `in` | — |
| `ui.set_widget_enabled` | Habilitar Widget | `in`, `widget_name`, `enabled` | `next` |

Palette: **171 → 175**, no removals. Aliases visible: **0**, asserted
generically as `visible_ids ∩ alias_ids == ∅`.

`update_ui_widget_property` was already declarative, visible and wired to an
executor — audited and left alone, as the brief asked.

## 5. Three things worth flagging

**`ui.button_clicked` now appears exactly once.** It was added to a shadowed
file historically and never appeared at all; the test pins that only the dotted
spelling is in the palette.

**Two orphan edges appeared in `MainMenuLogic`, and they are not new breakage.**
The asset wires `game.load_game.in` and `game.has_save.next`. Those ids had no
port contract before resolution existed, so `node_port_definitions` fell back to
a generic `in`/`next` pair and the edges appeared to resolve. Resolving them
onto `load_game`/`has_save` revealed that the real contracts declare `exec`,
`exec_loaded` and `exec_exists`. The mismatch was always there; it was hidden by
the node type being unknown. Reconciling the pin names is **port
normalization**, a later item. Recorded in the orphan baseline, 72 → 74, with
no asset edited.

**Two aliases match the pattern that made the scene/UI ids dotted:**

```
variables.set   4 uses   set_variable  10   -> flat canonical, correct as-is
game.load_game  1 use    load_game      0   \_ dotted is the only spelling used
game.has_save   1 use    has_save       0   /
```

By the same rule, `game.load_game` and `game.has_save` should be canonical. They
are outside this item's authorised set, so the direction is **left unchanged and
reported** rather than quietly extended. They keep loading through the alias.

## 6. Save policy

A legacy graph loads, normalizes and saves as canonical dotted ids — proven end
to end in `tmp_path`. No shipping asset changes merely by being opened: a test
reads every `.zlogic`, loads and normalizes it, and asserts the bytes on disk
are untouched.

## 7. Results

| | |
|---|---|
| `tests/logic` | 10 before, 10 after — 0 new, 0 fixed |
| new tests | 40, all passing |
| Item 1's tests | 34, still passing |
| `audit --ci` | exit 0, now including alias checks |
| assets touched | 0 |

The audit's CI gate fails on a dangling alias target, a cycle, or an alias
holding its own definition or port contract.

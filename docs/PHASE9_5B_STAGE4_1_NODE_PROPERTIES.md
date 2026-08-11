# PHASE 9.5B — Stage 4.1: Node Properties & Inspector Authoring

Status: **the reported bug is fixed and guarded; the typed-widget work is not
done.** Do not start Stage 5 from this document.

## The reported symptom, and what it actually was

> "Some nodes appear in the Logic Graph but their properties don't show in the
> Properties panel."

The panel renders what the catalogue declares. An AST sweep of every runtime
executor found the cause: **26 of 154 palette nodes read properties via
`properties.get(key, default)` that the catalogue never declared**, across 50
properties in total. An undeclared property is an invisible one, so those nodes
could only be configured by hand-editing the `.zlogic` JSON.

The worst cases were not obscure:

| node | invisible property | what it controls |
|---|---|---|
| `input_axis` | `negative`, `positive` | the movement keys — probably the most-authored setting in the palette |
| `set_variable` / `get_variable` | `name`, `scope` | which variable the node touches |
| `sequence` | `outputs` | how many output ports the node has |
| `find_tag` | `tag` | which objects it finds |
| `emit_event` | `name` | the event being emitted |
| `set_ui_text` | `widget_name` | which widget it writes to |

## The fix

No Inspector special-casing. The defaults were declared in the Stage 2
catalogue — the single source of truth — so they flow through the existing
pipeline automatically. Each default is the executor's own fallback literal,
read out of its source, so declaring it cannot change behaviour.

Result: **50 invisible properties → 14**, across **26 nodes → 11**.

### Deliberately still undeclared

These are not oversights; declaring them would change behaviour or expose
internals (brief items 17 and 18):

| property | why |
|---|---|
| `object`, `widget` | runtime handles, resolved from `object_name` / `widget_name` |
| `add_component.properties` | nested component payload, not a scalar |
| `call_subgraph.inputs` | dynamic interface, authored through the graph |
| `show_dialog.options` | list of choices with its own UI |
| `get_prefab_parameter.default`, `subgraph_return.default` | type follows the pin |
| `create_ui_*.color`, `bg_color`, `fill_color` | `None` means "inherit theme"; a declared `""` is a different value |
| `update_continuous_motion.acceleration` | `None` means "leave unchanged" |

## Property pipeline — the answer to "what is the source of truth?"

```
declarative NodeDefinition + _EXPLICIT_PROPERTY_DEFAULTS + _RUNTIME_READ_PROPERTY_DEFAULTS
                              ↓
                 NodeDefinitionRegistry  (Stage 2, the one mutable store)
                              ↓
              NODE_DEFINITIONS[type]["properties"]   ← defaults
                              ↓
        node["properties"] in the .zlogic            ← authored state
                              ↓
   properties_mixin._selection_changed  → QTreeWidget rows
                              ↓
        _property_changed → graph model → dirty → save
                              ↓
              executor: properties.get(key, fallback)
```

## Known inconsistency, recorded not fixed

65 properties declare a default that differs from the fallback literal in their
executor (`jump.force` is 500.0 in the catalogue, 420.0 in the executor). This is
**latent, not active**: the catalogue default is written into every node on
creation, so the executor fallback only applies to a legacy asset that omits the
property — and there the editor and the runtime disagree.

Reconciling all 65 would change authoring defaults across the palette, which is a
gameplay change and out of scope. Pinned in
`tests/fixtures/stage4/property_default_mismatch_baseline.json`; the test fails
on new divergence and on silent resolution.

## Not done in this stage

The brief asked for typed editors — enum dropdowns, key pickers, asset browse
buttons, colour wells, vector fields. **None of that was built.** The panel is a
`QTreeWidget` that edits every value as text and infers nothing from a schema;
there is no property-type metadata to drive widgets from, only the Python type of
the default value. Adding a real `PropertyDefinition` schema is the natural next
step and is a substantially larger change than this stage.

Also not done: undo/redo for property edits (item 13 — the gap is recorded, not
closed), and the object-reference picker (item 9).

## Tests

```
tests/editor/test_node_property_panel.py          # 149: golden set + all-node sweep
tests/editor/test_node_property_roundtrip.py      # save/close/reopen per type
tests/editor/test_node_property_dirty_state.py    # opening is clean, editing is dirty
tests/logic/test_node_property_runtime_contract.py  # the executor reads the authored value
tests/logic/test_node_property_schema_validation.py # no undeclared property, no new mismatch
```

The sweep in `test_selecting_any_node_builds_its_panel_without_crashing` covers
every node with properties, so this whole class of bug fails a test rather than
reaching a user.

## Manual validation still required

Open the Logic Graph Editor and select an Input, Animation, Physics, UI and
Scene node. Confirm the properties appear, are editable, and survive
save/reopen. In particular check that `input_axis` now offers its key bindings.

# PHASE 9 Recovery — Item 7: executor output contract integrity

Branch: `integration/phase9-recovery`
Base: `81ef7d6`

---

## 1. The number was real, but it was not 45 bugs

Item 6 recorded 45 executors returning a flow port their contract does not
declare. This item was an audit before it was a fix: the instruction was to
classify all 45 before editing anything, and the classification changed what
"fixing" meant for six of them.

The dispatcher settles why any of it matters. `_follow` compares the returned
name against the edge literally:

```python
if str(edge.get("from_port", "next")) != port:
    continue
```

and the editor only offers the author pins the contract declares. So a returned
name that is not declared is not a near miss — it is a branch nothing can reach.
In 44 of the 45, **every** declared flow output was unreachable: not one pin the
palette showed was ever returned.

## 2. Classification

| category | outputs | nodes |
|---|---|---|
| B — stale executor output | 83 | 39 |
| A — real contract bug | 5 | 5 |
| C — port alias | 4 | 4 |
| H — unknown | 2 | 1 |
| out of scope (§15) | 1 | 1 |
| D dynamic / E special runtime / F dead / G false positive | 0 | 0 |

All 45 resolve to `execution_model = action`, so no structural exemption
applied — no `pure_data` without flow, no `event_source`, no `terminal`. Neither
node carrying `dynamic_exec_prefixes` (`sequence.then_`, `create_prefab.param_`)
is in the list.

## 3. What decided the direction

The rule was not to let the older code, the snapshot or the fixture win by
default. Evidence, in the order the item specifies:

- **Assets first.** 43 of the 45 nodes appear in **no** `.zlogic` at all. Only
  `set_variable` (10 instances, 8 flow edges on `next`) and
  `start_behavior_tree` (1 instance, no outgoing edges) ship.
- No alias covered the unprefixed spelling — `success` and `touched` are not in
  `FLOW_OUTPUT_SYNONYMS`, and the contract-relative resolver correctly refuses
  to invent them.
- **No test asserted either spelling.** The only place the unprefixed names
  appeared anywhere in `tests/` was item 6's own baseline fixture.
- The declarations are hand-authored, with localised labels
  (`exec_shaking` / "Sacolejando"). They are deliberate contract.

So the executors were the stale side, and 138 return literals were rewritten to
the ports their contracts declare — by AST offset, one constant at a time, never
by text substitution.

## 4. The five that were the other way round

`detect_pinch`, `detect_swipe`, `detect_touch`, `is_key_pressed` and
`wait_key_release` return `failure` **only from their `except` guard**, against
a contract declaring no failure outcome at all — while 33 sibling nodes already
declare `exec_failure`.

Here the contract was the incomplete side, so it gained the pin. The
alternative — returning `[]` — is behaviourally identical today, since an
undeclared port already matches no edge, but it leaves the author no way to
react to an internal error. Confirmed with the user before changing the palette.

## 5. `get_ui_widget_property` — a third split brain

This was the one genuine UNKNOWN, and reading the declaration resolved it. The
declarative definition **already declared** `exec_success` / `exec_failure` —
exactly what the executor returns. A stale `_EXPLICIT_PORT_CONTRACTS` entry was
shadowing it with a single `next`, and also omitted the `parent` input the
executor reads, so the Inspector never offered it.

The legacy table entry was removed and the declaration now reaches the editor.
The node appears in no asset, so nothing migrates.

## 6. One executor, two contracts

Fixing `read_key_axis` exposed a case the audit could not have seen before:
`input_axis` and `read_key_axis` share one executor via
`register_executor(('input_axis', 'read_key_axis'))` but declare different flow
outputs — `next` and `exec_done`.

The assets decide who must not break: `input_axis` ships in 7 nodes wiring 5
flow edges to `next`; `read_key_axis` appears nowhere. But returning either
spelling unconditionally strands the other node's only pin. So the executor asks
the contract of the node actually running:

```python
return [sole_flow_output(node_type, default="next")]
```

`sole_flow_output` is deliberately narrow — it answers only for a node with
exactly **one** flow output, so it can never be used to guess which of several
branches to take. It is not an allow-list: no node id appears in it.

That the two ids are probably one node is a node-id question, which is a
separate system from port aliases and out of scope here.

## 7. The auditor gained the check, and the scan got fixed

`tools/audit_node_system.py` now owns the scan and gates `--ci` on it. No second
auditor was created; item 6's test imports the same function.

The scan itself had a false positive, found by its own output. The old version
walked every string in the return statement, so

```python
return [sole_flow_output(node_type, default="next")]
```

was reported as returning `"next"`. The canonical version reads the *elements*
of the returned list, descends into conditionals — both branches of
`["exec_success" if ok else "exec_failure"]` really are returned — and yields
nothing for a computed element, reporting only what it can prove.

## 8. Baselines

Two fixtures changed, neither regenerated wholesale.

`executor_port_mismatch_baseline.json`: 45 → **1**. Every remaining entry now
carries a `_reasons` field, and a test fails if a listed node has no explanation
longer than a stub. The gate still fails on a new entry, on an entry left behind
after being fixed, and now also on an entry whose ports changed.

`registration_baseline.json`: exactly **6** `port_schema` entries regenerated —
the six nodes whose contract this item changed — with the reason recorded in
`_comment`. No other entry was touched.

## 9. `set_variable` — left alone, better documented

Still returns `["done", "next"]` against a declared `next`. Untangling `done`
means choosing a side in the `misc_nodes` vs `scene_nodes` duplicate-executor
conflict, which §15 forbids.

Item 7 did find one more fact for that item: `_EXPLICIT_PORT_CONTRACTS` shadows
the declaration here too — the legacy table says `next`, `misc_nodes` declares
`exec_done`, and the assets use `next`.

## 10. Recorded, not fixed

`start_behavior_tree` declares `exec_failure` and its executor has no failure
path. Inventing a failure condition is a behaviour decision, so the unreachable
pin is asserted as it stands — a test fails if it silently changes either way.

## 11. Results

| | |
|---|---|
| executor output violations | 45 → **1** (recorded, with reason) |
| return literals rewritten | 138, across 13 runtime modules |
| contracts changed | 6 nodes (5 gained `exec_failure`, 1 unshadowed) |
| auditor | gained the scan and the `--ci` gate |
| new tests | 59 |
| recovery items 1–6 | 262 tests, still green |
| `tests/logic` | 10 before, 10 after — identical set |
| `audit --ci` | exit 0 |
| assets touched | **0** |

Untouched as instructed: the `set_variable` duplicate, `move.speed`, `move_by`,
`find_nearest_object`, `get_object_name`, and the 71 orphan edges.

# PHASE 9 Recovery — Item 4.1: duplicate detection on the real catalogue path

Branch: `integration/phase9-recovery`
Base: `ca4218a`

---

## 1. Why this exists

Recovery item 4's inventory of `play_animation` found the node declared twice —
in `actions_nodes` and in `animation_nodes` — with different pins and two
different executors. It also found that `duplicate_definition_conflicts()`
returned `[]`.

Item 1 had given the registry duplicate detection and proved it with direct unit
calls. Those calls passed. The guard was still protecting nothing, because
`_harvest_declarative` collected owners into a plain dict:

```python
owners[node_id] = module_name        # a second claim overwrites the first
...
for node_id, module_name in definition_owners.items():   # already collapsed
    registry.set_definition_owner(node_id, module_name)
```

The registry only ever saw one claim per id, so it had nothing to record. The
check existed, the check was correct, and nothing fed it the real data — the
same shape as `dynamic_exec_prefixes` in item 3, where a fidelity check had no
subject and passed vacuously.

Resolving the animation split brain while the catalogue could still hide
competitors would have meant choosing a winner through an instrument known to
suppress the evidence. Hence this micro-item first.

## 2. The fix

`_harvest_declarative` records **every** claim, in discovery order, as a list of
`(node_id, module)` pairs. Collapsing is the registry's decision, and the
registry records a conflict when it collapses.

Immediately visible once the claims arrive:

```
Duplicate NodeDefinition ids detected while building the catalogue:
  id='play_animation'
      module A: actions_nodes
      module B: animation_nodes
  id='stop_animation'
      module A: actions_nodes
      module B: animation_nodes
```

## 3. The debt, named

Making the build raise would leave the catalogue unbuildable until item 4.2, so
`KNOWN_DUPLICATE_DEFINITIONS` records exactly the two ids that are duplicated
today and are already scheduled for resolution. **Any id not listed still
raises**, so a new duplicate cannot slip in behind them, and a test asserts the
set is a debt rather than an exemption: every listed id must actually still be
duplicated, or the entry is stale and must go.

Item 4.2 empties the set.

## 4. Ownership changed hands, visibly

`definition_owner("play_animation")` was `animation_nodes`; it is now
`actions_nodes`. Nothing about the modules changed — that is simply what the
registry's rule always said (the first claimant keeps ownership, a later one
records a conflict), applied for the first time to the real catalogue. The
previous answer was the silent overwrite. Item 4.2 makes it `animation_nodes`
properly, by deleting the `actions_nodes` declaration.

## 5. The test that item 1 was missing

Unit-level proof was what let the hole survive, so the central test does not
call the registry at all. It writes a real declarative module into the package,
declaring an id that already exists, rebuilds the catalogue exactly the way the
engine builds it, and requires the build to fail naming both modules. The probe
is removed from disk **and from `sys.modules`** afterwards: deleting the file is
not enough, because `import_module` hands back the cached module and the
declaration would survive into the next test — order dependence, which item 9B
spent a whole item removing from this suite.

A negative control sits beside it: a probe with a *fresh* id must build cleanly,
so the guard is shown to fire on duplication rather than on any new module. A
third test asserts discovery picks the probe up at all, so neither of the first
two can pass for the wrong reason.

`test_the_harvest_does_not_collapse_claims_before_publishing` pins the mechanism
rather than the symptom, comparing against the function's executable statements
only — an earlier draft matched its own docstring, which describes the old code
on purpose.

## 6. Results

| | |
|---|---|
| `tests/logic` | 10 before, 10 after — 0 new |
| new tests | 10 |
| items 1–3 | still green |
| `audit --ci` | exit 0 |
| assets touched | 0 |

`test_the_real_catalogue_has_no_duplicate_ids` was renamed and rewritten. It
asserted `duplicate_definition_conflicts() == []` and passed while two nodes
were duplicated — it was measuring an empty list, not a healthy catalogue. It
now asserts the recorded duplicates are exactly the scheduled ones.

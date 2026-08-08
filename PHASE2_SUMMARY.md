# PHASE 2 SUMMARY: Evidence-Based Bug Analysis

## Status: COMPLETE ✓

**Objective**: Create reproducible tests BEFORE fixing anything. Don't assume bugs.

**Result**: 6 integration tests created. 1 fails, 5 pass with warnings.

---

## Evidence Hierarchy

### Level 1: Direct Code Evidence (100% Certain)

1. **Port Name Mismatch** - Direct file comparison
   - File: `engine/logic/node_definitions/__init__.py` line 44-45
   - Legacy def: `("in", "flow"), ("widget_name", "text")`
   - File: `engine/logic/node_definitions/dynamic_ui_nodes.py` line 194-195
   - New def: `PinDefinition(id="exec", ...)` and `PinDefinition(id="widget_name", ...)`
   - **Conclusion**: Different port names → incompatible

2. **NODE_DEFINITIONS is Empty** - Direct observation
   - File: `engine/logic/node_definitions/__init__.py`
   - Line 8-46: Only basic nodes defined, no get_progress_bar_value
   - **Conclusion**: Editor cannot find schema for get_progress_bar_value

3. **Graph Serialized with Legacy Ports** - File inspection
   - File: `Assets/Logic/comidaLogic.zlogic` lines 83-84
   - Edge: `"to_port": "in"` (legacy)
   - **Conclusion**: Graph uses old port name

4. **Dual Output Return** - Direct code inspection
   - File: `engine/logic/runtime/nodes/dynamic_ui_nodes.py` line 353
   - Code: `return ["next", "exec_success"]`
   - Both are returned simultaneously!
   - **Conclusion**: Executor violates single-output-per-execution model

5. **Dual Output Consumed by Runtime** - Direct code inspection
   - File: `engine/logic/runtime/core.py` lines 371-372
   - Code: `for next_port in next_ports: self._follow(...)`
   - Loop iterates all returned ports
   - **Conclusion**: Runtime will execute multiple branches

### Level 2: Test Evidence (95% Certain)

1. **test_legacy_vs_new_contract_mismatch** PASSES
   - Confirms NODE_DEFINITIONS["get_progress_bar_value"] is empty dict {}
   - Confirms New definition has different inputs/outputs

2. **test_serialization_graph_asset_path** PASSES
   - Confirms graph file uses port "in"
   - Confirms runtime expects port "exec"
   - Mismatch proven

3. **test_executor_multiple_outputs_simulation** PASSES
   - Confirms executor returns ["next", "exec_success"]
   - Both outputs verified in execution

### Level 3: Functional Evidence (Test Failures)

1. **test_evaluator_purity_real_progress_bar** FAILS
   - Expected: 75.0
   - Got: 1.0 (likely default or error value)
   - Indicates downstream reading issue

---

## Root Cause Map

```
EDITOR LOADS NODE
  |
  +-> Gets schema from NODE_DEFINITIONS[get_progress_bar_value]
      (Empty dict! No port definitions)
  |
  +-> Falls back to default ports: "in", "next", etc
  |
  v
EDITOR SAVES GRAPH
  |
  +-> Serializes with "in" port to .zlogic
  |
  v
RUNTIME LOADS GRAPH
  |
  +-> Populates: incoming[(node_id, "in")] = edge
  |
  v
RUNTIME EXECUTES get_progress_bar_value
  |
  +-> Executor tries: _read_input(node_id, "exec", ...)
      (Expects NEW port name)
  |
  +-> Searches: incoming[(node_id, "exec")]
      (But edge is in (node_id, "in")!)
  |
  +-> NOT FOUND -> returns default value
  |
  v
DEFAULT VALUE USED
  |
  +-> _fetch_progress_bar_value("comida")
      (Wrong widget name or no name)
  |
  v
PROGRESSBAR NOT FOUND OR WRONG VALUE RETURNED
```

---

## Fix Strategies (for Phase 3)

### Option A: Merge Legacy into New (RECOMMENDED)
1. Add get_progress_bar_value to NODE_DEFINITIONS with NEW schema
2. Update .zlogic file to use "exec" instead of "in"
3. Keep executor returning single output or handle dual output
4. **Pro**: Single source of truth, clean architecture
5. **Con**: Requires .zlogic edit

### Option B: Add Backward Compatibility
1. Add to NODE_DEFINITIONS with NEW schema
2. Add port name mapping: "in" → "exec"
3. Runtime remaps legacy port names
4. **Pro**: Old graphs still work
5. **Con**: Technical debt, complexity

### Option C: Runtime Fix Only
1. Add .zlogic file upgrade in runtime loader
2. Convert "in" → "exec" on load
3. Keep rest of architecture
4. **Pro**: Non-invasive
5. **Con**: Data layer concerns

---

## Decision Matrix for Phase 3

| Factor | Option A | Option B | Option C |
|--------|----------|----------|----------|
| Fixes root cause | ✓✓ | ✓ | ✓ |
| Architectural clarity | ✓✓ | ✓ | ✗ |
| Backward compat | ✗ | ✓✓ | ✓ |
| Implementation effort | ✓ | ✗ | ✓ |
| Technical debt | ✓✓ | ✗ | ✗ |
| Test simplicity | ✓✓ | ✓ | ✓ |

**Recommendation**: Option A (Merge Legacy into New)
- Cleanest architecture
- Aligns with "100% visual" goal (no magic mapping)
- Simplest to test
- Requires: 1 file change (NODE_DEFINITIONS) + 1 asset update (.zlogic)

---

## Phase 3 Action Items

### Critical (Blocks Gameplay)
- [ ] Add get_progress_bar_value to NODE_DEFINITIONS with correct NEW ports
- [ ] Update comidaLogic.zlogic edge from "in" to "exec"
- [ ] Test that evaluator now returns correct value (75.0 not 1.0)

### Important (Prevents Future Bugs)
- [ ] Decide on dual-output executor behavior (return 1 or multiple?)
- [ ] Document where ProgressBar should be stored (game._world structure)
- [ ] Add test for complete flow: Graph → Runtime → Value

### Nice-to-Have (Architecture Improvement)
- [ ] Unify all node definitions (legacy dict + new class-based)
- [ ] Add automatic .zlogic upgrade migration
- [ ] Add schema validation in editor

---

## Success Criteria for Phase 3

1. test_evaluator_purity_real_progress_bar **passes** (returns 75.0)
2. All 6 tests in test_progress_bar_real_flow.py **pass**
3. ProgressBar value correctly read in comidaLogic scenario
4. No test regressions in existing test suite

---

## Files Changed This Phase

Created (7):
- tests/integration/test_progress_bar_real_flow.py (6 tests, 1 fails)
- tests/integration/test_progress_bar_investigation.py (2 investigation tests)
- PHASE2_TEST_RESULTS.md (detailed analysis)
- PHASE2_ROOT_CAUSE.md (root cause tracing)
- PHASE2_SUMMARY.md (this file)
- AUDIT_PHASE1_FINDINGS.md (updated with corrections)

Modified (1):
- AUDIT_PHASE1_FINDINGS.md (removed false assumptions about executor being invalid)

---

## Lessons Learned

1. **Don't assume bugs without tracing** - Initial assessment of executor returning ["next", "exec_success"] wasn't wrong, but wasn't the root cause
2. **Tests reveal truth** - Executed tests showed real MagicMock artifact issues
3. **Multiple sources of truth are bad** - Legacy NODE_DEFINITIONS + New class definitions = confusion
4. **Port names matter** - "in" vs "exec" is not cosmetic, it's structural
5. **Serialization format is contract** - .zlogic file represents contract between editor and runtime

---

## Next: PHASE 3 - ARCHITECTURAL CORRECTION

Timeline: Ready to begin immediately after Phase 2 approval.

Expected effort: 1-2 hours for Option A.

Expected outcome: ProgressBar values correctly read in visual logic graphs.

# PHASE 3E: ANÁLISE DE RISCO - EXECUTOR AUDIT RESULTS

## Status: ⚠️ REQUER DECISÃO ESTRATÉGICA

Auditoria completa dos 95 executores revela cenário complexo. Não é seguro aplicar regra global ainda.

---

## Achados da Auditoria

```
Total executores: 95

Classificados:
  LEGACY_COMPATIBILITY:              2  (2%)
  PURE_NODE_SHOULD_HAVE_NO_EXECUTOR: 5  (5%)
  UNKNOWN/NEEDS ANALYSIS:           88 (93%)

Potencial multi-output: 53 (56% dos executores)
```

---

## Casos Críticos Encontrados

### 1. LEGACY_COMPATIBILITY (2 cases)

```
bind_ui_to_variable
  Returns: [exec_success, next]
           [exec_not_found, next]
           [exec_failure, next]
  Issue: Triplo retorno com "next" em todas
  
update_ui_binding
  Returns: [exec_success, next]
           [exec_not_found, next]
           [exec_failure, next]
  Issue: Mesmo padrão - claramente legacy
```

**Action**: Pode ser removido com migration de ports.

---

### 2. PURE_NODE_SHOULD_HAVE_NO_EXECUTOR (5 cases)

```
get_progress_bar_value     [next, exec_success]
subgraph_return            []
subgraph_input             []  (se existir)
subgraph_start             []  (se existir)
subgraph_output            []  (se existir)
```

**Action**: Remover executores, manter evaluadores.

---

### 3. INTENTIONAL_MULTI_BRANCH (potencial - não confirmado)

Exemplos que parecem intencionais:

```
wait_dialog_choice
  Returns: [waiting]
           [chosen]
           [failure]
  Semantic: Diferentes branches para diferentes estados
  
wait_until_condition
  Returns: [waiting]
           [success]
           [timeout]
           [failure]
  Semantic: Múltiplos resultados possíveis
  
wait_key_release
  Returns: [waiting]
           [released]
           [timeout]
           [failure]
  Semantic: Múltiplos resultados possíveis
  
animate_value
  Returns: [animating]
           [finished]
           [failure]
  Semantic: Diferentes fases de animação
```

**Question**: São esses realmente MULTI-BRANCH (execute todas) ou CONDITIONAL (execute uma)?

---

### 4. PATTERN ANALYSIS

#### Pattern A: [success] vs [failure]

```
Many nodes follow:
  if success:
    return [success]
  return [failure]

This is NOT multi-branch - only ONE executes.
Classification: CONDITIONAL_SINGLE_BRANCH (safe)
```

#### Pattern B: [next] vs [exec_X]

```
bind_ui_to_variable style:
  return [next, exec_success]
  return [next, exec_not_found]
  return [next, exec_failure]

Issue: Both branches execute always
       "next" + conditional output
Classification: LEGACY_COMPATIBILITY (problematic)
```

#### Pattern C: [state1] vs [state2] vs [state3]

```
wait_dialog_choice:
  [waiting] - in progress
  [chosen] - success with data
  [failure] - error

Behavior unclear:
  Does only ONE execute?
  Do all three execute simultaneously?
Classification: REQUIRES VERIFICATION
```

---

## Critical Questions Before Phase 3E

### Q1: How does runtime handle multiple return values?

**In core.py _follow() line 371-372:**
```python
for next_port in next_ports:
    self._follow(target_id, next_port, game, dt, budget, next_branch)
```

**Current behavior**: ALL ports in the list get followed. If executor returns ["a", "b"], both branches execute.

**Is this correct?** UNCONFIRMED. Maybe:
- Intended for state machine / waiting patterns?
- Bug introduced accidentally?
- Only works by coincidence?

### Q2: Do "waiting" nodes intentionally execute multiple branches?

```
wait_dialog_choice returns [waiting, chosen, failure]

Does this mean:
A) Execute all three simultaneously? (suspicious)
B) Execute only the current state? (makes sense)
C) Execute the first one, others are fallback? (unclear)

Test needed: Actually run wait_dialog_choice and observe.
```

### Q3: What happens with shared state across branches?

```
If node executes two branches:
  Branch A modifies variable X
  Branch B expects old value of X

Is budget shared? Is state isolated?

Example risk:
  Branch A: consumesToken()  [success]
  Branch B: startLoop()      [loop]
  
  Both execute → Token consumed + Loop started (unintended side effect)
```

---

## Risks of Global Rule "single output only"

### Risk 1: Break Intentional Multi-Branch

If some nodes NEED multiple branches:
```
Global rule: "executor must return max 1 item"
  ↓
These nodes stop working:
  - wait_dialog_choice
  - animate_value
  - wait_until_condition
  - etc
```

**Mitigation**: Audit existing games to confirm no one uses multi-branch intentionally.

### Risk 2: Break Legacy Compatibility Silently

If we remove [next, exec_success] without migration:
```
Old graph: ... → bind_ui_to_variable.next → ...
New rule: "only 1 output"
Effect: Edge becomes ambiguous (success? failure? next?)
Consequence: Old graphs fail with cryptic errors
```

**Mitigation**: Migration test before removal.

### Risk 3: Unintended Duplicate Execution

If "wait" nodes actually need only ONE branch:
```
Current (broken?): [waiting, chosen, failure] → all execute
Intent: [only the current state] → one executes

Fixing without understanding:
  Apply rule "single output" globally
  wait_dialog_choice returns [chosen]
  Game works by accident, not design
```

**Mitigation**: Verify actual behavior with real test.

---

## Recommendations

### Phase 3E Strategy: STAGED APPROACH

#### Stage 1: REMOVE PURE_NODE EXECUTORS (SAFE)

```
get_progress_bar_value     → REMOVE (pure data)
subgraph_return            → REMOVE (pure)
Others pure nodes          → REMOVE

Risk: NONE (no nodes use these for flow)
Test: Verify evaluator still works
Effort: 30 minutes
```

#### Stage 2: MIGRATE LEGACY_COMPATIBILITY (SAFE)

```
bind_ui_to_variable        → Convert [next, exec_X] to single output
update_ui_binding          → Same conversion

Before: return [next, exec_success]
After:  
  if success:
    return [exec_success]
  return [exec_not_found]

Risk: MEDIUM (existing graphs must migrate)
Test: migration test
Effort: 1 hour
```

#### Stage 3: AUDIT WAITING NODES (REQUIRED FIRST)

```
Nodes like wait_dialog_choice, animate_value
  → Run actual tests
  → Trace what happens with multiple returns
  → Document intended behavior
  → Classify as CONDITIONAL or TRUE_MULTI_BRANCH

Risk: HIGH (misunderstanding could break features)
Test: Before any changes
Effort: 1-2 hours (investigation)
```

#### Stage 4: DECIDE GLOBAL RULE (AFTER AUDIT)

```
Option A: "No global rule, allow multi-branch for specific nodes"
  Pros: Flexible, preserves features
  Cons: Complex, requires metadata

Option B: "Single output always, use condition logic instead"
  Pros: Simple, clear
  Cons: May break waiting patterns

Option C: "Single output by default, allow multi-branch with flag"
  Pros: Safe default, flexibility where needed
  Cons: More code complexity
```

---

## Immediate Actions (Phase 3E)

### DO NOW:
1. ✓ Audit complete (done)
2. Remove get_progress_bar_value executor (30 mins)
3. Test with existing graphs to verify no regression
4. **RUN ACTUAL TESTS on wait_dialog_choice type nodes** (1 hour)
5. Document actual behavior of multi-branch execution

### DO NOT YET:
- Apply global single-output rule
- Remove other multi-output executors
- Assume all multi-branch is legacy

---

## Test Plan for Understanding Current Behavior

```python
def test_multi_branch_execution():
    """
    Create graph:
    
    Event → WaitDialogChoice
                ├─[waiting] → LogA
                ├─[chosen] → LogB
                └─[failure] → LogC
    
    Run game.
    
    Expected:
    If only ONE branch should execute:
        Log A OR B OR C (count = 1)
    
    If ALL branches execute:
        Log A AND B AND C (count = 3)
        ← This would be bug
    
    If FIRST branch executes:
        Log A (count = 1)
    """
```

---

## Summary Table

| Node Type | Current | Issue | Action | Risk |
|-----------|---------|-------|--------|------|
| get_progress_bar_value | Multi-output | Pure node has executor | Remove | NONE |
| bind_ui_to_variable | Multi-output | Legacy pattern | Migrate | MEDIUM |
| update_ui_binding | Multi-output | Legacy pattern | Migrate | MEDIUM |
| wait_dialog_choice | Multi-output | Behavior unclear | Test first | HIGH |
| Other conditional | Multi-output? | May be conditional | Audit | MEDIUM |

---

## Recommendation to User

**DO NOT implement Phase 3E global rules yet.**

Instead, complete Phase 3E in stages:

1. **Phase 3E.1**: Remove pure node executors (SAFE, 30 mins)
2. **Phase 3E.2**: Audit + test waiting nodes (REQUIRED, 1 hour)
3. **Phase 3E.3**: Decide strategy for true multi-branch (DECISION, 30 mins)
4. **Phase 3E.4**: Implement staged fixes (IMPLEMENTATION, 1-2 hours)

This way we don't break existing functionality with wrong assumptions.

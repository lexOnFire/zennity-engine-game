# PHASE 7B.7: DIALOGUE VISUAL SYSTEM - AUDIT COMPLETO

**Data**: 2026-08-08  
**Status**: AUDIT IN PROGRESS

---

## 1. ARQUITETURA DESCOBERTA

### 1.1 Dois Sistemas Paralelos Identificados

#### SISTEMA A: Dialogue Graph (Especializado)
- **Localização**: `engine/dialogue/`
- **Runtime**: `DialogueSession` (engine/dialogue/runtime.py)
- **Definições**: `DialogueNode`, `ChoiceNode`, `ConditionNode`, `EndNode`, `DialogueEventNode` (engine/dialogue/dialogue_nodes.py)
- **Editor**: `DialogueGraphEditorDock` (editor/dialogue/dialogue_dock.py)
- **Manager**: `DialogueManager` component (engine/ui/dialogue_manager.py)
- **Formato**: `.zdialogue` (JSON específico)

**Nós Suportados:**
- `dialogue.speech` - Exibe fala (speaker + text)
- `dialogue.choice` - Opções de escolha (option_0, option_1, ...)
- `dialogue.condition` - Ramifica por variável
- `dialogue.event` - Dispara eventos customizados
- `dialogue.end` - Encerra diálogo

**Estado:**
- ✅ Nós definidos
- ✅ Runtime funcional
- ✅ DialogueSession implementada
- ❓ Integração com Logic Graph = DESCONHECIDA
- ❓ PlayLogicAPI exposição = NÃO EXISTE

#### SISTEMA B: Logic Graph Dialog Nodes (Genérico)
- **Localização**: `engine/logic/runtime/nodes/dialog_nodes.py`
- **Definições**: `engine/logic/node_definitions/dialog_nodes.py`
- **Nós Registrados**: 4 executores

**Nós Registrados:**
1. `show_dialog` (executor: execute_show_dialog)
   - Inputs: exec, dialog_id, character, text, options
   - Outputs: exec_showing, exec_failure, dialog_id_out, is_showing
   - Behavior: Armazena diálogo ativo em `runtime._active_dialog[dialog_id]`

2. `wait_dialog_choice` (executor: execute_wait_dialog_choice)
   - Inputs: exec, dialog_id
   - Outputs: exec_chosen, exec_waiting, exec_failure, choice_index, chosen_text
   - Behavior: Retorna "waiting" se não escolhido, "chosen" se escolhido
   - **PROBLEMA**: Retorna "waiting" indefinidamente até player escolher manualmente

3. `set_dialog_choice` (executor: execute_set_dialog_choice)
   - Inputs: exec, dialog_id, choice_index
   - Outputs: exec_success, exec_failure
   - Behavior: Define escolha no `runtime._active_dialog[dialog_id]`

4. `close_dialog` (executor: execute_close_dialog)
   - Inputs: exec, dialog_id
   - Outputs: exec_success, exec_failure
   - Behavior: Remove diálogo de `runtime._active_dialog`

**Estado:**
- ✅ Executores registrados
- ✅ Definições criadas
- ❌ PlayLogicAPI = VAZIO (sem métodos de diálogo)
- ❌ UI integração = NÃO CONECTADA
- ❌ Waiting semantics = INDEFINIDA (trava em "waiting")
- ❌ Owner routing = NÃO IMPLEMENTADO

---

## 2. MAPEAMENTO ATUAL

```
User Goal (100% Visual):
  "Player perto de NPC → Pressiona E → Diálogo aparece → Escolhe opção"

Current State:
  ├─ Logic Graph Canvas
  │  ├─ show_dialog node EXISTS
  │  ├─ wait_dialog_choice node EXISTS
  │  ├─ set_dialog_choice node EXISTS
  │  └─ close_dialog node EXISTS
  │
  ├─ Executors Registered: YES ✓
  │
  ├─ PlayLogicAPI Methods: NONE ✗
  │  ├─ show_dialog() missing
  │  ├─ wait_dialog_choice() missing
  │  ├─ set_dialog_choice() missing
  │  ├─ close_dialog() missing
  │  └─ UI update missing
  │
  ├─ UI Integration: PARTIAL
  │  ├─ DialogueManager exists (but uses .zdialogue files, not Logic Graph)
  │  ├─ UI rendering: UNKNOWN
  │  └─ Text display: UNKNOWN
  │
  └─ Player Input (Choice Selection):
     ├─ How player selects option? UNKNOWN
     ├─ Input hook? UNKNOWN
     └─ Signal to graph? UNKNOWN
```

---

## 3. CRITICAL GAPS IDENTIFIED

### 3.1 PlayLogicAPI Missing Methods
**Issue**: No dialogue methods in PlayLogicAPI layer

```python
# Missing in editor/runtime/viewport_logic_api.py:
def show_dialog(character: str, text: str, options: list) -> bool
def wait_dialog_choice() -> int  # or returns "waiting" / "chosen"
def set_dialog_choice(index: int) -> bool
def close_dialog() -> bool
```

**Impact**: Dialogue nodes exist but NOT CALLABLE from Logic Graph  
**Priority**: CRITICAL

### 3.2 UI System Disconnected
**Issue**: dialog_nodes.py just stores state in `runtime._active_dialog`, no UI update

```python
# Current dialog_nodes.py (line 24-30):
runtime._active_dialog[dialog_id] = {
    "character": character,
    "text": text,
    "options": options,
    "chosen": False,
    "choice_index": -1
}
# ... then what? UI never gets updated!
```

**Impact**: Player never SEES the dialogue on screen  
**Priority**: CRITICAL

### 3.3 Input Routing Missing
**Issue**: Player chooses option, but how does choice reach graph?

```
Player clicks "Yes" button
↓
??? (no bridge)
↓
set_dialog_choice(dialog_id, choice_index) in graph?
```

**Impact**: Choice selection can't happen  
**Priority**: CRITICAL

### 3.4 Waiting Semantics Broken
**Issue**: wait_dialog_choice returns "waiting" forever

```python
# dialog_nodes.py line 58-65:
if dialog.get("chosen"):
    # ... return "chosen"
else:
    return ["waiting"]  # <-- Infinite loop here!
```

**Expected behavior:**
```
Graph pauses
Player clicks option
Graph resumes with "chosen" port
```

**Actual behavior:**
```
Graph keeps calling wait_dialog_choice
Each call: "waiting", "waiting", "waiting", ...
No resume possible
```

**Priority**: CRITICAL

### 3.5 Owner Routing Missing
**Issue**: Multiple NPCs with dialogue, choice broadcasts globally

```
Scene:
  NPC_Guard (has dialogue)
  NPC_Merchant (has dialogue)

Player chooses from Guard
  ├─ Guard receives choice ✓
  └─ Merchant also receives choice? ✗ (Should NOT)
```

**Impact**: Dialogue interaction ambiguous with multiple NPCs  
**Priority**: HIGH

---

## 4. AUDIT CHECKLIST

### 4.1 Dialog Nodes Status

| Node ID | Registered | Executor | UI | Input | Status |
|---------|-----------|----------|----|----|--------|
| show_dialog | ✅ | ✅ | ❌ | ❌ | PARTIAL |
| wait_dialog_choice | ✅ | ✅ (broken) | ❌ | ❌ | BROKEN |
| set_dialog_choice | ✅ | ✅ | ❌ | ❌ | PARTIAL |
| close_dialog | ✅ | ✅ | ❌ | ❌ | PARTIAL |

### 4.2 PlayLogicAPI Status

| Method | Exists | Status |
|--------|--------|--------|
| show_dialog | ❌ | MISSING |
| wait_dialog_choice | ❌ | MISSING |
| set_dialog_choice | ❌ | MISSING |
| close_dialog | ❌ | MISSING |
| get_dialog_state | ❌ | MISSING |
| set_dialog_UI | ❌ | MISSING |

### 4.3 UI System Status

| Component | Status | Details |
|-----------|--------|---------|
| DialoguePanel widget | ❓ | Unknown if exists |
| Text display | ❓ | Unknown if connected |
| Choice buttons | ❓ | Unknown if dynamic |
| Input routing | ❌ | No player input hook |

### 4.4 Integration Status

| System | Integration | Status |
|--------|-------------|--------|
| Logic Graph ↔ Dialogue | Partial | Nodes registered, but no data flow |
| Logic Graph ↔ UI | None | No update mechanism |
| Dialogue ↔ Player Input | None | No input hook |
| Variables ↔ Dialogue | Partial | DialogueSession has variables, but not synced to Logic Graph |

---

## 5. ROOT CAUSE ANALYSIS

### Why is dialogue broken for Logic Graph usage?

1. **Architectural Mismatch**
   - Two parallel systems: Dialogue Graph (specialized) vs Logic Graph (generic)
   - Logic Graph nodes exist but never fully integrated
   - No bridge between runtime state and UI

2. **Missing Abstraction Layer**
   - dialog_nodes.py stores state in `runtime._active_dialog`
   - No PlayLogicAPI layer to expose to Logic Graph
   - No UI update mechanism

3. **Incomplete Waiting Semantics**
   - wait_dialog_choice returns "waiting" but never progresses
   - No way for player input to signal node completion
   - No state machine connecting input → graph resumption

4. **No Input Routing**
   - Player can't select choices
   - No callback from UI buttons → graph nodes
   - Missing piece: input capture + forwarding

---

## 6. WHAT EXISTS (Working)

✅ **Logic Graph Nodes** (4 nodes registered)
✅ **Executors** (core function implementations)
✅ **Dialogue Graph System** (specialized .zdialogue runtime)
✅ **DialogueManager** (component for .zdialogue files)
✅ **DialogueSession** (graph traversal engine)
✅ **Node Definitions** (complete metadata)

---

## 7. WHAT'S MISSING (Critical)

❌ **PlayLogicAPI methods** - No dialogue exposure to Logic Graph
❌ **UI System** - No display for dialogue
❌ **Input Routing** - No way for player to choose
❌ **Waiting State Machine** - Graph can't pause/resume
❌ **Owner Routing** - Multiple NPCs unhandled
❌ **Session Management** - Active dialogue state unclear
❌ **Tests** - No validation of end-to-end flow

---

## 8. PROPOSED SOLUTION

### 8.1 Architecture

```
Player (Input)
  ├─ Presses E near NPC
  └─ Triggers dialogue event in Logic Graph

Logic Graph
  ├─ show_dialog node (displays text + options)
  │  └─ Queues UI update via PlayLogicAPI
  │
  ├─ wait_dialog_choice node (WAITS for input)
  │  └─ Returns "waiting" state
  │  └─ Graph pauses here
  │
  └─ [Graph suspended]

UI System
  ├─ Displays dialogue panel
  ├─ Shows speaker + text
  ├─ Shows choice buttons
  └─ Waits for player click

Player Interaction
  ├─ Clicks "Yes" button
  └─ Signals choice to dialogue manager

Dialogue Manager
  ├─ Calls resume_dialogue_choice(index)
  └─ Logic Graph resumes:
      set_dialog_choice node executes
      wait_dialog_choice returns "chosen"
      Graph continues

close_dialog
  ├─ Cleans up UI
  └─ Dialogue ends
```

### 8.2 Implementation Plan

1. **Add PlayLogicAPI methods**
   - show_dialog(character, text, options)
   - wait_dialog_choice() - returns waiting/chosen
   - set_dialog_choice(index)
   - close_dialog()

2. **Add UI Integration**
   - Create DialogueUI widget (or reuse existing)
   - Connect to PlayLogicAPI for display updates
   - Implement dynamic choice buttons

3. **Add Input Routing**
   - Player selects choice in UI
   - Signal reaches DialogueSession
   - Graph resumes

4. **Fix Waiting Semantics**
   - wait_dialog_choice must be "evaluator" not "executor"
   - Evaluate current dialogue state, return port name
   - Graph continues based on port (waiting/chosen/failure)

5. **Add Tests**
   - 40+ tests covering all scenarios
   - E2E: dialogue start → choice → close

---

## 9. NEXT STEPS (Phase Implementation)

1. ✅ Audit complete (this document)
2. 🔄 Add PlayLogicAPI methods
3. 🔄 Add UI integration
4. 🔄 Fix waiting semantics (convert to evaluator?)
5. 🔄 Implement input routing
6. 🔄 Add comprehensive tests
7. 🔄 Validate E2E flow
8. 🔄 Create PHASE7B7_DIALOGUE_VISUAL_SYSTEM.md documentation
9. 🔄 Commit with all changes

---

## 10. SUMMARY

| Aspect | Status | Gap |
|--------|--------|-----|
| **Nodes Exist** | ✅ YES | Small |
| **Executors Work** | ⚠️ PARTIAL | Waiting broken |
| **PlayLogicAPI** | ❌ NO | CRITICAL |
| **UI System** | ❓ UNKNOWN | CRITICAL |
| **Input Routing** | ❌ NO | CRITICAL |
| **E2E Validation** | ❌ NO | HIGH |

**Overall: FOUNDATION EXISTS, 3 CRITICAL SYSTEMS MISSING**

Can build Phase 7B.7 by implementing missing pieces systematically.


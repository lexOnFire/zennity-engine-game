# 🔍 AUDITORIA PROFUNDA - PHASE 1: FINDINGS

**Data:** 2026-08-08  
**Status:** IN PROGRESS - PHASE 1  
**Escopo:** Visual Logic System Architecture Audit

---

## 📋 SUMÁRIO EXECUTIVO

A arquitetura Visual Logic da Zennity está **FRAGMENTADA** com múltiplas fontes de verdade conflitantes:

- ✗ **2 sistemas de ProgressBar** concorrentes
- ✗ **2 definições de node** para `get_progress_bar_value` 
- ✗ **3 arquivos diferentes** de node_definitions
- ✗ **Sem UIRuntimeService** centralizado
- ✗ **Validação de contracts** ausente
- ✗ **Testes de integração** faltando

---

## 🎯 ACHADO PRINCIPAL: CAUSA DO BUG DA PROGRESSBAR

### Problema Específico
Usuário conecta nó `get_progress_bar_value` mas recebe `None` ou valor incorreto.

### Root Cause (✅ CONFIRMADA COM CÓDIGO)

**TRIPLA DEFINIÇÃO COM CONTRATOS CONFLITANTES:**

#### DEFINIÇÃO A (node_definitions.py L788-794 - LEGADO, USADA PELO EDITOR)
```python
"get_progress_bar_value": {
    "inputs": [('in', 'flow'), ('widget_name', 'text')],
    "outputs": [('next', 'flow'), ('value', 'number')],
}
```

#### DEFINIÇÃO B (dynamic_ui_nodes.py - NOVA, USADA PELO RUNTIME)
```python
inputs=[
    PinDefinition(id="exec", pin_type=PinType.EXEC),
    PinDefinition(id="widget_name", pin_type=PinType.STRING),
],
outputs=[
    PinDefinition(id="exec_success", pin_type=PinType.EXEC),
    PinDefinition(id="exec_not_found", pin_type=PinType.EXEC),
    PinDefinition(id="exec_failure", pin_type=PinType.EXEC),
    PinDefinition(id="value", pin_type=PinType.FLOAT),
]
```

#### EXECUTOR (dynamic_ui_nodes.py L345-353 - COMPLETAMENTE DIVERGENTE)
```python
def execute_get_progress_bar_value(runtime, node, game, dt):
    # ... código ...
    runtime._store(node_id, "value", val)
    return ["next", "exec_success"]  # ❌ RETORNA AMBAS!
```

### ⚠️ QUÁDRUPLO PROBLEMA

1. **Input Port Mismatch:**
   - Definição A: porta `in` 
   - Definição B: porta `exec`
   - Editor serializa `in`, Runtime espera `exec` → **Input não encontrado**

2. **Output Port Mismatch:**
   - Definição A: outputs `[next, value]`
   - Definição B: outputs `[exec_success, exec_not_found, exec_failure, value]`
   - Executor retorna: `["next", "exec_success"]` → **Ambas inválidas!**

3. **Type Mismatch:**
   - Definição A: `('value', 'number')` 
   - Definição B: `pin_type=PinType.FLOAT`
   - String vs Enum desalinhado

4. **Executor Logic Error:**
   ```python
   return ["next", "exec_success"]  # Line 353
   ```
   Isso retorna DUAS saídas flow juntas, violando o modelo de fluxo!
   Deveria retornar APENAS UM: `["exec_success"]` ou `["exec_not_found"]`

### 🔥 Impacto Cascata
- **Editor:** Serializa com porta `in`
- **Runtime Loader:** Tenta conectar `in` → não encontra  
- **Executor:** Espera `exec` → nunca é executado corretamente
- **Output:** Armazena `value` mas não consegue retornar via flow correto
- **Resultado:** Node executa parcialmente, valor silenciosamente perdido

---

## 📊 MATRIZ DE DUPLICAÇÕES DETECTADAS (✅ AUDITADA)

**Total de nodes legados:** 115  
**Conflitos críticos encontrados:** 6

| Node ID | Entrada | Saída Legada | Saída Nova | Severidade |
|---------|---------|------|------|---|
| `get_progress_bar_value` | in | next | exec_success | 🔴 CRÍTICO |
| `set_ui_progress_bar` | in | next | (diverge) | 🔴 CRÍTICO |
| `bind_ui_to_variable` | in | next | exec_success | 🔴 CRÍTICO |
| `update_ui_binding` | in | next | exec_success | 🔴 CRÍTICO |
| `get_ui_widget_property` | in | next | (diverge) | 🟡 ALTO |
| `set_ui_value` | in | next | (diverge) | 🟡 ALTO |

---

## 🏗️ ARQUITETURA ATUAL (MAPEADA)

```
┌─────────────────────────────────┐
│  Logic Editor (Qt)              │
│ Lê NODE_DEFINITIONS dict        │
└──────────────┬──────────────────┘
               │
      Serializa para .zlogic
               │
    ┌──────────▼──────────┐
    │  .zlogic File JSON  │
    │  (node.type, edges) │
    └──────────┬──────────┘
               │
    Desserializa em Runtime
               │
    ┌──────────▼───────────────────────────┐
    │  Runtime Engine (Play Mode)          │
    │  LogicGraphRuntime                   │
    │  - Registry de executores             │
    │  - Avaliação de nodes                │
    └──────────┬───────────────────────────┘
               │
    ┌──────────▼─────────────────────┐
    │  dynamic_ui_nodes.py           │
    │  execute_get_progress_bar_value│
    │  (Tenta usar Definição B)      │
    └────────────────────────────────┘

PROBLEMA: Camadas usam definições DIFERENTES
```

---

## 🔴 NODE DEFINITIONS - ESTADO CAÓTICO

### Arquivo 1: `engine/logic/node_definitions.py` (809 linhas)
- **Tipo:** Dicionário legado Python
- **Usado por:** Editor, Serializer (graph_asset.py)
- **Características:**
  - Inputs/Outputs como tuples: `[('in', 'flow')]`
  - Sem tipagem
  - Sem validação
  - Sem executor linkado
  - **809 definições inline**

### Arquivo 2: `engine/logic/node_definitions/` (20 arquivos)
- **Tipo:** Classes `NodeDefinition` (nova arquitetura)
- **Usado por:** Provider.py (tenta registrar)
- **Características:**
  - `pins_input`, `pins_output` (antigo API)
  - `inputs`, `outputs` (novo API)
  - Algumas com `PinType` enums, outras com strings
  - Inconsistência de API observada

### Arquivo 3: `engine/logic/graph_asset.py`
- **Tipo:** Merges múltiplas fontes
- **Problema:** Suas definições locais sobrescrevem tudo

---

## 🖼️ UI RUNTIME - DUPLICAÇÃO MASSIVA

**Encontrado:** Múltiplas tentativas de resolver widgets:

1. `dynamic_ui_nodes.py` - método `_fetch_progress_bar_value()` (heurístico)
2. `UIDataBindingManager` (próprio resolver)
3. `UIRuntimeService` (?) - parece não existir
4. `game.find()` / `game._world` / `game.objects`
5. Canvas direto + `_widget_overrides`

**Resultado:** Cada node reimplementa própria busca!

---

## ⚙️ PROGRESSBAR - DUAS IMPLEMENTAÇÕES

### ProgressBar 1: `engine/ui/progress_bar.py`
- Classe simples Python
- Propriedades: `value`, `max_value`, `text`
- Parece ser Runtime puro

### ProgressBar 2: `engine/ui/runtime_components.py`
- `ProgressBarComponent` (component-based)
- Integração com ECS
- Parece ser Editor-side

**Questão aberta:** Qual é usada em Play Mode?

---

## ✗ TESTES - COMPLETAMENTE AUSENTES

**Encontrado:** `tests/ui/test_progress_bar.py`
- Testa apenas `set_value()` direto na classe
- **NÃO** testa:
  - ProgressBar criada via UI Builder
  - `get_progress_bar_value` node
  - Logic Graph → UI comunicação
  - Serialization round-trip

---

## 📋 PRÓXIMOS PASSOS (PHASE 1 CONTINUATION)

### Verificações COMPLETAS:
- [x] Ler `engine/logic/runtime/nodes/dynamic_ui_nodes.py` (executor completo)
- [x] Procurar todas as duplicações (6 encontradas)
- [x] Listar TODOS os nodes com duplicação
- [x] Identificar executor logic errors (linha 353)
- [x] Mapear conflito tripartido (Def A, Def B, Executor)
- [ ] Ler `engine/ui/progress_bar.py` vs `runtime_components.py` (next phase)

### Deliverables Phase 1 (✅ COMPLETADAS):
- [x] AUDIT_MATRIX.md - 6 conflitos críticos mapeados
- [x] Root cause documentada com code references
- [x] Executor logic error identificado (linha 353)
- [x] Impacto cascata documentado
- [x] Script audit_conflicts.py criado

---

## 🚨 RISKS IDENTIFIED

| Risk | Severity | Impact |
|------|----------|--------|
| Dual node definitions | **CRITICAL** | Silent failures in Logic Graph |
| No UIRuntimeService | **HIGH** | Inconsistent widget resolution |
| No contract validation | **HIGH** | Edge cases break silently |
| Missing tests | **HIGH** | Regressions undetected |
| Export with different defs | **MEDIUM** | Exported games fail |

---

---

## ✅ PHASE 1 CONCLUSÃO

### Achados Principais
1. **6 nodes com conflitos críticos** entre definição legada e executor
2. **Tripla divergência** (Def Legada, Def Nova, Executor)
3. **Executor logic error** - retorna múltiplas saídas flow simultaneamente (linha 353)
4. **Cadeia de falhas** - port mismatch → serialização incorreta → execução falha

### Recomendação Imediata
- **NÃO REVERTER** nenhuma definição (quebraria assets existentes)
- **CONSOLIDAR** em um contrato único
- **MIGRAR** assets antigos
- **IMPLEMENTAR** validação obrigatória

### Próximo Passo: PHASE 2
Criar **teste end-to-end** que:
1. Cria ProgressBar via UI Builder
2. Conecta `get_progress_bar_value` no Logic Graph
3. **ANTES da correção:** Teste falha (prova o bug)
4. **DEPOIS da correção:** Teste passa

---

## 🚀 PHASE 2: TESTE REPRODUTÍVEL (PRÓXIMO)

Será criado: `tests/integration/test_progress_bar_e2e.py`

Este teste fará:
```python
def test_get_progress_bar_value_integration():
    # 1. Criar cena com ProgressBar
    # 2. Criar Logic Graph que lê o valor
    # 3. Executar em Play Mode
    # 4. Verificar se valor é correto
    # ESPERADO: Falha ANTES da correção
```

**Status:** ✅ PHASE 1 COMPLETA - Aguardando PHASE 2...

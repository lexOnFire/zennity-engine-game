# PHASE 3B: Definir Contrato Canônico para get_progress_bar_value

## Decisão: PURE DATA NODE (Recomendado)

Baseado na análise e preferência arquitetural do usuário.

---

## Análise: Qual modelo?

### Opção 1: PURE DATA NODE ✓ ESCOLHIDA

**Conceito**: Getter sem efeitos colaterais. Lê valor, retorna. Sem flow control.

**Assinatura**:
```
Get Progress Bar Value

┌─────────────────────┐
│ Widget Name         │ (input string)
└─────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│ Get Progress Bar Value (Pure)       │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Value (output)      │ (output float)
└─────────────────────┘
```

**Portas**:
- Input: `widget_name` (STRING) - nome do widget
- Output: `value` (FLOAT) - valor ou None

**Sem**: `exec`, `exec_success`, `exec_not_found`, etc.

**Executor**: Nenhum (não é necessário)

**Evaluator**: Implementa lógica de busca (o que existe hoje)

**Comportamento**:
```python
def evaluate_get_progress_bar_value(...) -> float | None:
    widget_name = runtime._read_input(...)
    val = _fetch_progress_bar_value(runtime, widget_name, game)
    return val
```

**Uso no grafo**:
```
Variable widget_name ──┐
                      ▼
                Get Progress Bar Value
                      ▼
                    value
                      ▼
              Compare Number (75 > 50)
                      ▼
                    True/False
                      ▼
                  Branch on Boolean
```

**Vantagens**:
- ✓ Simples: apenas um output
- ✓ Puro: sem efeitos colaterais
- ✓ Compatível com dataflow avançado
- ✓ Semanticamente correto (é um getter)
- ✓ Sem confusão sobre flow vs data
- ✓ Alinhado com Blueprint UE4

**Desvantagens**:
- ✗ Sem tratamento explícito de "not found"
- ✗ Usuário decide o que fazer com None

---

### Opção 2: IMPURE NODE (Não Escolhida)

**Conceito**: Node com flow control. Requer acionamento via exec.

**Assinatura**:
```
Get Progress Bar Value (Flow)

       exec
        │
        ▼
┌─────────────────────┐
│ Widget Name         │
└─────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│ Get Progress Bar Value (Impure)      │
└──────────────────────────────────────┘
        ▼
     ┌──┴──┬──────────┐
     │     │          │
   success not_found failure
     │     │          │
```

**Portas**:
- Input: `exec` (EXEC), `widget_name` (STRING)
- Output: `exec_success`, `exec_not_found`, `exec_failure` (EXEC)
- Output: `value` (FLOAT)

**Problema com este modelo**:
```
Se houver edge entre eval_output e consumer:

Get Progress Bar Value.value
        ▼
    Compare Number
        │
        ├─► Conexão é dataflow, não flow
        │
        ✗ Mas consumer depende de "exec"
        ✓ ou "exec_success" para estar pronto?
```

**Confusão semântica**: `value` é output de dados, mas quando fica disponível?
- Se `execute_get_progress_bar_value` retorna ["exec_success"]
- Então `value` só existe após execução?
- Mas é uma porta de dados, deveria ser avaliável "sob demanda"

**Desvantagens**:
- ✗ Overcomplicated para getter simples
- ✗ Confusão entre flow e dataflow
- ✗ Requer executor (mais código)
- ✗ Possível dupla execução (bug existente)

---

## Decisão Final

### ✓ PURE DATA NODE

**Razão**: 
1. Getter simples não precisa flow control
2. Alinha com programação visual moderna (Blueprint)
3. Eliminaproblemas de timing/duplicação
4. Semanticamente correto

**Migração de existente**:
- Remover flow inputs (exec)
- Remover flow outputs (exec_success, exec_not_found, exec_failure)
- Manter apenas value output (FLOAT)
- Widget_name vira input de dados

**Contrato Canônico**:
```python
class GetProgressBarValueNode:
    __node_definition__ = NodeDefinition(
        id="get_progress_bar_value",
        title_key="Ler ProgressBar",
        category_key="UI/Data",
        description_key="Lê valor de uma ProgressBar. Retorna None se não encontrada.",
        
        inputs=[
            PinDefinition(
                id="widget_name",
                label_key="Nome ProgressBar",
                pin_type=PinType.STRING,
                default_value="progress",
            ),
        ],
        outputs=[
            PinDefinition(
                id="value",
                label_key="Valor",
                pin_type=PinType.FLOAT,
            ),
        ],
        pure=True,  # ← Marca como puro!
    )
```

**Executor**: Não registra executor (ou registra como no-op)

**Evaluator**: Mantém implementação atual (que funciona)

---

## Handling de Erros

Com PURE DATA NODE, o error handling muda:

### OLD (Flow-based)
```
exec
 ├─► exec_success ─► Next Node
 ├─► exec_not_found ─► Error Handler
 └─► exec_failure ─► Catch
```

### NEW (Pure data-based)
```
value: float | None
 ├─► None → Consumer node decide
 │   (pode usar "Is Valid" node)
 │
 └─► float → Compare Number, etc
```

**Consumer decide o que fazer com None**:
```
Get Progress Bar Value.value
        ▼
   Is Valid?
    ▼     ▼
  True   False ─► Use Default (50.0)
    │       │
    └───────┤
        ▼
    Compare Number
```

**Vantagem**: Explícito. Não há surpresas de flow.

---

## Testes para Validar Contrato

### Test 1: Pure Evaluator
```python
def test_get_progress_bar_pure_data():
    """Get value sem flow execution."""
    result = evaluate_get_progress_bar_value(
        runtime, "value", node, game, dt, set()
    )
    assert result == 75.0
```

### Test 2: Dataflow Chain
```python
Get ProgressBar Value.value ──► Compare Number
Result: True (75 > 50)
```

### Test 3: None Handling
```python
Get ProgressBar Value (widget not found)
Result: None
```

### Test 4: Dataflow without Flow
```python
Variable widget ──► Get ProgressBar Value
                          ▼
                         value
                          ▼
                     Display Text
(Nenhuma execução de flow, apenas dataflow)
```

---

## Implementação da Decisão

### Passo 1: Atualizar NodeDefinition
```python
# engine/logic/node_definitions/ui_nodes.py

GetProgressBarValueNode_def = NodeDefinition(
    id="get_progress_bar_value",
    title_key="Ler ProgressBar",
    category_key="UI/Data",
    inputs=[
        PinDefinition(id="widget_name", label_key="Nome", pin_type=PinType.STRING, default_value="progress"),
    ],
    outputs=[
        PinDefinition(id="value", label_key="Valor", pin_type=PinType.FLOAT),
    ],
    pure=True,
)
```

### Passo 2: Remover Flow do NODE_DEFINITIONS legado
```python
# engine/logic/node_definitions/__init__.py
NODE_DEFINITIONS["get_progress_bar_value"] = {
    "id": "get_progress_bar_value",
    "title": "Ler ProgressBar",
    "inputs": [("widget_name", "text")],  # Sem "in"!
    "outputs": [("value", "number")],  # Sem "next", sem "exec_*"!
}
```

### Passo 3: Manter Evaluator (funciona)
```python
@registry.register_evaluator('get_progress_bar_value')
def evaluate_get_progress_bar_value(...) -> Any:
    # Mantém implementação atual
    ...
```

### Passo 4: Remover Executor (ou no-op)
```python
# Opção A: Remover @register_executor
# Opção B: Registrar como no-op
@registry.register_executor('get_progress_bar_value')
def execute_get_progress_bar_value(...) -> list[str]:
    # Node puro não executa
    return []  # Nenhuma porta de saída
```

### Passo 5: Migrar Assets
```json
{
  "nodes": [{
    "id": "get_pb",
    "type": "get_progress_bar_value",
    "properties": {"widget_name": "comida"}
  }],
  "edges": [
    {
      "from_node": "event_update",
      "from_port": "next",
      "to_node": "compare_number",  // ← Não mais para get_pb!
      "to_port": "in",
      "kind": "flow"
    },
    {
      "from_node": "get_pb",
      "from_port": "value",         // ← Dataflow!
      "to_node": "compare_number",
      "to_port": "a",
      "kind": "data"                // ← Kind = data, não flow!
    }
  ]
}
```

---

## Verificação da Decisão

Checklist antes de implementar:

- ✓ Alinha com preferência arquitetural (PURE DATA)
- ✓ Elimina confusão de flow vs data
- ✓ Resolve o problema de dupla execução
- ✓ Comportamento é claro e testável
- ✓ Compatível com dataflow avançado
- ✓ Mantém evaluator correto
- ✓ Simplifica contrato

---

## Summary

**get_progress_bar_value é PURE DATA NODE.**

| Aspecto | Antes | Depois |
|---------|-------|--------|
| Inputs | exec, widget_name | widget_name |
| Outputs | next, exec_success, exec_not_found, exec_failure, value | value |
| Pure/Impure | Impure | Pure |
| Executor | Retorna ["next", "exec_success"] | Nenhum/No-op |
| Evaluator | Implementa lógica | Igual |
| Dataflow | Confuso (flow + data) | Claro (only data) |
| Erro handling | Flow branching | Consumer decide |

Próximo: Implementar esta decisão em Phase 3C.

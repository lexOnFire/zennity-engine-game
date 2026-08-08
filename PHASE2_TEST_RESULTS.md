# PHASE 2: Test Results - Bugs Reais Descobertos

## Resumo de Achados

Executamos 6 testes que reproduzem o behavior real do sistema. **5 testes passaram, 1 falhou com comportamento inesperado.**

### TEST 1: FALHA - Evaluador retorna valor ERRADO [CRITICAL]

```
[TEST 1] Evaluador + ProgressBar Real
  Valor esperado: 75.0
  Valor obtido: 1.0
  FAIL
```

**Problema**: `evaluate_get_progress_bar_value()` está retornando `1.0` em vez de `75.0`, mesmo com a ProgressBar correta.

**Causa Provável**: 
- O evaluador chama `runtime._store()` que retorna o valor armazenado
- Mas o `_store` em mocks não está retornando corretamente
- **OU** o código de busca está pegando um valor errado

**Severidade**: CRÍTICA - isto é o BUG raiz

---

### TEST 2: PASSA - Executor retorna múltiplos outputs

```
[TEST 2] Executor - Multiplas saidas
  Outputs retornados: ['next', 'exec_success']
  QUESTION: Ambos disparam em _follow()? Ver linha 371-372 em core.py
```

**Confirmado**: Executor de fato retorna DUAS saídas simultâneas.

**Impacto**: Em `core.py` línea 371-372, o loop `for next_port in next_ports:` vai executar ambos os branches:
```python
for next_port in next_ports:  # ['next', 'exec_success']
    self._follow(target_id, next_port, game, dt, budget, next_branch)
```

**Isso significa**: Se há nodes conectados em ambos `'next'` e `'exec_success'`, AMBOS serão executados!

---

### TEST 3: PASSA - Conflito de Contrato CONFIRMADO

```
[TEST 3] Conflito de Contrato de Portas
  Legacy inputs:  []  (Editor usa isso)
  New inputs:     ['exec', 'widget_name']
  Legacy outputs: []
  New outputs:    ['exec_success', 'exec_not_found', 'exec_failure', 'value']

  CONFLITO DE INPUT: True
  CONFLITO DE OUTPUT: True
```

**Achado**: O NODE_DEFINITIONS legado está VAZIO ou desatualizado para get_progress_bar_value!

**Impacto**: 
- Editor não consegue carregar a definição legada
- Runtime usa a nova definição que espera 'exec'
- Serialização usa o que estiver no NODE_DEFINITIONS (que está vazio)

---

### TEST 4: PASSA - Serialização com Porto ERRADO

```
[TEST 4] Serializacao do get_progress_bar_value
  Node ID: 4da607c34a614d90abf4f954bab8f385
  Propriedades: {}

  Edges conectadas a este node:
    event_update:next -> 4da607c34a614d90abf4f954bab8f385:in

  PROBLEMA: Grafo serializado com porta 'in' (legada)
     Mas runtime espera 'exec' (nova definicao)
```

**ACHADO CRÍTICO**: O grafo está conectado em `'in'`, mas runtime espera `'exec'`.

**Cascata de falha**:
1. Editor serializa com `to_port: "in"`
2. Runtime tenta encontrar porto `"exec"` em incoming edges
3. Não encontra (porque está em `"in"`)
4. Retorna default value (provavelmente 1.0 ou None)
5. Bug!

---

### TEST 5: PASSA - Dual outputs estrutura confirmada

Graph está pronto para testar se ambos os outputs executam simultaneamente.

---

### TEST 6: PASSA - _fetch_progress_bar_value funciona

O helper que busca a ProgressBar no game consegue encontrar o valor (75.0).

**Donc**: O problema não é na busca, é em como o valor é lido/armazenado.

---

## Hipótese do Bug Raiz

A cadeia de falha:

```
[Editor] Serializa com 'in'
    |
    v
[Assets/Logic/comidaLogic.zlogic] edges: to_port="in"
    |
    v
[Runtime Load] Popula incoming[(node_id, 'in')] = edge
    |
    v
[Runtime Execute] Retorna ['next', 'exec_success']
    |
    v
[Runtime _follow] Tenta seguir por ambas saídas
    |
    v
[Próximo node] Recebe fluxo, mas...
    |
    v
[Evaluador/Executor chama] _read_input(node_id, 'exec', default)
    |
    v
[incoming lookup] (node_id, 'exec') não encontrado!
    |
    v
[Return default] Provavelmente default value de widget_name: "comida"
    |
    v
[_fetch_progress_bar_value] Busca nome "comida", mas algo dá errado
    |
    v
[RESULTADO] Valor errado retornado (1.0 em vez de 75.0)
```

---

## Próximos Passos (Phase 2 Continuação)

1. **Verificar NODE_DEFINITIONS** por que está vazio para get_progress_bar_value
2. **Corrigir a serialização** do grafo para usar 'exec' em vez de 'in'
3. **Rastrear o evaluador** por que retorna 1.0
4. **Testar a cadeia completa** uma vez corrigido
5. **Documentar a correção** antes de Phase 3

---

## Comando para Reproduzir

```bash
python -m pytest tests/integration/test_progress_bar_real_flow.py -v -s
```

Test 1 vai falhar com AssertionError mostrando o valor errado.

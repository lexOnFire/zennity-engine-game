# PHASE 2: ROOT CAUSE ANALYSIS

## Bugs Descobertos (em ordem de severidade)

### BUG 1: PORT NAME MISMATCH (CRÍTICO)

**Problema**: Editor serializa node `get_progress_bar_value` com entrada `in`, mas runtime espera `exec`.

**Evidência** (TEST 4):
```
Edge no grafo: event_update:next -> get_progress_bar_value:in
Mas runtime tenta: runtime._read_input(node_id, "exec", ...)
Resultado: incoming[(node_id, "exec")] não encontrado!
```

**Cascata**:
1. Grafo conecta `"in"` (legacy)
2. Runtime procura `"exec"` (new)
3. Porta não encontrada → usa default value
4. Node não consegue ler a entrada corretamente

**Código afetado**:
- `engine/logic/node_definitions/__init__.py` - NODE_DEFINITIONS vazio para get_progress_bar_value
- `Assets/Logic/comidaLogic.zlogic` - serializado com "in" em vez de "exec"

---

### BUG 2: DUAL OUTPUT EXECUTION (PROBLEMA)

**Confirmado** (TEST 2 + código em core.py):

```python
# Linha 353 em dynamic_ui_nodes.py
return ["next", "exec_success"]  # Retorna AMBAS saídas

# Linha 371-372 em core.py
for next_port in next_ports:  # Itera AMBAS!
    self._follow(target_id, next_port, game, dt, budget, next_branch)
```

**Impacto**: Se há nodes conectados em AMBOS `"next"` E `"exec_success"`, ambos executarão simultaneamente!

**Questão**: É isto intencional para compatibilidade legada ou é um bug?

---

### BUG 3: NODE_DEFINITIONS DESATUALIZADO (CRÍTICO)

**Descoberta** (TEST 3):
```
Legacy NODE_DEFINITIONS inputs:  []  (Vazio!)
New definition inputs:    ['exec', 'widget_name']

NODE_DEFINITIONS para get_progress_bar_value = {}
```

**Problema**: Quando o editor tenta carregar o node, ele usa NODE_DEFINITIONS que está vazio.

**Arquivo**: `engine/logic/node_definitions/__init__.py` não popula `get_progress_bar_value`.

---

### BUG 4: PROGRESSBAR STORAGE LOCATION (DESCONHECIDO)

**Questão não respondida**: Onde exatamente a ProgressBar é armazenada em runtime?

**Investigação** (test_progress_bar_investigation.py):
- Scenario 1: ProgressBar object em runtime.variables → não funciona
- Scenario 2: Float value em runtime.variables → não funciona
- Scenario 3: Dict em game._world → não funciona
- **Scenario 4: Dict em game._world['UICanvas']['ui'] → FUNCIONA!**
- Scenario 5: Nenhum lugar → retorna 1.0 (MagicMock artifact)

**Descoberta**: ProgressBar deve estar em `game._world['UICanvas']['ui']['children'][...]` como dict!

**Implicação**: Quando é criada a ProgressBar no editor/UI Builder, ela precisa estar serializada nesta estrutura.

---

## Cadeia Completa de Falha

```
[1] Editor cria node get_progress_bar_value
  |
  +-> Procura NODE_DEFINITIONS["get_progress_bar_value"]
  |   (ENCONTRA: vazio {})
  |
  +-> Serializa com portas padrão: "in", "next"
  |   (DEVERIA USAR: "exec", "exec_success", etc)
  |
  v
[2] Runtime carrega grafo
  |
  +-> Popula incoming: (node_id, "in") -> edge
  |
  v
[3] Runtime executa event_update
  |
  +-> _follow() tenta seguir get_progress_bar_value com porta "next"
  |
  +-> Encontra edge: event_update:next -> get_progress_bar_value:in
  |
  +-> Executa execute_get_progress_bar_value()
  |   |
  |   +-> Retorna ["next", "exec_success"] (ambas!)
  |
  v
[4] Runtime _follow com ambas portas
  |
  +-> Tenta _follow por "next" -> OK
  +-> Tenta _follow por "exec_success" -> nenhum node conectado
  |
  v
[5] Se houver node conectado em "exec_success"
  |
  +-> Executa 2x (ambos "next" e "exec_success"!)
  |
  v
[6] get_progress_bar_value node tenta ler value
  |
  +-> Chama _read_input(node_id, "exec", ...)
  |
  +-> Procura incoming[(node_id, "exec")]
  |
  +-> NÃO ENCONTRA (está em "in", não "exec"!)
  |
  +-> Usa default value (provavelmente "comida" string)
  |
  v
[7] _fetch_progress_bar_value("comida")
  |
  +-> Procura em game._world estrutura
  |
  +-> Se ProgressBar não está em game._world['UICanvas']['ui']
      ENCONTRA 1.0 (via game.find() MagicMock)
  |
  v
[8] RESULTADO: Valor errado ou não encontrado
```

---

## Phase 2 Conclusão

**Problemas comprovados**:
1. ✓ NODE_DEFINITIONS desatualizado
2. ✓ Port name mismatch (in vs exec)
3. ✓ Dual output execution
4. ? ProgressBar storage location desconhecida

**Testes que falham**:
- test_evaluator_purity_real_progress_bar → Retorna valor errado

**Testes que passam mas alertam**:
- test_executor_multiple_outputs_simulation → Confirma dual outputs
- test_legacy_vs_new_contract_mismatch → Confirma conflicts
- test_serialization_graph_asset_path → Confirma "in" no grafo

**Próximos passos (Phase 3 - Arquitetura)**:
1. Corrigir NODE_DEFINITIONS para incluir get_progress_bar_value
2. Escolher entre:
   - Opção A: Mudar serialização do grafo de "in" para "exec"
   - Opção B: Adicionar compatibilidade de mapeamento "in" -> "exec"
3. Decidir: Executor deve retornar 1 ou múltiplas saídas?
4. Garantir ProgressBar está em local correto do game object

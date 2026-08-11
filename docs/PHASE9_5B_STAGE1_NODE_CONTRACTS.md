# Phase 9.5B Stage 1 — Node Contract Convergence

**Data:** 2026-08-10
**Objetivo:** eliminar a situação em que paleta, compilador, grafo serializado,
executor, avaliador e dispatcher podiam discordar sobre o contrato do MESMO nó.

**Meta atingida:** `ONE NODE ID → ONE DEFINITION → ONE PORT CONTRACT → ONE RUNTIME CONTRACT`

Stage 2 **não** foi iniciado.

---

## 1. Decisão arquitetural: porta de sucesso canônica

```
CANONICAL_SUCCESS_PORT = "next"
```

Registrada em `engine/logic/port_aliases.py`. Evidência medida:

| Sinal | Valor |
|---|---|
| arestas salvas usando `next` nos 56 `.zlogic` | **137** |
| arestas salvas usando `exec_done` | **0** |
| executores que já retornavam `["next"]` | 49 |
| default de `from_port` em `core.py` | `"next"` |

**A engine passou a ter exatamente um nome para "sucesso, continue": `next`.**

Isso não significa colapsar tudo. Nós com **desfechos genuinamente diferentes**
mantêm nomes semânticos, porque são ramos distintos e não sinônimos de sucesso:

```
next                      sucesso / continuação (único nome)
exec_failure              falha declarada
limit_reached             pool de spawn atingiu o limite
grounded / airborne       is_grounded
held / released           key_held
exec_pressed / exec_not_pressed   key_pressed
true / false              if_else, compare_number, compare_text
exec_hit / exec_no_hit    raycast
...                       (ver SEMANTIC_EXEC_PORTS)
```

Uma descoberta importante durante a execução: **as duas convenções estavam
vivas**, não uma legada e uma nova. Os executores já retornavam `exec_failure`
83 vezes e `exec_success` 19 vezes. Então a correção não foi "definição está
certa, runtime está errado" — foi canonizar **os dois lados**: 65 pinos de
saída renomeados nas definições e 19 `return` canonizados nos executores.

---

## 2. Política de aliases

Aliases são **ponte de migração, não fonte de verdade**. Todas as tabelas em
`engine/logic/port_aliases.py` são estritamente **uma via**, LEGADO → CANÔNICO,
e um invariante em tempo de import (`_assert_one_way`) garante que nenhum valor
de alias seja também chave — é isso que torna a normalização idempotente.

### 2.1 Aliases globais de porta exec

`exec_done`, `exec_success`, `exec`, `out`, `continue` → `next`

### 2.2 Aliases com escopo de nó

Não podem ser globais: `if_else` / `compare_number` / `compare_text` usam
`true`/`false` como portas **canônicas** e 23 arestas salvas dependem disso.

| Nó | Alias | Arestas salvas afetadas |
|---|---|---|
| `is_grounded` | `true`→`grounded`, `false`→`airborne` | 2 |
| `key_held` | `true`→`held`, `false`→`released` | 12 |
| `key_pressed` | `true`→`exec_pressed`, `false`→`exec_not_pressed` | 3 |

Aqui o **executor** foi corrigido (nomes de domínio são melhor UX), e o alias
preserva os 17 assets existentes.

### 2.3 Aliases de ID de nó

O runtime já agrupava as grafias num único `register_executor((...))`; o Stage 1
tornou isso explícito e deu entrada de paleta só ao id canônico.

| Canônico | Aliases | Por quê esse canônico |
|---|---|---|
| `scene.load_scene` | `load_scene`, `open_scene`, `scene_load`, `scene.load` | 5 usos em assets |
| `app.quit` | `exit_game`, `quit_game` | 1 uso em assets |
| `ui.button_clicked` | `button_clicked`, `on_ui_click` | 5 usos em assets |
| `ui.set_widget_enabled` | `set_ui_enabled` | 1 uso em assets |
| `set_variable` | `variables.set` | 18 usos do canônico |
| `load_game` / `has_save` | `game.load_game` / `game.has_save` | definição já existia |

**O autor não vê mais cinco nós "carregar cena" idênticos sem saber qual funciona.**

---

## 3. Onde a normalização acontece

```
asset legado (.zlogic)
        ↓
graph_normalizer.normalize_logic_graph()     ← ÚNICA vez, no LOAD
        ↓  ids de nó canônicos
        ↓  portas exec canônicas
grafo canônico → runtime só enxerga forma canônica
```

O alias de porta é aplicado **apenas a portas de execução**: um pino de dados
pode legitimamente se chamar `out` ou `value`, e dobrá-lo em `next` corromperia
arestas de dados. `_canonical_from_port` só reescreve quando a definição do nó
realmente declara o nome resolvido como saída de fluxo.

### Compatibilidade defensiva no runtime

`core._edge_matches_port` mantém um fallback de alias para grafos entregues ao
runtime **sem** passar pelo normalizador (testes unitários, payloads de
hot-reload, runtime exportado). Ele emite `DEBUG`:

```
Legacy port alias resolved at runtime: node=X type=key_held true -> held
  (graph was not normalised)
```

Isso permite **medir** o uso real antes de remover a camada de compatibilidade.
O caminho comum (match exato) é inline, então o fallback não custa nada por
frame — ver §8.

### Política de save

**Escolhida: normalizar no load, gravar canônico no próximo save.** Nenhum
asset em disco é reescrito automaticamente. Um asset legado carrega, roda e
permanece legado até o usuário salvá-lo, quando o normalizador já terá
convertido a forma em memória.

---

## 4. Split-brain do `play_animation` resolvido

Havia duas definições incompatíveis do mesmo id:

| | `actions_nodes` | `animation_nodes` |
|---|---|---|
| inputs | `exec`, **`state`** | `exec`, `target`, **`animation_name`**, `force` |
| outputs | `exec_done` | `exec_success`, `exec_failure` |

A paleta recebia a versão de `animation_nodes` (colheita reflexiva); o
`MetadataManager` recebia a de `actions_nodes` (registro explícito do provider);
e o executor lia o pino `state`.

**Evidência decisiva** — os 4 nós `play_animation` nos assets:

```
{'target': 'player', 'animation_name': 'idle', 'force': False, 'state': 'PlayerAttack'}
{'target': 'player', 'animation_name': 'idle', 'force': False, 'state': 'Run'}
{'target': 'player', 'animation_name': 'idle', 'force': False, 'state': 'Idle'}
{'target': 'player', 'animation_name': 'idle', 'force': False, 'state': 'Jump'}
```

`state` carrega os valores reais; `animation_name` é o default obsoleto `'idle'`
nos quatro. **Tornar `animation_name` canônico faria os 4 assets tocarem a
animação errada.**

Resolução: `animation_nodes` é o dono único (definição mais rica: `target` +
`force`), com o pino da animação renomeado para `state`. As duplicatas em
`actions_nodes` foram removidas e o `LogicProvider` foi religado.

Contrato final:
```
play_animation  IN  exec, target, state, force
                OUT next, exec_failure, animation
stop_animation  IN  exec, target
                OUT next, exec_failure, stopped
```

---

## 5. Detecção de conflitos ativada

`engine/logic/node_definitions/__init__.py` agora registra o módulo dono de cada
id e acumula conflitos. `assert_no_duplicate_definitions()` levanta
`DuplicateNodeDefinitionError`:

```
Duplicate NodeDefinition ids detected while building the catalogue:
  id='play_animation'
      module A: engine.logic.node_definitions.actions_nodes
      module B: engine.logic.node_definitions.animation_nodes
Exactly one module must own each node id --
ONE NODE ID -> ONE DEFINITION -> ONE PORT CONTRACT.
```

**Nunca mais last-write-wins silencioso.**

Chamado de `LogicProvider.boot()` via `engine/logic/boot_validation.py`:
duplicata = falha dura; violação de contrato = log ERROR; deprecado = WARNING.

---

## 6. Modelo de execução (fim da lista de exceções hardcoded)

`NodeDefinition.execution_model` (item 16):

| Modelo | Significado | Exemplos |
|---|---|---|
| `action` | executor roda e devolve portas exec | maioria |
| `event_source` | fluxo nasce aqui; o frame loop dirige, sem executor | `event_start`, `on_collision_enter` |
| `terminal` | fluxo para aqui por design; executor devolve `[]` | `restart_scene`, `subgraph_return`, `app.quit` |
| `pure_data` | sem portas exec; resolvido por avaliador | nós de math/logic, `get_position` |

Mais `dynamic_exec_prefixes` para nós que geram famílias de portas
(`sequence` → `then_0..then_N`).

O validador consulta o modelo em vez de uma lista de exceções que envelhece.

---

## 7. Contagens finais

```
                        BEFORE      AFTER
NODE DEFINITIONS           154        175    (+21)
EXECUTORS                  132        133    (+1, find_tag)
EVALUATORS                  64         64
PURE DATA NODES             20         36
FLOW NODES                 118        123

CONTRACT VIOLATIONS        167          0    (reais)
  EXEC_PORT_MISMATCH        45          0
  UNREACHABLE_EXEC_PORT     45          0
  NO_DEFINITION             33          0
  DATA_PORT_MISMATCH        24          0
  INPUT_PORT_MISMATCH       13          0
  NO_RUNTIME                 7          0

DUPLICATE NODE IDS           2          0
Duplicate executor IDs       0          0
Categorias >30 nós           0          0
```

**Allow-list restante: 2 avisos, ambos `DEPRECATED_NO_RUNTIME`.**

`animate_value` e `wait_until_condition` não têm executor nem avaliador, e
nenhum asset os usa. Implementá-los seria feature nova de gameplay
(explicitamente fora do escopo), então foram marcados `deprecated=True` e
ocultados da paleta — melhor que oferecer um nó que não faz nada.

### O que ganhou definição (33 → 0)

- **13 nós de math/logic/texto** — `add_number`, `subtract_number`,
  `multiply_number`, `divide_number`, `clamp_number`, `absolute_number`,
  `random_number`, `and`, `or`, `not`, `join_text`, `to_text`, `delta_time`.
  **Aritmética e lógica booleana eram inautoráveis visualmente** — a maior
  lacuna de autoria da auditoria 9.5A.
- **8 nós de cena/UI/objeto** — `scene.load_scene`, `app.quit`,
  `ui.button_clicked`, `ui.set_widget_enabled`, `get_position`,
  `get_object_name`, `subgraph_input`, `find_nearest_object`.
- **12 aliases** deixaram de contar como definição faltante.

---

## 8. Performance

Medição intercalada, 7 execuções por lado, mínimos (menos contaminados por ruído
de scheduler):

| Métrica | BEFORE | AFTER | Δ |
|---|---:|---:|---:|
| execução de grafo de 50 nós / frame | 121.4 µs | 119.1 µs | **−1.9 %** |
| execução de grafo de 200 nós / frame | 982.1 µs | 995.4 µs | **+1.3 %** |
| normalizar os 56 assets do projeto | 4.6 ms | 4.8 ms | **+4.9 %** |

**A execução por frame ficou inalterada dentro do ruído (±2 %).** O custo foi
para o *load* — que é exatamente o desenho: resolver alias uma vez ao carregar,
nunca por travessia de aresta.

O primeiro corte custava +3–4 % por frame porque `_edge_matches_port` era uma
chamada de método por aresta. O caminho comum foi colocado inline; o método só
roda quando o match exato falha.

---

## 9. Direção de namespace (documentada, não migrada)

A grafia pontuada já é a forma viva nos assets, e é a direção recomendada:

```
event.start      input.key_pressed   math.add        logic.and
physics.raycast  animation.play      ui.set_text     scene.load
game.save
```

**Stage 1 canonizou apenas onde os assets já usavam a forma pontuada**
(`scene.load_scene`, `app.quit`, `ui.button_clicked`, `ui.set_widget_enabled`).
Migrar `add_number` → `math.add` exigiria tocar o dispatcher e reescrever
assets; **fica para depois**, e a regra vale desde já para nós novos: **um id
canônico por operação**, nunca `add_number` + `math.add` + `number_add`
coexistindo.

---

## 10. Legado: classificação

| Item | Ação tomada |
|---|---|
| `exec_done` / `exec_success` / `exec` / `out` / `continue` | **MIGRADO** para `next`; alias mantido no load |
| `true`/`false` em `is_grounded`/`key_held`/`key_pressed` | **MIGRADO** para nomes de domínio; alias por nó |
| 4 grafias extras de "load scene" | **DEPRECADO** — alias de runtime, sem entrada na paleta |
| 2 grafias extras de "quit" | **DEPRECADO** — idem |
| 2 grafias extras de "UI click" | **DEPRECADO** — idem |
| `variables.set`, `game.load_game`, `game.has_save` | **DEPRECADO** — idem |
| `animate_value`, `wait_until_condition` | **DEPRECADO** — sem runtime, ocultos da paleta |
| `PlayAnimationNode`/`StopAnimationNode` em `actions_nodes` | **REMOVIDO** — duplicata |
| `_out` suffix (`slot_name_out`, `current_zoom`, `machine_id_out`, ...) | **REMOVIDO** — renome nunca propagado ao runtime |

Portas com sufixo `_out`: um renome foi aplicado às definições em algum momento
e nunca propagado ao runtime, deixando o pino declarado **permanentemente
vazio** (`runtime.values` é indexado pelo nome que o executor grava). Nenhum
asset lia esses nomes — verificado nos 56 arquivos.

---

## 11. Bug do `sequence`: falso positivo corrigido

O relatório 9.5A apontou `sequence` retornando o literal `"then_{index}"`.
**Isso estava errado.** O código sempre usou f-string corretamente:

```python
return [f"then_{index}" for index in range(outputs)] + ["next"]
```

Duas limitações da minha ferramenta de auditoria produziram o falso positivo:
o extrator tratava o texto-fonte da f-string como literal, e `RETURN_RE` parava
no primeiro `]`, escondendo o `+ ["next"]`. **A ferramenta foi corrigida, o nó
não** — ele nunca esteve quebrado.

O contrato real de `sequence` é uma *família* de portas, agora declarada via
`dynamic_exec_prefixes=("then_",)`. Assets usam até `then_3`.

---

## 12. Bridge de diálogo corrigido

`engine/dialogue/manager.py` chamava `LogicEventBus.get_instance()` — método que
nunca existiu. Todo evento de diálogo levantava `AttributeError` num handler
amplo que só fazia `print()`.

**Nenhum event bus novo foi criado.** O `LogicEventBus` é criado por sessão de
Play em `ViewportRuntimeInitializer._create_logic_services` e agora é injetado:

```python
get_dialogue_manager().bind_event_bus(self.logic_event_bus)
```

`reset()` solta o bus, para que um bus obsoleto não vaze para o próximo Play.
`tests/diagnostics/test_dialogue_dead_bridge.py` deixou de afirmar que o defeito
existe e passou a exigir que o evento **chegue** ao grafo, com isolamento por
owner.

---

## 13. Quarta fonte de verdade encontrada

Durante a regressão apareceu `NODE_PORT_DEFINITIONS` em
`engine/logic/graph_asset.py` — uma tabela de portas mantida à mão, usada pelo
validador do editor, **independente** das outras três. Os três nós de branch
recontratados foram sincronizados nela.

**Isso é dívida de Stage 2:** o objetivo "uma definição por nó" ainda tem essa
tabela paralela. Stage 1 a alinhou onde precisava; unificá-la pertence à
unificação de registries.

---

## 14. Testes

| Arquivo | Testes | Cobre |
|---|---:|---|
| `tests/logic/test_node_contracts.py` | 16 | as 6 classes de violação em zero, allow-list só encolhe, API do validador |
| `tests/logic/test_port_normalization.py` | 20 | tabela uma-via, idempotência, escopo de nó, dados não corrompidos, execução ponta a ponta |
| `tests/logic/test_node_definition_conflicts.py` | 7 | duplicata falha alto, split-brain resolvido, boot limpo |
| `tests/logic/test_current_palette_runtime_contract.py` | 28 | pinos da paleta = pinos do runtime, aliases não vazam |
| `tests/integration/test_new_graph_flow_contract.py` | 12 | **grafo novo da paleta atual executa** |
| `tests/integration/test_legacy_graph_compatibility.py` | 225 | **os 56 assets carregam, normalizam, constroem runtime, nenhuma aresta órfã** |
| `tests/diagnostics/test_dialogue_dead_bridge.py` | 8 | bridge de diálogo funciona |

**Total Stage 1: 316 testes, 0 falhas.**

### Gate de CI

```bash
python scripts/audit_node_system.py --ci
```

Sai com código ≠ 0 em: registro duplicado de executor/avaliador,
`EXEC_PORT_MISMATCH`, `UNREACHABLE_EXEC_PORT`, `NO_DEFINITION`,
`DATA_PORT_MISMATCH`, `INPUT_PORT_MISMATCH`, `NO_RUNTIME`,
`PURE_DATA_HAS_EXEC`, `TERMINAL_HAS_EXEC`, `TERMINAL_RETURNS_EXEC`,
`ALIAS_WITHOUT_TARGET`.

Saída atual:
```
CI GATE: PASS — 0 hard violations, 2 warning(s)
  (warning) [DEPRECATED_NO_RUNTIME] animate_value
  (warning) [DEPRECATED_NO_RUNTIME] wait_until_condition
```

---

## 15. Regressão

Worktree em `HEAD` (pré-Stage-0 e pré-Stage-1), mesmas suítes dos subsistemas
nomeados no briefing:

```
BEFORE: 1087 testes, 1065 passaram, 21 falharam, 1 skip
AFTER : 1158 testes, 1136 passaram, 21 falharam, 1 skip

NOVAS falhas do Stage 1: 0
CORRIGIDAS pelo Stage 1:  0
Pré-existentes mantidas: 21
```

O baseline é pré-Stage-0 **e** pré-Stage-1. Como o Stage 0 já demonstrou zero
regressões contra o mesmo ponto, qualquer falha nova aqui seria do Stage 1 —
não houve nenhuma.

Duas regressões **foram** introduzidas durante o trabalho e corrigidas antes do
fim: um template guiado e o catálogo de receitas quebraram quando os nós de
branch mudaram de porta, porque `NODE_PORT_DEFINITIONS` (§13) ainda tinha os
nomes antigos.

**Nenhuma das 21 falhas pré-existentes desapareceu.** As 9 em
`test_logic_graph_asset` são de contratos de recipes/templates que o Stage 1
não tocou, não do split `next`/`exec_done`.

---

## 16. Bug pré-existente de asset exposto (não causado pelo Stage 1)

`get_position` tem avaliador sensível à porta: `port == "x"` devolve `target.x`,
qualquer outra coisa devolve `target.y`. Logo `position` **sempre** devolveu Y.

`EnemyAILogic.zlogic` liga `get_position.position` em `vector2.x` **e**
`vector2.y` ao mesmo tempo, e em `distance_to_point.point_a`/`point_b`, que
esperam pontos. O asset já estava semanticamente quebrado.

O Stage 1 **não alterou o avaliador**. Antes não havia definição de
`get_position`, então nada podia detectar o problema; declarar o contrato real
(`x`, `y`) tornou-o visível. Está numa allow-list explícita em
`test_legacy_graph_compatibility.py`, que só pode encolher. **Corrigir o asset é
trabalho de autoria, para Stage 2.**

---

*Stage 1 concluído. Stage 2 NÃO iniciado.*

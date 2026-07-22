# Zennity Engine — Roadmap de conclusão arquitetural pré-v1.0

Atualizado em 21 de julho de 2026.

## Estado atual

O baseline arquitetural do PR #12 já entregou a separação dos principais controllers do editor, composition root, lifecycle da Viewport, Play Mode determinístico, `SceneDocument`, serialização consolidada, scheduler de lifecycle, broad phase espacial da física, caches de renderização, invalidation/dirty flags, Asset Browser, Console e remoção dos patches dinâmicos prioritários.

O editor oficial está funcional e a matriz de CI passa em Linux/Python 3.10–3.12 e Windows/Python 3.12. A suíte atual possui 2.149 testes aprovados e 2 ignorados.

Ainda não é recomendável declarar a v1.0 enquanto os hotspots abaixo permanecerem sem fronteiras menores e sem budgets automatizados.

## Métricas restantes do baseline

| Hotspot | Tamanho atual | Meta pré-v1.0 |
|---|---:|---:|
| `LogicGraphEditor` | 1.879 linhas | nenhum controller/view acima de 500 |
| `LogicGraphRuntime` | 1.346 linhas | executor dividido por domínio; métodos abaixo de 100 |
| `InterfaceSmokeTest` | 1.241 linhas | builders independentes; métodos abaixo de 100 |
| `_build_docks()` | 884 linhas | builders por painel abaixo de 100 |
| `AnimationWorkspaceOperations` | 660 linhas | serviços separados por persistência, preview e binding |
| `run_viewport()` | 461 linhas | bootstrap/orquestração abaixo de 150 |
| `_execute()` do Logic Runtime | 444 linhas | registry de executores; handlers abaixo de 60 |
| `IsolatedEditorWindow` | 499 linhas de classe | camada visual abaixo de 400 |

## Roadmap priorizado

### Bloco 1 — Fechar a fronteira do editor oficial

- [ ] Remover adaptadores triviais restantes de `IsolatedEditorWindow` quando os sinais puderem apontar diretamente aos controllers.
- [ ] Extrair `_build_center()` e `_build_docks()` para builders de Scene/Game View, Inspector, Hierarchy, Assets, Console, Logic e Animation.
- [ ] Dividir `AnimationWorkspaceOperations` em persistência `.zanim`, biblioteca, preview/binding e eventos.
- [ ] Manter `IsolatedEditorWindow` abaixo de 400 linhas e cada builder abaixo de 100 linhas.
- [ ] Adicionar testes de composição e desconexão dos sinais para impedir registros duplicados.

### Bloco 2 — Decompor Logic Graph Editor e Runtime

- [ ] Separar `LogicGraphEditor` em canvas, palette, properties, diagnostics e command/history controllers.
- [ ] Substituir a cadeia central de `_execute()` por registry tipado de executores de nós.
- [ ] Separar avaliação de valores, ações, movimento, prefab, componentes e fluxo assíncrono.
- [ ] Preservar ordem determinística, cooldown, once e rastreamento de execução.
- [ ] Criar testes de paridade entre o executor antigo caracterizado e os novos handlers.

### Bloco 3 — Concluir a extração da Viewport

- [ ] Reduzir `run_viewport()` a bootstrap e loop principal abaixo de 150 linhas.
- [ ] Extrair criação da sessão, roteamento de comandos, sincronização de cena e teardown.
- [ ] Garantir que timers, filas, áudio, scripts, texturas e superfícies sejam liberados no Stop/Close.
- [ ] Adicionar soak test de Play/Stop e Hot Reload com contagem estável de objetos e threads.

### Bloco 4 — Consolidar superfícies duplicadas e legado

- [ ] Definir política explícita para `phase1_editor`, `premium_editor`, `windows/main_window` e `editor_legacy`.
- [ ] Migrar consumidores ainda ativos para o entrypoint oficial e marcar APIs antigas como deprecated.
- [ ] Remover duplicações somente após telemetria/testes confirmarem ausência de consumidores.
- [ ] Resolver imports circulares remanescentes e adicionar verificação automática no CI.
- [ ] Consolidar definitivamente `Assets/` como casing canônico, mantendo migração segura para `assets/`.

### Bloco 5 — Performance, memória e release gate

- [ ] Registrar budgets de frame para Editor idle, Scene View, Game View, Logic Graph e Animation Preview.
- [ ] Medir draw calls, repaints, invalidations, tamanho dos caches e alocações por frame.
- [ ] Adicionar testes de regressão para dirty flags, batching, buffers e caches LRU.
- [ ] Executar profiling de memória em ciclos de abrir/fechar cena, Play/Stop e Hot Reload.
- [ ] Elevar cobertura das fronteiras críticas para pelo menos 70% e manter a suíte multiplataforma verde.
- [ ] Produzir relatório final de compatibilidade, migração e riscos aceitos da v1.0.

### Checkpoint final de auditoria

- [x] Gate de cobertura crítica com mínimo agregado de 70%.
- [x] Baseline focado medido em 76%.
- [x] Auditoria final de classes, métodos, imports e lifecycle publicada em
  `PRE_V1_FINAL_AUDIT.md`.
- [ ] Decompor as violações estruturais bloqueantes registradas na auditoria
  antes de promover a branch para v1.0.

## Sequência de entrega

1. Bloco 1: shell e builders do editor.
2. Bloco 2: Logic Graph Editor/Runtime.
3. Bloco 3: Viewport e recursos de sessão.
4. Bloco 4: legado, duplicações e imports.
5. Bloco 5: budgets, profiling e release gate.

Cada item deve ser entregue isoladamente, com teste de caracterização antes da mudança, métrica antes/depois e toda a matriz de CI aprovada.

## Definition of Done da arquitetura pré-v1.0

- Nenhuma classe de produção do caminho oficial acima de 500 linhas.
- Nenhum método do caminho oficial acima de 100 linhas, salvo exceção documentada e medida.
- Nenhum monkey patch aplicado durante import ou inicialização.
- Um único entrypoint, Play Mode, Scene model, serializer e lifecycle oficiais.
- Nenhum repaint, rebuild de árvore ou alocação de buffer por frame sem invalidation demonstrável.
- Play/Stop, Hot Reload e fechamento sem crescimento persistente de processos, threads, timers ou caches.
- CI verde em Python 3.10, 3.11, 3.12 e Windows 3.12.
- Roadmap, documentação de migração e riscos residuais atualizados.

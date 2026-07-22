# Zennity Engine — Auditoria técnica completa da RC2 pós-merge

Data: 22 de julho de 2026  
Branch-base auditada: `release/v1.0.0-rc2`  
Commit-base: `e8a099c93e619aadf64e8ae2247b13aa11067d9d`  
Branch do relatório: `audit/rc2-post-merge`

## 1. Resultado executivo

A RC2 está funcional, testável e significativamente mais segura do que o baseline anterior. O merge do PR #12 consolidou o composition root, controllers do editor, lifecycle da viewport, Play/Stop isolado, SceneDocument lossless, Asset Database, broad phase espacial, budgets de performance/memória e gates multiplataforma.

A matriz de CI pós-limpeza está verde em seis jobs: Ruff, Linux Python 3.10, 3.11 e 3.12, Windows Python 3.12 e cobertura crítica mínima de 70%.

Mesmo assim, a RC2 ainda não deve ser promovida diretamente para `main` como v1.0 final. O risco principal deixou de ser falha funcional imediata e passou a ser concentração estrutural: classes grandes, métodos longos, superfícies legadas ainda importáveis, duplicação de caminhos do editor e limites de performance ainda pouco observáveis em execução real.

**Decisão:** RC2 aprovada como base de estabilização; promoção para v1.0 condicionada ao fechamento dos bloqueios P0 e P1 deste relatório.

## 2. Escopo e método

A auditoria consolidou:

- estado do PR #12 após o merge;
- workflow `Python Tests` e seus seis jobs;
- auditoria AST pré-v1 já incorporada ao repositório;
- roadmap de conclusão arquitetural;
- fronteiras oficiais de Editor, Runtime, Scene, Serialization, Logic, Physics, Renderer/UI, Assets, Input e Scripts;
- riscos de compatibilidade entre superfícies modernas e legadas.

Esta é uma auditoria estática e de CI. Medições de frame time, draw calls, repaints e heap nativo precisam ser executadas localmente com o editor real, pois o CI headless não substitui profiling interativo.

## 3. Estado dos gates

| Gate | Estado | Observação |
|---|---|---|
| Ruff crítico | Aprovado | E9, F63, F7 e F82 |
| Linux Python 3.10 | Aprovado | suíte completa |
| Linux Python 3.11 | Aprovado | suíte completa |
| Linux Python 3.12 | Aprovado | suíte completa |
| Windows Python 3.12 | Aprovado | suíte completa |
| Cobertura crítica | Aprovado | mínimo obrigatório de 70% |
| Ciclos de import do runtime | Aprovado | gate existente não detecta ciclos críticos |
| Play/Stop e lifecycle | Aprovado | testes determinísticos e soak tests existentes |
| Promoção para v1.0 | Bloqueada | hotspots estruturais e legado |

## 4. Achados prioritários

### P0 — Bloqueios de promoção

#### P0.1 Classes oficiais acima do orçamento

Persistem cinco classes acima de 500 linhas na auditoria AST consolidada:

- `editor.phase1_editor.ZennityPhase1Editor`: 809 linhas;
- `engine.logic.runtime.core.LogicGraphRuntime`: 788 linhas de classe;
- `editor.widgets.phase1_viewport.Phase1ViewportWidget`: 762 linhas;
- `editor.windows.main_window.MainWindow`: 600 linhas;
- `editor.widgets.viewport_widget.ViewportWidget`: 585 linhas.

Impacto: alto blast radius, dificuldade de teste unitário, maior chance de regressão em mudanças pequenas e acoplamento implícito entre UI, estado e serviços.

Ação: decompor por responsabilidade, preservando testes de caracterização. Não realizar refatoração cosmética; cada extração deve reduzir tamanho, dependências diretas ou custo de teste.

#### P0.2 Métodos acima de 100 linhas

Ainda existem métodos oficiais entre 102 e 328 linhas, especialmente em montagem visual, validação/normalização de grafo, exportação e compatibilidade.

Impacto: caminhos com muitas ramificações, baixa observabilidade de falhas e testes excessivamente amplos.

Ação: extrair builders, validators e adapters por contrato. Meta: nenhum método oficial acima de 100 linhas, salvo exceção documentada com complexidade e benchmark.

#### P0.3 Duas gerações de editor continuam coexistindo

`phase1_editor`, `premium_editor`, `windows/main_window`, `ViewportWidget` e `editor_legacy` ainda representam superfícies sobrepostas ou importáveis.

Impacto: correções podem ser aplicadas no caminho errado; consumidores externos podem continuar presos a APIs antigas; aumenta o custo de suporte e de migração.

Ação: publicar matriz de depreciação, telemetria de imports e remoção em etapas. O entrypoint oficial deve continuar sendo único.

### P1 — Riscos altos

#### P1.1 Logic Graph ainda é o maior hotspot técnico

O arquivo do editor de grafo permanece muito grande e o runtime ainda concentra orquestração, avaliação e execução. Embora handlers tenham sido extraídos e limitados, a classe central continua acima do budget.

Riscos:

- regressões de determinismo;
- duplicação entre resolução de valores e execução de ações;
- crescimento de condicionais por tipo de nó;
- dificuldade de instrumentar cada domínio.

Ação: separar canvas, palette, properties, diagnostics e history; no runtime, manter registry tipado por domínio e testes de paridade determinística.

#### P1.2 Viewport ainda concentra bootstrap e compatibilidade

A viewport já possui sessions, command queues, event routers e systems, porém as classes de compatibilidade continuam grandes.

Riscos:

- atualização duplicada por frame;
- eventos processados em mais de uma camada;
- teardown incompleto em caminhos excepcionais;
- regressão de drag, seleção, gizmos ou Play Mode.

Ação: reduzir o caminho oficial a bootstrap, loop e composição. Toda atualização deve ter um único owner.

#### P1.3 Performance real ainda não possui telemetria suficiente

Existem budgets e testes de memória, dirty flags, cache e Spatial Hash, mas faltam métricas persistentes do editor interativo.

Métricas obrigatórias:

- frame time p50/p95/p99;
- repaints por painel;
- invalidations por frame;
- draw calls e blits;
- superfícies/texturas criadas e descartadas;
- tamanho dos caches LRU;
- tempo de Scene View, Game View, Logic Graph e Animation Preview;
- crescimento de memória em abrir/fechar cenas e Hot Reload.

Ação: criar overlay de diagnóstico e benchmark reproduzível antes da v1.0.

#### P1.4 Cobertura global continua baixa em comparação ao gate focado

O gate crítico é saudável, mas mede fronteiras determinísticas selecionadas. Ele não deve ser interpretado como cobertura global da engine.

Risco: módulos UI, integração, exportadores e caminhos legados podem permanecer pouco exercitados.

Ação: manter o gate crítico e adicionar budgets incrementais por módulo, sem elevar arbitrariamente um número global que incentive testes superficiais.

### P2 — Dívida controlada

#### P2.1 TODOs e implementações parciais fora do caminho crítico

Há marcadores de trabalho pendente em componentes antigos, documentação, UI e legado. Eles não bloqueiam a RC2 enquanto não forem alcançados pelo entrypoint oficial, mas precisam ser classificados.

Ação: converter TODOs ativos em issues; remover comentários obsoletos; marcar explicitamente código experimental.

#### P2.2 Assets e casing

`Assets/` está definido como raiz canônica, com compatibilidade para projetos antigos. O histórico de `Assets/` versus `assets/` demonstra risco real em Windows/Linux.

Ação: manter teste de casing no CI, migrador explícito e proibir novos caminhos minúsculos na raiz.

#### P2.3 Metadados de assets

A adição de `guid` junto de `uuid` melhora compatibilidade, mas aumenta o contrato de persistência.

Ação: documentar precedência, invariantes, migração e comportamento quando os dois valores divergem.

## 5. Auditoria por módulo

### Editor

**Responsabilidade:** composição da aplicação, janelas, workspaces, controllers, commands e integração com a viewport.

**Dependências:** PySide6, runtime da viewport, SceneDocument, Asset Database, serializers e serviços de projeto.

**Acoplamento:** médio/alto no shell oficial e baixo/médio nos controllers extraídos.

**Coesão:** melhorou significativamente; ainda prejudicada nas classes grandes e adapters de compatibilidade.

**Complexidade:** alta em montagem de docks, workspaces, lógica de comandos e entrypoints antigos.

**Bugs prováveis:** sinais duplicados, estado divergente entre controllers, fechamento parcial de recursos e execução pelo entrypoint errado.

**Escalabilidade:** boa após concluir builders independentes e política de extensão por plugins/controllers.

**Performance:** risco de rebuild/repaint de painel sem invalidation.

**Prioridade:** P0.

### Runtime

**Responsabilidade:** lifecycle, scripts, world, execução em Play Mode e teardown.

**Dependências:** Scene, Physics, Logic, Audio, Input e renderização.

**Acoplamento:** médio; scheduler e world reduziram dependências implícitas.

**Coesão:** boa nas novas fronteiras; compatibilidade ainda espalhada.

**Complexidade:** média/alta nos caminhos de inicialização e script hot reload.

**Bugs prováveis:** ordem de lifecycle, scripts executados após destruição, recursos retidos após Stop e exceções que interrompem teardown.

**Escalabilidade:** boa se a ordem do lifecycle permanecer formal e testada.

**Performance:** deve evitar reflexão/import dinâmico por frame.

**Prioridade:** P1.

### Scene e Serialization

**Responsabilidade:** modelo persistente, leitura/escrita, compatibilidade e preservação lossless.

**Dependências:** componentes, assets, prefabs e runtime.

**Acoplamento:** baixo/médio após `SceneDocument`.

**Coesão:** alta.

**Complexidade:** média na normalização e migração de formatos.

**Bugs prováveis:** divergência entre documento e objetos vivos, perda de campos desconhecidos em caminhos legados, IDs duplicados e escrita interrompida.

**Escalabilidade:** boa com versionamento explícito e migrations puras.

**Performance:** serialização não deve ocorrer no loop de frame; autosave precisa de debounce.

**Prioridade:** P1.

### Assets

**Responsabilidade:** descoberta, metadados, GUID/UUID, importers, cache e resolução de caminhos.

**Dependências:** filesystem, serializers, editor e runtime.

**Acoplamento:** médio.

**Coesão:** boa na Asset Database; legado de caminhos ainda amplia a superfície.

**Complexidade:** média/alta em migração, reimport e dependências.

**Bugs prováveis:** casing, metadado órfão, GUID divergente, reimport em loop e cache obsoleto.

**Escalabilidade:** boa se dependências forem indexadas e eventos de filesystem forem agrupados.

**Performance:** scans completos devem ser substituídos por atualização incremental.

**Prioridade:** P1.

### Physics

**Responsabilidade:** colisões, broad phase, tilemap e resolução.

**Dependências:** transform, scene/runtime e componentes.

**Acoplamento:** baixo/médio.

**Coesão:** boa após Spatial Hash.

**Complexidade:** média, concentrada em collider e tilemap.

**Bugs prováveis:** collider fora de sincronia com rotação/escala, pares duplicados, tunneling e células espaciais obsoletas.

**Escalabilidade:** adequada para 2D; 3D futuro deve ser outro backend, não extensão direta das estruturas atuais.

**Performance:** acompanhar pares candidatos, ocupação por célula e custo de rebuild.

**Prioridade:** P1.

### Renderer e UI Runtime

**Responsabilidade:** desenho, cache de sprites/superfícies, overlays e componentes UI.

**Dependências:** Pygame, scene, assets e viewport.

**Acoplamento:** médio.

**Coesão:** média; patches históricos indicam evolução incremental.

**Complexidade:** alta nos caminhos que misturam seleção, gizmos, sprites e overlays.

**Bugs prováveis:** cache inválido, bordas/overlays duplicados, alocação de Surface por frame e diferenças entre editor e Play Mode.

**Escalabilidade:** limitada sem render graph/batching formal; suficiente para a v1 2D se os budgets forem cumpridos.

**Performance:** área mais sensível; medir blits, surfaces, conversões, escalas e rotações.

**Prioridade:** P0/P1.

### Logic Graph

**Responsabilidade:** edição visual, persistência, validação e execução determinística de nós.

**Dependências:** scene, runtime, components, prefabs e editor.

**Acoplamento:** alto na classe central; menor nos handlers extraídos.

**Coesão:** média.

**Complexidade:** muito alta.

**Bugs prováveis:** ordem diferente entre execuções, loops, cooldown/once inconsistentes, valores não tipados e estado residual entre sessões.

**Escalabilidade:** boa somente após concluir registry tipado, domínios separados e contratos de nó.

**Performance:** instrumentar nós por frame, tempo por handler e grafos ativos.

**Prioridade:** P0.

### Animation

**Responsabilidade:** clips, animator controllers, eventos, preview, binding e persistência `.zanim`.

**Dependências:** assets, scene, runtime e editor.

**Acoplamento:** médio/alto no workspace operations.

**Coesão:** média; operações ainda concentram responsabilidades.

**Complexidade:** alta em preview e sincronização com objetos.

**Bugs prováveis:** preview alterando cena persistente, eventos disparados duas vezes, recursos não liberados e divergência de tempo entre editor/runtime.

**Escalabilidade:** boa após separar persistence, library, preview/binding e event services.

**Performance:** preview deve atualizar somente quando ativo/visível.

**Prioridade:** P1.

### Input

**Responsabilidade:** estado de teclado/mouse e comandos editor/runtime.

**Dependências:** Pygame/PySide e viewport.

**Acoplamento:** médio nos adapters.

**Coesão:** aceitável.

**Complexidade:** média devido a duas pilhas de eventos.

**Bugs prováveis:** evento consumido duas vezes, foco incorreto, atalhos ativos durante edição de texto e estado preso após troca de modo.

**Escalabilidade:** boa com mapa de ações e contexts explícitos.

**Performance:** polling deve ocorrer uma vez por frame e ser compartilhado.

**Prioridade:** P1.

### Scripts

**Responsabilidade:** descoberta, import, lifecycle, API de jogo e hot reload.

**Dependências:** runtime, scene, input, physics e assets.

**Acoplamento:** médio/alto pela natureza extensível.

**Coesão:** média.

**Complexidade:** alta em reload, isolamento de erros e compatibilidade de templates.

**Bugs prováveis:** módulos duplicados no `sys.modules`, referências antigas após reload, execução em Edit Mode e falha de um script interrompendo os demais.

**Escalabilidade:** exige sandbox de lifecycle, contratos estáveis e diagnóstico por script.

**Performance:** não procurar/importar scripts por frame; cachear resolução e invalidar por mudança.

**Prioridade:** P1.

### Build e Export

**Responsabilidade:** validar projeto, copiar dependências e gerar distribuição executável.

**Dependências:** assets, scene, scripts, configurações e filesystem.

**Acoplamento:** médio.

**Coesão:** boa nos novos validator/exporter; métodos longos ainda são risco.

**Complexidade:** alta devido a plataformas e arquivos opcionais.

**Bugs prováveis:** dependência ausente, path absoluto, casing, asset não referenciado e diferenças Windows/Linux.

**Escalabilidade:** boa com pipeline em etapas e relatório estruturado.

**Performance:** não crítica em frame; priorizar determinismo e incrementalidade.

**Prioridade:** P1.

## 6. Gargalos prováveis por frame

Os seguintes pontos precisam de medição explícita:

1. reconstrução de árvores de Hierarchy/Inspector sem mudança de seleção;
2. atualização de Animation Preview quando painel está oculto;
3. execução de handlers de Logic Graph sem grafo ativo;
4. conversão, escala ou rotação repetida de sprites;
5. criação de superfícies temporárias para overlays e gizmos;
6. scans de assets durante eventos frequentes de filesystem;
7. sincronização completa da cena em vez de deltas;
8. polling duplicado de input entre Qt e Pygame;
9. atualização de física para objetos estáticos;
10. renderização de painéis não visíveis.

## 7. Riscos de memória

1. referências de signals/slots impedindo coleta de controllers;
2. caches de Surface/textura sem limite por bytes;
3. módulos antigos preservados após hot reload;
4. closures e callbacks mantendo cenas anteriores;
5. filas de comandos/eventos não drenadas no Stop;
6. snapshots de undo/redo sem budget;
7. previews e thumbnails retidos após trocar de projeto;
8. áudio e canais não liberados;
9. metadados duplicados na Asset Database;
10. object pools sem métricas de uso real.

## 8. Plano seguro de execução

### Bloco A — Fechar shell e builders do editor

Meta mensurável:

- classes oficiais abaixo de 500 linhas;
- builders abaixo de 100 linhas;
- zero conexões duplicadas de sinais;
- nenhum comportamento funcional alterado.

### Bloco B — Decompor Logic Graph

Meta mensurável:

- runtime central abaixo de 500 linhas;
- handlers abaixo de 60 linhas;
- paridade determinística completa;
- tempo por nó observável.

### Bloco C — Consolidar Viewport

Meta mensurável:

- um owner por update system;
- bootstrap/loop abaixo de 150 linhas;
- zero crescimento após 500 ciclos Play/Stop;
- caches e filas zerados no teardown.

### Bloco D — Legado e casing

Meta mensurável:

- entrypoints antigos deprecated e testados;
- imports oficiais documentados;
- nenhuma nova ocorrência de raiz `assets/`;
- plano de remoção por versão.

### Bloco E — Performance e release gate

Meta mensurável:

- benchmarks p50/p95/p99 versionados;
- budgets de repaint, invalidation, cache e memória;
- relatório Windows real Editor → Play → Stop → Export;
- CI completamente verde.

## 9. Critérios para promoção a `main`

A promoção da RC2 somente deve ocorrer quando:

- não houver classe oficial acima de 500 linhas;
- não houver método oficial acima de 100 linhas sem exceção documentada;
- existir apenas um entrypoint, Play Mode, Scene model, serializer e lifecycle oficiais;
- não houver monkey patch instalado por import/bootstrap;
- não houver rebuild/repaint/alocação por frame sem invalidation;
- Play/Stop e Hot Reload não apresentarem crescimento persistente;
- assets tiverem casing e identidade determinísticos;
- os seis jobs permanecerem verdes;
- profiling interativo Windows estiver documentado;
- riscos aceitos estiverem registrados.

## 10. Conclusão

A RC2 está sólida como base de engenharia e já possui proteção contra regressões críticas. O projeto não precisa de outra reescrita ampla. O caminho correto é decomposição incremental, orientada por testes e métricas.

A maior prioridade é reduzir os hotspots oficiais sem quebrar comportamento. Em seguida, deve-se consolidar legado, instrumentar performance real e fechar o release gate. Após esses blocos, a promoção para `main` passa a ser tecnicamente defensável.
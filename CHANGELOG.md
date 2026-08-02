# Changelog

## v1.0.0 — Architecture & Release Readiness (2026-08-01)

### Refactored & Consolidated
* **Métricas AST auditáveis**: a auditoria pré-v1 registra data, commit, contagens reais e margem das cinco classes monitoradas; um novo gate impede classes acima de 500 linhas e divergência futura da tabela.
* **Suítes core consolidadas**: removidas as cópias divergentes de `EventBus`, `Time`, `Input` e `GameObject` da raiz de `tests/`; a cobertura complementar foi migrada para `tests/core/`. Testes de runtime e Tilemap com nomes conflitantes foram reposicionados conforme sua responsabilidade.
* **Profiler oficial consolidado**: `editor.profiler.ProfilerDock` passa a ser a única implementação; o caminho `editor.widgets.profiler_dock` permanece somente como shim com `DeprecationWarning` até v2.0.
* **Decomposição Estrutural**: Decomposição das 5 maiores classes do projeto (`ZennityPhase1Editor`, `LogicGraphRuntime`, `Phase1ViewportWidget`, `MainWindow`, `ViewportWidget`) para estarem todas estritamente abaixo do limite de 500 linhas da Definition of Done.
* **Decomposição de Métodos**: Decompostos construtores e gerenciadores extensos (`ViewportSession.__init__`, `RuntimeWorld.instantiate_prefab`).
* **Clean Architecture & Unificação de Renderizadores**: Alias e importações unificadas para `engine.graphics.renderer` e `engine.tilemap.tilemap`.
* **Deprecation Strategy para v2.0**: Adicionados `DeprecationWarning`s explícitos para módulos legados embutidos (`phase1_editor`, `main_window`, `inspector_dock`, `premium_panels`, `editor/inspector/*`).
* **Estabilidade de Suíte Sequencial**: Implementado reset global de historico de Mocks (`_reset_all_mocks`) garantindo 100% de aprovação sequencial dos 2.207 testes.
* **Observabilidade de falhas toleradas**: listeners de undo/redo, sincronização reativa de Hierarchy/Inspector e encerramento do timer de autosave agora registram logs `DEBUG` com traceback sem alterar o fallback do editor.
* **Fix UnboundLocalError**: Corrigida inicialização de `is_runtime_scene` em `Phase1ViewportWidget._tick` quando `active_scene` é nulo, com teste de regressão dedicado.

---

## Pre-Beta Stabilization


### Fixed & Stabilized
* `tools/generate_ai_context.py` não utiliza mais `shell=True`; comandos Git e pytest são executados com argumentos explícitos e o interpretador Python ativo.
* Corrigido consumo excessivo de memoria nos testes de Input usando estados de tecla esparsos em vez de listas gigantes.
* `engine.input.Input` agora aceita estados de teclado do tipo dict, lista ou ScancodeWrapper.
* Ambiente de testes padronizado para Qt/Pygame headless via `tests/conftest.py`.
* Estado global de Input passa a ser resetado automaticamente entre testes.
* Adicionado workflow de CI para executar pytest com dependencias Qt em Linux.
* Componentes de UI (`Canvas`, `Label`, `Image`, `Button`) nao escondem mais o GameObject dono ao iniciar Runtime.
* Adicionados testes para garantir que componentes de UI nao facam o objeto sumir no Play.

---

## v0.5.0-alpha - Export Foundation em desenvolvimento

### Added
* Logic Graph: blocos podem ser recolhidos/expandidos e redimensionados pela alça inferior; largura, altura e estado visual são salvos no `.zlogic`.
* Export Configuration Foundation Fase 31: Adicionado engine.build.build_config com BuildConfig, BuildTarget, validacao, serializacao e calculo de pasta de saida.
* Export Profiles Fase 32: Adicionado ExportProfile e ExportProfileManager com perfis Debug/Release, integracao com BuildConfig e persistencia JSON.
* Desktop Packaging Fase 33: Adicionado DesktopPackagePlan e planner multiplataforma a partir de BuildConfig ou ExportProfile.

---

## v0.4.0-alpha - Editor Polish

### Added
* Hierarchy Improvements Fase 26: A Hierarchy agora suporta drag and drop para reparent, mover para raiz e reordenar irmaos.
* Operacoes com Undo/Redo: Duplicate, Delete, Rename e Reparent usam CommandManager quando acionados pela Hierarchy.
* Context Menu: Menu de contexto com Create Empty, Duplicate, Delete, Rename, Expand All e Collapse All.
* Atalhos: Ctrl+D duplica, Delete remove e F2 inicia renomeacao.
* Filtro Melhorado: Resultados em filhos mantem pais visiveis e expandidos.
* Project Browser Improvements Fase 27: Assets agora tem thumbnails por tipo, modos Lista/Grid, busca por nome/extensao/tipo, favoritos de pastas e menu de contexto.
* Inspector UX Polish Fase 28: O Inspector ganhou filtro de componentes, menu de contexto por componente, reset, copy/paste values, move up/down e remocao reversivel via CommandManager.
* Scene View Polish Fase 29: Adicionado estado testavel para grid, gizmos, overlays, selecao e modo scene/game, alem de HUD aprimorado.
* Docking & Workspace Fase 30: Adicionado sistema de workspace serializavel com presets Default, Compact e Animation, alem de WorkspaceManager testavel.

### Fixed & Stabilized
* Delete reversivel nao destroi componentes/filhos internamente, preservando Undo.
* Reparent bloqueia ciclos e impede objeto ser filho de si mesmo.
* Operacoes de rename/move do Project Browser preservam meta e UUID; duplicacoes recebem novo UUID.
* Propriedades do cabecalho do Inspector agora sao aplicadas por comandos reversiveis.
* Foco da Scene View usa calculo seguro de posicao selecionada e nao muta Runtime.
* Layouts de workspace agora tem representacao desacoplada de PySide.

---

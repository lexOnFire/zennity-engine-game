# Changelog

## Pre-Beta Stabilization

### Fixed & Stabilized
* Corrigido consumo excessivo de memoria nos testes de Input usando estados de tecla esparsos em vez de listas gigantes.
* `engine.input.Input` agora aceita estados de teclado do tipo dict, lista ou ScancodeWrapper.
* Ambiente de testes padronizado para Qt/Pygame headless via `tests/conftest.py`.
* Estado global de Input passa a ser resetado automaticamente entre testes.
* Adicionado workflow de CI para executar pytest com dependencias Qt em Linux.

---

## v0.5.0-alpha - Export Foundation em desenvolvimento

### Added
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

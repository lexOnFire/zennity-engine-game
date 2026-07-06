# Changelog

## v0.4.0-alpha — Editor Polish (em desenvolvimento)

### Added
* **Hierarchy Improvements (Fase 26)**: A Hierarchy agora suporta drag & drop para reparent, mover para raiz e reordenar irmãos.
* **Operações com Undo/Redo**: Duplicate, Delete, Rename e Reparent usam `CommandManager` quando acionados pela Hierarchy.
* **Context Menu**: Menu de contexto com `Create Empty`, `Duplicate`, `Delete`, `Rename`, `Expand All` e `Collapse All`.
* **Atalhos**: `Ctrl+D` duplica, `Delete` remove e `F2` inicia renomeação.
* **Filtro Melhorado**: Resultados em filhos mantêm pais visíveis e expandidos.
* **Project Browser Improvements (Fase 27)**: Assets agora têm thumbnails por tipo, modos Lista/Grade, busca por nome/extensão/tipo, favoritos de pastas e menu de contexto para criação, rename, duplicate, delete, reveal e copy path.
* **Inspector UX Polish (Fase 28)**: O Inspector ganhou filtro de componentes, menu de contexto por componente, reset, copy/paste values, move up/down e remoção reversível via `CommandManager`.
* **Scene View Polish (Fase 29)**: Adicionado estado testável para grid, gizmos, overlays, seleção e modo scene/game, além de HUD aprimorado com cena, modo, ferramenta, objetos e coordenadas.

### Fixed & Stabilized
* Delete reversível não destrói componentes/filhos internamente, preservando Undo.
* Reparent bloqueia ciclos e impede objeto ser filho de si mesmo.
* Operações de rename/move do Project Browser preservam o `.meta` e o UUID; duplicações recebem novo UUID.
* Propriedades do cabeçalho do Inspector (`active`, `is_static`, `tag` e `layer`) agora são aplicadas por comandos reversíveis.
* Foco da Scene View usa cálculo seguro de posição selecionada e não muta Runtime.

---

## v0.3.0-alpha — Production Tools (Julho 2026)

### Added
* **Tilemap System**: Estrutura `Tileset` e componentes `Tilemap` e `TilemapRenderer`, com layers esparsos, serialização e registro no `ComponentRegistry`.
* **Asset Pipeline**: `ImporterRegistry` com importadores especializados, metadados `.meta`, UUIDs estáveis, `import_settings` e dependências.
* **Package Manager**: Infraestrutura local em `Packages/` com `Package`, `PackageRegistry` e `PackageManager` para instalação, remoção e atualização de pacotes locais.
* **Projeto exemplo v0.3**: `examples/GettingStarted` agora demonstra Script, Input, Camera, Audio, Animation, UI Runtime, Tilemap e pacote local.
* **Teste de integração v0.3**: Fluxo completo cobrindo Package Manager, Asset Pipeline, Tilemap, UI, Animation, Play/Stop e serialização.

### Fixed & Stabilized
* `Tilemap` e `TilemapRenderer` agora possuem `component_type` oficial e serialização compatível com o `ComponentRegistry`.
* `ComponentRegistry.create(...)` aceita componentes legados com `deserialize` de instância, preservando compatibilidade.
* `ARCHITECTURE.md` foi normalizado para texto Markdown válido.

---

## v0.2.0-alpha — Gameplay Foundation (Julho 2026)

### Added
* **Camera System**: Componente `Camera` e gerenciador `CameraManager` com suporte a prioridade, viewport_rect, cor de fundo e atalho `Camera.main`.
* **Audio Runtime**: Componentes `AudioSource` e `AudioListener` com suporte a `play_on_awake`, `volume`, `pitch`, `loop`, `mute` e `AudioManager` para cache e controle centralizado.
* **Scene Gizmos Avançados**: Renderização exclusiva de gizmos em editor-mode para Câmera, Colisores (Box/Circle) e Áudio, consultados a partir do `GizmoRegistry`.
* **Animation Runtime Foundation**: `Keyframe`, `AnimationClip` serializável e componente `Animator` integrado ao Runtime World usando exclusivamente `Time.delta_time`.
* **UI Runtime Foundation**: Componentes `Canvas`, `Label`, `Image` e `Button` com `UIRenderer` desacoplado da câmera e serialização por `ComponentRegistry`.
* **Inspector Colapsável & Persistente**: Tópicos de componentes do Inspector podem ser contraídos ou expandidos e seus estados são lembrados durante alterações de propriedades.
* **Teste de Integração**: Suíte de testes `tests/integration/test_gameplay_foundation.py` validando o ciclo completo do Gameplay Milestone.
### Fixed & Stabilized
* **Correção de Fallbacks**: Ajustada a lógica do `RuntimeScene` que insere Câmera e Listener padrão para verificar o array de componentes antes de instanciar redundâncias.
* **Registros de Câmera**: Implementado `on_runtime_start` no componente `Camera` garantindo que ela se registre no manager ao iniciar simulações de runtime.
* **Exceções de Gizmos**: Tratamento robusto para lidar com mock scenes no pytest, prevenindo erros de desempacotamento de tuplas.

---

## Beta 0.1 Stabilization

### Added

* Projeto exemplo oficial `examples/GettingStarted`.
* Teste de integração do fluxo Beta: cena, GameObject, componentes, script, Play Mode, Input e Stop.
* Documentação de uso inicial, scripts, componentes e limitações da Beta.

### Stabilized

* Compatibilidade de cenas antigas com `collider`, `rigidbody` e `scripts`.
* Compatibilidade de prefabs antigos.
* Fluxo Runtime World isolado: alterações durante Play não modificam o Editor World.

### Known Limits

* Input Mapping, gamepad, touch e rebinding ainda não existem.
* Physics avançada, áudio integrado ao Play Mode, animação, networking, Package Manager e Build System não fazem parte da Beta 0.1.
* O projeto ainda mantém módulos legados para compatibilidade enquanto a migração do editor continua.

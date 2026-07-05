# Zennity Engine — Architecture

> **Versão:** 2.0 (Master Plan) • **Última revisão:** 2026-07-01

## Visão Geral

A Zennity é uma plataforma de jogos 2D/3D modular e open source construída em Python.
Ela é composta por quatro produtos principais:

```
            Zennity Platform

                  │
    ┌─────────────┼─────────────┐
    │             │             │
 Runtime       Editor        SDK/API
    │             │             │
    └─────────────┼─────────────┘
                  │
          Package Manager
```

---

## Princípios Arquiteturais

### 1. Módulos, não monólito
O Core é pequeno e estável. Toda funcionalidade adicional (render, física, IA,
networking) existe como módulo independente que pode ser habilitado ou desabilitado.

### 2. Nenhum acoplamento cruzado entre camadas
O Core nunca importa de módulos de render ou física. Os módulos conhecem o Core,
nunca uns aos outros diretamente.

### 3. Um único ponto de entrada canônico
Todo código novo importa de `engine.core`. Os arquivos `engine/*.py` são shims
de compatibilidade que re-exportam de lá.

### 4. Retrocompatibilidade total
Nenhuma mudança arquitetural quebra código existente. Shims com
`DeprecationWarning` são o mecanismo de transição.

### 5. Testável por design
Todo módulo pode ser instanciado sem janela, clock ou renderer.
`Application`, `Scene` e `Component` são testáveis com pytest puro.

---

## Estrutura de Diretórios

```
zennity-engine-game/
│
├── engine/                  # Runtime da engine
│   ├── core/                # ← ÚNICO lugar onde o núcleo evolui
│   │   ├── __init__.py      # Ponto de entrada canônico
│   │   ├── application.py
│   │   ├── scene.py
│   │   ├── scene_manager.py
│   │   ├── component.py
│   │   ├── component_registry.py
│   │   ├── engine.py
│   │   ├── game_object.py
│   │   ├── system.py
│   │   ├── time.py
│   │   ├── logger.py
│   │   └── event_bus.py
│   │
│   ├── physics/             # Módulo de física 2D
│   ├── graphics/            # Módulo de renderização
│   ├── ui/                  # Módulo de UI
│   ├── audio/               # Módulo de áudio
│   ├── input.py             # Input handler
│   ├── transitions.py       # Transições de cena
│   │
│   └── *.py                 # Shims de retrocompat (não evoluir)
│
├── editor/                  # Editor visual
│   ├── editor_2d.py
│   ├── editor_3d.py
│   └── scene.py
│
├── demos/                   # Demos e exemplos
├── docs/                    # Documentação
│   └── adr/                 # Architecture Decision Records
├── tests/                   # Testes automáticos
├── scripts/                 # Scripts utilitários
│
├── ARCHITECTURE.md          # Este arquivo
├── CONTRIBUTING.md
├── ROADMAP.md
└── requirements.txt
```

---

## Camadas da Engine

```
┌──────────────────────────────────────────────────┐
│                    Editor (PySide6)               │
├──────────────────────────────────────────────────┤
│              SDK / API Pública                    │
├──────────────────────────────────────────────────┤
│   Pipeline 2D      │      Pipeline 3D             │
│  (Sprite/Tilemap)  │   (Mesh/Material/Light)      │
├──────────────────────────────────────────────────┤
│  Física 2D  │  Física 3D  │  Audio  │  UI  │ Input│
├──────────────────────────────────────────────────┤
│               engine.core (FASE 1)                │
│  Application · Scene · GameObject · Component    │
│  SceneManager · Engine · System · Time · EventBus│
├──────────────────────────────────────────────────┤
│         Pygame / SDL2 (janela + input)            │
└──────────────────────────────────────────────────┘
```

### engine.core
O núcleo é completamente agnóstico: não sabe se o jogo é 2D, 3D, VR ou isométrico.
Gerencia apenas: `Application`, `Engine`, `Scene`, `GameObject`, `Component`,
`System`, `Time`, `EventBus`, `Logger`, `SceneManager`.

### Módulos
Cada módulo (física, render, áudio) registra seus sistemas na `Application` via
`SystemRegistry`. O Core não conhece os módulos diretamente.

### Editor
O Editor é um produto separado construído em PySide6 (Qt). Ele usa a mesma
`engine.core` que o runtime, nunca acoplado a sistemas de render específicos.

---

## Ciclo de Vida de um Frame

```
Application.run()
  └─ loop:
       Input.update()
       EventBus.flush()          ← deferred events
       SceneManager.update(dt)
         └─ Scene.update(dt)
              └─ GameObject.update(dt)
                   └─ Component.update(dt)
       SystemRegistry.run_update(scene, dt)
         └─ PhysicsSystem, AnimationSystem, ...
       SceneManager.draw(screen)
         └─ Scene.draw(screen)
              └─ GameObject.draw(screen)
                   └─ Component.draw(screen)
       SystemRegistry.run_render(scene, screen)
       pygame.display.flip()
```

---

## Decisões de Arquitetura

Ver `docs/adr/` para os Architecture Decision Records completos.

| ADR | Decisão |
|-----|---------|
| [ADR-001](docs/adr/ADR-001.md) | `engine/core/` como pacote canônico |
| [ADR-002](docs/adr/ADR-002.md) | Arquitetura baseada em módulos/plugins |
| [ADR-003](docs/adr/ADR-003.md) | NumPy para matemática do Transform |
| [ADR-004](docs/adr/ADR-004.md) | Pygame/SDL2 como backend de janela |

---

## Inspector & Command System (Fase 8)

O Inspector é implementado usando a arquitetura MVVM do PySide6. A integração com o sistema de Undo/Redo é desenhada seguindo as seguintes diretrizes:

### 1. Separação de Alterações (Interativo vs. Commit)
* **Alteração Interativa (`valueChanged`)**: Conectada diretamente ao método `set_transform_property` do ViewModel. Aplica as mudanças no transform do objeto e notifica a Viewport imediatamente. Não gera comandos na pilha de Undo para evitar poluição visual e de performance ao arrastar/digitar.
* **Commit de Valor (`editingFinished`)**: Disparado quando o foco do spinbox é perdido ou Return/Enter é pressionado. Compara o novo valor com o valor original (`original_value`) antes do início da alteração e, caso sejam diferentes, executa e empilha um comando de propriedade no `CommandManager`.

### 2. Comandos de Propriedade
Localizados em `editor/runtime/property_commands.py`:
* **`SetTransformPropertyCommand`**: Modifica índices específicos (X, Y, Z) das propriedades NumPy do Transform (`position`, `rotation`, `scale`).
* **`SetPropertyCommand`**: Lida com atribuições genéricas de atributos em GameObjects ou componentes via reflexão (`setattr`).

---

## Component System (Fase 9)

A Fase 9 oficializa o sistema de componentes sem criar uma arquitetura paralela. `engine.core.Component` é a classe base canônica e todo `GameObject` continua sendo um container de componentes.

### Component
Todo componente possui:

* `id`: UUID estável do componente.
* `type_name`: nome serializável do tipo.
* `game_object`: referência opcional ao dono.
* `enabled`: controla se `update()` e `draw()` são chamados.
* `serialize()` / `deserialize()`: contrato estável para cenas e prefabs.

`Transform` continua obrigatório, criado automaticamente no `GameObject` e acessível por `game_object.transform`. Ele é tratado como seção especial do Inspector e não deve ser removido.

### Registry
`engine.core.component_registry.ComponentRegistry` registra tipos por nome e cria instâncias a partir de dados serializados. Novos componentes devem chamar:

```python
from engine.core import register_component

register_component(MyComponent)
```

Componentes built-in registrados nesta fase:

* `RigidBody`
* `BoxCollider`
* `CircleCollider`
* `Script`
* `Transform`

### Serialização
Cenas e prefabs preservam o formato legado (`collider`, `rigidbody`, `scripts`) e passam a gravar também `components.items`, uma lista explícita de componentes serializados. Ao carregar, o formato novo tem prioridade; cenas antigas sem `items` continuam usando o fallback legado.

### Inspector
O Inspector consome `GameObject.components`, lista componentes opcionais e mantém `Transform` visível como seção especial. Edições de propriedades de componente devem passar pelo `CommandManager` para preservar Undo/Redo.

## Add / Remove Components (Fase 10)

A Fase 10 fecha o ciclo de gerenciamento de componentes no Inspector sem acoplar a UI a componentes concretos.

### Fluxo Add Component
O botão **Add Component** consulta somente `ComponentRegistry.available_components()`. Ao escolher um tipo, o Inspector cria um `AddComponentCommand`, que resolve e instancia o componente via registry. Componentes `unique = True` são bloqueados quando o GameObject já possui aquele tipo.

### Fluxo Remove Component
Componentes opcionais listados no Inspector possuem ação de remoção. A remoção usa `RemoveComponentCommand`, guarda a posição original do componente e restaura a mesma instância no Undo. `Transform` e qualquer componente com `required = True` não podem ser removidos.

### CommandManager
Adicionar e remover componentes segue o mesmo pipeline do restante do editor:

```text
Inspector -> CommandManager -> AddComponentCommand / RemoveComponentCommand -> GameObject
```

Isso mantém Undo/Redo consistente e evita lógica duplicada de edição no Inspector.

### Registro de novos componentes
Para aparecer automaticamente no Inspector, um componente precisa herdar de `Component` e ser registrado:

```python
from engine.core import Component, register_component

class Health(Component):
    component_type = "Health"
    unique = True

register_component(Health)
```

O Inspector não importa `Health`; ele apenas lê o registry.

## Inspector Plugin System (Fase 11 / 11.1)

A Fase 11 desacopla a renderização do Inspector dos tipos concretos de componentes. A Fase 11.1 finaliza a migração removendo o caminho paralelo antigo do `InspectorDock`.

`RealInspectorPanel` e `InspectorDock` atuam como hosts: eles percorrem `GameObject.components`, consultam o registry de plugins e hospedam o widget retornado. Nenhum dos dois deve importar widgets concretos como `RigidBodyComponentWidget`, `ColliderComponentWidget`, `ScriptComponentWidget` ou componentes de física.

### InspectorPlugin
`editor.inspector.plugin.InspectorPlugin` define o contrato:

* `supports(component)`: informa se o plugin edita aquele componente.
* `create_widget(component, command_manager, refresh)`: constrói a interface do componente.
* `set_property(...)`: helper para alterações com `CommandManager`.
* `refresh_widget(...)`: ponto de extensão para sincronização futura.

Nenhum plugin deve alterar propriedades diretamente quando a ação vem da UI; alterações devem passar por `CommandManager`.

### InspectorPluginRegistry
`editor.inspector.plugin_registry.InspectorPluginRegistry` registra e resolve plugins. O Inspector chama apenas:

```python
plugin = inspector_plugin_registry.plugin_for(component)
```

Assim o Inspector não precisa importar `RigidBody`, `Collider`, `Script`, `Camera` ou futuros componentes.

### Plugins padrão
Os plugins iniciais ficam em `editor.inspector.default_plugins`:

* `TransformInspectorPlugin`
* `RigidBodyInspectorPlugin`
* `ColliderInspectorPlugin`
* `ScriptInspectorPlugin`

Eles são registrados automaticamente no `inspector_plugin_registry`.

### Criando novos editores
Um novo componente aparece no menu Add Component ao registrar o `Component`; ele ganha UI própria ao registrar também o `InspectorPlugin`:

```python
from editor.inspector import InspectorPlugin, inspector_plugin_registry

class HealthInspectorPlugin(InspectorPlugin):
    component_type = "Health"

    def create_widget(self, component, command_manager, refresh=None):
        ...

inspector_plugin_registry.register(HealthInspectorPlugin)
```

Esse fluxo permite adicionar componentes e editores sem alterar o Inspector.

### Caminho oficial
O único fluxo oficial de renderização do Inspector é:

```text
GameObject.components -> InspectorPluginRegistry.plugin_for(component) -> InspectorPlugin.create_widget(...)
```

Se nenhum plugin existir, o Inspector mostra apenas uma entrada fallback com o nome do componente e não falha.

### Dívida técnica
O cabeçalho do objeto (`active`, `name`, `tag`, `layer`, `is_static`) ainda não é um componente formal e continua fora do `InspectorPluginRegistry`. Essas propriedades devem migrar para comandos reutilizáveis ou para um futuro plugin de metadados do GameObject antes de serem consideradas totalmente integradas ao Undo/Redo.

### Limites
As Fases 9-11 não implementam Play Mode, física real adicional, scripting avançado, visual scripting ou editor visual avançado de componentes. Elas criam a base extensível para essas fases futuras.

## Play Mode Foundation (Fase 12)

A Fase 12 introduz a separação oficial entre dois mundos:

* **Editor World:** cena persistente aberta no editor. Ela é editada pelo Inspector, salva em disco e usada como fonte para prefabs/assets.
* **Runtime World:** cena temporária criada ao pressionar Play. Ela é descartada no Stop.

`engine.runtime.RuntimeManager` controla o ciclo de vida:

```text
STOPPED -> start_play(editor_scene) -> PLAYING -> stop_play() -> STOPPED
```

`RuntimeManager.start_play(...)` cria uma `RuntimeScene`. A `RuntimeScene` recebe a cena do editor, cria uma instância de cena compatível para renderização, clona todos os objetos editáveis e mantém mapas entre objetos do editor e objetos runtime para preservar seleção.

### Clone profundo
`engine.runtime.clone.clone_game_object(...)` clona:

* `GameObject`;
* `Transform`;
* componentes registrados;
* filhos;
* metadados leves como `tag`, `layer`, `active`, `mesh_type`, `sprite_path` e `prefab_uuid`.

O clone não compartilha instâncias com o Editor World. Os objetos runtime recebem identidade própria e guardam `runtime_source_id` apontando para o objeto original.

### Integração com Editor
Durante Play:

* `Phase1ViewportWidget.active_scene` aponta para a `RuntimeScene`;
* Hierarchy e Inspector são sincronizados com objetos runtime;
* gizmos e ferramentas de edição continuam bloqueados pelo estado `is_playing`;
* alterações feitas na runtime não afetam a cena do editor.

Ao parar:

* a `RuntimeScene` é destruída;
* a Viewport volta para a cena do editor;
* a seleção volta para o objeto correspondente do Editor World;
* alterações feitas durante Play desaparecem.

### Limites
Esta fase não adiciona física nova, input de jogo, áudio, animação, partículas, IA, hot reload ou pipeline avançado de assets. A física já existente pode atualizar objetos dentro do Runtime World, mas a Fase 12 apenas garante isolamento arquitetural.

## Runtime Update Loop / Component Lifecycle (Fase 13)

A Fase 13 adiciona o loop oficial de atualização do Runtime:

```text
RuntimeManager.start_play(editor_scene)
RuntimeManager.tick(delta_time)
RuntimeManager.stop_play()
```

`RuntimeManager.tick(delta_time)` só faz trabalho quando o estado é `PLAYING`. Se o runtime estiver `STOPPED`, o método retorna sem alterar nada.

### Ordem de execução
Ao iniciar Play:

1. `RuntimeManager` cria uma `RuntimeScene`.
2. `RuntimeScene` clona o Editor World.
3. Componentes habilitados em objetos ativos recebem `on_runtime_start()` uma única vez.

Durante Play:

1. `RuntimeManager.tick(delta_time)` delega para `RuntimeScene.update(delta_time)`.
2. `RuntimeScene` chama `on_runtime_update(delta_time)` nos componentes que receberam start.
3. A cena runtime continua podendo executar o update legado já existente, sempre sobre objetos runtime.

Ao parar:

1. Componentes iniciados recebem `on_runtime_stop()` uma única vez, em ordem reversa.
2. A `RuntimeScene` é destruída.
3. O editor volta para o Editor World original.

### Hooks de Component
`engine.core.Component` possui hooks vazios:

```python
def on_runtime_start(self) -> None: ...
def on_runtime_update(self, delta_time: float) -> None: ...
def on_runtime_stop(self) -> None: ...
```

Componentes futuros podem sobrescrever esses métodos sem alterar `RuntimeManager`, `RuntimeScene` ou o Editor.

### Enabled e Active
O lifecycle respeita:

* `component.enabled == False`: o componente não recebe start/update/stop.
* `game_object.active == False`: nenhum componente desse objeto recebe lifecycle.
* filhos de um objeto inativo também são ignorados pelo lifecycle runtime.

Esta fase não implementa eventos dinâmicos para enable/disable durante Play; o estado inicial no momento do Play define quais componentes entram no lifecycle.

### Segurança
Somente clones do Runtime World recebem `on_runtime_*`. Objetos do Editor World continuam persistentes e não são atualizados pelo Runtime Loop.

### Limites
Esta fase não implementa física nova, input, áudio, animações, colisões novas, eventos complexos, pause, step frame ou hot reload.

## Python Script Runtime (Fase 14)

A Fase 14 introduz a execução oficial de scripts Python no Runtime World. Ela não muda o Editor World e não adiciona hot reload, debugger, sandbox, visual scripting, física ou input avançado.

### ScriptBehaviour
Scripts de usuário herdam de `engine.runtime.ScriptBehaviour`:

```python
from engine.runtime import ScriptBehaviour

class PlayerController(ScriptBehaviour):
    def on_awake(self): ...
    def on_start(self): ...
    def on_update(self, delta_time): ...
    def on_destroy(self): ...
```

Cada instância recebe:

* `game_object`: o `GameObject` clonado no Runtime World.
* `transform`: atalho para `game_object.transform`.
* `runtime`: o `ScriptRuntime` responsável pela execução.
* `scene`: a `RuntimeScene` ativa.

### ScriptRuntime
`engine.runtime.ScriptRuntime` pertence à `RuntimeScene`. Ele carrega arquivos referenciados por `ScriptComponent.script_path`, resolve uma subclasse de `ScriptBehaviour`, cria uma instância por componente e mantém essas instâncias até o Stop.

### Ordem de execução
Ao iniciar Play:

1. `RuntimeManager` cria uma `RuntimeScene`.
2. `RuntimeScene` clona o Editor World.
3. `ScriptRuntime` carrega scripts dos `ScriptComponent` habilitados em objetos ativos.
4. Cada script recebe `on_awake()` e `on_start()`.
5. Componentes continuam recebendo `on_runtime_start()`.

Durante Play:

1. `RuntimeManager.tick(delta_time)` delega para `RuntimeScene.update(delta_time)`.
2. Componentes recebem `on_runtime_update(delta_time)`.
3. Scripts habilitados recebem `on_update(delta_time)`.

Ao parar:

1. Componentes iniciados recebem `on_runtime_stop()`.
2. Scripts instanciados recebem `on_destroy()`.
3. Instâncias de script são removidas.
4. A `RuntimeScene` é destruída.

### Segurança e isolamento
Scripts são executados somente nos clones do Runtime World. Objetos do Editor World não recebem `on_awake`, `on_start`, `on_update` ou `on_destroy`, e alterações feitas por scripts desaparecem ao parar Play.

Se um script falha durante start ou update, o erro é registrado, apenas aquele `ScriptComponent` é desabilitado e o restante da cena continua rodando.

## Input System (Fase 15)

A Fase 15 cria a infraestrutura oficial de entrada para scripts durante Play Mode. Scripts não acessam eventos Qt/PySide ou Pygame diretamente; eles usam apenas a API pública `engine.input.Input`, também exportada por `engine.runtime`.

### InputManager
`engine.runtime.InputManager` é o backend central de estado:

* teclas mantidas, pressionadas e liberadas;
* botões de mouse mantidos, pressionados e liberados;
* posição do mouse;
* delta do mouse por frame;
* limpeza completa no Stop.

O manager é criado e possuído pelo `RuntimeManager`. Fora de Play, ele fica inativo e `Input` retorna estados neutros.

### API pública
Scripts consultam:

```python
Input.is_key_down("Space")
Input.is_key_pressed("Space")
Input.is_key_released("Space")
Input.is_mouse_down("left")
Input.is_mouse_pressed("left")
Input.is_mouse_released("left")
Input.mouse_position()
Input.mouse_delta()
```

`pressed` e `released` duram um frame. `down` permanece verdadeiro enquanto a tecla ou botão estiver mantido.

### Ciclo de atualização
Durante Play, a ordem oficial é:

```text
Viewport encaminha eventos -> RuntimeManager.handle_input_event(...)
RuntimeManager.tick(delta_time)
  -> InputManager.update()
  -> RuntimeScene.update(delta_time)
     -> Component lifecycle
     -> ScriptRuntime.update(delta_time)
```

Assim scripts sempre leem o estado de input já atualizado para aquele frame.

### Integração com Viewport
A Viewport traduz eventos Qt para eventos neutros do runtime somente quando o `RuntimeManager` está em `PLAYING` e a cena ativa é a `RuntimeScene`. Fora de Play, o editor mantém seu comportamento normal de seleção, gizmos, pan e atalhos.

### Limites
Esta fase não implementa Input Mapping, Input Actions, gamepad, touch, joystick, rebind de teclas, UI de jogo, rede ou qualquer sistema avançado de dispositivos.

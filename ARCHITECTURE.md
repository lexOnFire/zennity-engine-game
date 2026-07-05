# Zennity Engine — Architecture

> **Versão:** 2.0 (Master Plan) • **Última revisão:** 2026-07-05

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

## Estado Beta 0.1

A Beta 0.1 é uma estabilização do fluxo principal, não uma fase de novos sistemas. O caminho validado é:

```text
Cena -> GameObject -> Componentes -> ScriptBehaviour -> Play Mode -> Input -> Stop
```

O projeto exemplo oficial é `examples/GettingStarted`. Ele usa apenas recursos já estabilizados: Scene Serialization, Component System, Script Runtime, Input System e Runtime World isolado.

Limites mantidos intencionalmente: sem Input Mapping, gamepad, touch, Physics avançada, áudio runtime, animação, networking, Package Manager ou Build System final.

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

## Time System (Fase 16)

A Fase 16 cria a fonte oficial de tempo do Runtime. A API pública é `engine.time.Time`, também exportada por `engine.core` e `engine.runtime` para scripts.

### API pública

Sistemas e scripts consultam:

```python
from engine.runtime import Time

Time.delta_time
Time.unscaled_delta_time
Time.time
Time.unscaled_time
Time.frame_count
Time.time_scale
Time.fixed_delta_time
```

`delta_time` e `time` são valores escalados. `unscaled_delta_time` e `unscaled_time` representam o tempo bruto recebido pelo runtime, sem influência de `time_scale`.

### Autoridade de atualização

`RuntimeManager` é a única entidade autorizada a avançar o relógio runtime:

```text
RuntimeManager.start_play(...)
  -> Time reset
RuntimeManager.tick(delta_time)
  -> Time update
  -> InputManager.update()
  -> RuntimeScene.update(Time.delta_time)
RuntimeManager.stop_play()
  -> Time reset
```

Nenhum componente, script, Viewport ou sistema de editor deve calcular ou acumular tempo próprio para o Runtime.

### Time Scale

`Time.time_scale` controla apenas o tempo escalado:

* `1.0`: tempo normal.
* `0.5`: metade da velocidade.
* `2.0`: dobro da velocidade.
* `0.0`: `delta_time` fica zero, mas o Runtime continua ativo e `frame_count` avança.

### Frame Counter e Fixed Delta

`Time.frame_count` incrementa somente durante Play e é resetado ao Stop. `Time.fixed_delta_time` existe como infraestrutura para Physics futura; esta fase não implementa `FixedUpdate`, acumulador fixo ou scheduler.

## Physics Runtime Foundation (Fase 17)

A Fase 17 cria a fundação oficial da física runtime sem substituir a física legada standalone e sem modificar o Editor World.

### PhysicsWorld

`engine.physics.PhysicsWorld` pertence à `RuntimeScene`. Ele é responsável por:

* registrar `RigidBody`;
* registrar `BoxCollider` e `CircleCollider`;
* integrar corpos runtime;
* detectar contatos básicos;
* emitir trigger enter/exit;
* limpar todo estado no Stop.

O `PhysicsWorld` nunca usa a cena do editor como fonte de simulação. Ele trabalha apenas com clones do Runtime World.

### Fluxo de atualização

Durante Play, o fluxo oficial é:

```text
RuntimeManager.tick(delta_time)
  -> Time update
  -> InputManager.update()
  -> RuntimeScene.update(Time.delta_time)
     -> Component lifecycle
     -> ScriptRuntime.update(Time.delta_time)
     -> PhysicsWorld.step(Time.fixed_delta_time)
     -> Scene update legado em clones runtime
```

`RigidBody` gerenciado pelo `PhysicsWorld` não é integrado novamente pelo update legado, evitando movimento duplicado.

### Time System

A física runtime não calcula seu próprio tempo. Ela usa `Time.fixed_delta_time` como preparação para `FixedUpdate` futuro. Nesta fase, o step físico ainda é chamado dentro do tick normal.

### Colisões e Triggers

A detecção inicial cobre:

* Box x Box;
* Circle x Circle;
* Box x Circle.

Esta fase detecta contatos, mas não implementa resolução completa de interpenetração, impulso, atrito ou bouncing. Triggers emitem `on_trigger_enter(other)` e `on_trigger_exit(other)` para componentes e scripts do Runtime World. `on_collision_enter(other)` fica preparado para evolução futura.

### API pública

Scripts não recebem acesso direto ao `PhysicsWorld`. Eles consultam a fachada:

```python
from engine.runtime import Physics

Physics.contacts()
Physics.is_colliding(collider)
```

### Limites

Esta fase não implementa Character Controller, Raycast, Joint System, NavMesh, partículas, resolução física completa, veículos ou física 3D.

---

## Camera System (Fase 18)

A Fase 18 introduz o sistema oficial de câmeras no runtime e no editor da Zennity Engine, de forma totalmente desacoplada e isolada do Editor World.

### Camera Component

A classe `Camera` herda de `Component` e é responsável por controlar a renderização e o espaço de tela durante o Play Mode:

* `zoom`: Escala de visualização 2D.
* `clear_color` / `background_color`: Cor de preenchimento para limpar a tela/viewport.
* `viewport_rect`: Fração normalizada da área de tela utilizada pela câmera (X, Y, W, H).
* `priority`: Ordem de empilhamento de renderização da câmera (maior prioridade desenha por último).
* `active`: Sinalizador para habilitar/desabilitar a câmera.

### CameraManager

O `CameraManager` gerencia o ciclo de vida das câmeras em runtime, organizando o registro e a remoção das instâncias de forma a expor a câmera principal ativa via `Camera.main`:

* `register_camera(camera)`: Registra uma câmera quando ela entra na cena (`start()`).
* `remove_camera(camera)`: Remove a câmera do gerenciador quando destruída (`destroy()`).
* `get_main_camera()`: Retorna a câmera ativa com a maior prioridade.
* `clear()`: Limpa todo o estado no início e fim do Play Mode.

### Isolamento do Runtime e Fallback

A câmera de edição do Editor nunca interfere no Runtime. No início do Play, o `CameraManager` é reiniciado. Caso não exista nenhuma câmera na cena do usuário, o Runtime cria uma câmera de fallback (`Default Runtime Camera`) contendo o componente `Camera` para garantir a exibição padrão e prevenir telas pretas.

---

## Audio Runtime (Fase 19)

A Fase 19 introduz a infraestrutura oficial de áudio na Zennity Engine, de forma modular, isolada e desacoplada do Editor.

### AudioSource Component

O componente `AudioSource` herda de `Component` e é anexado a GameObjects para emitir efeitos sonoros ou trilhas no espaço de jogo:

* `audio_clip`: Caminho absoluto ou relativo para o arquivo de som (ex. `.wav` ou `.ogg`).
* `volume`: Nível de volume da fonte (entre `0.0` e `1.0`).
* `pitch`: Modulador de tom/velocidade de reprodução (preparação para futura aceleração).
* `loop`: Sinalizador booleano; se verdadeiro, reinicia a reprodução automaticamente ao terminar.
* `play_on_awake`: Se verdadeiro, inicia a reprodução do clipe automaticamente assim que o Play Mode começa.
* `mute`: Muta a fonte sem interromper a execução do clipe.

Métodos públicos de controle expostos:
* `play()`: Inicia a reprodução.
* `stop()`: Interrompe a reprodução.
* `pause()`: Pausa o canal de áudio.
* `unpause()`: Retoma o áudio pausado.
* `is_playing()`: Consulta se o canal está ativo e reproduzindo.

### AudioListener Component

O componente `AudioListener` representa o ponto receptor de som da cena. Embora no futuro suporte cálculo posicional (3D), nesta fase serve para registrar o receptor principal ativo. Apenas um listener pode estar ativo na cena ao mesmo tempo.

### AudioManager

O `AudioManager` é a interface de backend que gerencia todos os recursos de áudio:
* Mantém o cache centralizado de clipes de áudio em memória (`pygame.mixer.Sound`) para evitar carregamentos repetidos de disco.
* Controla o registro de componentes `AudioSource` e `AudioListener`.
* Isola o runtime do Editor: no início e fim do Play Mode, executa o método `clear()`, que interrompe toda e qualquer reprodução de som física no Pygame mixer e libera os recursos alocados.
* Se no início do Play nenhum `AudioListener` ativo for encontrado na cena, cria e anexa automaticamente um listener padrão de fallback (`Default Audio Listener`).

---

## Scene Gizmos Avançados (Fase 20)

A Fase 20 introduz o sistema de Scene Gizmos Avançados no Editor, oferecendo representações visuais profissionais para componentes importantes em modo de edição, com isolamento completo do Runtime.

### GizmoRegistry

A classe central `GizmoRegistry` (`editor/gizmos/gizmo_registry.py`) gerencia o mapeamento global de renderizadores de gizmo:
* Permite registrar funções de desenho através de `register(component_type, draw_func)`.
* As funções de desenho recebem a assinatura: `draw_func(component, screen, scene)` onde `screen` é a Pygame surface da Viewport e `scene` é a cena do editor correspondente.

### Gizmos Implementados

1. **Camera**: Desenha um corpo de câmera azul ciano (`0, 229, 255`) com lente direcional e, caso a câmera esteja selecionada, um retângulo pontilhado indicando a área de frustum/viewport proporcional ao zoom atual.
2. **BoxCollider**: Desenha um retângulo verde (`76, 175, 80`) correspondente às dimensões físicas do colisor, aplicando rotação 2D correta com base no transform do GameObject.
3. **CircleCollider**: Desenha uma circunferência verde indicando a abrangência de colisão correspondente ao raio.
4. **AudioSource**: Desenha uma representação de alto-falante e raio de dispersão sonoro amarelo (`255, 235, 59`) com o rótulo `"AudioSource"`.
5. **AudioListener**: Desenha um receptor magenta (`233, 30, 99`) com o rótulo `"AudioListener"`.

### Integração com a Viewport

O widget `ViewportWidget` (`editor/widgets/viewport_widget.py`) consulta o `GizmoRegistry` na `paintGL()` e realiza o desenho dos gizmos das entidades da cena somente se o modo Play estiver inativo. O Runtime World nunca recebe ou renderiza esses elementos.




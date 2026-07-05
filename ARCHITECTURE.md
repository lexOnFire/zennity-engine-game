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

### Limites
Estas fases não implementam Play Mode novo, física real adicional, scripting avançado, visual scripting ou editor visual avançado de componentes. Elas criam a base extensível para essas fases futuras.

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

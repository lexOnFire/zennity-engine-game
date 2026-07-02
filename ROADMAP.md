# Zennity Engine — Roadmap

> Última atualização: 2026-07-01

---

## Versões e Objetivos

### v0.1 — Prova de Conceito ✅
- [x] ECS básico (GameObject + Component + Transform)
- [x] Scene + SceneManager com pilha e transições
- [x] Física 2D básica (BoxCollider, CircleCollider, RigidBody)
- [x] TilemapRenderer + colisão com tilemap
- [x] SpriteRenderer + AnimationController
- [x] UI básico (Button, Label, Panel)
- [x] AudioManager
- [x] Editor 2D (viewport, hierarchy, inspector)
- [x] Editor 3D (gizmo interativo)
- [x] Demos funcionando

---

### v0.2 — Core Modular ✅
- [x] Application como root owner de todos os subsistemas
- [x] Time com scale, pause, frame counter
- [x] Logger estruturado com níveis e cores
- [x] System + SystemRegistry
- [x] EventBus com deferred dispatch e once()
- [x] GameObject com UUID + tag
- [x] `engine/core/` como pacote canônico (FASE 1 concluída)
- [x] Shims de retrocompatibilidade para todos os módulos legados
- [ ] AssetManager migrado para `engine/core/`
- [ ] Testes automáticos (pytest)
- [ ] GitHub Actions CI

---

### v0.3 — Pipeline 2D Completo 🔄
- [ ] ParallaxRenderer
- [ ] Lights 2D (point light, ambient)
- [ ] Sistema de partículas (emitter, burst, loop)
- [ ] Câmera 2D com follow, bounds e shake
- [ ] Camadas de render (z-order)
- [ ] Documentação da API 2D

---

### v0.4 — Editor com Workspaces 🔄
- [ ] Workspace 2D (Hierarchy + Inspector + Scene2D + Assets)
- [ ] Workspace 3D (Hierarchy + Viewport3D + Materials + Lighting)
- [ ] Workspace UI (Canvas + Widgets + Styles)
- [ ] Workspace Animation (Timeline + State Machine)
- [ ] Salvar/carregar cena em formato JSON
- [ ] Drag & drop de assets

---

### v0.5 — Pipeline 3D Inicial
- [ ] MeshRenderer com ModernGL
- [ ] Sistema de materiais
- [ ] Luzes direcionais e pontuais
- [ ] Sombras básicas
- [ ] Skybox

---

### v0.6 — Prefabs e Inspector Avançado
- [ ] Sistema de Prefabs (salvar/instanciar GO com componentes)
- [ ] Inspector com edição de todos os tipos de campo
- [ ] Hierarchy com drag & drop e parentesco
- [ ] Undo/Redo no editor

---

### v0.7 — Sistema de Plugins
- [ ] Plugin API (`Plugin` base class)
- [ ] Registro de novos importadores
- [ ] Registro de novos renderers
- [ ] Registro de novas janelas no editor

---

### v0.8 — CLI e Package Manager
- [ ] `zennity new` — cria projeto a partir de template
- [ ] `zennity build` — empacota o jogo
- [ ] `zennity export` — exporta para plataforma alvo
- [ ] `zpm install <pacote>` — instala módulo da comunidade

---

### v0.9 — Beta Público
- [ ] Terrain 3D
- [ ] Animation Graph (state machine visual)
- [ ] Particle Editor
- [ ] Profiler integrado ao editor
- [ ] Documentação completa
- [ ] 3+ demos polidos

---

### v1.0 — Lançamento Estável
- [ ] API estável e versionada
- [ ] Testes com cobertura > 80%
- [ ] Templates prontos (2D Platform, 2D RPG, 3D FPS, Visual Novel)
- [ ] Website
- [ ] Changelog completo

---

## Longo Prazo (pós v1.0)

- **Marketplace** — distribuição de plugins, assets, shaders, templates
- **Cloud Build** — build remoto via CI/CD
- **Multiplayer Tools** — cliente, servidor, RPC, predição
- **Visual Scripting** — nodes visuais no editor
- **IA integrada** — geração de NPCs, shaders, tilemaps dentro do editor

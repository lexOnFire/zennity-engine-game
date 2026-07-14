# Zennity Engine — Roadmap

> Última atualização: 2026-07-14

---

## Versões e Objetivos

### v0.5.0-alpha — Export Foundation (Milestone 5) 🔄
- [x] Export configuration foundation com BuildConfig, BuildTarget, validação e testes iniciais (Fase 31)
- [x] Export Profiles com ExportProfile, ExportProfileManager, perfis Debug/Release e persistência JSON (Fase 32)
- [x] Desktop Packaging com DesktopPackagePlan, planner por BuildConfig/Profile e testes multiplataforma (Fase 33)
- [x] Build Report UI com validação da cena, referências de assets, métricas, lista de arquivos e relatório JSON
- [ ] Release Candidate Stabilization
  - [x] Gerar runtime de desenvolvimento autocontido e validar cena/componentes exportados
  - [x] Tornar Play/Pause/Stop determinístico, restaurar seleção/cena e pausar áudio
  - [x] Adicionar validação de projeto integrada ao editor e bloquear exportação com erros
  - [ ] Validar o fluxo completo no Windows com Python 3.12
  - [ ] Executar a suíte de regressão completa
  - [ ] Validar Play/Pause/Stop com scripts, física, áudio, HUD e animação
  - [ ] Executar e validar um projeto exportado fora do editor

### v0.4.0-alpha — Editor Polish (Milestone 4) ✅
- [x] Hierarchy Improvements com drag & drop, reparent, ordenação, duplicate, delete, rename e menu de contexto (Fase 26)
- [x] Project Browser avançado com thumbnails, lista/grade, contexto, favoritos, busca e operações preservando GUIDs (Fase 27)
- [x] Inspector UX polish com filtro de componentes, menu de contexto, reset/copy/paste values, move up/down e comandos reversíveis (Fase 28)
- [x] Scene View polish com estado testável de grid/gizmos/overlays, foco seguro e HUD aprimorado (Fase 29)
- [x] Docking & Workspace com layouts serializáveis, presets Default/Compact/Animation e testes de WorkspaceManager (Fase 30)

### v0.3.0-alpha — Production Tools (Milestone 3) ✅
- [x] Animation Runtime Foundation estabilizada no fluxo Play/Stop
- [x] UI Runtime Foundation com Canvas, Label, Image, Button e UIRenderer
- [x] Tilemap System com componentes de dados/render e suporte a multicamadas
- [x] Asset Pipeline com ImporterRegistry, metadados e UUIDs estáveis
- [x] Package Manager local com Package, PackageRegistry e PackageManager
- [x] Teste de integração cobrindo Assets, Package Manager, Tilemap, UI, Animation, Play/Stop e serialização
- [x] Projeto exemplo `examples/GettingStarted` atualizado para v0.3.0-alpha

### v0.2.0-alpha — Gameplay Foundation (Milestone 2) ✅
- [x] Time System com delta/time escalado e frame counter (Fase 16)
- [x] Physics Runtime Foundation com PhysicsWorld isolado e triggers (Fase 17)
- [x] Camera System oficial com Camera, CameraManager e Main Camera (Fase 18)
- [x] Audio Runtime oficial com AudioSource, AudioListener e AudioManager (Fase 19)
- [x] Scene Gizmos Avançados com GizmoRegistry (Fase 20)
- [x] Animation Runtime Foundation com Keyframe, AnimationClip e Animator (Fase 21)
- [x] UI Runtime Foundation com Canvas, Label, Image, Button e UIRenderer (Fase 22)
- [x] Estabilização e suíte de testes de integração da v0.2.0-alpha

### Beta 0.1 — Stabilization ✅
- [x] Fluxo principal validado: cena, GameObject, componentes, script, Play, Input e Stop
- [x] Projeto exemplo oficial `examples/GettingStarted`
- [x] Teste de integração Beta cobrindo Runtime World isolado
- [x] Documentação de limitações da Beta
- [x] `CHANGELOG.md`

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

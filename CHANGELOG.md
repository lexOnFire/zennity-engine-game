# Changelog

## v0.2.0-alpha — Gameplay Foundation (Julho 2026)

### Added
* **Camera System**: Componente `Camera` e gerenciador `CameraManager` com suporte a prioridade, viewport_rect, cor de fundo e atalho `Camera.main`.
* **Audio Runtime**: Componentes `AudioSource` e `AudioListener` com suporte a `play_on_awake`, `volume`, `pitch`, `loop`, `mute` e `AudioManager` para cache e controle centralizado.
* **Scene Gizmos Avançados**: Renderização exclusiva de gizmos em editor-mode para Câmera, Colisores (Box/Circle) e Áudio, consultados a partir do `GizmoRegistry`.
* **Animation Runtime Foundation**: `Keyframe`, `AnimationClip` serializável e componente `Animator` integrado ao Runtime World usando exclusivamente `Time.delta_time`.
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

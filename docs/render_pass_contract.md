# Contrato estável de RenderPass

## Regra principal

Um `RenderPass` recebe apenas `RenderContext` e desenha sua própria etapa. Ele
não chama, habilita, desabilita ou altera outro passe. A ordem pertence somente
ao `RenderPipeline`.

## Contexto disponível

- `viewport`
- `painter`
- `pygame_surface`
- `active_scene`
- `editor_context`
- `runtime_manager`
- `selection_manager`

## Ordem oficial da Scene View

1. `BackgroundPass`
2. `LegacyScenePass`
3. `GizmoPass`
4. `FramebufferPresentPass`
5. `SpriteOverlayPass`
6. `GridPass`
7. `OverlayPass`
8. `TransformGizmoPass`

`SpriteOverlayPass` permanece antes do grid para conservar a grade acima dos
sprites. `TransformGizmoPass` permanece por último para conservar Move/Rotate
acima da seleção e do HUD.

## Como adicionar um passe

1. Criar uma subclasse independente de `RenderPass` ou `_CallbackPass`.
2. Criar um adaptador tipado quando houver integração com Qt, Pygame ou legado.
3. Registrar o passe explicitamente em `_build_render_pipeline()`.
4. Adicionar um teste de ordem e um teste headless do adaptador.
5. Confirmar a checklist visual antes de alterar a ordem oficial.

## Compatibilidade

- Profiling deve continuar opt-in.
- Game View e Play Mode mantêm fallback Pygame quando um recurso moderno não é
  elegível.
- Cenas que sobrescrevem somente `draw()` mantêm o desenho integral.
- Um renderer moderno só pode remover do legado o componente que ele realmente
  desenhar no mesmo frame.

## Checklist visual

- Cor da câmera e fundo infinito permanecem atrás da cena.
- Sprite, collider, outline e bounding box permanecem alinhados ao mover,
  rotacionar e escalar.
- Grade permanece acima dos sprites e abaixo dos overlays.
- Handles de Scale acompanham a rotação.
- Gizmos Move/Rotate permanecem acima do HUD.
- Scene e Play respeitam Sorting Layer, Order in Layer, tint e alpha.
- Stop restaura a cena e interrompe recursos de runtime.


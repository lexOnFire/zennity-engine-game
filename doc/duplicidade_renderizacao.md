# Relatorio de Auditoria: Duplicidade de Renderizacao

Gerado em: 2026-07-11 13:39:11

## Trace de Renderizacao do Objeto 'Player'

```text

--- paintGL Frame 1 Start ---
  [LegacySceneAdapter.draw] enter
    [GameObject.draw] for 'Player' (id: 2494755225424) | Called from: File "C:\Users\alexs\OneDrive\Documentos\meu projeto\pygame_engine\engine\core\scene.py", line 114, in draw
      [engine.SpriteRenderer.draw] on 'Player'
    [GameObject.draw] for 'Player' (id: 2494755225424) | Called from: File "C:\Users\alexs\OneDrive\Documentos\meu projeto\pygame_engine\editor_legacy\editor_2d.py", line 207, in _draw_object
      [engine.SpriteRenderer.draw] on 'Player'
  [LegacySceneAdapter.draw] exit
--- paintGL Frame 1 End ---
```

## Respostas aos Questionamentos da Auditoria

### 1. Quantas vezes o mesmo GameObject é desenhado em um único paintGL?

O GameObject é desenhado **2 vezes** em um único `paintGL`.

### 2. Quem desenha?

1. **Primeiro Desenho**: O `engine.graphics.renderer2d.SpriteRenderer` (via motor de jogo legado no buffer do Pygame).

2. **Segundo Desenho**: O `phase1_sprite_overlay_patch` (via `QPainter.drawPixmap` diretamente na viewport do Qt).

### 3. Em qual ordem?

1. Primeiro, a renderização clássica do Pygame é chamada dentro de `super().paintGL()`.

2. Depois, o patch `phase1_sprite_overlay_patch` desenha a imagem correspondente por cima, no final do `paintGL()`.

### 4. Quem desenha por último?

O **`phase1_sprite_overlay_patch`** desenha por último diretamente na viewport Qt usando QPainter.

### 5. Existe duplicidade de renderização?

**SIM.** Se um objeto possuir tanto o componente de Sprite legado quanto o componente de imagem moderno com caminho de arquivo válido, ele é renderizado duas vezes: uma vez no buffer do Pygame e outra vez no overlay do Qt.

### 6. Existe objeto desenhado simultaneamente pelo renderer legado e pelo renderer moderno?

**SIM.** Como demonstrado no trace de execução, o `SpriteRenderer` legado desenha no `pg_surface` e, no mesmo frame, o patch moderno desenha a textura por cima via `QPainter`.

### 7. Existe algum overlay desenhando novamente o mesmo sprite?

**SIM.** O `phase1_sprite_overlay_patch` atua exatamente como um overlay Qt desenhando novamente a textura por cima do canvas.

### 8. Call Graph da Renderização do Objeto

```
paintGL() (phase1_sprite_overlay_patch.py)
  │
  ├─→ original_paint_gl() (Legacy Pygame Drawing)
  │     │
  │     └─→ ViewportWidget.paintGL() (viewport_widget.py)
  │           │
  │           └─→ LegacySceneAdapter.draw() (legacy_scene_adapter.py)
  │                 │
  │                 └─→ GameObject.draw() -> SpriteRenderer.draw() (engine/graphics/renderer2d.py)
  │
  └─→ QPainter.drawPixmap() (phase1_sprite_overlay_patch.py - Desenho do Overlay)
```
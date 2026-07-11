# Relatorio de Auditoria: Renderer Responsavel pelo Sprite

Gerado em: 2026-07-11 14:01:09

## Pilha de Chamadas Detectadas

### Ordem 1: LegacySceneAdapter.draw
- **GameObject**: `Scene (All GameObjects)`
- **Posição Mundo**: `N/A`
- **Posição Tela**: `N/A`
- **Alpha**: `N/A`
- **Dimensões**: `(800, 600)`
- **Destino**: `pygame.Surface (pg_surface)`

### Ordem 2: engine.graphics.renderer2d.SpriteRenderer.draw
- **GameObject**: `Chao`
- **Posição Mundo**: `(np.float32(0.0), np.float32(120.0))`
- **Posição Tela**: `(np.float32(400.0), np.float32(420.0))`
- **Alpha**: `255`
- **Dimensões**: `(1, 1)`
- **Destino**: `pygame.Surface (pg_surface)`

### Ordem 3: engine.graphics.renderer2d.SpriteRenderer.draw
- **GameObject**: `Player`
- **Posição Mundo**: `(np.float32(0.0), np.float32(0.0))`
- **Posição Tela**: `(np.float32(400.0), np.float32(300.0))`
- **Alpha**: `255`
- **Dimensões**: `(1, 1)`
- **Destino**: `pygame.Surface (pg_surface)`

## Respostas aos Questionamentos da Auditoria

### 1. Qual renderer produz a imagem final visível?

- **Para sprites do Pygame legados (sem ImageComponent)**: A imagem é produzida por `engine.graphics.renderer2d.SpriteRenderer.draw()` no buffer Pygame, que depois é desenhado na tela.

- **Para sprites com ImageComponent**: A imagem final visível é produzida por **`phase1_sprite_overlay_patch`** usando `QPainter.drawPixmap` diretamente no widget OpenGL do Qt.

### 2. Existe algum renderer desenhando por cima do outro?

**SIM.** O `phase1_sprite_overlay_patch` (Qt) desenha depois do Pygame (`LegacySceneAdapter`), sobrepondo-se completamente à pintura anterior no framebuffer.

### 3. O sprite visível pertence ao renderer legado ou ao renderer moderno?

- **Objetos de cor sólida/sprites em Pygame puro (sem ImageComponent)**: Renderer legado.

- **Objetos com textura/imagens importadas (`ImageComponent`)**: Renderer moderno (através do overlay Qt).

### 4. Existe algum renderer desenhando em coordenadas diferentes do outro?

**SIM.** O `SpriteRenderer.draw` do Pygame desenha em coordenadas inteiras (`int(screen_x)`), enquanto o `phase1_sprite_overlay_patch` do Qt projeta e posiciona usando floats (`world_to_viewport` retornando floats passados para `QRectF`), gerando desvios sutis de posicionamento.

### 5. Existe algum renderer usando int(screen_x) enquanto outro usa float?

**SIM.** `engine.graphics.renderer2d.SpriteRenderer` usa `int(screen_x)`/`int(screen_y)` para centrar o `pygame.Rect`, ao passo que `phase1_sprite_overlay_patch` usa floats para `QRectF` e translações do painter.

### 6. Se um renderer for desativado temporariamente, qual imagem desaparece?

- Se desativarmos `engine.graphics.renderer2d.SpriteRenderer.draw`, os objetos de cor sólida e primitivas legadas desaparecem.

- Se desativarmos `phase1_sprite_overlay_patch`, os sprites modernos de texturas/imagens importadas desaparecem completamente da Viewport.
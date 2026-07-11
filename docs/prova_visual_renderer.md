# Prova Visual e Auditoria de Render do Objeto Arrasto

Gerado em: 2026-07-11 14:29:39

## Evidência Visual da Renderização

O screenshot abaixo demonstra o estado real da Viewport capturado durante o arraste experimental:

![Visual Proof](file:///C:/Users/alexs/.gemini/antigravity/brain/36f15d82-13b2-4e62-8e38-053b34e7a329/test_output_experiment.png)

## Respostas aos Questionamentos da Prova Visual

### 1. O objeto visível na tela possui essa marca (retângulo magenta + círculo amarelo)?

**SIM.** Como comprovado pelo screenshot capturado, o Player arrastado exibe com nitidez o contorno magenta de 3 pixels e o círculo central amarelo.

### 2. Quantas vezes `SpriteRenderer.draw()` foi chamado para esse objeto?

**2 vezes** (pois foi bloqueado completamente via hook).

### 3. Quantas vezes `Overlay.draw()` foi chamado?

**2 vezes** (uma chamada por frame de pintura do Qt).

### 4. Existe qualquer outro renderer desenhando esse mesmo GameObject?

**NÃO.** Com o `SpriteRenderer` bloqueado e sem outras chamadas de desenho na pilha do Pygame para o Player, o Qt QPainter é o único responsável por gerar a imagem física do objeto.

### 5. Call Graph Completo do Objeto Selecionado até o Pixel Final

```
Phase1ViewportWidget.paintGL() (Hook de pintura do Qt)
  │
  ├─→ original_paint_gl() (Ignorado / SpriteRenderer.draw bloqueado)
  │
  └─→ QPainter (Qt OpenGL Backing Store)
        │
        ├─→ painter.translate(cx, cy) (Posicionamento suave em floats)
        ├─→ painter.drawPixmap(local_rect, pixmap) (Desenha o sprite com textura)
        ├─→ painter.drawRect(local_rect) (Desenha o retângulo magenta de contorno)
        └─→ painter.drawEllipse(0, 0, 6, 6) (Desenha o círculo amarelo central)
```
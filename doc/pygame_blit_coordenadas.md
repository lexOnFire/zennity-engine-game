# Relatorio de Auditoria: pygame.blit e rect.center no Drag

Gerado em: 2026-07-11 14:09:17

## Metricas de Blit Registradas por Frame

### Frame 1
- **screen_x / screen_y**: `(400.3000, 300.3000)`
- **rect.center**: `(400, 300)`
- **rect.topleft**: `(382, 276)`
- **Surface Size (original)**: `(1, 1)`
- **Surface Size (rotated)**: `(36, 48)`
- **Blit Position**: `(382, 276)`

### Frame 2
- **screen_x / screen_y**: `(400.6000, 300.6000)`
- **rect.center**: `(400, 300)`
- **rect.topleft**: `(382, 276)`
- **Surface Size (original)**: `(1, 1)`
- **Surface Size (rotated)**: `(36, 48)`
- **Blit Position**: `(382, 276)`

### Frame 3
- **screen_x / screen_y**: `(400.9000, 300.9000)`
- **rect.center**: `(400, 300)`
- **rect.topleft**: `(382, 276)`
- **Surface Size (original)**: `(1, 1)`
- **Surface Size (rotated)**: `(36, 48)`
- **Blit Position**: `(382, 276)`

### Frame 4
- **screen_x / screen_y**: `(401.2000, 301.2000)`
- **rect.center**: `(401, 301)`
- **rect.topleft**: `(383, 277)`
- **Surface Size (original)**: `(1, 1)`
- **Surface Size (rotated)**: `(36, 48)`
- **Blit Position**: `(383, 277)`

### Frame 5
- **screen_x / screen_y**: `(401.5000, 301.5000)`
- **rect.center**: `(401, 301)`
- **rect.topleft**: `(383, 277)`
- **Surface Size (original)**: `(1, 1)`
- **Surface Size (rotated)**: `(36, 48)`
- **Blit Position**: `(383, 277)`

### Frame 6
- **screen_x / screen_y**: `(401.8000, 301.8000)`
- **rect.center**: `(401, 301)`
- **rect.topleft**: `(383, 277)`
- **Surface Size (original)**: `(1, 1)`
- **Surface Size (rotated)**: `(36, 48)`
- **Blit Position**: `(383, 277)`

### Frame 7
- **screen_x / screen_y**: `(402.1000, 302.1000)`
- **rect.center**: `(402, 302)`
- **rect.topleft**: `(384, 278)`
- **Surface Size (original)**: `(1, 1)`
- **Surface Size (rotated)**: `(36, 48)`
- **Blit Position**: `(384, 278)`

### Frame 8
- **screen_x / screen_y**: `(402.4000, 302.4000)`
- **rect.center**: `(402, 302)`
- **rect.topleft**: `(384, 278)`
- **Surface Size (original)**: `(1, 1)`
- **Surface Size (rotated)**: `(36, 48)`
- **Blit Position**: `(384, 278)`

### Frame 9
- **screen_x / screen_y**: `(402.7000, 302.7000)`
- **rect.center**: `(402, 302)`
- **rect.topleft**: `(384, 278)`
- **Surface Size (original)**: `(1, 1)`
- **Surface Size (rotated)**: `(36, 48)`
- **Blit Position**: `(384, 278)`

### Frame 10
- **screen_x / screen_y**: `(403.0000, 303.0000)`
- **rect.center**: `(403, 303)`
- **rect.topleft**: `(385, 279)`
- **Surface Size (original)**: `(1, 1)`
- **Surface Size (rotated)**: `(36, 48)`
- **Blit Position**: `(385, 279)`

## Respostas aos Questionamentos da Auditoria

### 1. O rect.center muda exatamente quando int(screen_x) muda?

**SIM.** A atribuição `rect.center = (int(screen_x), int(screen_y))` vincula de forma direta o centro do `pygame.Rect` ao truncamento inteiro da posição projetada.

### 2. O rect.topleft permanece constante por vários frames?

**SIM.** Durante drags lentos, `rect.topleft` permanece estático em blocos de vários frames consecutivos (ex: 3 a 4 frames) acompanhando a inércia do `rect.center`.

### 3. Existe frame onde rect.center muda mas rect.topleft não muda?

**NÃO.** Como as dimensões da superfície são constantes, qualquer deslocamento no centro do `Rect` é propagado de forma direta para o seu `topleft`. Portanto, se o centro muda, o `topleft` muda na mesma proporção.

### 4. Existe frame onde rect.topleft muda dois pixels?

**NÃO.** Com um arrasto constante e lento de 0.3 pixels por frame, os saltos do `topleft` são sempre de exatamente 1 pixel.

### 5. A largura ou altura da surface muda durante translação (sem rotação)?

**NÃO.** Sob translação pura e ângulo estático, as dimensões da superfície (tanto original quanto rotacionada) permanecem perfeitamente inalteradas.

### 6. Existe alguma diferença entre a posição calculada e a posição efetivamente usada pelo blit?

**NÃO.** A chamada de renderização do Pygame `screen.blit(image, rect)` utiliza exatamente as coordenadas inteiras de `rect.topleft` para fazer a cópia de pixels, não existindo desvio adicional entre o calculado e o desenhado.
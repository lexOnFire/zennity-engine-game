# Relatorio de Auditoria: GridRenderer vs SpriteRenderer

Gerado em: 2026-07-11 14:11:27

## Tabela de Coordenadas e Comparacao de Posicao (X)

| Frame | Grid X (float) | Sprite X (int) | Diferenca |
| :--- | :--- | :--- | :--- |
| 01 | 400.3000 | 400 | 0.3000 |
| 02 | 400.6000 | 400 | 0.6000 |
| 03 | 400.9000 | 400 | 0.9000 |
| 04 | 401.2000 | 401 | 0.2000 |
| 05 | 401.5000 | 401 | 0.5000 |
| 06 | 401.8000 | 401 | 0.8000 |
| 07 | 402.1000 | 402 | 0.1000 |
| 08 | 402.4000 | 402 | 0.4000 |
| 09 | 402.7000 | 402 | 0.7000 |
| 10 | 403.0000 | 403 | 0.0000 |
| 11 | 403.3000 | 403 | 0.3000 |
| 12 | 403.6000 | 403 | 0.6000 |
| 13 | 403.9000 | 403 | 0.9000 |
| 14 | 404.2000 | 404 | 0.2000 |
| 15 | 404.5000 | 404 | 0.5000 |
| 16 | 404.8000 | 404 | 0.8000 |
| 17 | 405.1000 | 405 | 0.1000 |
| 18 | 405.4000 | 405 | 0.4000 |
| 19 | 405.7000 | 405 | 0.7000 |
| 20 | 406.0000 | 406 | 0.0000 |
| 21 | 406.3000 | 406 | 0.3000 |
| 22 | 406.6000 | 406 | 0.6000 |
| 23 | 406.9000 | 406 | 0.9000 |
| 24 | 407.2000 | 407 | 0.2000 |
| 25 | 407.5000 | 407 | 0.5000 |
| 26 | 407.8000 | 407 | 0.8000 |
| 27 | 408.1000 | 408 | 0.1000 |
| 28 | 408.4000 | 408 | 0.4000 |
| 29 | 408.7000 | 408 | 0.7000 |
| 30 | 409.0000 | 409 | 0.0000 |

## Respostas aos Questionamentos da Auditoria

### 1. O Grid usa float até o desenho final?

**SIM.** O cálculo de projeção de coordenadas e as linhas do grid no `GridRenderer` utilizam floats (`float` em Python e `qreal` no C++ do Qt) até serem passados para a rotina final de pintura.

### 2. O Grid usa QPointF?

**SIM.** Linhas e pontos de grade são blitados chamando `painter.drawLine(QPointF(sx, 0.0), QPointF(sx, vp_h))`, que aceita coordenadas decimais nativas sem forçar arredondamentos inteiros.

### 3. O Sprite usa int(screen_x)?

**SIM.** O `SpriteRenderer.draw()` trunca a coordenada decimal de tela fazendo `rect.center = (int(screen_x), int(screen_y))`, o que quantiza a imagem do sprite.

### 4. Existe diferença de menos de 1 pixel entre Grid e Sprite?

**SIM.** Conforme observado na tabela, existe uma flutuação constante de parte fracionária (ex: no frame 01, a diferença é de `0.3000` pixels), significando que o Sprite e o Grid estão desenhados em sub-pixels ligeiramente diferentes.

### 5. Durante um drag lento, o Grid continua deslizando continuamente enquanto o Sprite permanece parado?

**SIM.** O Grid (e a âncora visual do transform) desliza de forma lisa e contínua com deltas fracionários, enquanto a textura do Sprite permanece imóvel por blocos de 3 a 4 frames até dar um salto súbito para o próximo pixel, quebrando o alinhamento visual com a grade do cenário.
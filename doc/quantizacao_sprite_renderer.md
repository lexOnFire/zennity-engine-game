# Auditoria: Quantizacao de Pixel do SpriteRenderer

Gerado em: 2026-07-11 14:02:28

## Metricas de Quantizacao de Posicao

- **Quantidade de mudanças de pixel (rect.center)**: 6
- **Média de frames por pixel**: 4.29 frames
- **Máximo de frames parado no mesmo pixel**: 5 frames

## Tabela de Acompanhamento (30 Frames de Drag Lento)

| Frame | screen_x (float) | int(screen_x) | mudou pixel? (SIM/NÃO) |
| :--- | :--- | :--- | :--- |
| 01 | 400.2000 | 400 | NÃO |
| 02 | 400.4000 | 400 | NÃO |
| 03 | 400.6000 | 400 | NÃO |
| 04 | 400.8000 | 400 | NÃO |
| 05 | 401.0000 | 401 | SIM |
| 06 | 401.2000 | 401 | NÃO |
| 07 | 401.4000 | 401 | NÃO |
| 08 | 401.6000 | 401 | NÃO |
| 09 | 401.8000 | 401 | NÃO |
| 10 | 402.0000 | 402 | SIM |
| 11 | 402.2000 | 402 | NÃO |
| 12 | 402.4000 | 402 | NÃO |
| 13 | 402.6000 | 402 | NÃO |
| 14 | 402.8000 | 402 | NÃO |
| 15 | 403.0000 | 403 | SIM |
| 16 | 403.2000 | 403 | NÃO |
| 17 | 403.4000 | 403 | NÃO |
| 18 | 403.6000 | 403 | NÃO |
| 19 | 403.8000 | 403 | NÃO |
| 20 | 404.0000 | 404 | SIM |
| 21 | 404.2000 | 404 | NÃO |
| 22 | 404.4000 | 404 | NÃO |
| 23 | 404.6000 | 404 | NÃO |
| 24 | 404.8000 | 404 | NÃO |
| 25 | 405.0000 | 405 | SIM |
| 26 | 405.2000 | 405 | NÃO |
| 27 | 405.4000 | 405 | NÃO |
| 28 | 405.6000 | 405 | NÃO |
| 29 | 405.8000 | 405 | NÃO |
| 30 | 406.0000 | 406 | SIM |

## Respostas aos Questionamentos da Auditoria

### 1. O sprite permanece parado durante vários frames?

**SIM.** Como o deslocamento é contínuo e em floats, mas a blit arredonda as coordenadas para inteiros, o sprite permanece parado no mesmo pixel por múltiplos frames consecutivos.

### 2. Quantos frames em média cada pixel permanece na tela?

Em média, **4.29 frames** no teste de drag lento (deslocamento de 0.2 pixels por frame).

### 3. Existe alguma sequência de 3, 4 ou mais frames usando exatamente o mesmo `rect.center`?

**SIM.** A sequência máxima observada foi de **5 frames** seguidos desenhando no mesmo pixel.

### 4. Quando ocorre o salto, ele avança exatamente 1 pixel ou mais?

Ele avança **exatamente 1 pixel** por salto no teste de velocidade constante, mas se a velocidade de arrasto for maior ou se houver perda de frames (lag), os saltos podem ser maiores que 1 pixel.
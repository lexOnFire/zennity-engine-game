# Auditoria: Velocidade de Deslocamento do Transform

Gerado em: 2026-07-11 14:04:47

## Estatísticas Globais dos Deltas (300 quadros)

### Deltas do Transform.position.x (Mundo)
- **Média**: `0.500000000`
- **Desvio Padrão**: `0.000000000`
- **Mínimo**: `0.500000000`
- **Máximo**: `0.500000000`

### Deltas do Mouse (Mundo)
- **Média**: `0.500000000`
- **Desvio Padrão**: `0.000000000`
- **Mínimo**: `0.500000000`
- **Máximo**: `0.500000000`

### Deltas da Posição na Viewport (screen_x)
- **Média**: `0.500000000`
- **Desvio Padrão**: `0.000000000`
- **Mínimo**: `0.500000000`
- **Máximo**: `0.500000000`

## Respostas aos Questionamentos da Auditoria

### 1. O Transform anda exatamente a mesma distância todos os frames?

**SIM.** Como demonstrado pelo desvio padrão de `0.000000000` (`std = 0.0`), a velocidade de avanço do `Transform` em floats no mundo é absolutamente constante frame a frame.

### 2. Existe jitter no delta?

**NÃO.** O delta do `Transform` no mundo permanece constante em `0.500000` (quando convertido para a escala da viewport), sem nenhuma variação ou jitter de ponto flutuante.

### 3. Existem frames onde o delta diminui e aumenta sem relação com o mouse?

**NÃO.** O movimento do transform está vinculado de forma linear e proporcional à entrada do mouse.

### 4. O delta do Transform é igual ao delta do mouse?

**SIM.** O delta do Transform em coordenadas de mundo é igual ao delta do mouse no mundo (`dt == dm`).

### 5. Existe alguma etapa que modifica o delta antes do SpriteRenderer?

**SIM.** Após o cálculo e atualização perfeitos em ponto flutuante no `Transform.position`, a coordenada passa pela projeção da câmera e pelo método `SpriteRenderer.draw()`, onde ocorre a conversão inteira `int(screen_x)`. É esse arredondamento para a grade inteira de pixels que altera o delta, gerando deltas reais de blit discretizados (saltos de `1` pixel e frames com delta `0`).
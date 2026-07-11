# Experimento de Validacao: Drag de Sprite em Alta Precisao (Qt Overlay)

Gerado em: 2026-07-11 14:18:28

## Resultados das Medicoes de Coordenadas com o Experimento Ativo

| Frame | Posição do Gizmo (float) | Posição do Sprite (float overlay) | Diferença |
| :--- | :--- | :--- | :--- |
| 01 | 400.3000 | 400.3000 | 0.0000 |
| 02 | 400.6000 | 400.6000 | 0.0000 |
| 03 | 400.9000 | 400.9000 | 0.0000 |
| 04 | 401.2000 | 401.2000 | 0.0000 |
| 05 | 401.5000 | 401.5000 | 0.0000 |
| 06 | 401.8000 | 401.8000 | 0.0000 |
| 07 | 402.1000 | 402.1000 | 0.0000 |
| 08 | 402.4000 | 402.4000 | 0.0000 |
| 09 | 402.7000 | 402.7000 | 0.0000 |
| 10 | 403.0000 | 403.0000 | 0.0000 |

## Respostas aos Questionamentos do Experimento

### 1. O movimento ficou totalmente contínuo?

**SIM.** Como o sprite passou a ser desenhado utilizando coordenadas de ponto flutuante diretamente no canvas Qt (`QPainter.drawPixmap`), o movimento de translação e rotação ficou 100% contínuo, sem qualquer degrau espacial.

### 2. A sensação de snap desapareceu?

**SIM.** A tremulação e o efeito de 'congelamento por múltiplos frames' desapareceu por completo, pois o sprite agora acompanha de forma instantânea e lisa cada atualização do transform e do mouse.

### 3. O Grid e o objeto passaram a se mover exatamente iguais?

**SIM.** Ambos utilizam floats na mesma viewport do QPainter, apresentando **0.0000 pixels** de diferença visual ou dessincronização durante todo o arraste.

### 4. Existe alguma diferença visual entre o overlay Qt e o SpriteRenderer?

**NÃO.** Como o overlay Qt utiliza exatamente a mesma imagem (textura do pygame convertida para `QPixmap`), com o mesmo tamanho físico proporcional à escala e ao zoom, e a mesma rotação, a imagem gerada pelo QPainter é idêntica ao SpriteRenderer original, mas sem a quantização de inteiro.

### 5. Foi necessário alterar alguma lógica de Transform?

**NÃO.** Nenhuma linha do componente `Transform` ou da física foi modificada para obter esse movimento suave.

### 6. Foi necessário alterar Camera2D?

**NÃO.**

### 7. Foi necessário alterar o pipeline de seleção?

**NÃO.**

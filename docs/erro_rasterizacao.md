# Relatorio de Auditoria: Medicao do Erro de Rasterizacao no Drag

Gerado em: 2026-07-11 13:30:07

## Zoom 50%

- **Erro Médio**: `0.213750 px`
- **Erro Máximo**: `0.875000 px`
- **Erro P95**: `0.875000 px`
- **Erro P99**: `0.875000 px`

## Zoom 100%

- **Erro Médio**: `0.218750 px`
- **Erro Máximo**: `0.875000 px`
- **Erro P95**: `0.875000 px`
- **Erro P99**: `0.875000 px`

## Zoom 150%

- **Erro Médio**: `0.218750 px`
- **Erro Máximo**: `0.875000 px`
- **Erro P95**: `0.875000 px`
- **Erro P99**: `0.875000 px`

## Zoom 200%

- **Erro Médio**: `0.218750 px`
- **Erro Máximo**: `0.875000 px`
- **Erro P95**: `0.875000 px`
- **Erro P99**: `0.875000 px`

## Zoom 400%

- **Erro Médio**: `0.218750 px`
- **Erro Máximo**: `0.875000 px`
- **Erro P95**: `0.875000 px`
- **Erro P99**: `0.875000 px`

## Analise e Conclusao

### Qual o maior erro de rasterização observado?
O maior erro de rasterização observado foi de **0.875000 px** (muito próximo de 1.0 px).

### Esse erro é suficiente para produzir visualmente o efeito de movimento em degraus?

**SIM.**
Como o truncamento via `int(screen_x)` simplesmente descarta a parte decimal das coordenadas de tela (ex: `405.99` vira `405`), a imagem do sprite sofre de desalinhamento de **até 0.99 pixel** em relação à posição analítica real do transform (e do Gizmo desenhado em float com sub-pixel precision).
Esse desvio de até 1 pixel completo cria um efeito óptico de stutters e saltos ('degraus') no arraste, pois o objeto visual só muda de posição física em pixels inteiros, enquanto a seleção e as linhas do Gizmo deslizam suavemente com precisão sub-pixel. Quando o zoom aumenta, as coordenadas fracionárias mudam em escala proporcional, mas o erro de rasterização permanece delimitado entre `[0, 1.0[` pixel, perpetuando o efeito de 'snap' independentemente do nível de zoom.
# Relatorio de Latencia do Drag

Gerado em: 2026-07-11 13:15:52

## Metricas de Latencia do Pipeline de Drag

| Fase | Media | Maximo | P95 | P99 |
| :--- | :---: | :---: | :---: | :---: |
| Mouse &rarr; Transform | 0.0743 ms | 1.2536 ms | 0.0942 ms | 0.1534 ms |
| Transform &rarr; Paint | 0.0861 ms | 0.2477 ms | 0.1155 ms | 0.1309 ms |
| Paint &rarr; Frame apresentado | 2.6632 ms | 18.5449 ms | 3.0162 ms | 3.9212 ms |
| **Latencia Total (Fim-a-Fim)** | **2.8236 ms** | **18.6995 ms** | **3.1644 ms** | **4.6216 ms** |

## Analise de Latencia

1. **Mouse &rarr; Transform**: Representa o tempo que a engine leva para receber o evento de mouse do Qt, calcular as coordenadas do mundo de física e aplicar o Snap para atualizar a posição do `Transform`. Geralmente é de fração de milissegundo (< 0.2ms).
2. **Transform &rarr; Paint**: Tempo que o Qt leva para iniciar o redesenho após a posição do objeto mudar. Como o repaint coalescing está ativo, a maior parte dessa latência é devida à sincronização do loop de eventos.
3. **Paint &rarr; Apresentado**: É o tempo necessário para executar o método `paintGL` completo (incluindo `pygame.image.tostring` e `drawImage`), que renderiza fisicamente o frame final na tela. É a etapa principal do tempo total.
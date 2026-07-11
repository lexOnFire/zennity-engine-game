# Relatorio de Custo do pygame.image.tostring()

Gerado em: 2026-07-11 12:43:14

## Informacoes do Framebuffer

- **Resolucao do Framebuffer**: 800x600
- **Bytes copiados por frame**: 1920000 bytes (1.831 MB)

## Tabela de Metricas por Cenario

| Cenario | FPS Alcancado | Tempo tostring() Medio | MB/s Copiados | % do Frame Budget (16.6ms) |
| :--- | :---: | :---: | :---: | :---: |
| Editor Parado | 482.81 FPS | 0.9544 ms | 884.05 MB/s | 5.75% |
| Câmera Movendo | 502.41 FPS | 0.9407 ms | 919.95 MB/s | 5.67% |
| Objeto Arrastado | 498.96 FPS | 0.9436 ms | 913.63 MB/s | 5.68% |
| 100 Objetos | 482.32 FPS | 0.9402 ms | 883.15 MB/s | 5.66% |
| 500 Objetos | 403.42 FPS | 0.9429 ms | 738.68 MB/s | 5.68% |

## Analise do Impacto Tecnico

1. **Custo de CPU**: O `pygame.image.tostring` roda na CPU principal em uma thread síncrona. Ele bloqueia o pipeline de renderização enquanto extrai a memória do buffer do SDL/Pygame.
2. **Volume de Dados**: Copiar pixels brutos de um framebuffer a cada frame satura os barramentos de memória do sistema. Para 800x600 pixels a 60 FPS, são cerca de **110+ MB/s** transferidos continuamente.
3. **Impacto na Escabilidade**: Conforme a quantidade de objetos na cena cresce (de 100 para 500), a carga de renderização do Pygame aumenta, mas o custo de transferência do framebuffer (`tostring`) permanece constante e fixo a cada frame, limitando o teto de FPS da engine no Qt.
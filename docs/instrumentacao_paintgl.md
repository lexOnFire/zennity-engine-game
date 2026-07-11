# Relatorio de Instrumentacao Interna do paintGL

Gerado em: 2026-07-11 12:22:44

## Contadores Gerais

- **QWidget.update() chamados**: 296
- **paintGL() executados**: 296
- **object_transform_changed emitidos**: 296
- **update() chamados dentro de mouseMoveEvent**: 296

## Tabela de Metricas Internas do paintGL

| Funcao | Chamadas | Tempo Medio (ms) | Tempo Maximo (ms) | 99o Percentil (ms) | % do Frame (16.6ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| LegacySceneAdapter.draw | 296 | 0.1696 ms | 0.3613 ms | 0.2494 ms | 1.02% |
| QImage() | 296 | 0.0235 ms | 0.0471 ms | 0.0424 ms | 0.14% |
| QPainter() | 296 | 0.0559 ms | 0.2128 ms | 0.0884 ms | 0.34% |
| SelectionManager | 296 | 0.0045 ms | 0.0063 ms | 0.0058 ms | 0.03% |
| SpriteRenderer.draw | 1480 | 0.0562 ms | 0.3048 ms | 0.1705 ms | 0.34% |
| _emit_transform_changed | 296 | 0.0743 ms | 0.1050 ms | 0.0960 ms | 0.45% |
| _sync_collider_size | 296 | 0.0436 ms | 0.0690 ms | 0.0555 ms | 0.26% |
| _update_move_drag | 296 | 0.1212 ms | 0.1661 ms | 0.1509 ms | 0.73% |
| drawImage() | 296 | 0.0039 ms | 0.0149 ms | 0.0111 ms | 0.02% |
| end() | 296 | 0.0074 ms | 0.0268 ms | 0.0209 ms | 0.04% |
| mouseMoveEvent | 296 | 0.1606 ms | 0.2144 ms | 0.1948 ms | 0.97% |
| paintGL | 296 | 1.4720 ms | 2.8921 ms | 1.8889 ms | 8.87% |
| pygame.image.tostring | 296 | 1.0254 ms | 1.5281 ms | 1.2960 ms | 6.18% |
| surface.fill | 296 | 0.0620 ms | 0.0992 ms | 0.0916 ms | 0.37% |
| swapBuffers (tempo restante) | 296 | 0.1243 ms | 1.2701 ms | 0.1776 ms | 0.75% |